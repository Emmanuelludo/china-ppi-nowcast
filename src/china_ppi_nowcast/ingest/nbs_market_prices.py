"""Collect and parse NBS circulation-price releases.

Discovery starts from the official NBS release-list archive. Raw HTML is immutable and
content-addressed. The parser deliberately leaves `exact_product_id` blank when no curated
dictionary match exists; it never invents continuity from names.
"""

from __future__ import annotations

import calendar
import hashlib
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import pandas as pd
from lxml import html as lxml_html

from china_ppi_nowcast.core.ids import observation_id, stable_hash


LIST_BASE = "https://www.stats.gov.cn/sj/zxfb/"
TITLE_PATTERN = re.compile(
    r"(?P<year>20\d{2})年(?P<month>1[0-2]|[1-9])月(?P<slot>上旬|中旬|下旬)"
    r"流通领域重要生产资料市场价格(?:变动)?情况"
)
CATEGORY_PATTERN = re.compile(r"^[一二三四五六七八九十]+、")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ChinaPPINowcast/0.1; research)"}


@dataclass(frozen=True)
class ReleaseLink:
    title: str
    url: str
    listing_date: str | None


def _fetch(url: str, timeout: int = 60) -> bytes:
    with urlopen(Request(url, headers=HEADERS), timeout=timeout) as response:
        return response.read()


def discover_release_links(page_count: int = 67) -> list[ReleaseLink]:
    """Discover canonical links from official NBS release listing pages."""

    found: dict[str, ReleaseLink] = {}
    pages: list[tuple[int, str]] = []
    for page in range(page_count):
        url = LIST_BASE if page == 0 else urljoin(LIST_BASE, f"index_{page}.html")
        pages.append((page, url))

    def parse_listing(item: tuple[int, str]) -> list[ReleaseLink]:
        _, url = item
        document = lxml_html.fromstring(_fetch(url))
        links: list[ReleaseLink] = []
        for anchor in document.xpath("//a[@href]"):
            title = "".join(anchor.itertext()).strip()
            title = re.sub(r"\s+", "", title)
            if not TITLE_PATTERN.search(title):
                continue
            absolute = urljoin(url, anchor.get("href"))
            parent_text = " ".join(anchor.getparent().itertext()) if anchor.getparent() is not None else ""
            date_match = re.search(r"20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}", parent_text)
            listing_date = date_match.group(0).replace("/", "-").replace(".", "-") if date_match else None
            links.append(ReleaseLink(title=title, url=absolute, listing_date=listing_date))
        return links

    with ThreadPoolExecutor(max_workers=min(16, page_count)) as pool:
        for links in pool.map(parse_listing, pages):
            for link in links:
                # The same link is commonly repeated for responsive layouts.
                found.setdefault(link.url, link)
    return sorted(found.values(), key=lambda item: item.title)


def _reference_dates(title: str) -> tuple[str, str, str]:
    match = TITLE_PATTERN.search(title)
    if not match:
        raise ValueError(f"unrecognized title: {title}")
    year, month, slot = int(match["year"]), int(match["month"]), match["slot"]
    if slot == "上旬":
        start, end, slot_code = 1, 10, "early"
    elif slot == "中旬":
        start, end, slot_code = 11, 20, "mid"
    else:
        start, end, slot_code = 21, calendar.monthrange(year, month)[1], "late"
    return f"{year:04d}-{month:02d}-{start:02d}", f"{year:04d}-{month:02d}-{end:02d}", slot_code


def _publication_date(payload: bytes, link: ReleaseLink) -> tuple[str, str]:
    document = lxml_html.fromstring(payload)
    candidates: list[str] = []
    for key in ("PubDate", "publishdate", "PublicationDate", "date"):
        candidates.extend(document.xpath(f"//meta[translate(@name,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='{key.lower()}']/@content"))
    text = " ".join(document.xpath("//text()"))
    candidates.extend(re.findall(r"20\d{2}[-年/]\d{1,2}[-月/]\d{1,2}", text[:12000]))
    if link.listing_date:
        candidates.append(link.listing_date)
    for candidate in candidates:
        normalized = candidate.strip().replace("年", "-").replace("月", "-").replace("日", "")
        normalized = normalized.replace("/", "-").replace(".", "-")
        match = re.search(r"(20\d{2})-(\d{1,2})-(\d{1,2})", normalized)
        if match:
            return f"{int(match[1]):04d}-{int(match[2]):02d}-{int(match[3]):02d}", "page_or_listing_date"
    # URL paths normally embed the page creation day, not necessarily the publication
    # day. It is a final conservative fallback and remains labelled.
    match = re.search(r"/t(20\d{6})_", link.url)
    if match:
        value = match.group(1)
        return f"{value[:4]}-{value[4:6]}-{value[6:8]}", "url_creation_date_fallback"
    raise ValueError("publication date not recoverable")


def _select_price_table(payload: bytes) -> pd.DataFrame:
    tables = pd.read_html(StringIO(payload.decode("utf-8", "replace")))
    candidates = [table for table in tables if table.shape[1] >= 4 and table.shape[0] >= 30]
    for table in candidates:
        names = "|".join(str(column) for column in table.columns)
        if "产品" in names and ("价格" in names or "本期" in names):
            return table.iloc[:, : min(5, table.shape[1])].copy()
    raise ValueError("no market-price table found")


def parse_release(link: ReleaseLink, payload: bytes, retrieved_at: datetime) -> tuple[dict[str, object], list[dict[str, object]]]:
    ref_start, ref_end, slot = _reference_dates(link.title)
    publication_date, date_precision = _publication_date(payload, link)
    available_at = pd.Timestamp(publication_date, tz="Asia/Shanghai") + pd.Timedelta(hours=9, minutes=30)
    content_sha = hashlib.sha256(payload).hexdigest()
    release_id = stable_hash([link.url, available_at.isoformat(), ref_start, ref_end, content_sha])
    release = {
        "source_release_id": release_id,
        "schema_version": "0.1.0",
        "source_agency": "National Bureau of Statistics of China",
        "source_language": "zh",
        "title": link.title,
        "canonical_source_url": link.url,
        "archive_url": "",
        "publication_datetime": available_at.isoformat(),
        "publication_date_precision": date_precision + "_time_scheduled_0930",
        "available_at": available_at.isoformat(),
        "reference_period_start": ref_start,
        "reference_period_end": ref_end,
        "reference_slot": slot,
        "vintage": "original_page_snapshot",
        "retrieval_datetime": retrieved_at.isoformat(),
        "content_sha256": content_sha,
        "http_status": 200,
        "parse_status": "parsed",
        "notes": "09:30 time inferred from contemporaneous NBS release-calendar convention",
    }
    table = _select_price_table(payload)
    table.columns = ["raw_product_name", "original_unit", "raw_price_text", "raw_change_text", "raw_pct_text"][: table.shape[1]]
    category = ""
    rows: list[dict[str, object]] = []
    source_row = 0
    for _, item in table.iterrows():
        name = str(item.iloc[0]).strip()
        if not name or name.lower() == "nan":
            continue
        if CATEGORY_PATTERN.match(name):
            category = name
            continue
        raw_price = pd.to_numeric(item.get("raw_price_text"), errors="coerce")
        raw_change = pd.to_numeric(item.get("raw_change_text"), errors="coerce")
        if pd.isna(raw_price):
            continue
        source_row += 1
        unit = "" if pd.isna(item.get("original_unit")) else str(item.get("original_unit")).strip()
        rows.append(
            {
                "observation_id": observation_id(release_id, source_row, name, "", unit),
                "source_release_id": release_id,
                "schema_version": "0.1.0",
                "source_row_number": source_row,
                "reference_period_start": ref_start,
                "reference_period_end": ref_end,
                "publication_datetime": available_at.isoformat(),
                "available_at": available_at.isoformat(),
                "raw_category_name": category,
                "raw_product_name": name,
                "raw_product_name_en": "",
                "specification": "",
                "original_unit": unit,
                "raw_price_text": str(item.get("raw_price_text")),
                "raw_price": float(raw_price),
                "raw_change_text": str(item.get("raw_change_text")),
                "raw_change": None if pd.isna(raw_change) else float(raw_change),
                "raw_pct_change": pd.to_numeric(item.get("raw_pct_text"), errors="coerce"),
                "exact_product_id": "",
                "source_url": link.url,
                "vintage": "original_page_snapshot",
                "observation_status": "observed",
                "parser_version": "0.1.0",
                "row_sha256": stable_hash([release_id, source_row, name, unit, raw_price, raw_change]),
            }
        )
    if not rows:
        release["parse_status"] = "parse_failed"
    return release, rows


def _download_one(link: ReleaseLink, raw_dir: Path, retrieved_at: datetime) -> tuple[dict[str, object], list[dict[str, object]], str | None]:
    try:
        payload = _fetch(link.url)
        digest = hashlib.sha256(payload).hexdigest()
        raw_path = raw_dir / f"{digest}.html"
        if not raw_path.exists():
            raw_path.write_bytes(payload)
        release, rows = parse_release(link, payload, retrieved_at)
        release["raw_path"] = str(raw_path)
        return release, rows, None
    except Exception as exc:  # source audit must preserve failures
        release = {
            "source_release_id": stable_hash([link.url, link.title, "fetch_or_parse_failure"]),
            "schema_version": "0.1.0",
            "source_agency": "National Bureau of Statistics of China",
            "source_language": "zh",
            "title": link.title,
            "canonical_source_url": link.url,
            "publication_datetime": "",
            "available_at": "",
            "reference_period_start": "",
            "reference_period_end": "",
            "vintage": "original_page_snapshot",
            "retrieval_datetime": retrieved_at.isoformat(),
            "parse_status": "failed",
            "notes": f"{type(exc).__name__}: {exc}",
        }
        return release, [], f"{type(exc).__name__}: {exc}"


def _missing_periods(releases: pd.DataFrame) -> pd.DataFrame:
    parsed = releases.loc[releases["parse_status"] == "parsed"].copy()
    if parsed.empty:
        return pd.DataFrame(columns=["reference_period", "status"])
    parsed["period"] = pd.to_datetime(parsed["reference_period_start"]).dt.to_period("M")
    present = set(zip(parsed["period"].astype(str), parsed["reference_slot"]))
    first, last = parsed["period"].min(), parsed["period"].max()
    rows = []
    for period in pd.period_range(first, last, freq="M"):
        for slot in ("early", "mid", "late"):
            if (str(period), slot) not in present:
                rows.append({"schema_version": "0.1.0", "reference_period": str(period), "reference_slot": slot, "status": "source_missing_or_undiscovered"})
    return pd.DataFrame(rows)


def collect_market_price_releases(root: Path, workers: int = 12, page_count: int = 67) -> dict[str, object]:
    raw_dir = root / "data/raw/nbs_market_prices/html"
    interim = root / "data/interim/nbs_market_prices"
    raw_dir.mkdir(parents=True, exist_ok=True)
    interim.mkdir(parents=True, exist_ok=True)
    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0)
    links = discover_release_links(page_count=page_count)
    releases: list[dict[str, object]] = []
    rows: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_download_one, link, raw_dir, retrieved_at): link for link in links}
        for future in as_completed(futures):
            release, observations, error = future.result()
            releases.append(release)
            rows.extend(observations)
            if error:
                failures.append({"source_url": futures[future].url, "error": error})
    release_frame = pd.DataFrame(releases).sort_values(["reference_period_start", "canonical_source_url"], na_position="last")
    observation_frame = pd.DataFrame(rows).sort_values(["reference_period_start", "source_row_number"])
    release_frame.to_csv(interim / "source_releases.csv", index=False)
    observation_frame.to_csv(interim / "raw_market_prices.csv", index=False)
    pd.DataFrame(failures, columns=["source_url", "error"]).to_csv(interim / "source_failures.csv", index=False)
    missing = _missing_periods(release_frame)
    missing.to_csv(interim / "missing_releases.csv", index=False)
    duplicates = observation_frame.loc[observation_frame.duplicated("observation_id", keep=False)] if not observation_frame.empty else observation_frame
    duplicates.to_csv(interim / "duplicate_revision_log.csv", index=False)
    return {
        "discovered_releases": len(links),
        "parsed_releases": int((release_frame["parse_status"] == "parsed").sum()),
        "raw_observations": len(observation_frame),
        "missing_periods": len(missing),
        "failures": len(failures),
    }

"""Discover, snapshot, and parse official NBS release pages."""

from __future__ import annotations

import json
import gzip
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from lxml import html

from ..registry import append_actuals
from ..schema import ACTUAL_COLUMNS, OBSERVATION_COLUMNS, ReleaseIdentity
from ..storage import atomic_write_csv, atomic_write_text, read_csv_or_empty, sha256_bytes
from ..time import CHINA_TZ, parse_release_title
from ..validation import validate_release

TEN_DAY_PHRASE = "流通领域重要生产资料市场价格"
PPI_TITLE_RE = re.compile(r"(20\d{2})年(\d{1,2})月份工业生产者出厂价格")
PUBLISHED_RE = re.compile(r"(20\d{2})[/-](\d{2})[/-](\d{2})\s+(\d{2}):(\d{2})")
PPI_MOM_RE = re.compile(
    r"环比(?:价格)?(?:均|分别|继续)?(上涨|下降)([0-9]+(?:\.[0-9]+)?)%"
)
PPI_MOM_FLAT_RE = re.compile(r"环比(?:价格)?(?:均|分别|继续)?持平")
CATEGORY_RE = re.compile(r"^[一二三四五六七八九十]+、")


@dataclass(frozen=True)
class ReleaseLink:
    title: str
    url: str
    kind: str


class NBSClient:
    def __init__(self, timeout: int = 30, retries: int = 3) -> None:
        self.timeout = timeout
        self.retries = retries
        self.headers = {
            "User-Agent": "china-ppi-nowcast/0.5 (+https://github.com/Emmanuelludo/china-ppi-nowcast)"
        }

    def fetch(self, url: str) -> bytes:
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                request = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return response.read()
            except (urllib.error.URLError, TimeoutError) as exc:
                last_error = exc
                if attempt + 1 < self.retries:
                    time.sleep(2**attempt)
        raise RuntimeError(f"failed to fetch {url}: {last_error}")

    @staticmethod
    def _index_url(index_url: str, page: int) -> str:
        return index_url if page == 0 else index_url.replace("index.html", f"index_{page}.html")

    def _discover_page(self, index_url: str, page: int) -> list[ReleaseLink]:
        url = self._index_url(index_url, page)
        document = html.fromstring(self.fetch(url), base_url=url)
        links: dict[str, ReleaseLink] = {}
        for anchor in document.xpath("//a[@href]"):
            title = " ".join(anchor.text_content().split())
            href = anchor.get("href")
            if not title or not href:
                continue
            if TEN_DAY_PHRASE in title and parse_release_title(title):
                kind = "ten_day"
            elif PPI_TITLE_RE.search(title):
                kind = "ppi"
            else:
                continue
            absolute = urllib.parse.urljoin(url, href)
            links[absolute] = ReleaseLink(title=title, url=absolute, kind=kind)
        return list(links.values())

    def discover(self, index_url: str, pages: int = 4, workers: int = 4) -> list[ReleaseLink]:
        links: dict[str, ReleaseLink] = {}
        with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
            futures = {executor.submit(self._discover_page, index_url, page): page for page in range(pages)}
            for future in as_completed(futures):
                for link in future.result():
                    links[link.url] = link
        return sorted(links.values(), key=lambda item: item.url)


def _cell_text(cell: object) -> str:
    return " ".join(cell.text_content().replace("\xa0", " ").split())


def _parse_published_at(document: object) -> datetime:
    text = " ".join(document.text_content().split())
    match = PUBLISHED_RE.search(text)
    if not match:
        raise ValueError("NBS page publication timestamp not found")
    parts = [int(value) for value in match.groups()]
    return datetime(*parts, tzinfo=CHINA_TZ)


def parse_ten_day_page(content: bytes, url: str, retrieved_at: datetime) -> pd.DataFrame:
    document = html.fromstring(content)
    title_nodes = document.xpath("//title | //h1 | //h2")
    title_text = " ".join(" ".join(node.text_content().split()) for node in title_nodes)
    if not title_text:
        title_text = " ".join(document.text_content().split())[:300]
    parsed = parse_release_title(title_text)
    if not parsed:
        raise ValueError("ten-day release month/window not found")
    release_month, window = parsed
    published_at = _parse_published_at(document)
    identity = ReleaseIdentity(release_month, window, published_at, url)

    table = None
    for candidate in document.xpath("//table"):
        head = " ".join(candidate.text_content().split())
        if "产品名称" in head and "本期价格" in head and "涨跌幅" in head:
            table = candidate
            break
    if table is None:
        raise ValueError("NBS product-price table not found")

    rows: list[dict[str, object]] = []
    category = ""
    digest = sha256_bytes(content)
    for tr in table.xpath(".//tr"):
        cells = [_cell_text(cell) for cell in tr.xpath("./th|./td")]
        if not cells:
            continue
        first = cells[0]
        if CATEGORY_RE.match(first):
            category = first
            continue
        if first in {"产品名称", "序号"} or len(cells) < 5:
            continue
        try:
            price, change, change_pct = (float(cells[2]), float(cells[3]), float(cells[4]))
        except (ValueError, IndexError):
            continue
        rows.append(
            {
                "release_id": identity.release_id,
                "release_month": release_month,
                "window": window.value,
                "category_cn": category,
                "product_name_cn": first,
                "unit_cn": cells[1],
                "price_cny": price,
                "change_cny": change,
                "change_pct": change_pct,
                "published_at": published_at.isoformat(),
                "retrieved_at": retrieved_at.astimezone(timezone.utc).isoformat(),
                "source_url": url,
                "content_sha256": digest,
            }
        )
    if not rows:
        raise ValueError("NBS product-price table contained no numeric observations")
    frame = pd.DataFrame(rows, columns=OBSERVATION_COLUMNS)
    duplicates = frame.duplicated(["product_name_cn", "unit_cn"], keep=False)
    if duplicates.any():
        names = frame.loc[duplicates, "product_name_cn"].tolist()
        raise ValueError(f"duplicate products in release: {names}")
    return frame


def parse_ppi_page(content: bytes, url: str, retrieved_at: datetime) -> dict[str, object]:
    document = html.fromstring(content)
    text = " ".join(document.text_content().split())
    title_match = PPI_TITLE_RE.search(text[:1000])
    if not title_match:
        raise ValueError("PPI target month not found")
    direction_match = PPI_MOM_RE.search(text)
    flat_match = PPI_MOM_FLAT_RE.search(text)
    if not direction_match and not flat_match:
        raise ValueError("headline PPI MoM value not found")
    if direction_match:
        direction, magnitude = direction_match.groups()
        value = float(magnitude)
        if direction == "下降":
            value = -value
    else:
        value = 0.0
    published_at = _parse_published_at(document)
    return {
        "target_month": f"{int(title_match.group(1)):04d}-{int(title_match.group(2)):02d}",
        "actual_mom_pct": value,
        "published_at": published_at.isoformat(),
        "retrieved_at": retrieved_at.astimezone(timezone.utc).isoformat(),
        "source_url": url,
        "content_sha256": sha256_bytes(content),
        "notes": "Official NBS headline PPI MoM parsed from release text.",
    }


def _store_snapshot(root: Path, link: ReleaseLink, content: bytes, retrieved_at: datetime) -> tuple[Path, bool]:
    digest = sha256_bytes(content)
    directory = root / "data" / "raw" / "nbs" / "objects"
    html_path = directory / f"{digest}.html.gz"
    meta_path = directory / f"{digest}.json"
    created = not html_path.exists()
    if created:
        directory.mkdir(parents=True, exist_ok=True)
        html_path.write_bytes(gzip.compress(content, compresslevel=9, mtime=0))
        atomic_write_text(
            meta_path,
            json.dumps(
                {
                    "title": link.title,
                    "url": link.url,
                    "kind": link.kind,
                    "retrieved_at": retrieved_at.astimezone(timezone.utc).isoformat(),
                    "content_sha256": digest,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        )
    return html_path, created


def _link_month(link: ReleaseLink) -> str:
    if link.kind == "ten_day":
        parsed = parse_release_title(link.title)
        return parsed[0] if parsed else ""
    match = PPI_TITLE_RE.search(link.title)
    return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}" if match else ""


def _ingest_links(
    root: Path,
    links: list[ReleaseLink],
    client: NBSClient,
    workers: int,
    skip_known_urls: bool,
) -> dict[str, object]:
    client = client or NBSClient()
    retrieved_at = datetime.now(timezone.utc)
    observations_path = root / "data" / "processed" / "nbs_ten_day_observations.csv.gz"
    actuals_path = root / "data" / "registry" / "actuals.csv"
    observations = read_csv_or_empty(observations_path, OBSERVATION_COLUMNS)
    actuals = read_csv_or_empty(actuals_path, ["source_url"])
    known_urls = set(observations.get("source_url", pd.Series(dtype=str)).astype(str))
    known_urls.update(actuals.get("source_url", pd.Series(dtype=str)).astype(str))
    pending = [link for link in links if not (skip_known_urls and link.url in known_urls)]
    counts: dict[str, object] = {
        "discovered": len(links), "pending": len(pending), "snapshots": 0,
        "observations": 0, "actuals": 0, "failed": 0, "errors": [], "warnings": [],
    }
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {executor.submit(client.fetch, link.url): link for link in pending}
        for future in as_completed(futures):
            link = futures[future]
            try:
                content = future.result()
                # Process and persist each completed page immediately. This makes
                # long historical runs genuinely resumable after interruption.
                _, created = _store_snapshot(root, link, content, retrieved_at)
                counts["snapshots"] = int(counts["snapshots"]) + int(created)
                digest = sha256_bytes(content)
                if link.kind == "ten_day":
                    already = not observations.empty and observations["content_sha256"].eq(digest).any()
                    if already:
                        continue
                    parsed = parse_ten_day_page(content, link.url, retrieved_at)
                    warnings = validate_release(parsed)
                    counts["warnings"].extend(
                        {"url": link.url, "warning": warning} for warning in warnings
                    )
                    observations = parsed.copy() if observations.empty else pd.concat([observations, parsed], ignore_index=True)
                    counts["observations"] = int(counts["observations"]) + len(parsed)
                    persisted = observations.drop_duplicates(
                        ["content_sha256", "product_name_cn", "unit_cn"], keep="last"
                    ).sort_values(["release_month", "window", "product_name_cn"])
                    atomic_write_csv(observations_path, persisted[OBSERVATION_COLUMNS])
                else:
                    row = parse_ppi_page(content, link.url, retrieved_at)
                    counts["actuals"] = int(counts["actuals"]) + append_actuals(actuals_path, [row])
            except Exception as exc:  # retain a resumable, inspectable failure list
                counts["failed"] = int(counts["failed"]) + 1
                counts["errors"].append({"url": link.url, "error": str(exc)})
    if counts["observations"]:
        observations = observations.drop_duplicates(["content_sha256", "product_name_cn", "unit_cn"], keep="last")
        observations = observations.sort_values(["release_month", "window", "product_name_cn"])
        atomic_write_csv(observations_path, observations[OBSERVATION_COLUMNS])
    return counts


def ingest_nbs(
    root: Path, index_url: str, pages: int = 4, client: NBSClient | None = None, workers: int = 4
) -> dict[str, object]:
    client = client or NBSClient()
    links = client.discover(index_url, pages, workers=workers)
    return _ingest_links(root, links, client, workers, skip_known_urls=False)


def ingest_nbs_history(
    root: Path,
    index_url: str,
    start_month: str,
    end_month: str,
    pages: int = 67,
    workers: int = 6,
    client: NBSClient | None = None,
) -> dict[str, object]:
    """Resumably ingest the full relevant range exposed by the NBS index."""
    start, end = pd.Period(start_month, freq="M"), pd.Period(end_month, freq="M")
    if start > end:
        raise ValueError("start_month must not be after end_month")
    client = client or NBSClient()
    discovered = client.discover(index_url, pages, workers=workers)
    links = [link for link in discovered if _link_month(link) and start <= pd.Period(_link_month(link)) <= end]
    result = _ingest_links(root, links, client, workers, skip_known_urls=True)
    result["archive_pages_scanned"] = pages
    result["requested_start_month"] = start_month
    result["requested_end_month"] = end_month
    months = sorted({_link_month(link) for link in links})
    result["source_range_start"] = months[0] if months else None
    result["source_range_end"] = months[-1] if months else None
    return result


def rebuild_actuals_from_snapshots(root: Path) -> dict[str, object]:
    """Reparse the actuals registry from immutable PPI snapshots after parser changes."""
    directory = root / "data" / "raw" / "nbs" / "objects"
    rows: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    for meta_path in sorted(directory.glob("*.json")):
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        if metadata.get("kind") != "ppi":
            continue
        digest = str(metadata["content_sha256"])
        gz_path = directory / f"{digest}.html.gz"
        plain_path = directory / f"{digest}.html"
        try:
            if gz_path.exists():
                content = gzip.decompress(gz_path.read_bytes())
            else:
                content = plain_path.read_bytes()
            retrieved_at = datetime.fromisoformat(str(metadata["retrieved_at"]))
            rows.append(parse_ppi_page(content, str(metadata["url"]), retrieved_at))
        except Exception as exc:
            errors.append({"url": str(metadata.get("url", "")), "error": str(exc)})
    if errors:
        return {"actuals_rebuilt": 0, "failed": len(errors), "errors": errors}
    frame = pd.DataFrame(rows, columns=ACTUAL_COLUMNS)
    frame = frame.drop_duplicates(["target_month", "content_sha256"], keep="last").sort_values(
        ["target_month", "published_at"]
    )
    atomic_write_csv(root / "data" / "registry" / "actuals.csv", frame)
    return {"actuals_rebuilt": len(frame), "failed": 0, "errors": []}

"""Discover, snapshot, and parse official NBS release pages."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from lxml import html

from ..registry import append_actuals
from ..schema import OBSERVATION_COLUMNS, ReleaseIdentity
from ..storage import atomic_write_csv, atomic_write_text, read_csv_or_empty, sha256_bytes
from ..time import CHINA_TZ, parse_release_title
from ..validation import validate_release

TEN_DAY_PHRASE = "流通领域重要生产资料市场价格"
PPI_TITLE_RE = re.compile(r"(20\d{2})年(\d{1,2})月份工业生产者出厂价格")
PUBLISHED_RE = re.compile(r"(20\d{2})[/-](\d{2})[/-](\d{2})\s+(\d{2}):(\d{2})")
PPI_MOM_RE = re.compile(r"环比(?:价格)?(上涨|下降|持平)([0-9]+(?:\.[0-9]+)?)?%?")
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

    def discover(self, index_url: str, pages: int = 4) -> list[ReleaseLink]:
        links: dict[str, ReleaseLink] = {}
        for page in range(pages):
            url = index_url if page == 0 else index_url.replace("index.html", f"index_{page}.html")
            document = html.fromstring(self.fetch(url), base_url=url)
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
    if not direction_match:
        raise ValueError("headline PPI MoM value not found")
    direction, magnitude = direction_match.groups()
    value = 0.0 if direction == "持平" else float(magnitude or "nan")
    if direction == "下降":
        value = -value
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
    directory = root / "data" / "raw" / "nbs" / retrieved_at.strftime("%Y-%m-%d")
    html_path = directory / f"{digest}.html"
    meta_path = directory / f"{digest}.json"
    created = not html_path.exists()
    if created:
        directory.mkdir(parents=True, exist_ok=True)
        html_path.write_bytes(content)
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


def ingest_nbs(root: Path, index_url: str, pages: int = 4, client: NBSClient | None = None) -> dict[str, int]:
    client = client or NBSClient()
    retrieved_at = datetime.now(timezone.utc)
    observations_path = root / "data" / "processed" / "nbs_ten_day_observations.csv"
    actuals_path = root / "data" / "registry" / "actuals.csv"
    observations = read_csv_or_empty(observations_path, OBSERVATION_COLUMNS)
    links = client.discover(index_url, pages)
    counts = {"discovered": len(links), "snapshots": 0, "observations": 0, "actuals": 0}
    for link in links:
        content = client.fetch(link.url)
        _, created = _store_snapshot(root, link, content, retrieved_at)
        counts["snapshots"] += int(created)
        digest = sha256_bytes(content)
        if link.kind == "ten_day":
            already = not observations.empty and observations["content_sha256"].eq(digest).any()
            if already:
                continue
            parsed = parse_ten_day_page(content, link.url, retrieved_at)
            validate_release(parsed)
            observations = pd.concat([observations, parsed], ignore_index=True)
            counts["observations"] += len(parsed)
        else:
            row = parse_ppi_page(content, link.url, retrieved_at)
            counts["actuals"] += append_actuals(actuals_path, [row])
    if counts["observations"]:
        atomic_write_csv(observations_path, observations[OBSERVATION_COLUMNS])
    return counts

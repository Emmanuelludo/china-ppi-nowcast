"""Fetch headline PPI from the post-2026 NBS UUID API.

The API is the current NBS statistical database snapshot, not a historical-vintage
archive. Exact first-release target vintages must be reconstructed from dated releases;
the output here is therefore suitable for a settled-target diagnostic and preliminary
model development, with an explicit vintage label.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd


API_URL = (
    "https://data.stats.gov.cn/dg/website/publicrelease/web/external/stream/esData"
)
ROOT_MONTHLY = "fc982599aa684be7969d7b90b1bd0e84"
HEADLINE_SERIES = {
    "headline_ppi_yoy": {
        "cid": "60e8b361f11c4a878c652a6487a25561",
        "indicator_id": "150633e52b9a470a9a9fd1b296dd6c5b",
        "series_name_en": "Producer ex-factory price index: year-on-year",
        "unit": "percent",
    },
    "headline_ppi_mom": {
        "cid": "677cfbb4f06941af8c1761c4804e58cf",
        "indicator_id": "e64079bae9064aebad1c4c5fe0c8a6ef",
        "series_name_en": "Producer ex-factory price index: month-on-month",
        "unit": "percent",
    },
}
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://data.stats.gov.cn/dg/website/page.html",
    "User-Agent": "Mozilla/5.0 (compatible; ChinaPPINowcast/0.1; research)",
}


def _request_payload(cid: str, indicator_id: str, start_year: int, end_year: int) -> bytes:
    body = {
        "cid": cid,
        "indicatorIds": [indicator_id],
        "daCatalogId": "",
        "das": [{"text": "全国", "value": "000000000000"}],
        "showType": "1",
        "dts": [f"{start_year}01MM-{end_year}12MM"],
        "rootId": ROOT_MONTHLY,
    }
    request = Request(
        API_URL,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=HEADERS,
        method="POST",
    )
    with urlopen(request, timeout=60) as response:
        return response.read()


def _parse_series(payload: bytes, series_id: str, retrieved_at: datetime) -> pd.DataFrame:
    document = json.loads(payload)
    if document.get("state") != 20000:
        raise RuntimeError(
            f"NBS API failure for {series_id}: state={document.get('state')} "
            f"message={document.get('message')}"
        )
    rows: list[dict[str, object]] = []
    meta = HEADLINE_SERIES[series_id]
    vintage = f"current_snapshot_{retrieved_at:%Y%m%dT%H%M%SZ}"
    for period in document.get("data", []):
        code = str(period.get("code", ""))
        digits = "".join(character for character in code if character.isdigit())
        if len(digits) < 6:
            continue
        month = pd.Timestamp(year=int(digits[:4]), month=int(digits[4:6]), day=1)
        raw_values = period.get("values", [])
        if not raw_values:
            continue
        raw = raw_values[0].get("value")
        if raw in (None, ""):
            continue
        index_value = float(raw)
        # API series are indexes with 100 as the comparison period.
        value = index_value - 100.0
        # Exact release calendars are a later vintage-reconstruction input. This
        # conservative upper bound prevents prior targets entering a model too early.
        conservative_available = (month + pd.offsets.MonthEnd(1) + pd.Timedelta(days=16))
        conservative_available = conservative_available.tz_localize("Asia/Shanghai")
        target_id = hashlib.sha256(
            f"{month:%Y-%m}|{series_id}|{vintage}".encode("utf-8")
        ).hexdigest()
        rows.append(
            {
                "target_id": target_id,
                "schema_version": "0.1.0",
                "month": month.date().isoformat(),
                "series_id": series_id,
                "series_name_zh": "工业生产者出厂价格指数",
                "series_name_en": meta["series_name_en"],
                "value": value,
                "raw_index_value": index_value,
                "unit": meta["unit"],
                "publication_datetime": "",
                "available_at": conservative_available.isoformat(),
                "availability_precision": "conservative_calendar_upper_bound",
                "vintage": vintage,
                "source_url": API_URL,
                "classification_version": "current_nbs_database_snapshot",
            }
        )
    return pd.DataFrame(rows).sort_values("month").reset_index(drop=True)


def fetch_headline_ppi(
    start_year: int = 2013,
    end_year: int | None = None,
) -> tuple[pd.DataFrame, dict[str, bytes]]:
    """Return settled/current-vintage headline MoM and YoY target observations."""

    end_year = end_year or datetime.now(timezone.utc).year
    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0)
    frames: list[pd.DataFrame] = []
    raw: dict[str, bytes] = {}
    for series_id, meta in HEADLINE_SERIES.items():
        payload = _request_payload(meta["cid"], meta["indicator_id"], start_year, end_year)
        raw[series_id] = payload
        frames.append(_parse_series(payload, series_id, retrieved_at))
    return pd.concat(frames, ignore_index=True), raw


def write_headline_targets(
    output_dir: Path,
    raw_dir: Path,
    start_year: int = 2013,
    end_year: int | None = None,
) -> pd.DataFrame:
    """Fetch and write current-snapshot targets plus immutable raw JSON bytes."""

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    frame, payloads = fetch_headline_ppi(start_year, end_year)
    vintage = frame["vintage"].iloc[0]
    for series_id, payload in payloads.items():
        digest = hashlib.sha256(payload).hexdigest()
        (raw_dir / f"{series_id}_{vintage}_{digest[:12]}.json").write_bytes(payload)
    frame.to_csv(output_dir / "headline_ppi_current_vintage.csv", index=False)
    return frame


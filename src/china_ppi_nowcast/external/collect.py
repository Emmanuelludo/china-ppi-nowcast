"""Reproducible collector for the public external benchmark panel."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

from .catalog import FRED_GRAPH, PUBLIC_SERIES, UNCOLLECTED_SERIES
from .ingest import monthly_external_features, parse_fred_csv


def _download(url: str) -> bytes:
    with urlopen(Request(url, headers={"User-Agent": "ChinaPPINowcast/0.1 research"}), timeout=90) as response:
        return response.read()


def collect_external_benchmarks(
    root: Path,
    start: str = "2000-01-01",
    end: str | None = None,
    retrieval_datetime: datetime | None = None,
) -> dict[str, object]:
    """Collect current snapshots and retain source and real-time limitations.

    Setting ``retrieval_datetime`` makes tests deterministic; it does not turn a
    current snapshot into a historical vintage.
    """

    retrieved = pd.Timestamp(retrieval_datetime or datetime.now(timezone.utc)).tz_convert("UTC")
    end = end or retrieved.date().isoformat()
    output_dir = root / "data/interim/external"
    output_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []
    log: list[dict[str, object]] = []
    for spec in PUBLIC_SERIES:
        url = FRED_GRAPH + "?" + urlencode({"id": spec.source_series_id, "cosd": start, "coed": end})
        payload = _download(url)
        digest = hashlib.sha256(payload).hexdigest()
        frame = parse_fred_csv(payload, spec, retrieved)
        frames.append(frame)
        log.append({"series_id": spec.series_id, "source_series_id": spec.source_series_id, "status": "collected", "raw_rows": len(frame), "first_date": frame["date"].min().date().isoformat(), "last_date": frame["date"].max().date().isoformat(), "content_sha256": digest, "request_url": url, "strict_backtest_eligible": spec.strict_backtest_eligible})
    raw = pd.concat(frames, ignore_index=True).sort_values(["date", "series_id"]).reset_index(drop=True)
    catalog = {item.series_id: item for item in PUBLIC_SERIES}
    monthly = monthly_external_features(raw, catalog)
    raw.to_csv(output_dir / "raw_external_observations.csv", index=False)
    monthly.to_csv(output_dir / "external_features_monthly.csv", index=False)
    for missing in UNCOLLECTED_SERIES:
        log.append({**missing, "strict_backtest_eligible": False})
    pd.DataFrame(log).to_csv(output_dir / "collection_log.csv", index=False)
    metadata = {
        "schema_version": "0.1.0",
        "retrieval_datetime": retrieved.isoformat(),
        "start": start,
        "end": end,
        "raw_rows": len(raw),
        "monthly_rows": len(monthly),
        "current_vintage_warning": "FRED graph downloads do not preserve historical release vintages. strict_backtest_eligible is false.",
    }
    (output_dir / "collection_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata

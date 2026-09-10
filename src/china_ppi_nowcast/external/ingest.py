"""Parsing and monthly aggregation for external benchmark observations."""

from __future__ import annotations

import hashlib
from io import BytesIO

import pandas as pd

from .catalog import ExternalSeries


SCHEMA_VERSION = "0.1.0"


def parse_fred_csv(payload: bytes, spec: ExternalSeries, retrieval_datetime: pd.Timestamp) -> pd.DataFrame:
    frame = pd.read_csv(BytesIO(payload))
    if frame.shape[1] != 2 or frame.columns[1] != spec.source_series_id:
        raise ValueError(f"unexpected FRED columns for {spec.source_series_id}: {list(frame.columns)}")
    frame = frame.rename(columns={frame.columns[0]: "date", frame.columns[1]: "value"})
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame.dropna(subset=["value"]).copy()
    frame["available_at"] = frame["date"] + pd.to_timedelta(spec.availability_lag_days, unit="D")
    frame["available_at"] = frame["available_at"].dt.tz_localize("UTC")
    frame["schema_version"] = SCHEMA_VERSION
    frame["series_id"] = spec.series_id
    frame["source_series_id"] = spec.source_series_id
    frame["unit"] = spec.unit
    frame["raw_frequency"] = spec.raw_frequency
    frame["source_agency"] = spec.source_agency
    frame["source_url"] = spec.source_url
    frame["retrieval_datetime"] = retrieval_datetime.isoformat()
    frame["vintage"] = "current_fred_snapshot_" + retrieval_datetime.strftime("%Y%m%dT%H%M%SZ")
    frame["strict_backtest_eligible"] = spec.strict_backtest_eligible
    frame["observation_id"] = [
        hashlib.sha256(f"{spec.series_id}|{date.date()}|{value}|{frame.iloc[i]['vintage']}".encode()).hexdigest()
        for i, (date, value) in enumerate(zip(frame["date"], frame["value"], strict=True))
    ]
    return frame[
        ["observation_id", "schema_version", "date", "series_id", "source_series_id", "value", "unit", "raw_frequency", "available_at", "vintage", "source_agency", "source_url", "retrieval_datetime", "strict_backtest_eligible"]
    ]


def monthly_external_features(raw: pd.DataFrame, catalog: dict[str, ExternalSeries]) -> pd.DataFrame:
    """Aggregate without making an unavailable value appear earlier than its inputs."""

    parts: list[pd.DataFrame] = []
    for series_id, group in raw.groupby("series_id", sort=False):
        spec = catalog[series_id]
        work = group.copy()
        work["month"] = pd.to_datetime(work["date"]).dt.to_period("M").dt.to_timestamp()
        if spec.aggregation == "monthly_mean":
            result = work.groupby("month", as_index=False).agg(value=("value", "mean"), available_at=("available_at", "max"), raw_observation_count=("value", "size"))
        elif spec.aggregation == "as_reported":
            if work.duplicated("month").any():
                raise ValueError(f"multiple monthly observations for {series_id}")
            result = work[["month", "value", "available_at"]].copy()
            result["raw_observation_count"] = 1
        else:
            raise ValueError(f"unknown aggregation {spec.aggregation}")
        result["schema_version"] = SCHEMA_VERSION
        result["series_id"] = series_id
        result["unit"] = spec.unit
        result["vintage"] = group["vintage"].iloc[0]
        result["source_url"] = spec.source_url
        result["source_agency"] = spec.source_agency
        result["strict_backtest_eligible"] = bool(spec.strict_backtest_eligible)
        result["aggregation"] = spec.aggregation
        parts.append(result)
    output = pd.concat(parts, ignore_index=True).rename(columns={"month": "date"})
    return output[["schema_version", "date", "series_id", "value", "unit", "available_at", "vintage", "source_url", "source_agency", "strict_backtest_eligible", "aggregation", "raw_observation_count"]].sort_values(["date", "series_id"]).reset_index(drop=True)

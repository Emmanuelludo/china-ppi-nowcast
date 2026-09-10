"""Pseudo-real-time data guards."""

from __future__ import annotations

import pandas as pd


def _utc(value: object) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    return stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")


def asof_filter(frame: pd.DataFrame, cutoff: object, available_column: str = "available_at") -> pd.DataFrame:
    if available_column not in frame:
        raise KeyError(f"required real-time column missing: {available_column}")
    available = pd.to_datetime(frame[available_column], utc=True, errors="coerce")
    if available.isna().any():
        raise ValueError("unparseable or missing available_at")
    return frame.loc[available <= _utc(cutoff)].copy()


def assert_realtime_safe(frame: pd.DataFrame, cutoff: object, available_column: str = "available_at") -> None:
    if len(asof_filter(frame, cutoff, available_column)) != len(frame):
        raise AssertionError("look-ahead detected")


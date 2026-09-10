"""Construction and validation of early, mid and final public-data cutoffs."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class VintageCutoff:
    target_month: pd.Timestamp
    forecast_vintage: str
    forecast_cutoff: pd.Timestamp


def infer_vintage_cutoffs(releases: pd.DataFrame, target_month: str | pd.Timestamp) -> list[VintageCutoff]:
    """Return cutoffs from the first, second and latest public release in a month.

    The function does not manufacture dates from processing timestamps.  If fewer
    than three releases are public, only genuinely available vintages are returned.
    """

    required = {"reference_period_end", "available_at"}
    missing = required.difference(releases.columns)
    if missing:
        raise ValueError(f"releases missing required columns: {sorted(missing)}")
    month = pd.Timestamp(target_month).to_period("M").to_timestamp()
    frame = releases.copy()
    frame["reference_period_end"] = pd.to_datetime(frame["reference_period_end"])
    frame["month"] = frame["reference_period_end"].dt.to_period("M").dt.to_timestamp()
    frame["available_at"] = pd.to_datetime(frame["available_at"], utc=True)
    dates = frame.loc[frame["month"].eq(month), "available_at"].drop_duplicates().sort_values()
    labels = ("early", "mid")
    result = [VintageCutoff(month, labels[index], value) for index, value in enumerate(dates.iloc[:2])]
    if len(dates) >= 3:
        result.append(VintageCutoff(month, "final", dates.iloc[-1]))
    return result


def assert_public_cutoff(frame: pd.DataFrame, cutoff: str | pd.Timestamp) -> None:
    """Raise if a constructed vintage contains a source that was not yet public."""

    if "available_at" not in frame:
        raise ValueError("frame missing available_at")
    boundary = pd.Timestamp(cutoff)
    boundary = boundary.tz_localize("UTC") if boundary.tzinfo is None else boundary.tz_convert("UTC")
    values = pd.to_datetime(frame["available_at"], utc=True)
    if values.gt(boundary).any():
        raise ValueError("feature vintage contains observations after forecast_cutoff")

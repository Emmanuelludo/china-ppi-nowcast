"""Leakage-safe empirical forecast intervals."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from .realtime import _one_timestamp_utc


def add_pseudo_realtime_intervals(
    forecasts: pd.DataFrame,
    *,
    alpha: float = 0.20,
    min_vintage_n: int = 12,
    min_pooled_n: int = 24,
    forecast_col: str = "forecast",
    actual_col: str = "actual",
    forecast_cutoff_col: str = "forecast_cutoff",
    actual_available_at_col: str = "primary_actual_available_at",
    vintage_col: str = "forecast_vintage",
    pool_keys: Sequence[str] = ("model_id", "target_series_id", "shock_scenario"),
) -> pd.DataFrame:
    """Add sequential empirical intervals using only already-released errors.

    Calibration first uses residuals from the same nowcast vintage. If that history
    is too short it may use all vintages within ``pool_keys``. The fallback is always
    exposed in ``interval_calibration_scope``; it is never silently presented as a
    vintage-specific interval.
    """

    if not 0 < alpha < 1:
        raise ValueError("alpha must lie strictly between 0 and 1")
    if min_vintage_n < 1 or min_pooled_n < 1:
        raise ValueError("minimum calibration sizes must be positive")
    required = {
        forecast_col,
        actual_col,
        forecast_cutoff_col,
        actual_available_at_col,
        vintage_col,
        *pool_keys,
    }
    missing = required.difference(forecasts.columns)
    if missing:
        raise ValueError(f"forecasts missing interval columns: {sorted(missing)}")

    out = forecasts.copy()
    out["_cutoff"] = out[forecast_cutoff_col].map(_one_timestamp_utc)
    out["_actual_available"] = out[actual_available_at_col].map(_one_timestamp_utc)
    out["_residual"] = out[actual_col] - out[forecast_col]
    out["lower_bound"] = np.nan
    out["upper_bound"] = np.nan
    out["interval_alpha"] = alpha
    out["interval_calibration_scope"] = "unavailable"
    out["interval_calibration_n"] = 0

    for idx, row in out.sort_values("_cutoff", kind="stable").iterrows():
        known = out.loc[
            out["_actual_available"].notna()
            & out["_actual_available"].le(row["_cutoff"])
            & out["_cutoff"].lt(row["_cutoff"])
            & out["_residual"].notna()
        ]
        for key in pool_keys:
            known = known.loc[known[key].eq(row[key])]
        vintage_known = known.loc[known[vintage_col].eq(row[vintage_col])]
        if len(vintage_known) >= min_vintage_n:
            calibration = vintage_known
            scope = "vintage_specific"
        elif len(known) >= min_pooled_n:
            calibration = known
            scope = "pooled_vintages"
        else:
            continue
        q_low, q_high = calibration["_residual"].quantile(
            [alpha / 2, 1 - alpha / 2]
        )
        out.loc[idx, "lower_bound"] = row[forecast_col] + q_low
        out.loc[idx, "upper_bound"] = row[forecast_col] + q_high
        out.loc[idx, "interval_calibration_scope"] = scope
        out.loc[idx, "interval_calibration_n"] = len(calibration)
    return out.drop(columns=["_cutoff", "_actual_available", "_residual"])

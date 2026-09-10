"""Forecast evaluation metrics based on first-release actuals."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from .turning_points import turning_point_metrics


def forecast_metrics(
    frame: pd.DataFrame,
    *,
    actual_col: str = "actual",
    forecast_col: str = "forecast",
    date_col: str = "target_month",
) -> dict[str, float | int | str]:
    """Compute the required point-forecast and turning-point metrics."""

    valid = frame.loc[frame[[actual_col, forecast_col]].notna().all(axis=1)].copy()
    if valid.empty:
        return {
            "n": 0,
            "rmse": np.nan,
            "mae": np.nan,
            "median_absolute_error": np.nan,
            "directional_accuracy": np.nan,
            "bias": np.nan,
            "maximum_forecast_miss": np.nan,
            "turn_definition": "sign_reversal",
            "turn_precision": np.nan,
            "turn_recall": np.nan,
            "turn_f1": np.nan,
        }
    error = valid[forecast_col].astype(float) - valid[actual_col].astype(float)
    direction = np.sign(valid[forecast_col].astype(float)).eq(
        np.sign(valid[actual_col].astype(float))
    )
    result: dict[str, float | int | str] = {
        "n": int(len(valid)),
        "rmse": float(np.sqrt(np.mean(np.square(error)))),
        "mae": float(np.mean(np.abs(error))),
        "median_absolute_error": float(np.median(np.abs(error))),
        "directional_accuracy": float(direction.mean()),
        "bias": float(error.mean()),
        "maximum_forecast_miss": float(np.abs(error).max()),
    }
    result.update(
        turning_point_metrics(
            valid, actual_col=actual_col, forecast_col=forecast_col, date_col=date_col
        )
    )
    return result


def performance_leaderboard(
    forecasts: pd.DataFrame,
    *,
    group_cols: Sequence[str] = ("model_id", "forecast_vintage"),
    actual_col: str = "actual",
    forecast_col: str = "forecast",
    date_col: str = "target_month",
) -> pd.DataFrame:
    """Build a leaderboard without mixing early, mid, and final vintages."""

    missing = set(group_cols).difference(forecasts.columns)
    if missing:
        raise ValueError(f"forecasts missing grouping columns: {sorted(missing)}")
    rows: list[dict[str, object]] = []
    grouper: str | list[str] = list(group_cols)
    for keys, group in forecasts.groupby(grouper, dropna=False, sort=True):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys, strict=True))
        row.update(
            forecast_metrics(
                group,
                actual_col=actual_col,
                forecast_col=forecast_col,
                date_col=date_col,
            )
        )
        rows.append(row)
    if not rows:
        return pd.DataFrame(columns=[*group_cols, "n", "rmse", "mae"])
    return pd.DataFrame(rows).sort_values([*group_cols]).reset_index(drop=True)

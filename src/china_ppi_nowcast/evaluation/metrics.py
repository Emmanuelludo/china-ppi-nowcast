"""Per-forecast errors and deliberately cautious aggregate metrics."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def evaluate_registry(forecasts_path: Path, actuals_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    forecasts = pd.read_csv(forecasts_path)
    actuals = pd.read_csv(actuals_path)
    actuals["retrieved_at"] = pd.to_datetime(actuals["retrieved_at"], utc=True, errors="coerce")
    actuals = actuals.sort_values("retrieved_at", na_position="first").drop_duplicates("target_month", keep="last")
    merged = forecasts.drop(columns=["actual_mom_pct"], errors="ignore").merge(
        actuals[["target_month", "actual_mom_pct"]], on="target_month", how="inner"
    )
    merged["estimate_mom_pct"] = pd.to_numeric(merged["estimate_mom_pct"])
    merged["actual_mom_pct"] = pd.to_numeric(merged["actual_mom_pct"])
    merged["error_pp"] = merged["estimate_mom_pct"] - merged["actual_mom_pct"]
    merged["absolute_error_pp"] = merged["error_pp"].abs()
    merged["squared_error"] = merged["error_pp"] ** 2
    merged["direction_correct"] = np.sign(merged["estimate_mom_pct"]) == np.sign(merged["actual_mom_pct"])
    summary = (
        merged.groupby(["model_key", "vintage"], as_index=False)
        .agg(
            n=("error_pp", "size"),
            mae=("absolute_error_pp", "mean"),
            rmse=("squared_error", lambda x: float(np.sqrt(x.mean()))),
            bias=("error_pp", "mean"),
            directional_accuracy=("direction_correct", "mean"),
        )
    )
    return merged, summary

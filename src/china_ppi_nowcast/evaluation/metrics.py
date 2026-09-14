"""Per-forecast errors and deliberately cautious aggregate metrics."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..storage import atomic_write_csv, atomic_write_text


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


def write_registry_evaluation(root: Path) -> dict[str, int]:
    forecasts_path = root / "data" / "registry" / "forecasts.csv"
    actuals_path = root / "data" / "registry" / "actuals.csv"
    if not forecasts_path.exists() or not actuals_path.exists():
        return {"evaluated_forecasts": 0, "evaluated_target_months": 0}
    errors, summary = evaluate_registry(forecasts_path, actuals_path)
    directory = root / "data" / "processed" / "evaluation"
    atomic_write_csv(directory / "forecast_errors.csv", errors)
    atomic_write_csv(directory / "model_summary.csv", summary)
    lines = [
        "# Prospective forecast evaluation",
        "",
        "Forecast rows are joined to official results without altering the frozen registry.",
        "With fewer than six prospective target months, individual errors should be read directly",
        "and aggregate ranking should not be treated as decisive.",
        "",
        "| Model | Vintage | n | MAE | RMSE | Bias | Direction |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['model_key']} | {row['vintage']} | {int(row['n'])} | {row['mae']:.3f} | "
            f"{row['rmse']:.3f} | {row['bias']:.3f} | {row['directional_accuracy']:.3f} |"
        )
    atomic_write_text(root / "reports" / "forecast_evaluation.md", "\n".join(lines) + "\n")
    return {
        "evaluated_forecasts": len(errors),
        "evaluated_target_months": int(errors["target_month"].nunique()) if len(errors) else 0,
    }

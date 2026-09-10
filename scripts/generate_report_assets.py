#!/usr/bin/env python3
"""Generate the required figure set from the empirical prototype outputs."""

from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd

from china_ppi_nowcast.reporting.visualizations import build_required_figures


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    raw = pd.read_csv(ROOT / "data/interim/nbs_market_prices/raw_market_prices.csv")
    raw["month"] = pd.to_datetime(raw.reference_period_start).dt.to_period("M").dt.to_timestamp()
    category_map = {
        "黑色金属": "Ferrous",
        "有色金属": "Non-ferrous",
        "化工产品": "Chemicals",
        "石油天然气": "Petroleum/gas",
        "煤炭": "Coal",
        "非金属": "Non-metallic",
        "农产品": "Agriculture",
        "农业生产资料": "Ag inputs",
        "农资": "Ag inputs",
        "林产品": "Forest",
        "林业": "Forest",
    }

    def cat(value: object) -> str:
        for token, label in category_map.items():
            if token in str(value):
                return label
        return "Unmapped"

    raw["category_id"] = raw.raw_category_name.map(cat)
    basket = (
        raw.groupby(["month", "category_id"]).raw_product_name.nunique().rename("active_product_count").reset_index()
        .rename(columns={"month": "date"})
    )
    active = basket.groupby("date", as_index=False).active_product_count.sum()

    features = pd.read_csv(ROOT / "data/processed/features/vintage_features.csv", parse_dates=["month"])
    targets_long = pd.read_csv(ROOT / "data/processed/targets/headline_ppi_current_vintage.csv", parse_dates=["month"])
    targets = targets_long.pivot(index="month", columns="series_id", values="value").reset_index()
    final_features = features.loc[
        features.forecast_vintage.eq("final")
        & features.aggregation_method.eq("published_10d_compound")
    ].merge(targets[["month", "headline_ppi_mom"]], on="month", how="left")

    rolling = pd.read_csv(ROOT / "data/processed/forecasts/rolling_forecasts.csv", parse_dates=["target_month"])
    run_summary = json.loads((ROOT / "data/processed/forecasts/run_summary.json").read_text())
    preferred_method = run_summary["preferred_method"]
    preferred_model = run_summary["preferred_model"]
    selected = rolling.loc[
        rolling.forecast_vintage.eq("final")
        & rolling.aggregation_method.eq(preferred_method)
        & rolling.model_id.eq(preferred_model)
    ].copy()
    leaderboard = pd.read_csv(ROOT / "data/processed/forecasts/model_leaderboard.csv")
    selected_leader = leaderboard.loc[
        leaderboard.aggregation_method.eq(preferred_method)
        & leaderboard.model_id.eq(preferred_model)
    ]
    vintage_accuracy = selected_leader[["forecast_vintage", "mae", "rmse"]]
    model_performance = leaderboard.loc[
        leaderboard.forecast_vintage.eq("final")
        & leaderboard.aggregation_method.eq(preferred_method)
    ][["model_id", "rmse"]]

    coefficients = pd.read_csv(ROOT / "data/processed/forecasts/model_coefficients.csv")
    coefficients = coefficients.loc[
        coefficients.forecast_vintage.eq("final")
        & coefficients.aggregation_method.eq(preferred_method)
        & coefficients.model_id.eq(preferred_model)
    ][["feature", "importance"]]
    contributions = pd.read_csv(ROOT / "data/processed/forecasts/current_contributions.csv")
    scenarios = pd.read_csv(ROOT / "data/processed/forecasts/current_shock_scenarios.csv")

    lineage = pd.read_csv(ROOT / "data/interim/harmonization/product_lineage.csv")
    turning = selected.copy()
    actual_sign = np.sign(turning.actual).replace(0, np.nan).ffill()
    forecast_sign = np.sign(turning.forecast).replace(0, np.nan).ffill()
    turning["actual_turn"] = actual_sign.ne(actual_sign.shift(1)) & actual_sign.shift(1).notna()
    turning["predicted_turn"] = forecast_sign.ne(forecast_sign.shift(1)) & forecast_sign.shift(1).notna()

    inputs = {
        "basket_composition": basket,
        "active_products": active,
        "product_lineage": lineage,
        "diffusion_vs_ppi": final_features.rename(columns={"headline_ppi_mom": "ppi_mom"})[
            ["month", "diffusion", "ppi_mom"]
        ],
        "market_index_vs_ppi": final_features.rename(
            columns={"market_price_factor": "market_price_change", "headline_ppi_mom": "ppi_mom"}
        )[["month", "market_price_change", "ppi_mom"]],
        # Corresponding industry PPI targets are not yet collected. Omitting this
        # input forces an explicit unavailable audit panel instead of a proxy.
        "forecast_vs_actual": selected,
        "rolling_errors": selected,
        "vintage_accuracy": vintage_accuracy,
        "model_performance": model_performance,
        "feature_importance": coefficients,
        "contributions": contributions,
        "shock_comparison": scenarios,
        "turning_points": turning,
        "forecast_fan": selected,
    }
    _, manifest = build_required_figures(inputs, output_dir=ROOT / "reports/figures")
    manifest.to_csv(ROOT / "reports/figures/manifest.csv", index=False)
    print(manifest[["figure_id", "status", "reason"]].to_string(index=False))


if __name__ == "__main__":
    main()

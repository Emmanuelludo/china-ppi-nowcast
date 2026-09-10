#!/usr/bin/env python3
"""Build vintage features, run expanding-window backtests, and emit a live nowcast.

This is deliberately a small, auditable empirical layer.  It uses the NBS-published
ten-day price changes or price-level aggregations, an AR term, and only information
subject to recorded availability cutoffs. The bundled targets are a *current
database snapshot*: their historical availability is unverified. This legacy
diagnostic therefore requires explicit --allow-snapshot-diagnostic consent and
must not be represented as a first-release real-time backtest or live model.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


SCHEMA_VERSION = "0.1.0"
VINTAGE_SLOTS = {"early": 1, "mid": 2, "final": 3}


def category_id(raw: object) -> str:
    value = str(raw)
    mapping = {
        "黑色金属": "CAT_ferrous_metals",
        "有色金属": "CAT_nonferrous_metals",
        "化工产品": "CAT_chemicals",
        "石油天然气": "CAT_petroleum_gas",
        "煤炭": "CAT_coal",
        "非金属建材": "CAT_nonmetallic_minerals",
        "非金属矿物": "CAT_nonmetallic_minerals",
        "农产品": "CAT_agriculture",
        "农业生产资料": "CAT_ag_inputs",
        "农资": "CAT_ag_inputs",
        "林产品": "CAT_forest_products",
        "林业": "CAT_forest_products",
    }
    for token, stable in mapping.items():
        if token in value:
            return stable
    return "CAT_unmapped"


def slot_from_start(series: pd.Series) -> pd.Series:
    day = pd.to_datetime(series).dt.day
    return np.select([day.le(10), day.le(20)], [1, 2], default=3).astype(int)


def prepare_raw(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    raw["reference_period_start"] = pd.to_datetime(raw["reference_period_start"])
    raw["reference_period_end"] = pd.to_datetime(raw["reference_period_end"])
    raw["month"] = raw.reference_period_start.dt.to_period("M").dt.to_timestamp()
    raw["slot"] = slot_from_start(raw.reference_period_start)
    raw["category_id"] = raw.raw_category_name.map(category_id)
    raw["product_key"] = (
        raw.raw_product_name.fillna("").astype(str).str.replace(r"\s+", "", regex=True)
        + "|"
        + raw.original_unit.fillna("").astype(str)
    )
    raw["days_represented"] = (
        raw.reference_period_end - raw.reference_period_start
    ).dt.days.add(1).clip(lower=1)
    return raw.sort_values(["month", "slot", "source_row_number"]).reset_index(drop=True)


def _product_level(sub: pd.DataFrame, method: str) -> pd.Series:
    if method == "monthly_average":
        return sub.groupby("product_key").raw_price.mean()
    if method == "day_weighted_average":
        work = sub.assign(weighted=sub.raw_price * sub.days_represented)
        return work.groupby("product_key").weighted.sum() / work.groupby("product_key").days_represented.sum()
    if method == "end_to_end":
        return sub.sort_values(["slot", "reference_period_end"]).groupby("product_key").raw_price.last()
    raise ValueError(method)


def _published_product_changes(sub: pd.DataFrame) -> pd.Series:
    clean = sub.dropna(subset=["raw_pct_change"]).copy()
    clean["gross"] = 1.0 + clean.raw_pct_change.astype(float) / 100.0
    return (clean.groupby("product_key").gross.prod() - 1.0) * 100.0


def _level_product_changes(raw: pd.DataFrame, month: pd.Timestamp, max_slot: int, method: str) -> pd.Series:
    current = raw.loc[raw.month.eq(month) & raw.slot.le(max_slot)]
    previous_month = month - pd.offsets.MonthBegin(1)
    previous = raw.loc[raw.month.eq(previous_month)]
    current_level = _product_level(current, method)
    previous_level = _product_level(previous, method)
    joined = pd.concat([current_level.rename("current"), previous_level.rename("previous")], axis=1).dropna()
    joined = joined.loc[joined.previous.ne(0)]
    return (joined.current / joined.previous - 1.0) * 100.0


def build_features(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    category_rows: list[dict[str, object]] = []
    methods = ["published_10d_compound", "monthly_average", "end_to_end", "day_weighted_average"]
    for month in sorted(raw.month.unique()):
        month = pd.Timestamp(month)
        for vintage, max_slot in VINTAGE_SLOTS.items():
            observed = raw.loc[raw.month.eq(month) & raw.slot.le(max_slot)]
            present_slots = sorted(observed.slot.unique().tolist())
            if present_slots != list(range(1, max_slot + 1)):
                continue
            for method in methods:
                if method == "published_10d_compound":
                    changes = _published_product_changes(observed)
                else:
                    changes = _level_product_changes(raw, month, max_slot, method)
                changes = changes.replace([np.inf, -np.inf], np.nan).dropna()
                if changes.empty:
                    continue
                rows.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "month": month,
                        "forecast_vintage": vintage,
                        "aggregation_method": method,
                        "market_price_factor": changes.mean(),
                        "median_change": changes.median(),
                        "trimmed_mean_change": changes.sort_values().iloc[
                            max(0, int(len(changes) * 0.1)) : max(1, int(np.ceil(len(changes) * 0.9)))
                        ].mean(),
                        "diffusion": changes.gt(0).mean() - changes.lt(0).mean(),
                        "share_rising": changes.gt(0).mean(),
                        "share_falling": changes.lt(0).mean(),
                        "share_unchanged": changes.eq(0).mean(),
                        "volatility": changes.std(ddof=0),
                        "n_products": len(changes),
                        "n_releases": len(present_slots),
                        "latest_available_at": observed.available_at.max(),
                        "target_vintage_status": "current_snapshot_proxy_not_first_release",
                    }
                )
            # Category factors use published changes, which preserve NBS's own change base.
            product_changes = _published_product_changes(observed)
            product_meta = observed.groupby("product_key", as_index=False).last()[["product_key", "category_id"]]
            category_data = product_meta.join(product_changes.rename("change"), on="product_key")
            for category, group in category_data.dropna(subset=["change"]).groupby("category_id"):
                category_rows.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "month": month,
                        "forecast_vintage": vintage,
                        "category_id": category,
                        "category_factor": group.change.mean(),
                        "category_diffusion": group.change.gt(0).mean() - group.change.lt(0).mean(),
                        "n_products": len(group),
                    }
                )
    features = pd.DataFrame(rows).sort_values(["forecast_vintage", "aggregation_method", "month"])
    categories = pd.DataFrame(category_rows).sort_values(["forecast_vintage", "month", "category_id"])
    return features, categories


def load_target(path: Path, allow_snapshot_diagnostic: bool = False) -> pd.DataFrame:
    target = pd.read_csv(path)
    snapshot = target.get("vintage", pd.Series("", index=target.index)).astype(str).str.contains("snapshot").any()
    if snapshot and not allow_snapshot_diagnostic:
        raise ValueError("Current-snapshot targets cannot establish real-time performance. Use --allow-snapshot-diagnostic only for explicitly labelled diagnostics.")
    if "available_at" not in target:
        raise ValueError("Target available_at is required; publication dates must not be invented.")
    target["month"] = pd.to_datetime(target.month)
    pivot = target.pivot(index="month", columns="series_id", values="value").reset_index()
    dates = target.assign(available_at=pd.to_datetime(target.available_at, utc=True)).pivot(index="month", columns="series_id", values="available_at")
    dates.columns = [f"{name}_available_at" for name in dates.columns]
    return pivot.merge(dates.reset_index(), on="month").rename_axis(columns=None)


def design_frame(features: pd.DataFrame, target: pd.DataFrame, vintage: str, method: str) -> pd.DataFrame:
    data = features.loc[
        features.forecast_vintage.eq(vintage) & features.aggregation_method.eq(method)
    ].copy()
    data = data.merge(target, on="month", how="left")
    data["latest_available_at"] = pd.to_datetime(data.latest_available_at, utc=True)
    prior_target = target[["month", "headline_ppi_mom", "headline_ppi_mom_available_at"]].copy()
    prior_target["month"] = prior_target.month + pd.offsets.MonthBegin(1)
    prior_target = prior_target.rename(columns={"headline_ppi_mom": "ppi_mom_lag1", "headline_ppi_mom_available_at": "ppi_mom_lag1_available_at"})
    data = data.merge(prior_target, on="month", how="left")
    lag_known = data.ppi_mom_lag1_available_at.notna() & data.ppi_mom_lag1_available_at.le(data.latest_available_at)
    data.loc[~lag_known, "ppi_mom_lag1"] = np.nan
    prior = data[["month", "market_price_factor"]].copy()
    prior["month"] = prior.month + pd.offsets.MonthBegin(1)
    prior = prior.rename(columns={"market_price_factor": "market_price_factor_lag1"})
    return data.merge(prior, on="month", how="left").sort_values("month")


def fit_ols(frame: pd.DataFrame, columns: list[str], target: str = "headline_ppi_mom") -> tuple[np.ndarray, list[str]]:
    clean = frame.dropna(subset=[target, *columns])
    x = np.column_stack([np.ones(len(clean)), clean[columns].to_numpy(float)])
    y = clean[target].to_numpy(float)
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    return beta, ["intercept", *columns]


def predict_row(row: pd.Series, beta: np.ndarray, columns: list[str]) -> float:
    return float(np.r_[1.0, row[columns].to_numpy(float)] @ beta)


def expanding_backtest(
    frame: pd.DataFrame,
    model_id: str,
    columns: list[str],
    min_train: int = 36,
) -> pd.DataFrame:
    required = ["headline_ppi_mom", *columns]
    complete = frame.dropna(subset=required).reset_index(drop=True)
    rows: list[dict[str, object]] = []
    for i in range(min_train, len(complete)):
        test = complete.iloc[i]
        cutoff = pd.to_datetime(test.latest_available_at, utc=True)
        train = complete.iloc[:i]
        known = pd.to_datetime(train.headline_ppi_mom_available_at, utc=True)
        train = train.loc[known.notna() & known.le(cutoff)]
        if len(train) < min_train:
            continue
        if model_id == "naive_zero":
            forecast = 0.0
        else:
            beta, _ = fit_ols(train, columns)
            forecast = predict_row(test, beta, columns)
        residual_history = np.asarray([r["error"] for r in rows if pd.notna(r["actual_available_at"]) and r["actual_available_at"] <= cutoff], dtype=float)
        if len(residual_history) >= 8:
            lower, upper = error_interval(forecast, residual_history)
            interval_status = "vintage_specific_empirical_80"
        else:
            lower = np.nan
            upper = np.nan
            interval_status = "insufficient_prior_errors"
        actual = float(test.headline_ppi_mom)
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "forecast_vintage": test.forecast_vintage,
                "target_month": test.month,
                "aggregation_method": test.aggregation_method,
                "model_id": model_id,
                "forecast": forecast,
                "lower_bound": lower,
                "upper_bound": upper,
                "actual": actual,
                "error": forecast - actual,
                "forecast_cutoff": cutoff,
                "actual_available_at": test.headline_ppi_mom_available_at,
                "interval_status": interval_status,
                "target_vintage_status": "current_snapshot_proxy_not_first_release",
                "n_train": len(train),
            }
        )
    return pd.DataFrame(rows)


def error_interval(forecast: float, forecast_minus_actual: np.ndarray) -> tuple[float, float]:
    """Invert forecast-minus-actual errors; positive bias shifts bounds down."""
    return (forecast - float(np.quantile(forecast_minus_actual, 0.90)),
            forecast - float(np.quantile(forecast_minus_actual, 0.10)))


def metrics(frame: pd.DataFrame) -> dict[str, float | int]:
    error = frame.error.to_numpy(float)
    actual = frame.actual.to_numpy(float)
    forecast = frame.forecast.to_numpy(float)
    return {
        "n_forecasts": len(frame),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "mae": float(np.mean(np.abs(error))),
        "median_ae": float(np.median(np.abs(error))),
        "bias": float(np.mean(error)),
        "maximum_miss": float(np.max(np.abs(error))),
        "directional_accuracy": float(np.mean(np.sign(forecast) == np.sign(actual))),
    }


def model_outputs(features: pd.DataFrame, target: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    all_forecasts: list[pd.DataFrame] = []
    leaderboard: list[dict[str, object]] = []
    current_rows: list[dict[str, object]] = []
    coefficient_rows: list[dict[str, object]] = []
    model_specs = {
        "naive_zero": [],
        "ar1": ["ppi_mom_lag1"],
        "bridge_current": ["market_price_factor", "diffusion", "ppi_mom_lag1"],
        "bridge_full": ["market_price_factor", "market_price_factor_lag1", "diffusion", "ppi_mom_lag1"],
    }
    current_month = features.month.max()
    for vintage in VINTAGE_SLOTS:
        for method in features.aggregation_method.unique():
            frame = design_frame(features, target, vintage, method)
            for model_id, columns in model_specs.items():
                bt = expanding_backtest(frame, model_id, columns)
                if bt.empty:
                    continue
                all_forecasts.append(bt)
                leaderboard.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "forecast_vintage": vintage,
                        "aggregation_method": method,
                        "model_id": model_id,
                        **metrics(bt),
                        "evaluation_status": "development_current_snapshot_target",
                    }
                )
                now = frame.loc[frame.month.eq(current_month)]
                train = frame.loc[frame.month.lt(current_month)].dropna(subset=["headline_ppi_mom", *columns])
                if not now.empty:
                    cutoff = pd.to_datetime(now.iloc[0].latest_available_at, utc=True)
                    known = pd.to_datetime(train.headline_ppi_mom_available_at, utc=True)
                    train = train.loc[known.notna() & known.le(cutoff)]
                if now.empty or now[columns].isna().any(axis=None) or len(train) < 36:
                    continue
                if model_id == "naive_zero":
                    forecast = 0.0
                    beta = np.array([0.0])
                    names = ["intercept"]
                else:
                    beta, names = fit_ols(train, columns)
                    forecast = predict_row(now.iloc[0], beta, columns)
                historical = bt.loc[bt.actual_available_at.notna() & bt.actual_available_at.le(cutoff), "error"].to_numpy(float)
                lower, upper = error_interval(forecast, historical) if len(historical) >= 8 else (np.nan, np.nan)
                current_rows.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "forecast_vintage": vintage,
                        "target_month": current_month,
                        "aggregation_method": method,
                        "model_id": model_id,
                        "forecast_mom": forecast,
                        "lower_80": lower,
                        "upper_80": upper,
                        "n_train": len(train),
                        "n_oos_errors": len(historical),
                        "status": "development_only_current_snapshot_targets",
                    }
                )
                if model_id.startswith("bridge"):
                    for name, value in zip(names, beta, strict=True):
                        coefficient_rows.append(
                            {
                                "forecast_vintage": vintage,
                                "aggregation_method": method,
                                "model_id": model_id,
                                "feature": name,
                                "importance": float(value),
                                "target_month": current_month,
                            }
                        )
    return (
        pd.concat(all_forecasts, ignore_index=True),
        pd.DataFrame(leaderboard),
        pd.DataFrame(current_rows),
        pd.DataFrame(coefficient_rows),
    )


def add_mechanical_yoy(current: pd.DataFrame, target: pd.DataFrame) -> pd.DataFrame:
    result = current.copy()
    month = pd.Timestamp(result.target_month.max())
    lookup = target.set_index("month")
    prior_yoy = float(lookup.loc[month - pd.offsets.MonthBegin(1), "headline_ppi_yoy"])
    base_mom = float(lookup.loc[month - pd.DateOffset(years=1), "headline_ppi_mom"])
    result["forecast_yoy"] = ((1 + prior_yoy / 100) * (1 + result.forecast_mom / 100) / (1 + base_mom / 100) - 1) * 100
    result["yoy_identity_prior_month"] = prior_yoy
    result["yoy_identity_base_month_mom"] = base_mom
    result["yoy_reconciliation_residual"] = 0.0
    return result


def contribution_and_scenarios(
    raw: pd.DataFrame,
    features: pd.DataFrame,
    target: pd.DataFrame,
    current: pd.DataFrame,
    coefficients: pd.DataFrame,
    preferred_vintage: str,
    preferred_method: str,
    preferred_model: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    month = features.month.max()
    max_slot = VINTAGE_SLOTS[preferred_vintage]
    observed = raw.loc[raw.month.eq(month) & raw.slot.le(max_slot)].copy()
    frame = design_frame(features, target, preferred_vintage, preferred_method)
    now = frame.loc[frame.month.eq(month)].iloc[0]
    coef = coefficients.loc[
        coefficients.forecast_vintage.eq(preferred_vintage)
        & coefficients.aggregation_method.eq(preferred_method)
        & coefficients.model_id.eq(preferred_model)
    ].set_index("feature").importance
    preferred_now = current.loc[
        current.forecast_vintage.eq(preferred_vintage)
        & current.aggregation_method.eq(preferred_method)
        & current.model_id.eq(preferred_model)
    ].iloc[0]
    if preferred_method == "published_10d_compound":
        product_changes = _published_product_changes(observed)
    else:
        product_changes = _level_product_changes(raw, month, max_slot, preferred_method)
    product_meta = observed.groupby("product_key", as_index=False).last()[["product_key", "category_id", "raw_product_name"]]
    pdata = product_meta.join(product_changes.rename("change"), on="product_key").dropna(subset=["change"])
    n_total = len(pdata)
    contributions: list[dict[str, object]] = []
    for category, group in pdata.groupby("category_id"):
        factor_piece = group.change.sum() / n_total
        diffusion_piece = (group.change.gt(0).sum() - group.change.lt(0).sum()) / n_total
        contribution = coef.get("market_price_factor", 0.0) * factor_piece + coef.get("diffusion", 0.0) * diffusion_piece
        contributions.append({"contributor_id": category, "contribution_pp": contribution, "contribution_type": "current_signal"})
    for contributor, value in [
        ("lagged_market_factor", coef.get("market_price_factor_lag1", 0.0) * now.market_price_factor_lag1),
        ("ppi_ar_term", coef.get("ppi_mom_lag1", 0.0) * now.ppi_mom_lag1),
        ("intercept", coef.get("intercept", 0.0)),
    ]:
        contributions.append({"contributor_id": contributor, "contribution_pp": value, "contribution_type": "model_term"})
    contribution_frame = pd.DataFrame(contributions)
    contribution_frame["target_month"] = month
    contribution_frame["forecast_vintage"] = preferred_vintage
    contribution_frame["aggregation_method"] = preferred_method
    contribution_frame["model_forecast"] = preferred_now.forecast_mom
    contribution_frame["rounding_residual"] = preferred_now.forecast_mom - contribution_frame.contribution_pp.sum()

    scenarios = {
        "baseline": pd.Series(False, index=pdata.index),
        "ex_coal": pdata.category_id.eq("CAT_coal"),
        "ex_energy": pdata.category_id.isin(["CAT_coal", "CAT_petroleum_gas"]),
        "ex_fertilizer": pdata.category_id.eq("CAT_ag_inputs"),
        "ex_polysilicon": pdata.raw_product_name.astype(str).str.contains("多晶硅", na=False),
    }
    scenario_rows: list[dict[str, object]] = []
    for name, mask in scenarios.items():
        adjusted = pdata.change.where(~mask, 0.0)
        factor = adjusted.sum() / n_total
        diffusion = (adjusted.gt(0).sum() - adjusted.lt(0).sum()) / n_total
        scenario_forecast = (
            coef.get("intercept", 0.0)
            + coef.get("market_price_factor", 0.0) * factor
            + coef.get("market_price_factor_lag1", 0.0) * now.market_price_factor_lag1
            + coef.get("diffusion", 0.0) * diffusion
            + coef.get("ppi_mom_lag1", 0.0) * now.ppi_mom_lag1
        )
        scenario_rows.append(
            {
                "target_month": month,
                "forecast_vintage": preferred_vintage,
                "shock_scenario": name,
                "forecast": scenario_forecast,
                "products_downweighted": int(mask.sum()),
                "method": "set_selected_current_signals_to_zero_keep_denominator",
            }
        )
    return contribution_frame, pd.DataFrame(scenario_rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=Path("data/interim/nbs_market_prices/raw_market_prices.csv"))
    parser.add_argument("--targets", type=Path, default=Path("data/processed/targets/headline_ppi_current_vintage.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/processed"))
    parser.add_argument("--allow-snapshot-diagnostic", action="store_true", help="Explicitly run non-real-time current-snapshot diagnostics; not production-approved.")
    args = parser.parse_args()

    raw = prepare_raw(args.raw)
    target = load_target(args.targets, allow_snapshot_diagnostic=args.allow_snapshot_diagnostic)
    features, categories = build_features(raw)
    forecasts, leaderboard, current, coefficients = model_outputs(features, target)
    current = add_mechanical_yoy(current, target)

    preferred_vintage = "final"
    eligible = leaderboard.loc[
        leaderboard.forecast_vintage.eq(preferred_vintage)
        & leaderboard.model_id.str.startswith("bridge")
        & leaderboard.n_forecasts.ge(10)
    ].sort_values(["rmse", "mae"])
    preferred_method = str(eligible.iloc[0].aggregation_method)
    preferred_model = str(eligible.iloc[0].model_id)
    contributions, scenarios = contribution_and_scenarios(
        raw, features, target, current, coefficients, preferred_vintage, preferred_method, preferred_model
    )

    paths = {
        "features": args.output / "features" / "vintage_features.csv",
        "categories": args.output / "features" / "category_features.csv",
        "forecasts": args.output / "forecasts" / "rolling_forecasts.csv",
        "leaderboard": args.output / "forecasts" / "model_leaderboard.csv",
        "current": args.output / "forecasts" / "current_nowcast.csv",
        "coefficients": args.output / "forecasts" / "model_coefficients.csv",
        "contributions": args.output / "forecasts" / "current_contributions.csv",
        "scenarios": args.output / "forecasts" / "current_shock_scenarios.csv",
    }
    objects = [features, categories, forecasts, leaderboard, current, coefficients, contributions, scenarios]
    for path, frame in zip(paths.values(), objects, strict=True):
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "target_month": str(features.month.max().date()),
        "preferred_vintage": preferred_vintage,
        "preferred_method": preferred_method,
        "preferred_model": preferred_model,
        "selection_rule": "lowest-RMSE bridge with at least 10 OOS forecasts, subject to auditability; not production-approved",
        "target_vintage_status": "current_snapshot_proxy_not_first_release",
        "archive_start": str(raw.reference_period_start.min().date()),
        "archive_end": str(raw.reference_period_end.max().date()),
        "n_observations": int(len(raw)),
    }
    summary_path = args.output / "forecasts" / "run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

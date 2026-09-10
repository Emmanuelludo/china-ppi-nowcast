"""Forecast integration, intervals, coverage gates and MoM/YoY identities."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .base import ForecastEstimate, ModelSpec
from .benchmarks import naive_forecast
from .factors import fit_factor_model
from .linear import fit_linear
from .state_space import fit_state_space
from .tvp import fit_tvp


@dataclass(frozen=True)
class EmpiricalInterval:
    lower: float
    upper: float
    sample_size: int
    method: str


@dataclass(frozen=True)
class YoYReconciliation:
    mom_forecast: float
    mechanical_yoy: float
    reconciliation_residual: float
    reconciled_yoy: float
    residual_sample_size: int


def yoy_from_mom_path(monthly_mom_percent: pd.Series | list[float] | np.ndarray) -> float:
    """Chain exactly twelve monthly rates into a same-month YoY rate."""

    values = np.asarray(monthly_mom_percent, dtype=float)
    if values.size != 12 or not np.isfinite(values).all():
        raise ValueError("YoY identity requires exactly 12 finite monthly MoM rates")
    return float((np.prod(1 + values / 100) - 1) * 100)


def reconcile_yoy_to_mom(
    mom_forecast: float,
    previous_eleven_mom: pd.Series | list[float] | np.ndarray,
    *,
    historical_reconciliation_residuals: pd.Series | list[float] | np.ndarray | None = None,
    residual_lookback: int = 60,
    min_residual_history: int = 12,
) -> YoYReconciliation:
    """Make the MoM path primary and report the NBS rounding residual explicitly."""

    previous = np.asarray(previous_eleven_mom, dtype=float)
    if previous.size != 11 or not np.isfinite(previous).all():
        raise ValueError("previous_eleven_mom must contain 11 finite observations")
    mechanical = yoy_from_mom_path(np.r_[previous, float(mom_forecast)])
    correction = 0.0
    residual_n = 0
    if historical_reconciliation_residuals is not None:
        residuals = pd.to_numeric(
            pd.Series(historical_reconciliation_residuals), errors="coerce"
        ).dropna().iloc[-residual_lookback:]
        residual_n = len(residuals)
        if residual_n >= min_residual_history:
            # Median is robust to occasional changes in published rounding.
            correction = float(residuals.median())
    return YoYReconciliation(
        mom_forecast=float(mom_forecast),
        mechanical_yoy=mechanical,
        reconciliation_residual=correction,
        reconciled_yoy=mechanical + correction,
        residual_sample_size=residual_n,
    )


def empirical_interval(
    forecast: float,
    errors: pd.DataFrame | pd.Series,
    *,
    forecast_vintage: str | None = None,
    coverage: float = 0.80,
    min_vintage_errors: int = 20,
    pooled_widening: float = 1.25,
) -> EmpiricalInterval:
    """Vintage-specific empirical error interval with labelled widened fallback."""

    if not 0 < coverage < 1:
        raise ValueError("coverage must be in (0, 1)")
    if isinstance(errors, pd.DataFrame):
        if "error" not in errors:
            raise ValueError("errors DataFrame requires error")
        selected = errors
        if forecast_vintage is not None and "forecast_vintage" in errors:
            vintage_errors = errors.loc[errors["forecast_vintage"].eq(forecast_vintage), "error"].dropna()
        else:
            vintage_errors = pd.Series(dtype=float)
        if len(vintage_errors) >= min_vintage_errors:
            values = vintage_errors
            method = "vintage_specific_empirical"
            widening = 1.0
        else:
            values = selected["error"].dropna()
            method = "pooled_empirical_widened"
            widening = pooled_widening
    else:
        values = pd.to_numeric(errors, errors="coerce").dropna()
        method = "pooled_empirical_widened"
        widening = pooled_widening
    if len(values) < 5:
        raise ValueError("at least five historical errors are required")
    alpha = (1 - coverage) / 2
    lower_error, upper_error = values.quantile([alpha, 1 - alpha])
    center = float(values.median())
    lower_error = center + widening * (float(lower_error) - center)
    upper_error = center + widening * (float(upper_error) - center)
    # error = actual - forecast, so add empirical error quantiles to the forecast.
    return EmpiricalInterval(
        lower=float(forecast + lower_error),
        upper=float(forecast + upper_error),
        sample_size=len(values),
        method=method,
    )


def coverage_gate(
    current_row: pd.Series,
    training_rows: pd.DataFrame,
    *,
    relative_product_floor: float = 0.70,
    known_weight_mass_floor: float = 0.60,
) -> tuple[bool, str]:
    """Apply coverage fallback/no-forecast rules before model fitting."""

    if "coverage_ratio" in current_row and "coverage_ratio" in training_rows:
        median = pd.to_numeric(training_rows["coverage_ratio"], errors="coerce").median()
        current = pd.to_numeric(pd.Series([current_row["coverage_ratio"]]), errors="coerce").iloc[0]
        if np.isfinite(median) and (not np.isfinite(current) or current < relative_product_floor * median):
            return False, "product_coverage_below_70pct_training_median"
    if "weight_mass_coverage" in current_row:
        value = pd.to_numeric(pd.Series([current_row["weight_mass_coverage"]]), errors="coerce").iloc[0]
        if np.isfinite(value) and value < known_weight_mass_floor:
            return False, "known_weight_mass_below_60pct"
    return True, "coverage_ok"


def fit_and_forecast(
    spec: ModelSpec,
    training: pd.DataFrame,
    current_row: pd.DataFrame,
    *,
    target_column: str = "target",
) -> ForecastEstimate:
    """Fit one ladder member on a caller-supplied, already vintage-filtered sample."""

    if len(current_row) != 1:
        raise ValueError("current_row must have exactly one row")
    if target_column not in training:
        raise ValueError(f"training missing {target_column}")
    ok, reason = coverage_gate(current_row.iloc[0], training)
    if not ok:
        raise ValueError(f"coverage gate failed: {reason}")
    family = spec.family
    y = training[target_column]
    if family == "naive":
        forecast = naive_forecast(y, rule=spec.parameters.get("rule", "zero_mom"))
        return ForecastEstimate(spec.model_id, forecast, metadata={"coverage_status": reason})
    features = list(spec.feature_columns)
    if family in {"ar", "bridge", "ridge", "elastic_net", "midas"}:
        fitted_family = "ridge" if family == "midas" else family
        model = fit_linear(
            training,
            y,
            feature_names=features,
            family=fitted_family,
            model_id=spec.model_id,
            alpha=float(spec.parameters.get("alpha", 1.0)),
            l1_ratio=float(spec.parameters.get("l1_ratio", 0.5)),
        )
        forecast = float(model.predict(current_row)[0])
        contributions = model.contributions(current_row)
        residuals = model.residuals
    elif family == "factor":
        model = fit_factor_model(
            training, y, feature_names=features,
            n_factors=int(spec.parameters.get("n_factors", 1)),
            alpha=float(spec.parameters.get("alpha", 1.0)),
        )
        forecast = float(model.predict(current_row)[0])
        contributions = model.factor_contributions(current_row)
        residuals = model.residuals
    elif family == "state_space":
        model = fit_state_space(training, y, feature_names=features)
        forecast = model.forecast(current_row)
        contributions = {}
        residuals = model.residuals
    elif family == "tvp":
        model = fit_tvp(
            training, y, feature_names=features,
            forgetting_factor=float(spec.parameters.get("forgetting_factor", 0.98)),
        )
        forecast = model.forecast(current_row)
        contributions = model.contributions(current_row)
        residuals = model.residuals
    else:
        raise ValueError(f"unsupported family: {family}")
    metadata = {
        "coverage_status": reason,
        "sample_size": int(pd.to_numeric(y, errors="coerce").notna().sum()),
        "training_residuals": residuals,
    }
    return ForecastEstimate(spec.model_id, forecast, contributions=contributions, metadata=metadata)


def pseudo_real_time_backtest(
    feature_snapshots: pd.DataFrame,
    targets: pd.DataFrame,
    origins: pd.DataFrame,
    spec: ModelSpec,
    *,
    aggregation_method: str,
    transformation_version: str,
    target_series_id: str = "headline_ppi_mom",
) -> pd.DataFrame:
    """Run an expanding-window backtest with strict public-time filtering.

    ``origins`` supplies target month, forecast vintage and cutoff.  Target values
    may enter training only when their own ``available_at`` is no later than that
    cutoff.  ``processed_at`` is ignored.  Actuals are joined after forecasting for
    scoring and therefore never enter a model early.
    """

    feature_required = {
        "month", "forecast_vintage", "available_at", "aggregation_method",
        "transformation_version",
    }
    target_required = {"month", "series_id", "value", "available_at"}
    origin_required = {"target_month", "forecast_vintage", "forecast_cutoff"}
    for frame, required, name in (
        (feature_snapshots, feature_required, "feature_snapshots"),
        (targets, target_required, "targets"),
        (origins, origin_required, "origins"),
    ):
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{name} missing columns: {sorted(missing)}")
    features = feature_snapshots.copy()
    features["month"] = pd.to_datetime(features["month"]).dt.to_period("M").dt.to_timestamp()
    features["available_at"] = pd.to_datetime(features["available_at"], utc=True)
    if "forecast_cutoff" in features:
        features["forecast_cutoff"] = pd.to_datetime(features["forecast_cutoff"], utc=True)
    target_frame = targets.loc[targets["series_id"].eq(target_series_id)].copy()
    target_frame["month"] = pd.to_datetime(target_frame["month"]).dt.to_period("M").dt.to_timestamp()
    target_frame["available_at"] = pd.to_datetime(target_frame["available_at"], utc=True)
    target_frame = target_frame.sort_values(["month", "available_at"])
    result: list[dict[str, object]] = []
    for _, origin in origins.iterrows():
        month = pd.Timestamp(origin["target_month"]).to_period("M").to_timestamp()
        cutoff = pd.Timestamp(origin["forecast_cutoff"])
        cutoff = cutoff.tz_localize("UTC") if cutoff.tzinfo is None else cutoff.tz_convert("UTC")
        vintage = str(origin["forecast_vintage"])
        eligible = features.loc[
            features["forecast_vintage"].eq(vintage)
            & features["aggregation_method"].eq(aggregation_method)
            & features["transformation_version"].eq(transformation_version)
            & features["available_at"].le(cutoff)
            & features["month"].le(month)
        ].copy()
        if "forecast_cutoff" in eligible:
            eligible = eligible.loc[eligible["forecast_cutoff"].le(cutoff)]
            eligible = eligible.sort_values(["month", "forecast_cutoff", "available_at"])
        else:
            eligible = eligible.sort_values(["month", "available_at"])
        eligible = eligible.drop_duplicates("month", keep="last")
        current = eligible.loc[eligible["month"].eq(month)]
        public_targets = target_frame.loc[
            target_frame["available_at"].le(cutoff) & target_frame["month"].lt(month)
        ].drop_duplicates("month", keep="last")
        training = eligible.loc[eligible["month"].lt(month)].merge(
            public_targets[["month", "value"]].rename(columns={"value": "target"}),
            on="month",
            how="inner",
        )
        # AR terms are constructed exclusively from target releases public at cutoff.
        target_by_month = public_targets.set_index("month")["value"]
        for lag in range(1, 7):
            training[f"ppi_lag_{lag}"] = [
                target_by_month.get(row_month - pd.DateOffset(months=lag), np.nan)
                for row_month in training["month"]
            ]
            if len(current):
                current = current.copy()
                current[f"ppi_lag_{lag}"] = target_by_month.get(month - pd.DateOffset(months=lag), np.nan)
        base = {
            "forecast_vintage": vintage,
            "forecast_cutoff": cutoff,
            "target_month": month,
            "target_series_id": target_series_id,
            "model_id": spec.model_id,
            "aggregation_method": aggregation_method,
            "transformation_version": transformation_version,
        }
        try:
            if current.empty:
                raise ValueError("no current feature row public by cutoff")
            estimate = fit_and_forecast(spec, training, current.iloc[[-1]], target_column="target")
            row = {
                **base,
                "forecast": estimate.forecast,
                "sample_size": estimate.metadata.get("sample_size", len(training)),
                "forecast_status": "forecast",
                "status_reason": estimate.metadata.get("coverage_status", "ok"),
            }
        except (ValueError, np.linalg.LinAlgError) as exc:
            row = {
                **base,
                "forecast": np.nan,
                "sample_size": len(training),
                "forecast_status": "no_forecast",
                "status_reason": str(exc),
            }
        actual_match = target_frame.loc[target_frame["month"].eq(month)].sort_values("available_at")
        actual = float(actual_match["value"].iloc[0]) if len(actual_match) else np.nan
        row["actual"] = actual
        row["error"] = actual - row["forecast"] if np.isfinite(actual) and np.isfinite(row["forecast"]) else np.nan
        result.append(row)
    return pd.DataFrame(result).sort_values(["target_month", "forecast_vintage"]).reset_index(drop=True)

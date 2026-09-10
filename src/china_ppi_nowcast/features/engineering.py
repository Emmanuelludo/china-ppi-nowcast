"""Feature engineering for the ten-day NBS circulation-price survey.

The functions in this module deliberately separate *public availability* from
pipeline processing time.  ``available_at`` is source-derived and is the only
timestamp used to admit an observation to a vintage.  ``processed_at`` is audit
metadata and must never be used as a real-time filter.

All monthly outputs carry both ``aggregation_method`` and
``transformation_version``.  These are part of the logical primary key: results
made with different temporal aggregation rules must never be silently combined.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Iterable

import numpy as np
import pandas as pd


SIGNAL_COLUMNS = (
    "change_10d",
    "change_20d",
    "intra_month_change",
    "monthly_avg_change",
    "month_end_change",
    "change_3m",
    "change_6m",
    "yoy_change",
    "yoy_acceleration",
)


@dataclass(frozen=True)
class FeatureConfig:
    """Auditable feature parameters.

    Four monthly observations is the minimum for short-horizon transformations;
    twelve prior monthly observations are still required by the individual annual
    features themselves.  Coverage is assessed after the history screen.
    """

    transformation_version: str = "market_price_features_v1"
    min_product_history: int = 4
    min_category_products: int = 2
    min_category_coverage: float = 0.70
    min_weight_mass_coverage: float = 0.60
    rolling_standardization_months: int = 36
    rolling_min_periods: int = 12
    trim_fraction: float = 0.10
    robust_lower_quantile: float = 0.025
    robust_upper_quantile: float = 0.975
    shock_adjustment_strength: float = 1.0

    def __post_init__(self) -> None:
        if self.min_product_history < 2:
            raise ValueError("min_product_history must be at least 2")
        if self.min_category_products < 1:
            raise ValueError("min_category_products must be positive")
        if not 0 < self.min_category_coverage <= 1:
            raise ValueError("min_category_coverage must be in (0, 1]")
        if not 0 < self.min_weight_mass_coverage <= 1:
            raise ValueError("min_weight_mass_coverage must be in (0, 1]")
        if not 0 <= self.trim_fraction < 0.5:
            raise ValueError("trim_fraction must be in [0, 0.5)")
        if not 0 <= self.shock_adjustment_strength <= 1:
            raise ValueError("shock_adjustment_strength must be in [0, 1]")


def _require(frame: pd.DataFrame, columns: Iterable[str], label: str) -> None:
    missing = sorted(set(columns).difference(frame.columns))
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _as_utc(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="raise", utc=True)


def _month_start(series: pd.Series) -> pd.Series:
    # Drop timezone before converting to Period to avoid pandas' timezone warning.
    values = pd.to_datetime(series, errors="raise")
    if getattr(values.dt, "tz", None) is not None:
        values = values.dt.tz_localize(None)
    return values.dt.to_period("M").dt.to_timestamp()


def _weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    mask = values.notna() & weights.notna() & (weights > 0)
    if not mask.any():
        return np.nan
    return float(np.average(values[mask], weights=weights[mask]))


def _weighted_median(values: pd.Series, weights: pd.Series) -> float:
    mask = values.notna() & weights.notna() & (weights > 0)
    if not mask.any():
        return np.nan
    ordered = pd.DataFrame({"value": values[mask], "weight": weights[mask]}).sort_values("value")
    cutoff = ordered["weight"].sum() / 2
    return float(ordered.loc[ordered["weight"].cumsum() >= cutoff, "value"].iloc[0])


def _trimmed_mean(values: pd.Series, fraction: float) -> float:
    clean = np.sort(values.dropna().to_numpy(dtype=float))
    if clean.size == 0:
        return np.nan
    trim = int(np.floor(clean.size * fraction))
    if trim and clean.size > 2 * trim:
        clean = clean[trim:-trim]
    return float(clean.mean())


def _latest_non_null(series: pd.Series) -> object:
    clean = series.dropna()
    return clean.iloc[-1] if len(clean) else np.nan


def _prepare_observations(
    observations: pd.DataFrame,
    cutoff: str | pd.Timestamp | None,
) -> pd.DataFrame:
    required = [
        "harmonized_product_id",
        "reference_period_start",
        "reference_period_end",
        "available_at",
    ]
    _require(observations, required, "observations")
    price_column = "standardized_price" if "standardized_price" in observations else "raw_price"
    _require(observations, [price_column], "observations")
    frame = observations.copy()
    frame["available_at"] = _as_utc(frame["available_at"])
    frame["reference_period_start"] = pd.to_datetime(frame["reference_period_start"], errors="raise")
    frame["reference_period_end"] = pd.to_datetime(frame["reference_period_end"], errors="raise")
    frame["price"] = pd.to_numeric(frame[price_column], errors="coerce")
    frame["month"] = _month_start(frame["reference_period_end"])
    if cutoff is not None:
        cutoff_ts = pd.Timestamp(cutoff)
        cutoff_ts = cutoff_ts.tz_localize("UTC") if cutoff_ts.tzinfo is None else cutoff_ts.tz_convert("UTC")
        frame = frame.loc[frame["available_at"] <= cutoff_ts].copy()
    if "observation_status" in frame:
        frame = frame.loc[frame["observation_status"].eq("observed")].copy()
    frame = frame.loc[frame["price"].notna() & frame["price"].gt(0)].copy()
    frame["represented_days"] = (
        frame["reference_period_end"] - frame["reference_period_start"]
    ).dt.days.add(1).clip(lower=1)
    frame = frame.sort_values(
        ["harmonized_product_id", "reference_period_end", "available_at"],
        kind="mergesort",
    )
    # If a source revision is public by the cutoff, use the latest public vintage of
    # that exact product/reference period.  Earlier raw vintages remain in raw data.
    frame = frame.drop_duplicates(
        ["harmonized_product_id", "reference_period_start", "reference_period_end"],
        keep="last",
    )
    return frame


def aggregate_monthly_prices(
    observations: pd.DataFrame,
    *,
    aggregation_method: str,
    forecast_vintage: str,
    cutoff: str | pd.Timestamp | None = None,
    processed_at: str | pd.Timestamp | None = None,
    config: FeatureConfig | None = None,
) -> pd.DataFrame:
    """Aggregate eligible ten-day price levels without using future releases.

    Supported methods are ``monthly_average``, ``end_to_end`` and
    ``day_weighted_average``.  The latter weights a ten-day observation by the
    number of calendar days represented by its stated reference interval.
    """

    config = config or FeatureConfig()
    allowed = {"monthly_average", "end_to_end", "day_weighted_average"}
    if aggregation_method not in allowed:
        raise ValueError(f"aggregation_method must be one of {sorted(allowed)}")
    frame = _prepare_observations(observations, cutoff)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "month", "forecast_vintage", "harmonized_product_id",
                "aggregation_method", "transformation_version", "aggregated_price",
                "first_price", "last_price", "observation_count", "represented_days",
                "available_at", "forecast_cutoff", "processed_at", "schema_version",
                "source_snapshot_hash",
            ]
        )
    processed_ts = pd.Timestamp.now(tz="UTC") if processed_at is None else pd.Timestamp(processed_at)
    processed_ts = processed_ts.tz_localize("UTC") if processed_ts.tzinfo is None else processed_ts.tz_convert("UTC")
    if cutoff is None:
        cutoff_ts = frame["available_at"].max()
    else:
        cutoff_ts = pd.Timestamp(cutoff)
        cutoff_ts = cutoff_ts.tz_localize("UTC") if cutoff_ts.tzinfo is None else cutoff_ts.tz_convert("UTC")
    if "source_snapshot_hash" in frame and frame["source_snapshot_hash"].notna().any():
        snapshot_hash = hashlib.sha256(
            "|".join(sorted(frame["source_snapshot_hash"].dropna().astype(str).unique())).encode()
        ).hexdigest()
    else:
        identity_columns = [
            column for column in ("observation_id", "harmonized_product_id", "reference_period_end", "price")
            if column in frame
        ]
        snapshot_hash = hashlib.sha256(
            frame[identity_columns].astype(str).to_csv(index=False).encode()
        ).hexdigest()
    group_columns = ["month", "harmonized_product_id"]
    rows: list[dict[str, object]] = []
    carry_columns = [
        column for column in ("category_id", "product_family_id", "ppi_industry_id", "data_quality")
        if column in frame
    ]
    for (month, product_id), group in frame.groupby(group_columns, sort=True):
        group = group.sort_values(["reference_period_end", "available_at"], kind="mergesort")
        if aggregation_method == "monthly_average":
            aggregated = float(group["price"].mean())
        elif aggregation_method == "day_weighted_average":
            aggregated = _weighted_mean(group["price"], group["represented_days"])
        else:
            aggregated = float(group["price"].iloc[-1])
        row: dict[str, object] = {
            "month": pd.Timestamp(month),
            "forecast_vintage": forecast_vintage,
            "harmonized_product_id": product_id,
            "aggregation_method": aggregation_method,
            "transformation_version": config.transformation_version,
            "aggregated_price": aggregated,
            "first_price": float(group["price"].iloc[0]),
            "last_price": float(group["price"].iloc[-1]),
            "observation_count": int(len(group)),
            "represented_days": int(group["represented_days"].sum()),
            "available_at": group["available_at"].max(),
            "forecast_cutoff": cutoff_ts,
            "processed_at": processed_ts,
            "schema_version": "0.1.0",
            "source_snapshot_hash": snapshot_hash,
        }
        for column in carry_columns:
            row[column] = _latest_non_null(group[column])
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["harmonized_product_id", "month"]).reset_index(drop=True)


def classify_regime(
    monthly_change: float | None,
    change_3m: float | None,
    yoy_change: float | None,
    yoy_acceleration: float | None,
    *,
    shock_flag: bool = False,
    policy_flag: bool = False,
) -> str:
    """Transparent initial seven-state classification; continuous inputs remain."""

    values = np.array([monthly_change, change_3m, yoy_change, yoy_acceleration], dtype=float)
    mom, three, yoy, accel = values
    if policy_flag and np.isfinite(mom) and mom > 0:
        return "policy_induced_repricing"
    if shock_flag and np.isfinite(mom) and np.isfinite(accel) and mom * accel < 0:
        return "shock_normalization"
    if np.isfinite(yoy) and np.isfinite(three) and np.isfinite(mom):
        if yoy > 0 and three > 0 and mom > 0:
            return "persistent_structural_uplift"
        if yoy > 0 and three <= 0 and mom > 0:
            return "elevated_level_reacceleration"
        if yoy <= 0 and three > 0 and mom > 0:
            return "cyclical_rebound"
        if yoy < 0 and three < 0 and mom <= 0:
            return "persistent_weakness"
    return "mixed_uncertain"


def build_product_features(
    monthly_prices: pd.DataFrame,
    *,
    config: FeatureConfig | None = None,
) -> pd.DataFrame:
    """Create product features while retaining rows with insufficient history."""

    config = config or FeatureConfig()
    required = [
        "month", "forecast_vintage", "harmonized_product_id", "aggregation_method",
        "transformation_version", "aggregated_price", "first_price", "last_price",
        "observation_count", "available_at", "forecast_cutoff", "processed_at",
        "schema_version", "source_snapshot_hash",
    ]
    _require(monthly_prices, required, "monthly_prices")
    if monthly_prices.empty:
        return monthly_prices.copy()
    frame = monthly_prices.copy()
    frame["month"] = pd.to_datetime(frame["month"])
    frame["available_at"] = _as_utc(frame["available_at"])
    key = [
        "forecast_vintage", "aggregation_method", "transformation_version",
        "harmonized_product_id",
    ]
    frame = frame.sort_values(key + ["month"], kind="mergesort")
    grouped = frame.groupby(key, sort=False, group_keys=False)
    frame["history_count"] = grouped.cumcount().add(1)
    frame["change_10d"] = grouped["last_price"].pct_change(fill_method=None).mul(100)
    frame["change_20d"] = grouped["last_price"].pct_change(2, fill_method=None).mul(100)
    frame["intra_month_change"] = (frame["last_price"] / frame["first_price"] - 1).mul(100)
    frame["monthly_avg_change"] = grouped["aggregated_price"].pct_change(fill_method=None).mul(100)
    frame["month_end_change"] = grouped["last_price"].pct_change(fill_method=None).mul(100)
    frame["change_3m"] = grouped["aggregated_price"].pct_change(3, fill_method=None).mul(100)
    frame["change_6m"] = grouped["aggregated_price"].pct_change(6, fill_method=None).mul(100)
    frame["yoy_change"] = grouped["aggregated_price"].pct_change(12, fill_method=None).mul(100)
    frame["yoy_acceleration"] = grouped["yoy_change"].diff()

    frame["z_score"] = np.nan
    frame["history_percentile"] = np.nan
    frame["volatility"] = np.nan
    for _, indices in frame.groupby(key, sort=False).groups.items():
        signal = frame.loc[indices, "monthly_avg_change"]
        rolling = signal.shift(1).rolling(
            config.rolling_standardization_months,
            min_periods=config.rolling_min_periods,
        )
        mean = rolling.mean()
        std = rolling.std(ddof=1).replace(0, np.nan)
        frame.loc[indices, "z_score"] = ((signal - mean) / std).to_numpy()
        percentile = signal.expanding(config.rolling_min_periods).apply(
            lambda values: float(np.mean(values[:-1] <= values[-1])) if len(values) > 1 else np.nan,
            raw=True,
        )
        frame.loc[indices, "history_percentile"] = percentile.to_numpy()
        frame.loc[indices, "volatility"] = rolling.std(ddof=1).to_numpy()
    frame["history_eligible"] = frame["history_count"].ge(config.min_product_history)
    frame["feature_status"] = np.where(frame["history_eligible"], "valid", "insufficient_history")
    shock_flags = frame["shock_flag"].fillna(False).astype(bool) if "shock_flag" in frame else pd.Series(False, index=frame.index)
    policy_flags = frame["policy_flag"].fillna(False).astype(bool) if "policy_flag" in frame else pd.Series(False, index=frame.index)
    frame["regime"] = [
        classify_regime(mom, three, yoy, accel, shock_flag=shock, policy_flag=policy)
        for mom, three, yoy, accel, shock, policy in zip(
            frame["monthly_avg_change"], frame["change_3m"], frame["yoy_change"],
            frame["yoy_acceleration"], shock_flags, policy_flags,
        )
    ]
    return frame.sort_values(key + ["month"]).reset_index(drop=True)


def _attach_signal_multipliers(
    frame: pd.DataFrame,
    event_flags: pd.DataFrame | None,
    config: FeatureConfig,
) -> pd.DataFrame:
    result = frame.copy()
    result["signal_multiplier"] = 1.0
    result["shock_flag"] = False
    result["policy_flag"] = False
    if event_flags is None or event_flags.empty:
        return result
    _require(event_flags, ["entity_id", "start_date", "available_at"], "event_flags")
    events = event_flags.copy()
    events["start_date"] = pd.to_datetime(events["start_date"])
    events["end_date"] = pd.to_datetime(events.get("end_date"), errors="coerce")
    events["available_at"] = _as_utc(events["available_at"])
    events["confidence"] = pd.to_numeric(events.get("confidence", 1.0), errors="coerce").fillna(0).clip(0, 1)
    for index, row in result.iterrows():
        row_cutoff = row.get("forecast_cutoff", row["available_at"])
        entity_ids = {
            str(row[column])
            for column in ("harmonized_product_id", "product_family_id", "category_id", "ppi_industry_id")
            if column in row.index and pd.notna(row[column])
        }
        matches = events.loc[
            events["entity_id"].astype(str).isin(entity_ids)
            & events["available_at"].le(row_cutoff)
            & events["start_date"].le(row["month"] + pd.offsets.MonthEnd(0))
            & (events["end_date"].isna() | events["end_date"].ge(row["month"]))
        ]
        if matches.empty:
            continue
        confidence = float(matches["confidence"].max())
        # This multiplier is applied to the price *signal* below, never to the
        # product's economic/PPI weight.
        result.at[index, "signal_multiplier"] = max(
            0.0, 1.0 - config.shock_adjustment_strength * confidence
        )
        result.at[index, "shock_flag"] = True
        if "shock_type" in matches:
            result.at[index, "policy_flag"] = matches["shock_type"].astype(str).str.contains(
                "policy", case=False
            ).any()
    return result


def build_category_features(
    product_features: pd.DataFrame,
    *,
    weights: pd.DataFrame | None = None,
    weight_variant: str = "equal_product",
    shock_scenario: str = "baseline",
    event_flags: pd.DataFrame | None = None,
    expected_product_counts: pd.DataFrame | None = None,
    config: FeatureConfig | None = None,
) -> pd.DataFrame:
    """Aggregate product signals into category factors with explicit coverage.

    ``shock_adjusted`` multiplies signals by an event-derived multiplier.  It does
    not alter the selected weights.  ``robust`` winsorizes signals cross-sectionally
    within each month/category using only observations in that vintage.
    """

    config = config or FeatureConfig()
    if shock_scenario not in {"baseline", "robust", "shock_adjusted"}:
        raise ValueError("unknown shock_scenario")
    required = [
        "month", "forecast_vintage", "harmonized_product_id", "category_id",
        "aggregation_method", "transformation_version", "available_at",
        "processed_at", "history_eligible", "monthly_avg_change",
    ]
    _require(product_features, required, "product_features")
    frame = _attach_signal_multipliers(product_features, event_flags, config)
    if weights is None:
        frame["model_weight"] = 1.0
    else:
        _require(weights, ["effective_date", "available_at", "harmonized_product_id", "weight_variant", "composite_weight"], "weights")
        weight_frame = weights.loc[weights["weight_variant"].eq(weight_variant)].copy()
        weight_frame["effective_date"] = pd.to_datetime(weight_frame["effective_date"])
        weight_frame["available_at"] = _as_utc(weight_frame["available_at"])
        # A row receives the latest structural weight both effective and public by
        # that feature's source availability.  Future revisions cannot leak back.
        assigned: list[float] = []
        for _, row in frame.iterrows():
            eligible = weight_frame.loc[
                weight_frame["harmonized_product_id"].eq(row["harmonized_product_id"])
                & weight_frame["effective_date"].le(row["month"])
                & weight_frame["available_at"].le(row.get("forecast_cutoff", row["available_at"]))
            ].sort_values(["effective_date", "available_at"])
            assigned.append(float(eligible["composite_weight"].iloc[-1]) if len(eligible) else np.nan)
        frame["model_weight"] = assigned
    frame["unadjusted_model_weight"] = frame["model_weight"]
    if shock_scenario == "shock_adjusted":
        for column in SIGNAL_COLUMNS:
            if column in frame:
                frame[column] = frame[column] * frame["signal_multiplier"]
    group_keys = [
        "month", "forecast_vintage", "category_id", "aggregation_method",
        "transformation_version",
    ]
    if expected_product_counts is not None:
        _require(expected_product_counts, ["month", "category_id", "expected_product_count"], "expected_product_counts")
        denominators = expected_product_counts.copy()
        denominators["month"] = pd.to_datetime(denominators["month"])
    else:
        # The observed category membership at each month is the non-aggressive
        # default.  A curated active-basket denominator should be supplied when
        # available; it may not be inferred from future product appearances.
        denominators = (
            frame.groupby(["month", "category_id"])["harmonized_product_id"]
            .nunique().rename("expected_product_count").reset_index()
        )
    rows: list[dict[str, object]] = []
    for keys, group in frame.groupby(group_keys, sort=True):
        month, vintage, category, method, version = keys
        eligible = group.loc[group["history_eligible"] & group["model_weight"].notna()].copy()
        signal = eligible["monthly_avg_change"].copy()
        if shock_scenario == "robust" and len(signal) > 1:
            lower, upper = signal.quantile([config.robust_lower_quantile, config.robust_upper_quantile])
            signal = signal.clip(lower=lower, upper=upper)
        denominator_match = denominators.loc[
            denominators["month"].eq(month) & denominators["category_id"].eq(category),
            "expected_product_count",
        ]
        expected = int(denominator_match.iloc[-1]) if len(denominator_match) else int(group["harmonized_product_id"].nunique())
        active = int(eligible["harmonized_product_id"].nunique())
        coverage = active / expected if expected else 0.0
        weights_here = eligible["model_weight"]
        total_known_weight = group["model_weight"].dropna().sum()
        eligible_weight = weights_here.dropna().sum()
        weight_mass_coverage = (
            float(eligible_weight / total_known_weight) if total_known_weight > 0 else np.nan
        )
        weight_mass_valid = (
            True if weight_variant in {"equal_product", "equal_category"}
            else bool(np.isfinite(weight_mass_coverage) and weight_mass_coverage >= config.min_weight_mass_coverage)
        )
        valid = (
            active >= config.min_category_products
            and coverage >= config.min_category_coverage
            and weight_mass_valid
        )
        positive = signal.gt(0)
        negative = signal.lt(0)
        unchanged = signal.eq(0)
        metrics = {
            "weighted_mean_change": _weighted_mean(signal, weights_here),
            "weighted_median_change": _weighted_median(signal, weights_here),
            "trimmed_mean_change": _trimmed_mean(signal, config.trim_fraction),
            "share_rising": float(positive.mean()) if active else np.nan,
            "share_falling": float(negative.mean()) if active else np.nan,
            "share_unchanged": float(unchanged.mean()) if active else np.nan,
            "diffusion": float(positive.mean() - negative.mean()) if active else np.nan,
            "volatility": float(signal.std(ddof=1)) if active > 1 else np.nan,
        }
        if not valid:
            metrics = {name: np.nan for name in metrics}
        rows.append({
            "month": month,
            "forecast_vintage": vintage,
            "category_id": category,
            "weight_variant": weight_variant,
            "shock_scenario": shock_scenario,
            "aggregation_method": method,
            "transformation_version": version,
            **metrics,
            "active_product_count": active,
            "expected_product_count": expected,
            "coverage_ratio": coverage,
            "weight_mass_coverage": weight_mass_coverage,
            "feature_status": "valid" if valid else "insufficient_coverage",
            "available_at": eligible["available_at"].max() if active else group["available_at"].max(),
            "processed_at": group["processed_at"].max(),
            "forecast_cutoff": group["forecast_cutoff"].max() if "forecast_cutoff" in group else group["available_at"].max(),
            "schema_version": str(group["schema_version"].iloc[-1]) if "schema_version" in group else "0.1.0",
            "source_snapshot_hash": str(group["source_snapshot_hash"].iloc[-1]) if "source_snapshot_hash" in group else "",
            "shock_affected_product_count": int(eligible["shock_flag"].sum()) if active else 0,
        })
    return pd.DataFrame(rows).sort_values(group_keys).reset_index(drop=True)


def build_feature_panel(
    observations: pd.DataFrame,
    *,
    aggregation_method: str,
    forecast_vintage: str,
    cutoff: str | pd.Timestamp | None = None,
    processed_at: str | pd.Timestamp | None = None,
    weights: pd.DataFrame | None = None,
    weight_variant: str = "equal_product",
    shock_scenario: str = "baseline",
    event_flags: pd.DataFrame | None = None,
    expected_product_counts: pd.DataFrame | None = None,
    config: FeatureConfig | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convenience pipeline returning product and category feature panels."""

    config = config or FeatureConfig()
    monthly = aggregate_monthly_prices(
        observations,
        aggregation_method=aggregation_method,
        forecast_vintage=forecast_vintage,
        cutoff=cutoff,
        processed_at=processed_at,
        config=config,
    )
    product = build_product_features(monthly, config=config)
    category = build_category_features(
        product,
        weights=weights,
        weight_variant=weight_variant,
        shock_scenario=shock_scenario,
        event_flags=event_flags,
        expected_product_counts=expected_product_counts,
        config=config,
    )
    return product, category

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from china_ppi_nowcast.features.engineering import (
    FeatureConfig,
    aggregate_monthly_prices,
    build_category_features,
    build_product_features,
)
from china_ppi_nowcast.features.matrices import category_feature_matrix
from china_ppi_nowcast.models.base import validate_sample_size
from china_ppi_nowcast.models.forecasting import reconcile_yoy_to_mom, yoy_from_mom_path
from china_ppi_nowcast.models.linear import fit_linear


def _observations(months: int = 5) -> pd.DataFrame:
    rows = []
    for month_index, month in enumerate(pd.date_range("2024-01-01", periods=months, freq="MS")):
        last_day = (month + pd.offsets.MonthEnd()).day
        for product, base in (("HP_a", 100.0), ("HP_b", 200.0)):
            for slot, (start, end) in enumerate(((1, 10), (11, 20), (21, last_day))):
                rows.append(
                    {
                        "observation_id": f"{month:%Y%m}_{product}_{slot}",
                        "harmonized_product_id": product,
                        "category_id": "CAT_metals",
                        "reference_period_start": month + pd.Timedelta(days=start - 1),
                        "reference_period_end": month + pd.Timedelta(days=end - 1),
                        "available_at": (month + pd.Timedelta(days=end + 2)).tz_localize("UTC"),
                        "standardized_price": base * (1 + 0.01 * (month_index + slot)),
                        "observation_status": "observed",
                    }
                )
    return pd.DataFrame(rows)


def test_cutoff_uses_public_available_at_not_processed_at_and_keeps_keys() -> None:
    observations = _observations(1)
    cutoff = pd.Timestamp("2024-01-23T00:00:00Z")
    result = aggregate_monthly_prices(
        observations,
        aggregation_method="monthly_average",
        forecast_vintage="mid",
        cutoff=cutoff,
        processed_at="2099-01-01T00:00:00Z",
    )
    # Late-period release is not public at the cutoff; future processing time does
    # not affect eligibility.
    assert set(result["observation_count"]) == {2}
    assert result["available_at"].max() <= cutoff
    assert result["processed_at"].min() > cutoff
    assert set(result["aggregation_method"]) == {"monthly_average"}
    assert set(result["transformation_version"]) == {"market_price_features_v1"}
    assert result["source_snapshot_hash"].str.len().eq(64).all()


def test_insufficient_history_and_coverage_are_retained_not_dropped() -> None:
    monthly = aggregate_monthly_prices(
        _observations(2),
        aggregation_method="end_to_end",
        forecast_vintage="final",
        cutoff="2024-03-10T00:00:00Z",
        processed_at="2024-03-10T00:00:00Z",
    )
    products = build_product_features(monthly, config=FeatureConfig(min_product_history=3))
    assert len(products) == 4
    assert products["feature_status"].eq("insufficient_history").all()

    # Lower the history gate but supply a curated active-basket denominator of 3:
    # 2 / 3 is below the adjudicated 70% coverage threshold.
    products = build_product_features(monthly, config=FeatureConfig(min_product_history=2))
    expected = pd.DataFrame(
        {
            "month": pd.date_range("2024-01-01", periods=2, freq="MS"),
            "category_id": ["CAT_metals", "CAT_metals"],
            "expected_product_count": [3, 3],
        }
    )
    categories = build_category_features(
        products,
        expected_product_counts=expected,
        config=FeatureConfig(min_product_history=2, min_category_products=2),
    )
    february = categories.loc[categories["month"].eq(pd.Timestamp("2024-02-01"))].iloc[0]
    assert february["coverage_ratio"] == pytest.approx(2 / 3)
    assert february["feature_status"] == "insufficient_coverage"
    assert np.isnan(february["weighted_mean_change"])


def test_shock_multiplier_changes_signal_not_economic_weight() -> None:
    product = pd.DataFrame(
        {
            "month": [pd.Timestamp("2026-08-01")] * 2,
            "forecast_vintage": ["final"] * 2,
            "harmonized_product_id": ["HP_a", "HP_b"],
            "category_id": ["CAT_metals"] * 2,
            "aggregation_method": ["monthly_average"] * 2,
            "transformation_version": ["v1"] * 2,
            "available_at": pd.to_datetime(["2026-09-03T00:00:00Z", "2026-09-03T00:00:00Z"]),
            "forecast_cutoff": pd.to_datetime(["2026-09-04T00:00:00Z", "2026-09-04T00:00:00Z"]),
            "processed_at": pd.to_datetime(["2026-09-04T00:00:00Z", "2026-09-04T00:00:00Z"]),
            "history_eligible": [True, True],
            "monthly_avg_change": [10.0, 0.0],
            "schema_version": ["0.1.0"] * 2,
            "source_snapshot_hash": ["x"] * 2,
        }
    )
    weights = pd.DataFrame(
        {
            "effective_date": pd.to_datetime(["2026-01-01", "2026-01-01"]),
            "available_at": pd.to_datetime(["2026-02-01T00:00:00Z", "2026-02-01T00:00:00Z"]),
            "harmonized_product_id": ["HP_a", "HP_b"],
            "weight_variant": ["industry_output"] * 2,
            "composite_weight": [0.8, 0.2],
        }
    )
    events = pd.DataFrame(
        {
            "entity_id": ["HP_a"],
            "start_date": ["2026-08-01"],
            "end_date": ["2026-08-31"],
            "available_at": ["2026-08-15T00:00:00Z"],
            "confidence": [0.5],
            "shock_type": ["policy_restriction"],
        }
    )
    baseline = build_category_features(product, weights=weights, weight_variant="industry_output")
    adjusted = build_category_features(
        product,
        weights=weights,
        weight_variant="industry_output",
        shock_scenario="shock_adjusted",
        event_flags=events,
    )
    assert baseline.iloc[0]["weighted_mean_change"] == pytest.approx(8.0)
    assert adjusted.iloc[0]["weighted_mean_change"] == pytest.approx(4.0)
    # Same known-weight coverage proves the scenario did not downweight the weight series.
    assert adjusted.iloc[0]["weight_mass_coverage"] == baseline.iloc[0]["weight_mass_coverage"]


def test_matrix_requires_explicit_matching_method_and_version() -> None:
    frame = pd.DataFrame(
        {
            "month": ["2024-01-01"],
            "forecast_vintage": ["final"],
            "category_id": ["CAT_a"],
            "available_at": ["2024-02-03T00:00:00Z"],
            "aggregation_method": ["monthly_average"],
            "transformation_version": ["v1"],
            "weighted_mean_change": [1.0],
            "diffusion": [0.5],
        }
    )
    with pytest.raises(ValueError, match="no rows match"):
        category_feature_matrix(
            frame,
            aggregation_method="end_to_end",
            transformation_version="v1",
        )


def test_regularized_history_gate_and_exact_linear_attribution() -> None:
    with pytest.raises(ValueError, match="required=60"):
        validate_sample_size("ridge", 59, 10, regularized=True)
    rng = np.random.default_rng(7)
    X = pd.DataFrame(rng.normal(size=(60, 2)), columns=["coal", "chemicals"])
    y = 0.2 + 0.4 * X["coal"] - 0.1 * X["chemicals"]
    model = fit_linear(X, y, feature_names=list(X), family="ridge", alpha=0.01)
    row = X.iloc[[0]]
    assert sum(model.contributions(row).values()) == pytest.approx(model.predict(row)[0])


def test_mom_primary_yoy_identity_reports_reconciliation_residual() -> None:
    previous = np.repeat(0.1, 11)
    mechanical = yoy_from_mom_path(np.r_[previous, 0.2])
    result = reconcile_yoy_to_mom(
        0.2,
        previous,
        historical_reconciliation_residuals=np.repeat(0.03, 20),
    )
    assert result.mechanical_yoy == pytest.approx(mechanical)
    assert result.reconciliation_residual == pytest.approx(0.03)
    assert result.reconciled_yoy == pytest.approx(mechanical + 0.03)

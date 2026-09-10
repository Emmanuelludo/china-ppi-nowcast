from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from china_ppi_nowcast.events.catalog import build_event_catalog
from china_ppi_nowcast.events.flags import events_available_at, expand_event_flags
from china_ppi_nowcast.external.catalog import PUBLIC_SERIES
from china_ppi_nowcast.external.ingest import monthly_external_features
from china_ppi_nowcast.weights.builder import combine_hybrid_weights, latest_available_weights


ROOT = Path(__file__).resolve().parents[1]


def test_recovered_external_artifacts_have_expected_reproducible_counts() -> None:
    raw = pd.read_csv(ROOT / "data/interim/external/raw_external_observations.csv")
    monthly = pd.read_csv(ROOT / "data/interim/external/external_features_monthly.csv")
    assert len(raw) == 21_095
    assert len(monthly) == 1_919
    assert raw["observation_id"].is_unique
    assert not raw["strict_backtest_eligible"].astype(bool).any()
    assert not monthly["strict_backtest_eligible"].astype(bool).any()


def test_external_monthly_availability_is_latest_input_availability() -> None:
    raw = pd.read_csv(ROOT / "data/interim/external/raw_external_observations.csv")
    catalog = {item.series_id: item for item in PUBLIC_SERIES}
    rebuilt = monthly_external_features(raw, catalog)
    raw["month"] = pd.to_datetime(raw["date"]).dt.to_period("M").dt.to_timestamp()
    expected = pd.to_datetime(raw["available_at"], utc=True).groupby([raw["series_id"], raw["month"]]).max()
    actual = pd.to_datetime(rebuilt["available_at"], utc=True)
    keys = list(zip(rebuilt["series_id"], pd.to_datetime(rebuilt["date"]), strict=True))
    assert all(value == expected.loc[key] for key, value in zip(keys, actual, strict=True))


def test_current_snapshot_cannot_enter_strict_backtest() -> None:
    monthly = pd.read_csv(ROOT / "data/interim/external/external_features_monthly.csv")
    candidate = monthly.loc[pd.to_datetime(monthly["available_at"], utc=True) <= pd.Timestamp("2022-12-31", tz="UTC")]
    strict = candidate.loc[candidate["strict_backtest_eligible"].astype(bool)]
    assert strict.empty


def test_equal_weights_sum_to_one_and_are_not_official() -> None:
    panel = pd.read_csv(ROOT / "data/interim/weights/historical_weight_panel.csv")
    sums = panel.groupby(["effective_date", "weight_variant"])["composite_weight"].sum()
    assert np.allclose(sums.to_numpy(), 1.0)
    assert set(panel["weight_variant"]) == {"equal_product", "equal_category"}
    assert not panel["is_official_weight"].astype(bool).any()


def test_weight_asof_selection_excludes_future_release() -> None:
    panel = pd.DataFrame(
        {
            "harmonized_product_id": ["HP_a", "HP_a"],
            "weight_variant": ["equal_product", "equal_product"],
            "effective_date": ["2025-01-01", "2026-01-01"],
            "available_at": ["2025-01-05T00:00:00Z", "2026-01-15T00:00:00Z"],
            "composite_weight": [1.0, 1.0],
        }
    )
    selected = latest_available_weights(panel, "2026-01-10T00:00:00Z", "2026-01-31")
    assert selected["effective_date"].tolist() == ["2025-01-01"]


def test_hybrid_refuses_missing_inputs_and_normalises_observed_inputs() -> None:
    missing = pd.DataFrame({"harmonized_product_id": ["HP_a"], "economic_weight": [np.nan], "predictive_weight": [1.0], "data_quality_weight": [1.0]})
    try:
        combine_hybrid_weights(missing)
    except ValueError as exc:
        assert "no silent fill" in str(exc)
    else:
        raise AssertionError("missing economic weights must not be imputed")
    observed = pd.DataFrame({"harmonized_product_id": ["HP_a", "HP_b"], "economic_weight": [0.75, 0.25], "predictive_weight": [2.0, -1.0], "data_quality_weight": [1.0, 0.5]})
    result = combine_hybrid_weights(observed)
    assert np.isclose(result["composite_weight"].sum(), 1.0)
    assert result["predictive_sign"].tolist() == [1.0, -1.0]


def test_event_entities_reconcile_to_shared_taxonomy_and_fertilizers_are_split() -> None:
    events = build_event_catalog()
    ids = set(events["entity_id"])
    assert {"CAT_ferrous_metals", "PF_solar_materials", "CAT_petroleum_gas"}.issubset(ids)
    fertilizer = events.loc[events["event_name"].str.contains("Fertilizer")]
    assert set(fertilizer["entity_id"]) == {
        "PF_nitrogen_fertilizer",
        "PF_phosphate_fertilizer",
        "PF_potash_fertilizer",
        "PF_compound_fertilizer",
    }
    assert fertilizer["event_id"].nunique() == 1

    categories = set(pd.read_csv(ROOT / "data/interim/harmonization/categories.csv")["category_id"])
    families = set(pd.read_csv(ROOT / "data/interim/harmonization/product_families.csv")["product_family_id"])
    for event in events.itertuples(index=False):
        permitted = categories if event.entity_level == "category" else families
        assert event.entity_id in permitted


def test_events_are_unavailable_before_publication_and_active_only_in_interval() -> None:
    events = build_event_catalog()
    assert events_available_at(events, "2021-06-01T00:00:00Z").empty
    expanded = expand_event_flags(events, ["2021-10-14", "2021-10-20", "2023-01-01"], "2021-10-21T00:00:00Z")
    fertilizer = expanded.loc[expanded["entity_id"].str.contains("fertilizer")]
    assert set(pd.to_datetime(fertilizer["date"]).dt.date.astype(str)) == {"2021-10-20"}
    assert not (pd.to_datetime(expanded["available_at"], utc=True) > pd.Timestamp("2021-10-21", tz="UTC")).any()

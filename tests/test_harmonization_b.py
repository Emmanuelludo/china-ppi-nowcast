from pathlib import Path

import pandas as pd

from china_ppi_nowcast.harmonize.build import build_harmonization_artifacts
from china_ppi_nowcast.harmonize.ontology import (
    HarmonizationRegistry,
    make_exact_product_id,
    normalize_identity_text,
)
from china_ppi_nowcast.harmonize.units import convert_price


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/interim/harmonization"


def test_exact_id_is_deterministic_across_unicode_punctuation():
    left = make_exact_product_id("螺纹钢", "Φ20mm，HRB400E", "tonne", "rebar")
    right = make_exact_product_id("螺纹钢", "Φ20mm, HRB400E", "tonne", "rebar")
    assert left == right
    assert normalize_identity_text(" 5／6 mm ") == "5/6mm"


def test_recovered_dictionary_and_baskets_have_expected_cardinality():
    products = pd.read_csv(DATA / "product_dictionary.csv")
    categories = pd.read_csv(DATA / "categories.csv")
    membership = pd.read_csv(DATA / "basket_membership.csv")
    assert len(products) == 58  # 50 old + 7 replacements + one separately versioned glass spec
    assert products["exact_product_id"].is_unique
    assert len(categories) == 9
    assert {"CAT_ferrous_metals", "CAT_petroleum_gas"}.issubset(set(categories["category_id"]))
    assert "PF_solar_materials" in set(products["product_family_id"])
    assert membership.groupby("basket_snapshot_id").size().to_dict() == {
        "BASKET_2025_09_OFFICIAL_EN": 50,
        "BASKET_2026_01_OFFICIAL_EN": 50,
    }


def test_2025_english_release_never_enters_realtime_on_september_14():
    snapshots = pd.read_csv(DATA / "basket_snapshots.csv")
    row = snapshots.loc[snapshots["basket_snapshot_id"].eq("BASKET_2025_09_OFFICIAL_EN")].iloc[0]
    available = pd.Timestamp(row["available_at"])
    assert available.date() >= pd.Timestamp("2025-09-15").date()
    assert available.date() != pd.Timestamp(row["publication_datetime_displayed"]).date()


def test_2026_official_change_accounting_is_seven_in_and_seven_out():
    changes = pd.read_csv(DATA / "basket_changes.csv")
    official = changes.loc[changes["official_change_counted"].astype(bool)]
    assert (official["change_type"] == "added").sum() == 7
    assert (official["change_type"] == "removed").sum() == 7
    assert (changes["change_type"] == "specification_change").sum() == 1


def test_discontinued_products_are_preserved_not_spliced_to_replacements():
    products = pd.read_csv(DATA / "product_dictionary.csv")
    removed = products.loc[products["normalized_name_en"].isin(["Styrene", "Polyvinyl Chloride"])]
    assert len(removed) == 2
    assert set(removed["end_date"]) == {"2025-12-31"}
    assert removed["harmonized_product_id"].notna().all()


def test_float_glass_spec_change_is_explicit_and_blocks_raw_level_splice():
    lineage = pd.read_csv(DATA / "product_lineage.csv")
    row = lineage.iloc[0]
    assert row["relationship_type"] == "partially_comparable"
    assert pd.isna(row["adjustment_factor"])
    matrix = pd.read_csv(DATA / "comparability_matrix.csv")
    link = matrix.loc[
        matrix["left_exact_product_id"].eq(row["predecessor_id"])
        & matrix["right_exact_product_id"].eq(row["successor_id"])
    ].iloc[0]
    assert link["relationship_type"] == "partially_comparable"
    assert not bool(link["raw_level_splice_permitted"])


def test_registry_matches_curated_alias_but_does_not_fuzzy_match():
    registry = HarmonizationRegistry.from_directory(DATA)
    exact = registry.match_exact("Rebar (Φ20mm, HRB400E)", unit="ton")
    fuzzy = registry.match_exact("roughly similar steel rebar", unit="tonne")
    assert exact.exact_product_id is not None
    assert exact.mapping_status == "exact_curated_alias"
    assert fuzzy.exact_product_id is None
    assert fuzzy.mapping_status == "unmatched"


def test_mapping_preserves_unmatched_observations():
    registry = HarmonizationRegistry.from_directory(DATA)
    source = pd.DataFrame([
        {"observation_id": "a", "raw_product_name": "Rebar (Φ20mm, HRB400E)", "specification": "", "original_unit": "tonne"},
        {"observation_id": "b", "raw_product_name": "Unknown commodity", "specification": "", "original_unit": "tonne"},
    ])
    mapped = registry.map_frame(source)
    assert list(mapped["observation_id"]) == ["a", "b"]
    assert mapped.loc[mapped["observation_id"].eq("b"), "mapping_status"].iloc[0] == "unmatched"


def test_reviewed_quote_basis_conversion_only():
    products = pd.read_csv(DATA / "product_dictionary.csv")
    conversions = pd.read_csv(DATA / "unit_conversions.csv")
    hog_id = products.loc[products["normalized_name_en"].eq("Live Hog"), "exact_product_id"].iloc[0]
    value, status = convert_price(12.5, hog_id, "CNY/kg", "CNY/tonne", conversions, "2026-01-10")
    missing, missing_status = convert_price(12.5, hog_id, "kg", "tonne", conversions)
    assert value == 12_500.0
    assert status == "converted_reviewed_rule"
    assert missing is None
    assert missing_status == "missing_or_ambiguous_conversion"


def test_builder_is_reproducible(tmp_path):
    paths = build_harmonization_artifacts(tmp_path)
    assert set(paths) == {
        "categories", "product_families", "product_dictionary", "product_aliases",
        "basket_snapshots", "basket_membership", "basket_changes", "product_lineage",
        "unit_conversions", "comparability_matrix",
    }
    rebuilt = pd.read_csv(paths["product_dictionary"])
    committed = pd.read_csv(DATA / "product_dictionary.csv")
    pd.testing.assert_frame_equal(rebuilt, committed)

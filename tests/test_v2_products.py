"""Focused invariants for historical exact-specification panel."""
import importlib.util
from pathlib import Path

import pandas as pd

MODULE = Path(__file__).resolve().parents[1] / "scripts/v2_build_product_panel.py"
SPEC = importlib.util.spec_from_file_location("v2products", MODULE)
v2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v2)


def fixture(months):
    rows = []
    for month, slots in months.items():
        for slot, price in slots.items():
            period = pd.Period(month, freq="M")
            day = 1 + (slot - 1) * 10
            end = slot * 10 if slot < 3 else period.days_in_month
            rows.append(dict(reference_period_start=f"{month}-{day:02d}", reference_period_end=f"{month}-{end:02d}",
                             available_at=str(pd.Timestamp(f"{month}-{end:02d}", tz="UTC") + pd.Timedelta(days=4)),
                             exact_product_id="P1", harmonized_product_id="H1", product_family_id="F1", category_id="C1",
                             ppi_industry_id="I1", raw_price=price, raw_pct_change=1.0, source_release_id=f"{month}-{slot}"))
    return pd.DataFrame(rows)


def test_typography_only_identity():
    assert v2.product_identity("线材（Φ8—10mm，HPB300）注1", "", "吨") == v2.product_identity("线材(Φ8-10mm,HPB300)", "", "吨")
    assert v2.product_identity("线材(Φ8-10mm,HPB300)", "", "吨") != v2.product_identity("线材(Φ6.5mm,HPB300)", "", "吨")


def test_month_gap_not_bridged():
    panel, _, _ = v2.build_features(fixture({"2024-01": {1: 100, 2: 100, 3: 100}, "2024-03": {1: 110, 2: 120, 3: 130}}))
    march = panel[(panel.month == "2024-03") & (panel.vintage == "final")].iloc[0]
    assert pd.isna(march.mom_average)
    assert len(panel[panel.month == "2024-02"]) == 3


def test_early_excludes_later_prices_and_returns():
    panel, _, _ = v2.build_features(fixture({"2024-01": {1: 100, 2: 100, 3: 100}, "2024-02": {1: 110, 2: 500, 3: 1000}}))
    early = panel[(panel.month == "2024-02") & (panel.vintage == "early")].iloc[0]
    assert abs(early.mom_average - 10) < 1e-9
    assert pd.isna(early.slot_2_published_change)
    assert pd.isna(early.mom_sampling_5th_20th)


def test_only_verified_cancellation_changes_completeness():
    raw = fixture({"2024-01": {1: 100, 2: 100}, "2024-02": {1: 110, 2: 110, 3: 110}})
    incomplete, _, _ = v2.build_features(raw)
    assert pd.isna(incomplete[(incomplete.month == "2024-02") & (incomplete.vintage == "final")].iloc[0].mom_average)
    cancelled = pd.DataFrame([dict(reference_period_start="2024-01-21", slot=3)])
    corrected, _, _ = v2.build_features(raw, cancelled)
    row = corrected[(corrected.month == "2024-02") & (corrected.vintage == "final")].iloc[0]
    assert abs(row.mom_average - 10) < 1e-9


def test_full_mapping_conserves_original_observations():
    root = MODULE.parents[1]
    raw = pd.read_csv(root / "data/interim/nbs_market_prices/raw_market_prices.csv")
    mapped = pd.read_csv(root / "data/v2/products/mapped_raw_observations.csv")
    assert len(raw) == len(mapped)
    assert mapped.exact_product_id.notna().all()
    assert set(raw.observation_id) == set(mapped.observation_id)
    assert mapped.product_family_id.ne("UNRESOLVED").all()

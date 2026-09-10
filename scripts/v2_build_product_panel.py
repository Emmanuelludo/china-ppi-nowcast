#!/usr/bin/env python3
"""Versioned, unbalanced exact-specification panel. No inferred price splices."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2.0.0"


def canonical_text(value: object) -> str:
    """Only typographical equivalence: never alter grades, dimensions or units."""
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"注\d+$", "", text.strip())
    text = re.sub(r"\s+", "", text)
    return text.replace("—", "-").replace("–", "-")


def stable_id(prefix: str, *values: str) -> str:
    return prefix + hashlib.sha256("|".join(values).encode()).hexdigest()[:20]


def product_identity(name: str, specification: str, unit: str) -> str:
    return stable_id("EP2_", canonical_text(name), canonical_text(specification), canonical_text(unit))


def ratio_change(current: pd.Series, previous: pd.Series) -> pd.Series:
    return 100 * (current.div(previous.where(previous > 0)) - 1)


def build_mapping(raw: pd.DataFrame, dictionary: pd.DataFrame, aliases: pd.DataFrame,
                  categories: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    original = raw.copy()
    original["original_exact_product_id"] = original.get("exact_product_id", "")
    bases = dictionary.drop_duplicates("normalized_name_zh").set_index("normalized_name_zh")
    # Explicit semantic mappings reviewed against literal source names, not fuzzy joins.
    base_equivalence = {"白糖": "白砂糖", "热轧普通薄板": "热轧普通板卷"}
    exact_alias = {}
    for _, alias in aliases[aliases.language == "zh"].iterrows():
        exact_alias.setdefault(canonical_text(alias["alias"]), set()).add(alias.exact_product_id)
    cats = categories.set_index("category_name_zh")
    rows = []
    for keys, group in raw.groupby(["raw_product_name", "specification", "original_unit"], dropna=False):
        name, spec, unit = ("" if pd.isna(v) else str(v) for v in keys)
        canonical = canonical_text(name)
        base = canonical.split("(")[0]
        lookup = base_equivalence.get(base, base)
        matches = exact_alias.get(canonical, set())
        # Reuse reviewed exact ID only when entire source alias matches and unit is equivalent.
        old_id = next(iter(matches)) if len(matches) == 1 else None
        if old_id:
            old = dictionary[dictionary.exact_product_id == old_id].iloc[0]
            compatible_unit = (unit == "吨" and old.original_unit == "tonne") or (unit == "千克" and old.original_unit == "kg")
            if not compatible_unit or spec:
                old_id = None
        exact_id = old_id or product_identity(name, spec, unit)
        family = bases.loc[lookup] if lookup in bases.index else None
        cat_raw = str(group.iloc[0].raw_category_name)
        cat_name = re.sub(r"^[一二三四五六七八九十]+、", "", cat_raw)
        cat_name = {'农产品（主要用于加工）':'农产品', '非金属建材':'非金属矿产品',
                    '非金属矿物制品':'非金属矿产品', '农资':'农业生产资料', '林业':'林产品'}.get(cat_name,cat_name)
        category = cats.loc[cat_name] if cat_name in cats.index else None
        row = {
            "raw_product_name": name, "specification": spec, "original_unit": unit,
            "canonical_name": canonical, "exact_product_id": exact_id,
            # No broad harmonized-product bridge: specifications remain separate.
            "harmonized_product_id": stable_id("HP2_", exact_id),
            "product_family_id": family.product_family_id if family is not None else "UNRESOLVED",
            "category_id": category.category_id if category is not None else (family.category_id if family is not None else "UNRESOLVED"),
            "ppi_industry_id": family.ppi_industry_id if family is not None else "UNRESOLVED",
            "mapping_method": "exact_official_alias" if old_id else "exact_spec_identity_literal_family_map",
            "family_mapping_note": "explicit name equivalence " + base + " -> " + lookup if base in base_equivalence else "literal Chinese base name",
            "link_confidence": 1.0 if old_id else (0.95 if family is not None else 0.0),
            "first_observed": group.reference_period_start.min(), "last_observed": group.reference_period_end.max(),
            "first_available_at": group.available_at.min(),
            "standard_unit": "CNY/tonne" if unit == "吨" else "CNY/kg" if unit == "千克" else "UNRESOLVED",
            "unit_conversion_factor": 1.0, "observations": len(group), "schema_version": VERSION,
            "source_url": group.iloc[0].source_url,
        }
        rows.append(row)
    mapping = pd.DataFrame(rows)
    join_keys = ["raw_product_name", "specification", "original_unit"]
    for key in join_keys:
        original[key] = original[key].fillna("")
    original = original.drop(columns=["exact_product_id"])
    cols = join_keys + ["exact_product_id", "harmonized_product_id", "product_family_id", "category_id", "ppi_industry_id", "mapping_method", "link_confidence"]
    mapped = original.merge(mapping[cols], on=join_keys, how="left", validate="many_to_one")
    assert len(mapped) == len(raw) and mapped.exact_product_id.notna().all()
    return mapped, mapping


def build_features(mapped: pd.DataFrame, cancellations: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    data = mapped.copy()
    data["start"] = pd.to_datetime(data.reference_period_start)
    data["end"] = pd.to_datetime(data.reference_period_end)
    data["month"] = data.start.dt.to_period("M")
    data["slot"] = np.where(data.start.dt.day <= 10, 1, np.where(data.start.dt.day <= 20, 2, 3))
    data["days"] = (data.end - data.start).dt.days + 1
    data["available"] = pd.to_datetime(data.available_at, utc=True)
    duplicate_keys = ["month", "slot", "exact_product_id"]
    duplicates = data[data.duplicated(duplicate_keys, keep=False)].copy()
    # Existing collector records original page snapshots; earliest release always wins.
    selected = data.sort_values(["available", "source_release_id"]).drop_duplicates(duplicate_keys, keep="first")
    calendar = pd.period_range(selected.month.min(), selected.month.max(), freq="M")
    expected = pd.DataFrame(True, index=calendar, columns=[1, 2, 3])
    if cancellations is not None and len(cancellations):
        for _, cancellation in cancellations.iterrows():
            month = pd.Period(cancellation.reference_period_start, freq="M")
            if month in expected.index:
                slot = cancellation.get('slot', {'early':1, 'mid':2, 'late':3}.get(cancellation.get('reference_slot')))
                expected.loc[month, int(slot)] = False
    identities = selected[["exact_product_id", "harmonized_product_id", "product_family_id", "category_id", "ppi_industry_id"]].drop_duplicates("exact_product_id")
    frames = []
    for pid, group in selected.groupby("exact_product_id"):
        slot_prices = group.pivot(index="month", columns="slot", values="raw_price").reindex(calendar)
        slot_returns = group.pivot(index="month", columns="slot", values="raw_pct_change").reindex(calendar)
        for slot in (1, 2, 3):
            if slot not in slot_prices:
                slot_prices[slot] = np.nan
                slot_returns[slot] = np.nan
        sampled_price = slot_prices[[1, 2]].mean(axis=1).where(slot_prices[[1, 2]].notna().all(axis=1))
        full = group.groupby("month").agg(
            full_average=("raw_price", "mean"), full_n=("slot", "nunique"),
            full_end=("raw_price", "last"), full_available=("available", "max"))
        weighted = group.assign(price_days=group.raw_price * group.days).groupby("month").agg(price_days=("price_days", "sum"), days=("days", "sum"))
        full["full_days"] = weighted.price_days / weighted.days
        full = full.reindex(calendar)
        # Missing month or missing release must not silently become a full-month price.
        full.loc[full.full_n != expected.sum(axis=1), ["full_average", "full_end", "full_days"]] = np.nan
        for limit, vintage in [(1, "early"), (2, "mid"), (3, "final")]:
            part = group[group.slot <= limit].sort_values(["month", "slot"])
            agg = part.groupby("month").agg(
                price_average=("raw_price", "mean"), price_end=("raw_price", "last"),
                n_observations=("slot", "nunique"), last_slot=("slot", "max"),
                available_at=("available", "max"), published_latest=("raw_pct_change", "last"),
                monthly_volatility=("raw_pct_change", "std"))
            weighted = part.assign(price_days=part.raw_price * part.days).groupby("month").agg(price_days=("price_days", "sum"), days=("days", "sum"))
            agg["price_day_weighted"] = weighted.price_days / weighted.days
            agg["published_chain"] = part.groupby("month").raw_pct_change.apply(lambda s: 100 * (np.prod(1 + s / 100) - 1) if s.notna().all() else np.nan)
            agg = agg.reindex(calendar)
            agg["n_observations"] = agg.n_observations.fillna(0).astype(int)
            agg["observed_mask"] = agg.n_observations > 0
            agg["expected_observations"] = expected.loc[:, :limit].sum(axis=1)
            agg["complete_vintage_mask"] = (agg.n_observations == agg.expected_observations) & (agg.expected_observations > 0)
            agg["coverage"] = agg.n_observations / agg.expected_observations.replace(0, np.nan)
            for slot in (1, 2, 3):
                agg[f"slot_{slot}_published_change"] = slot_returns[slot] if slot <= limit else np.nan
                agg[f"slot_{slot}_month_change"] = ratio_change(slot_prices[slot], slot_prices[slot].shift(1)) if slot <= limit else np.nan
            # Prespecified NBS sampling-day proxy, not a retrospectively chosen exclusion.
            # PPI prices are sampled on 5th and 20th: early/mid circulation windows proxy these.
            agg["mom_sampling_5th_20th"] = ratio_change(sampled_price, sampled_price.shift(1)) if limit >= 2 else np.nan
            agg.loc[~agg.complete_vintage_mask, "published_chain"] = np.nan
            # Vintage return features are unavailable when that vintage release is missing.
            for name, previous in [("average", "full_average"), ("end", "full_end"), ("day_weighted", "full_days")]:
                agg["mom_" + name] = ratio_change(agg["price_" + name], full[previous].shift(1))
                agg.loc[~agg.complete_vintage_mask, "mom_" + name] = np.nan
            for horizon, months in [("3m", 3), ("6m", 6), ("yoy", 12)]:
                agg["change_" + horizon] = ratio_change(agg.price_average, full.full_average.shift(months))
                agg.loc[~agg.complete_vintage_mask, "change_" + horizon] = np.nan
            agg["exact_product_id"] = pid
            agg["vintage"] = vintage
            agg["month"] = calendar.astype(str)
            # Prior denominator is only usable if actually published by the vintage cut-off.
            prev_available = full.full_available.shift(1)
            forbidden = prev_available > agg.available_at
            agg.loc[forbidden, ["mom_average", "mom_end", "mom_day_weighted"]] = np.nan
            agg["schema_version"] = VERSION
            frames.append(agg.reset_index(drop=True))
    features = pd.concat(frames, ignore_index=True).merge(identities, on="exact_product_id", validate="many_to_one")
    coverage = features.groupby(["month", "vintage"]).agg(
        observed_exact_products=("observed_mask", "sum"), complete_exact_products=("complete_vintage_mask", "sum"),
        return_eligible_products=("mom_average", "count"), available_at=("available_at", "max")).reset_index()
    return features, coverage, duplicates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default=str(ROOT / "data/interim/nbs_market_prices/raw_market_prices.csv"))
    parser.add_argument("--output", default=str(ROOT / "data/v2/products"))
    parser.add_argument("--cancellations", default=str(ROOT / "data/v2/archive/scheduled_cancellations.csv"))
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    base = ROOT / "data/interim/harmonization"
    raw = pd.read_csv(args.raw)
    mapped, mapping = build_mapping(raw, pd.read_csv(base / "product_dictionary.csv"), pd.read_csv(base / "product_aliases.csv"), pd.read_csv(base / "categories.csv"))
    cancellations = pd.read_csv(args.cancellations) if Path(args.cancellations).exists() else None
    features, coverage, duplicates = build_features(mapped, cancellations)
    mapped.to_csv(out / "mapped_raw_observations.csv", index=False)
    mapping.to_csv(out / "exact_specification_dictionary.csv", index=False)
    features.to_csv(out / "product_vintage_features.csv", index=False)
    coverage.to_csv(out / "coverage.csv", index=False)
    duplicates.to_csv(out / "duplicate_selection_audit.csv", index=False)
    mapping[mapping.product_family_id == "UNRESOLVED"].to_csv(out / "unresolved_mappings.csv", index=False)
    summary = {"schema_version": VERSION, "raw_rows": len(raw), "mapped_rows": len(mapped),
               "raw_name_variants": len(mapping), "exact_specifications": mapping.exact_product_id.nunique(),
               "families": mapping.product_family_id.nunique(), "unresolved_observations": int((mapped.product_family_id == "UNRESOLVED").sum()),
               "feature_rows": len(features), "duplicate_observations": len(duplicates),
               "first_month": features.month.min(), "last_month": features.month.max(),
               "input_sha256": hashlib.sha256(Path(args.raw).read_bytes()).hexdigest(),
               "verified_cancellations": 0 if cancellations is None else len(cancellations),
               "policy": "No cross-specification price splices; literal family mapping; no forward/backward filling; preceding calendar full month required."}
    (out / "build_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

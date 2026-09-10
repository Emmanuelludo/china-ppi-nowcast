"""Build reviewed harmonization artifacts as relational CSV tables."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from .ontology import SCHEMA_VERSION, make_exact_product_id, make_lineage_id, validate_lineage, validate_product_dictionary
from .seeds import (
    ADDED_2026,
    CATEGORIES,
    FLOAT_GLASS_2026,
    PRODUCTS_2025,
    PRODUCTS_2026,
    REMOVED_2026,
    SOURCE_2025,
    SOURCE_2026,
    ProductSeed,
)


def _cat_id(slug: str) -> str:
    return f"CAT_{slug}"


def _family_id(slug: str) -> str:
    return f"PF_{slug}"


def _harmonized_id(product: ProductSeed) -> str:
    # Specification revisions of the same monitored product can share a harmonized ID;
    # lineage still governs whether levels may be spliced.
    if product.family == "float_glass":
        return "HP_float_glass"
    return f"HP_{product.slug}"


def _exact_id(product: ProductSeed) -> str:
    return make_exact_product_id(product.name_zh, product.specification, product.unit, product.slug)


def _all_products() -> list[ProductSeed]:
    by_id = {_exact_id(product): product for product in PRODUCTS_2025 + PRODUCTS_2026}
    return list(by_id.values())


def build_categories() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "schema_version": SCHEMA_VERSION,
            "category_id": _cat_id(slug),
            "category_name_zh": values[0],
            "category_name_en": values[1],
            "economic_production_stage": values[2],
            "default_ppi_industry_id": values[3],
            "source_url": SOURCE_2026,
            "quality_score": 0.95,
        }
        for slug, values in CATEGORIES.items()
    ])


def build_product_dictionary() -> pd.DataFrame:
    common_slugs = {product.slug for product in PRODUCTS_2025} & {product.slug for product in PRODUCTS_2026}
    records = []
    for product in _all_products():
        in_2025 = product in PRODUCTS_2025
        in_2026 = product in PRODUCTS_2026
        if in_2025 and in_2026:
            start, end, source = "2025-09-01", "", SOURCE_2025
            note = "Confirmed in both reviewed snapshots; start date is a coverage lower bound, not series inception."
        elif in_2025:
            start, end, source = "2025-09-01", "2025-12-31", SOURCE_2025
            note = "Preserved discontinued/pre-revision exact product; earlier history remains usable."
        else:
            start, end, source = "2026-01-01", "", SOURCE_2026
            note = "Added or revised specification effective 2026-01-01."
        records.append({
            "exact_product_id": _exact_id(product),
            "schema_version": SCHEMA_VERSION,
            "normalized_name_zh": product.name_zh,
            "normalized_name_en": product.name_en,
            "normalized_specification": product.specification,
            "original_unit": product.unit,
            "harmonized_product_id": _harmonized_id(product),
            "product_family_id": _family_id(product.family),
            "category_id": _cat_id(product.category),
            "production_stage_id": CATEGORIES[product.category][2],
            "ppi_industry_id": product.ppi_industry,
            "standard_unit": "CNY/tonne",
            "start_date": start,
            "end_date": end,
            "mapping_method": "manual_official_specification_table",
            "quality_score": 0.95,
            "source_url": source,
            "curator_notes": note,
        })
    frame = pd.DataFrame(records).sort_values(["category_id", "product_family_id", "exact_product_id"])
    validate_product_dictionary(frame)
    return frame


def build_families(products: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for family_id, group in products.groupby("product_family_id", sort=True):
        rows.append({
            "schema_version": SCHEMA_VERSION,
            "product_family_id": family_id,
            "family_name_en": family_id.removeprefix("PF_").replace("_", " ").title(),
            "category_id": group["category_id"].iloc[0],
            "ppi_industry_id": group["ppi_industry_id"].mode().iloc[0],
            "member_exact_product_count": len(group),
            "bridge_rule": "aggregate standardized changes; never average incomparable raw levels",
            "quality_score": float(group["quality_score"].min()),
        })
    return pd.DataFrame(rows)


def _full_alias(product: ProductSeed, language: str) -> str:
    name = product.name_zh if language == "zh" else product.name_en
    return f"{name}（{product.specification}）" if language == "zh" else f"{name} ({product.specification})"


def build_aliases() -> pd.DataFrame:
    rows = []
    for product in _all_products():
        for language in ("zh", "en"):
            alias = _full_alias(product, language)
            payload = f"{_exact_id(product)}|{language}|{alias}|{product.unit}"
            rows.append({
                "schema_version": SCHEMA_VERSION,
                "alias_id": "ALIAS_" + hashlib.sha256(payload.encode()).hexdigest()[:16],
                "exact_product_id": _exact_id(product),
                "language": language,
                "alias": alias,
                "unit": product.unit,
                "alias_type": "official_name_plus_specification",
                "valid_from": "2025-09-01" if product in PRODUCTS_2025 else "2026-01-01",
                "valid_to": "2025-12-31" if product.slug in REMOVED_2026 or product.slug == "float_glass_4_8_5mm" else "",
                "source_url": SOURCE_2025 if product in PRODUCTS_2025 else SOURCE_2026,
                "confidence": 0.95,
            })
    return pd.DataFrame(rows).sort_values(["exact_product_id", "language"])


def build_snapshots() -> tuple[pd.DataFrame, pd.DataFrame]:
    # The English page's displayed date is inconsistent with its URL/listing sequence.
    # For real-time safety the earliest availability is conservatively set to Sep 15,
    # never Sep 14. This is the correction required by the source audit.
    snapshots = pd.DataFrame([
        {
            "schema_version": SCHEMA_VERSION,
            "basket_snapshot_id": "BASKET_2025_09_OFFICIAL_EN",
            "reference_period_start": "2025-09-01",
            "reference_period_end": "2025-09-10",
            "effective_start": "2025-09-01",
            "effective_end": "2025-12-31",
            "publication_datetime_displayed": "2025-09-14 09:30:00+08:00",
            "available_at": "2025-09-15 09:30:00+08:00",
            "publication_date_precision": "conservative_after_display_url_conflict",
            "product_count": 50,
            "category_count": 9,
            "source_url": SOURCE_2025,
            "vintage": "official_english_page",
            "status": "reviewed",
            "notes": "Do not use 2025-09-14 as available_at; URL/listing is dated 2025-09-15.",
        },
        {
            "schema_version": SCHEMA_VERSION,
            "basket_snapshot_id": "BASKET_2026_01_OFFICIAL_EN",
            "reference_period_start": "2026-01-01",
            "reference_period_end": "2026-01-10",
            "effective_start": "2026-01-01",
            "effective_end": "",
            "publication_datetime_displayed": "2026-01-14 09:30:00+08:00",
            "available_at": "2026-01-14 09:30:00+08:00",
            "publication_date_precision": "page_timestamp",
            "product_count": 50,
            "category_count": 9,
            "source_url": SOURCE_2026,
            "vintage": "official_english_page",
            "status": "reviewed",
            "notes": "NBS explicitly identifies seven additions and seven removals effective 2026-01-01.",
        },
    ])
    membership = []
    for snapshot_id, products, start, end in (
        ("BASKET_2025_09_OFFICIAL_EN", PRODUCTS_2025, "2025-09-01", "2025-12-31"),
        ("BASKET_2026_01_OFFICIAL_EN", PRODUCTS_2026, "2026-01-01", ""),
    ):
        for position, product in enumerate(products, start=1):
            membership.append({
                "schema_version": SCHEMA_VERSION,
                "basket_snapshot_id": snapshot_id,
                "basket_position": position,
                "exact_product_id": _exact_id(product),
                "effective_start": start,
                "effective_end": end,
                "membership_status": "active",
            })
    return snapshots, pd.DataFrame(membership)


def build_changes() -> pd.DataFrame:
    rows = []
    old = {product.slug: product for product in PRODUCTS_2025}
    for slug in sorted(REMOVED_2026):
        product = old[slug]
        rows.append({
            "schema_version": SCHEMA_VERSION, "effective_date": "2026-01-01",
            "change_type": "removed", "predecessor_id": _exact_id(product), "successor_id": "",
            "official_change_counted": True, "source_url": SOURCE_2026,
            "notes": "Explicitly listed by NBS among seven removed products.",
        })
    for product in ADDED_2026:
        rows.append({
            "schema_version": SCHEMA_VERSION, "effective_date": "2026-01-01",
            "change_type": "added", "predecessor_id": "", "successor_id": _exact_id(product),
            "official_change_counted": True, "source_url": SOURCE_2026,
            "notes": "Explicitly listed by NBS among seven added products.",
        })
    old_glass = next(product for product in PRODUCTS_2025 if product.slug == "float_glass_4_8_5mm")
    rows.append({
        "schema_version": SCHEMA_VERSION, "effective_date": "2026-01-01",
        "change_type": "specification_change", "predecessor_id": _exact_id(old_glass),
        "successor_id": _exact_id(FLOAT_GLASS_2026), "official_change_counted": False,
        "source_url": SOURCE_2026,
        "notes": "Attached table changes float-glass thickness from 4.8/5mm to 5/6mm; not one of the seven stated replacements.",
    })
    return pd.DataFrame(rows)


def build_lineage(products: pd.DataFrame) -> pd.DataFrame:
    old_glass = next(product for product in PRODUCTS_2025 if product.slug == "float_glass_4_8_5mm")
    predecessor = _exact_id(old_glass)
    successor = _exact_id(FLOAT_GLASS_2026)
    rows = pd.DataFrame([{
        "lineage_id": make_lineage_id(predecessor, successor, "partially_comparable"),
        "schema_version": SCHEMA_VERSION,
        "predecessor_id": predecessor,
        "successor_id": successor,
        "relationship_type": "partially_comparable",
        "adjustment_method": "no_level_splice; family_factor_from_standardized_changes",
        "adjustment_factor": None,
        "confidence": 0.75,
        "evidence_url": SOURCE_2026,
        "decision_status": "reviewed_conservative",
        "decision_date": "2026-09-06",
        "notes": "Same monitored product and family, changed thickness specification; raw levels must remain separate.",
    }])
    validate_lineage(rows, products["exact_product_id"])
    return rows


def build_unit_conversions(products: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "conversion_id": "UC_CNY_PER_TONNE_IDENTITY",
            "schema_version": SCHEMA_VERSION,
            "from_unit": "CNY/tonne", "to_unit": "CNY/tonne", "exact_product_id": None,
            "valid_from": "", "valid_to": "", "factor": 1.0, "formula": "standardized_price = raw_price",
            "confidence": 1.0, "source_url": SOURCE_2025, "notes": "Identity conversion for observations quoted per tonne.",
        }
    ]
    for slug in ("live_hog_three_way", "polysilicon_dense"):
        product = next(item for item in _all_products() if item.slug == slug)
        rows.append({
            "conversion_id": f"UC_{slug.upper()}_KG_TO_TONNE",
            "schema_version": SCHEMA_VERSION,
            "from_unit": "CNY/kg", "to_unit": "CNY/tonne", "exact_product_id": _exact_id(product),
            "valid_from": "2025-09-01" if product in PRODUCTS_2025 else "2026-01-01",
            "valid_to": "", "factor": 1000.0, "formula": "standardized_price = raw_price * 1000",
            "confidence": 1.0, "source_url": SOURCE_2025 if product in PRODUCTS_2025 else SOURCE_2026,
            "notes": "Quote-basis conversion only; original value and unit remain preserved.",
        })
    return pd.DataFrame(rows)


def build_comparability_matrix(products: pd.DataFrame, lineage: pd.DataFrame) -> pd.DataFrame:
    lineage_lookup = {}
    for row in lineage.itertuples(index=False):
        lineage_lookup[(row.predecessor_id, row.successor_id)] = (row.relationship_type, row.confidence, row.lineage_id)
        lineage_lookup[(row.successor_id, row.predecessor_id)] = (row.relationship_type, row.confidence, row.lineage_id)
    rows = []
    for left in products.itertuples(index=False):
        for right in products.itertuples(index=False):
            if left.exact_product_id == right.exact_product_id:
                relation, confidence, lineage_id = "identical", 1.0, ""
            elif (left.exact_product_id, right.exact_product_id) in lineage_lookup:
                relation, confidence, lineage_id = lineage_lookup[(left.exact_product_id, right.exact_product_id)]
            else:
                relation, confidence, lineage_id = "non_comparable", 1.0, ""
            rows.append({
                "schema_version": SCHEMA_VERSION,
                "left_exact_product_id": left.exact_product_id,
                "right_exact_product_id": right.exact_product_id,
                "relationship_type": relation,
                "confidence": confidence,
                "lineage_id": lineage_id,
                "raw_level_splice_permitted": relation in {"identical", "directly_comparable", "comparable_with_scaling"},
            })
    return pd.DataFrame(rows)


def build_harmonization_artifacts(output_dir: str | Path) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    products = build_product_dictionary()
    lineage = build_lineage(products)
    snapshots, membership = build_snapshots()
    tables = {
        "categories": build_categories(),
        "product_families": build_families(products),
        "product_dictionary": products,
        "product_aliases": build_aliases(),
        "basket_snapshots": snapshots,
        "basket_membership": membership,
        "basket_changes": build_changes(),
        "product_lineage": lineage,
        "unit_conversions": build_unit_conversions(products),
        "comparability_matrix": build_comparability_matrix(products, lineage),
    }
    paths = {}
    for name, frame in tables.items():
        path = output / f"{name}.csv"
        frame.to_csv(path, index=False)
        paths[name] = path
    return paths


if __name__ == "__main__":
    build_harmonization_artifacts(Path("data/interim/harmonization"))

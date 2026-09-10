"""Curated event hypotheses for shock-robustness analysis.

Expected direction is a testable sign prior, not an instruction to alter prices.
Events remain in the baseline data.  The shock-adjusted scenario may interact with
or downweight them, and must report sensitivity to that choice.
"""

from __future__ import annotations

import hashlib

import pandas as pd


SCHEMA_VERSION = "0.1.0"


def _event_id(start_date: str, slug: str) -> str:
    suffix = hashlib.sha256(f"{start_date}|{slug}".encode()).hexdigest()[:8]
    return f"EV_{start_date}_{slug}_{suffix}"


def build_event_catalog() -> pd.DataFrame:
    """Return event/entity rows using the harmonization workstream's stable IDs."""

    definitions = [
        {
            "slug": "state_nonferrous_reserve_releases",
            "entities": [("category", "CAT_nonferrous_metals")],
            "start_date": "2021-07-05", "end_date": "2021-12-31", "available_at": "2021-06-16T17:00:00+08:00",
            "event_name": "State reserve releases of copper, aluminium and zinc", "shock_type": "reserve_release", "expected_direction": -1, "confidence": 0.80,
            "source_url": "https://www.ndrc.gov.cn/xwdt/ztzl/wzglgg/", "source_quality": "official_agency_topic_archive",
            "notes": "Use interactions/sensitivity only; category direction is a prior, not an observed effect.",
        },
        {
            "slug": "fertilizer_export_inspection_controls",
            "entities": [("product_family", "PF_nitrogen_fertilizer"), ("product_family", "PF_phosphate_fertilizer"), ("product_family", "PF_potash_fertilizer"), ("product_family", "PF_compound_fertilizer")],
            "start_date": "2021-10-15", "end_date": "2022-09-30", "available_at": "2021-10-15T17:00:00+08:00",
            "event_name": "Fertilizer export inspection and related trade controls", "shock_type": "export_restriction", "expected_direction": -1, "confidence": 0.60,
            "source_url": "https://www.fas.usda.gov/data/china-impacts-china-s-fertilizer-export-restrictions", "source_quality": "reputable_secondary_government_report",
            "notes": "Family scope is deliberately split. Legal coverage and transmission differed across nitrogen, phosphate, potash and compound products; estimate interactions separately.",
        },
        {
            "slug": "coal_price_intervention",
            "entities": [("category", "CAT_coal")],
            "start_date": "2021-10-19", "end_date": "2022-05-01", "available_at": "2021-10-19T20:00:00+08:00",
            "event_name": "Coal price intervention and supply stabilisation measures", "shock_type": "price_control", "expected_direction": -1, "confidence": 0.80,
            "source_url": "https://www.ndrc.gov.cn/xwdt/ztzl/mtbcyjgzl/", "source_quality": "official_agency_topic_archive",
            "notes": "Broad category flag; event study should also inspect thermal and coking-coal families.",
        },
        {
            "slug": "crude_steel_output_reduction",
            "entities": [("category", "CAT_ferrous_metals")],
            "start_date": "2021-07-01", "end_date": "2021-12-31", "available_at": "2021-07-01T17:00:00+08:00",
            "event_name": "Crude-steel output reduction implementation", "shock_type": "production_quota", "expected_direction": 1, "confidence": 0.65,
            "source_url": "https://www.miit.gov.cn/", "source_quality": "official_agency_home_archive_needed",
            "notes": "Exact national/local implementation dates require further archival work; keep confidence below high.",
        },
        {
            "slug": "russia_invasion_energy_shock",
            "entities": [("category", "CAT_petroleum_gas")],
            "start_date": "2022-02-24", "end_date": "2022-12-31", "available_at": "2022-02-24T12:00:00+00:00",
            "event_name": "Russia invasion of Ukraine and global energy shock", "shock_type": "geopolitical_supply_shock", "expected_direction": 1, "confidence": 0.90,
            "source_url": "https://press.un.org/en/2022/ga12407.doc.htm", "source_quality": "primary_international_organization",
            "notes": "Direction refers to imported petroleum/gas price pressure, not domestic demand.",
        },
        {
            "slug": "photovoltaic_manufacturing_norms",
            "entities": [("product_family", "PF_solar_materials")],
            "start_date": "2024-11-20", "end_date": None, "available_at": "2024-11-20T17:00:00+08:00",
            "event_name": "Revised photovoltaic manufacturing industry norms", "shock_type": "capacity_rationalization", "expected_direction": 1, "confidence": 0.55,
            "source_url": "https://www.miit.gov.cn/", "source_quality": "official_agency_home_archive_needed",
            "notes": "Maps polysilicon to the shared PF_solar_materials bridge; sign and timing must be estimated, not imposed.",
        },
        {
            "slug": "ets_extension_heavy_industry",
            "entities": [("category", "CAT_ferrous_metals")],
            "start_date": "2025-03-21", "end_date": None, "available_at": "2025-03-21T17:00:00+08:00",
            "event_name": "National ETS extension to steel, cement and aluminium", "shock_type": "environmental_policy", "expected_direction": 0, "confidence": 0.85,
            "source_url": "https://www.mee.gov.cn/xxgk2018/xxgk/xxgk03/202503/t20250326_1104736.html", "source_quality": "primary_official_release",
            "notes": "Zero direction records ambiguity; test state-dependent effects rather than forcing a price sign.",
        },
        {
            "slug": "energy_efficiency_three_year_action",
            "entities": [("category", "CAT_ferrous_metals"), ("category", "CAT_petroleum_gas")],
            "start_date": "2026-06-15", "end_date": None, "available_at": "2026-06-15T17:00:00+08:00",
            "event_name": "Three-year energy-efficiency action for key industries", "shock_type": "capacity_energy_policy", "expected_direction": 0, "confidence": 0.90,
            "source_url": "https://www.ndrc.gov.cn/xxgk/zcfb/tz/202606/t20260615_1405852.html", "source_quality": "primary_official_release",
            "notes": "Covers steel and refining among nine industries; zero sign reflects offsetting investment, cost and capacity channels.",
        },
    ]
    rows: list[dict[str, object]] = []
    for event in definitions:
        event_id = _event_id(event["start_date"], event["slug"])
        for level, entity_id in event["entities"]:
            rows.append({
                "event_id": event_id, "schema_version": SCHEMA_VERSION, "entity_level": level, "entity_id": entity_id,
                "start_date": event["start_date"], "end_date": event["end_date"], "event_name": event["event_name"],
                "shock_type": event["shock_type"], "expected_direction": event["expected_direction"], "confidence": event["confidence"],
                "source_url": event["source_url"], "available_at": event["available_at"], "source_quality": event["source_quality"], "notes": event["notes"],
            })
    return pd.DataFrame(rows)

#!/usr/bin/env python3
"""Materialize all delivered CSV artifacts into a portable DuckDB database."""

from __future__ import annotations

import hashlib
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/processed/china_ppi_nowcast.duckdb"
TABLES = {
    "raw_market_prices": "data/interim/nbs_market_prices/raw_market_prices.csv",
    "source_releases": "data/interim/nbs_market_prices/source_releases.csv",
    "missing_releases": "data/interim/nbs_market_prices/missing_releases.csv",
    "source_failures": "data/interim/nbs_market_prices/source_failures.csv",
    "duplicate_revision_log": "data/interim/nbs_market_prices/duplicate_revision_log.csv",
    "product_dictionary": "data/interim/harmonization/product_dictionary.csv",
    "product_lineage": "data/interim/harmonization/product_lineage.csv",
    "unit_conversions": "data/interim/harmonization/unit_conversions.csv",
    "comparability_matrix": "data/interim/harmonization/comparability_matrix.csv",
    "basket_snapshots": "data/interim/harmonization/basket_snapshots.csv",
    "basket_membership": "data/interim/harmonization/basket_membership.csv",
    "basket_changes": "data/interim/harmonization/basket_changes.csv",
    "weights": "data/interim/weights/historical_weight_panel.csv",
    "event_flags": "data/interim/events/event_flags.csv",
    "external_observations": "data/interim/external/raw_external_observations.csv",
    "external_features_monthly": "data/interim/external/external_features_monthly.csv",
    "targets": "data/processed/targets/headline_ppi_current_vintage.csv",
    "vintage_features": "data/processed/features/vintage_features.csv",
    "category_features": "data/processed/features/category_features.csv",
    "rolling_forecasts": "data/processed/forecasts/rolling_forecasts.csv",
    "model_leaderboard": "data/processed/forecasts/model_leaderboard.csv",
    "current_nowcast": "data/processed/forecasts/current_nowcast.csv",
    "model_coefficients": "data/processed/forecasts/model_coefficients.csv",
    "current_contributions": "data/processed/forecasts/current_contributions.csv",
    "current_shock_scenarios": "data/processed/forecasts/current_shock_scenarios.csv",
}


def main() -> None:
    if OUTPUT.exists():
        OUTPUT.unlink()
    con = duckdb.connect(str(OUTPUT))
    con.execute(
        "CREATE TABLE artifact_manifest(table_name VARCHAR, relative_path VARCHAR, sha256 VARCHAR, row_count BIGINT)"
    )
    for table, relative in TABLES.items():
        path = ROOT / relative
        if not path.exists():
            continue
        safe_path = str(path).replace("'", "''")
        con.execute(
            f"CREATE TABLE {table} AS SELECT * FROM read_csv_auto('{safe_path}', header=true, sample_size=-1, all_varchar=false)"
        )
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        count = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        con.execute("INSERT INTO artifact_manifest VALUES (?, ?, ?, ?)", [table, relative, digest, count])
    con.execute("CREATE VIEW preferred_nowcast AS SELECT * FROM current_nowcast WHERE forecast_vintage='final' AND aggregation_method='monthly_average' AND model_id='bridge_current'")
    con.close()
    print(f"created {OUTPUT} with {len(TABLES)} candidate tables")


if __name__ == "__main__":
    main()

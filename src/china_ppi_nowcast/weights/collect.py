"""Build reproducible equal-weight variants from reviewed basket snapshots."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .builder import build_equal_weight_panel


def collect_weights(root: Path) -> dict[str, int]:
    source = root / "data/interim/harmonization"
    output = root / "data/interim/weights"
    output.mkdir(parents=True, exist_ok=True)
    panel = build_equal_weight_panel(
        pd.read_csv(source / "product_dictionary.csv"),
        pd.read_csv(source / "basket_membership.csv"),
        pd.read_csv(source / "basket_snapshots.csv"),
    )
    panel.to_csv(output / "historical_weight_panel.csv", index=False)
    source_log = pd.DataFrame(
        [
            {"weight_variant": "equal_product", "status": "produced", "is_official_weight": False, "notes": "Derived from reviewed NBS basket membership; not an official PPI weight."},
            {"weight_variant": "equal_category", "status": "produced", "is_official_weight": False, "notes": "Equal category shares; not an official PPI weight."},
            {"weight_variant": "industry_output", "status": "not_produced", "is_official_weight": False, "notes": "No vintage-aware industry output/revenue panel acquired; values were not fabricated."},
            {"weight_variant": "ppi_relevance", "status": "not_produced", "is_official_weight": False, "notes": "Official detailed PPI item weights were not located; values were not inferred from item counts."},
            {"weight_variant": "predictive", "status": "model_stage_required", "is_official_weight": False, "notes": "Must be estimated inside each rolling training window."},
            {"weight_variant": "hybrid", "status": "blocked_by_inputs", "is_official_weight": False, "notes": "Produced only when vintage-aware economic and training-only predictive weights exist."},
        ]
    )
    source_log.to_csv(output / "weight_source_log.csv", index=False)
    return {"weight_rows": len(panel), "snapshots": panel["basket_snapshot_id"].nunique(), "variants": panel["weight_variant"].nunique()}

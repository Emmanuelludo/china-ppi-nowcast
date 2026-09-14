"""End-to-end reconstructed bundle training and evaluation reporting."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ..storage import atomic_write_text
from .models import train_bundle
from .training_data import build_training_matrix, write_training_matrix


def train_project_bundles(root: Path, bundle_root: Path, carry_weight: float = 0.5) -> dict[str, object]:
    observations = pd.read_csv(root / "data" / "processed" / "nbs_ten_day_observations.csv.gz")
    actuals = pd.read_csv(root / "data" / "registry" / "actuals.csv")
    variants: dict[str, dict[str, object]] = {}
    for vintage in ("early", "final"):
        matrix, matrix_manifest = build_training_matrix(observations, actuals, vintage, carry_weight)
        write_training_matrix(root, vintage, matrix, matrix_manifest)
        variants[vintage] = train_bundle(
            matrix,
            bundle_root / vintage,
            validate=True,
            vintage=vintage,
            training_metadata=matrix_manifest,
        )
    root_manifest: dict[str, object] = {
        "bundle_version": "reconstructed-v1",
        "provenance": "reconstructed",
        "validated": all(item["validated"] for item in variants.values()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "variants": {
            vintage: {
                "directory": vintage,
                "validated": manifest["validated"],
                "training_rows": manifest["training_rows"],
                "training_start": manifest["training_start"],
                "training_end": manifest["training_end"],
            }
            for vintage, manifest in variants.items()
        },
        "warning": "Operationally validated reconstructed candidates; this does not recover or reproduce the missing v0.4 objects.",
    }
    atomic_write_text(bundle_root / "manifest.json", json.dumps(root_manifest, ensure_ascii=False, indent=2) + "\n")
    _write_evaluation_report(root, variants)
    return root_manifest


def _write_evaluation_report(root: Path, variants: dict[str, dict[str, object]]) -> None:
    lines = [
        "# Reconstructed-model backfill evaluation",
        "",
        "All results below are **pseudo-real-time**. Publication timestamps were used as cutoffs,",
        "but the NBS pages were retrieved later and revision-vintage correctness is not claimed.",
        "Operational validation means that the artifacts, leakage guards, chronology, and model",
        "interfaces passed; it is not a claim that any model is superior.",
        "",
        "| Vintage | Model | OOF n | MAE | RMSE | Bias | Direction | 10% mask MAE |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for vintage, manifest in variants.items():
        for model in manifest["models"]:
            metrics = model["metrics"]
            stress = metrics["missing_panel_stress"]
            lines.append(
                f"| {vintage} | {model['label']} | {metrics['n_oof']} | {metrics['mae']:.3f} | "
                f"{metrics['rmse']:.3f} | {metrics['bias']:.3f} | {metrics['directional_accuracy']:.3f} | "
                f"{stress['mae']:.3f} |"
            )
        lines.extend(["", f"**{vintage} baselines**", ""])
        for name, metrics in manifest["baselines"].items():
            lines.append(
                f"- `{name}`: MAE {metrics['mae']:.3f}, RMSE {metrics['rmse']:.3f}, "
                f"bias {metrics['bias']:.3f}, direction {metrics['directional_accuracy']:.3f}."
            )
        panel = manifest["panel_diagnostics"]
        lines.extend(
            [
                "",
                f"Panel: {panel['product_columns']} product columns; {panel['stable_90pct_products']} "
                f"observed in at least 90% of months; median coverage {panel['median_product_coverage']:.1%}; "
                f"median monthly entry/exit count {panel['median_monthly_entry_exit_count']:.1f}.",
                "",
            ]
        )
    atomic_write_text(root / "reports" / "backfill_evaluation.md", "\n".join(lines) + "\n")

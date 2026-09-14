"""Create one immutable multi-model forecast vintage."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ..features import build_feature_vintage
from ..modeling import predict_bundle
from ..registry import append_forecasts
from ..storage import atomic_write_csv, atomic_write_text


def _commit_sha(root: Path) -> str:
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return "unknown"


def create_forecast(
    root: Path,
    target_month: str,
    as_of: str,
    bundle_dir: Path,
    carry_weight: float = 0.5,
) -> dict[str, object]:
    observations_path = root / "data" / "processed" / "nbs_ten_day_observations.csv"
    if not observations_path.exists():
        raise FileNotFoundError("no processed NBS observations are available")
    observations = pd.read_csv(observations_path)
    vintage = build_feature_vintage(observations, target_month, as_of, carry_weight)
    predictions = predict_bundle(bundle_dir, vintage.frame, require_validated=True)
    now = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for prediction in predictions:
        rows.append(
            {
                **prediction,
                "target_month": target_month,
                "as_of": vintage.manifest["as_of"],
                "as_of_precision": "timestamp",
                "vintage": vintage.manifest["vintage"],
                "data_cutoff": vintage.manifest["as_of"],
                "feature_hash": vintage.manifest["feature_hash"],
                "code_commit": _commit_sha(root),
                "status": "frozen_pre_release",
                "created_at": now,
                "notes": "Reconstructed candidate; generated from immutable prospective source snapshots.",
            }
        )
    added = append_forecasts(root / "data" / "registry" / "forecasts.csv", rows)
    vintage_dir = root / "data" / "processed" / "vintages" / target_month / vintage.manifest["feature_hash"][:16]
    atomic_write_csv(vintage_dir / "features.csv", vintage.frame)
    atomic_write_csv(vintage_dir / "products.csv", vintage.product_changes)
    atomic_write_text(vintage_dir / "manifest.json", json.dumps(vintage.manifest, ensure_ascii=False, indent=2) + "\n")
    return {"forecasts_added": added, "vintage": vintage.manifest["vintage"], "feature_hash": vintage.manifest["feature_hash"]}

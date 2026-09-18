"""Create one immutable multi-model forecast vintage."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import numpy as np

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


def _persist_vintage(vintage_dir: Path, vintage: object) -> None:
    artifacts = (
        vintage_dir / "features.csv",
        vintage_dir / "products.csv",
        vintage_dir / "manifest.json",
    )
    present = [path.exists() for path in artifacts]
    if any(present):
        if not all(present):
            raise RuntimeError(f"incomplete immutable feature vintage: {vintage_dir}")
        stored = json.loads(artifacts[2].read_text(encoding="utf-8"))
        identity = ("target_month", "vintage", "feature_hash")
        if any(str(stored.get(key)) != str(vintage.manifest.get(key)) for key in identity):
            raise ValueError(f"immutable feature vintage identity conflict: {vintage_dir}")
        return
    atomic_write_csv(artifacts[0], vintage.frame)
    atomic_write_csv(artifacts[1], vintage.product_changes)
    atomic_write_text(artifacts[2], json.dumps(vintage.manifest, ensure_ascii=False, indent=2) + "\n")


def create_forecast(
    root: Path,
    target_month: str,
    as_of: str,
    bundle_dir: Path,
    carry_weight: float = 0.5,
) -> dict[str, object]:
    observations_path = root / "data" / "processed" / "nbs_ten_day_observations.csv.gz"
    if not observations_path.exists():
        raise FileNotFoundError("no processed NBS observations are available")
    observations = pd.read_csv(observations_path)
    vintage = build_feature_vintage(observations, target_month, as_of, carry_weight)
    variant_dir = bundle_dir / str(vintage.manifest["vintage"])
    if not (variant_dir / "manifest.json").exists():
        variant_dir = bundle_dir
    model_manifest = json.loads((variant_dir / "manifest.json").read_text())
    if str(model_manifest.get("training_end", "")) >= target_month:
        raise ValueError("model bundle training overlaps target month")
    trained_at_cutoff = model_manifest.get("training_actual_cutoff")
    if trained_at_cutoff and pd.Timestamp(trained_at_cutoff) > pd.Timestamp(as_of):
        raise ValueError("model bundle includes targets unavailable at as_of")
    actual_path = root / "data" / "registry" / "actuals.csv"
    if actual_path.exists():
        actuals = pd.read_csv(actual_path)
        if (actuals.target_month.eq(target_month) & pd.to_datetime(actuals.published_at, utc=True).le(pd.Timestamp(as_of))).any():
            raise ValueError("target actual already public; prospective inference prohibited")
    predictions = predict_bundle(variant_dir, vintage.frame, require_validated=True)
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
    _persist_vintage(vintage_dir, vintage)
    registry = pd.read_csv(root / "data" / "registry" / "forecasts.csv", keep_default_na=False)
    stored = registry[
        registry["target_month"].astype(str).eq(target_month)
        & registry["feature_hash"].astype(str).eq(str(vintage.manifest["feature_hash"]))
        & registry["model_version"].astype(str).eq(str(rows[0]["model_version"]))
    ]
    report_manifest = dict(vintage.manifest)
    if not stored.empty:
        report_manifest["as_of"] = stored["as_of"].iloc[0]
    _write_nowcast_report(root, report_manifest, stored.to_dict(orient="records") or rows)
    return {"forecasts_added": added, "vintage": vintage.manifest["vintage"], "feature_hash": vintage.manifest["feature_hash"]}


def _write_nowcast_report(root: Path, manifest: dict[str, object], rows: list[dict[str, object]]) -> None:
    estimates = np.asarray([float(row["estimate_mom_pct"]) for row in rows if row["model_key"] != "twentieth_to_twentieth_direct"])
    lines = [
        "# Latest China headline PPI MoM nowcast",
        "",
        f"- Target month: **{manifest['target_month']}**",
        f"- Frozen cutoff: **{manifest['as_of']}**",
        f"- Information set: **{manifest['vintage']}**",
        f"- Comparable products: **{manifest['n_products']}**",
        f"- Model median: **{np.median(estimates):+.3f}% MoM**",
        f"- Model range: **{estimates.min():+.3f}% to {estimates.max():+.3f}% MoM**",
        "",
        "| Model | Estimate (% MoM) | Provenance |",
        "|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['model_label']} | {float(row['estimate_mom_pct']):+.3f} | {row['model_provenance']} |"
        )
    lines.extend(
        [
            "",
            "The cross-model range is descriptive dispersion, not a calibrated prediction interval.",
            "The direct 20th-to-20th index is an uncalibrated circulation-price proxy and is excluded from the model median/range.",
            "Both 20th-to-20th benchmarks require the current and prior months’ 11–20 releases; unavailable early in the month.",
            "All candidates are reconstructed because the original v0.4 fitted objects were not recovered.",
            "No permanent model winner is selected from this backfill.",
            "",
        ]
    )
    atomic_write_text(root / "reports" / "latest_nowcast.md", "\n".join(lines))

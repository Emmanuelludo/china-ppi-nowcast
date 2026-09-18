"""Build auditable pseudo-real-time matrices from later-retrieved NBS pages."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import numpy as np

from ..features import build_feature_vintage
from ..storage import atomic_write_csv, atomic_write_text, stable_hash


def build_training_matrix(
    observations: pd.DataFrame,
    actuals: pd.DataFrame,
    vintage: str,
    carry_weight: float = 0.5,
) -> tuple[pd.DataFrame, dict[str, object]]:
    if vintage not in {"early", "final"}:
        raise ValueError("vintage must be 'early' or 'final'")
    source_window = "1-10" if vintage == "early" else "11-20"
    obs = observations.copy()
    obs["published_at"] = pd.to_datetime(obs["published_at"], utc=True, errors="raise")
    targets = actuals.copy()
    targets["published_at"] = pd.to_datetime(targets["published_at"], utc=True, errors="raise")
    targets["actual_mom_pct"] = pd.to_numeric(targets["actual_mom_pct"], errors="raise")
    targets = targets[np.isfinite(targets["actual_mom_pct"])].copy()
    targets = targets.sort_values("published_at").drop_duplicates("target_month", keep="last")
    rows: list[pd.DataFrame] = []
    exclusions: list[dict[str, str]] = []
    for _, actual in targets.sort_values("target_month").iterrows():
        month = str(actual["target_month"])
        releases = obs[(obs["release_month"].astype(str) == month) & (obs["window"] == source_window)]
        if releases.empty:
            exclusions.append({"target_month": month, "reason": f"missing {source_window} release"})
            continue
        cutoff = releases["published_at"].max()
        if actual["published_at"] <= cutoff:
            exclusions.append({"target_month": month, "reason": "actual was not published after feature cutoff"})
            continue
        try:
            built = build_feature_vintage(
                observations,
                month,
                cutoff.to_pydatetime(),
                carry_weight,
                availability_basis="publication",
            )
        except ValueError as exc:
            exclusions.append({"target_month": month, "reason": str(exc)})
            continue
        if built.manifest["vintage"] != vintage:
            exclusions.append({"target_month": month, "reason": f"constructed {built.manifest['vintage']} vintage"})
            continue
        row = built.frame.copy()
        row["target_mom_pct"] = float(actual["actual_mom_pct"])
        row["feature_cutoff"] = cutoff.isoformat()
        row["actual_published_at"] = actual["published_at"].isoformat()
        row["availability_basis"] = "publication"
        row["realtime_status"] = "pseudo_real_time"
        rows.append(row)
    matrix = pd.concat(rows, ignore_index=True, sort=False) if rows else pd.DataFrame()
    if not matrix.empty:
        matrix = matrix.sort_values("target_month").reset_index(drop=True)
    manifest: dict[str, object] = {
        "vintage": vintage,
        "realtime_status": "pseudo_real_time",
        "availability_basis": "publication",
        "revision_vintage_correct": False,
        "actual_after_cutoff": bool(
            len(matrix)
            and (
                pd.to_datetime(matrix["actual_published_at"], utc=True)
                > pd.to_datetime(matrix["feature_cutoff"], utc=True)
            ).all()
        ),
        "warning": "Historical pages were retrieved later; publication cutoffs prevent obvious look-ahead but do not reconstruct page revisions.",
        "rows": len(matrix),
        "start": str(matrix["target_month"].min()) if len(matrix) else None,
        "end": str(matrix["target_month"].max()) if len(matrix) else None,
        "exclusions": exclusions,
        "matrix_hash": stable_hash(matrix.fillna("__NA__").to_dict(orient="records")) if len(matrix) else None,
    }
    return matrix, manifest


def write_training_matrix(root: Path, vintage: str, matrix: pd.DataFrame, manifest: dict[str, object], version: str = "reconstructed-v2") -> None:
    directory = root / "data" / "processed" / "training" / version
    atomic_write_csv(directory / f"{vintage}.csv", matrix)
    atomic_write_text(directory / f"{vintage}.manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

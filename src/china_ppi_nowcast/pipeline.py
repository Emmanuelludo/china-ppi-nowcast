"""Scheduled pipeline orchestration and human-readable status."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from .forecast import create_forecast
from .ingest import NBSClient, ingest_nbs
from .storage import atomic_write_text
from .time import CHINA_TZ, default_target_month


def load_config(root: Path) -> dict[str, object]:
    return json.loads((root / "config" / "pipeline.json").read_text(encoding="utf-8"))


def repository_status(root: Path) -> dict[str, object]:
    observations_path = root / "data" / "processed" / "nbs_ten_day_observations.csv"
    forecasts_path = root / "data" / "registry" / "forecasts.csv"
    bundle_path = root / "models" / "reconstructed-v1" / "manifest.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8")) if bundle_path.exists() else None
    return {
        "observations": int(len(pd.read_csv(observations_path))) if observations_path.exists() else 0,
        "forecasts": int(len(pd.read_csv(forecasts_path))) if forecasts_path.exists() else 0,
        "model_bundle_present": bundle is not None,
        "model_bundle_validated": bool(bundle and bundle.get("validated")),
        "production_inference": "enabled" if bundle and bundle.get("validated") else "blocked_missing_validated_models",
    }


def write_status_report(root: Path, status: dict[str, object], run: dict[str, object] | None = None) -> None:
    run = {key: value for key, value in (run or {}).items() if key != "as_of"}
    lines = [
        "# China PPI nowcast status",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    for key, value in {**status, **run}.items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(
        [
            "",
            "Frozen August 2026 forecasts remain historical imports. Current inference is",
            "permitted only from a validated reconstructed model bundle.",
            "",
        ]
    )
    atomic_write_text(root / "reports" / "latest.md", "\n".join(lines))


def run_pipeline(root: Path, target_month: str | None = None, as_of: str | None = None) -> dict[str, object]:
    config = load_config(root)
    now = datetime.now(CHINA_TZ)
    cutoff = as_of or now.isoformat()
    target = target_month or default_target_month(now)
    client = NBSClient(
        timeout=int(config["request_timeout_seconds"]), retries=int(config["request_retries"])
    )
    ingest_counts = ingest_nbs(
        root, str(config["nbs_index_url"]), pages=int(config["index_pages"]), client=client
    )
    result: dict[str, object] = {**{f"ingest_{k}": v for k, v in ingest_counts.items()}, "target_month": target, "as_of": cutoff}
    bundle_dir = root / str(config["model_bundle"])
    try:
        forecast_result = create_forecast(
            root, target, cutoff, bundle_dir, float(config["first_survey_carry_weight"])
        )
        result.update(forecast_result)
        result["forecast_status"] = "created_or_idempotent"
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        message = str(exc)
        expected = (
            "model bundle" in message
            or "not marked validated" in message
            or "lacks prior" in message
            or "no processed NBS observations" in message
        )
        if not expected:
            raise
        result["forecast_status"] = "blocked"
        result["forecast_reason"] = message
    status = repository_status(root)
    write_status_report(root, status, result)
    return result

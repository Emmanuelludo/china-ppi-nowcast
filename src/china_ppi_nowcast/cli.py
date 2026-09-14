"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from .features import build_feature_vintage
from .forecast import create_forecast
from .ingest import NBSClient, ingest_nbs, ingest_nbs_history, rebuild_actuals_from_snapshots
from .modeling import train_bundle, train_project_bundles
from .pipeline import load_config, repository_status, run_pipeline, write_status_report
from .storage import atomic_write_csv, atomic_write_text


def _root(value: str) -> Path:
    return Path(value).resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ppi-nowcast")
    parser.add_argument("--root", default=".", help="repository root")
    commands = parser.add_subparsers(dest="command", required=True)

    ingest = commands.add_parser("ingest")
    ingest.add_argument("--index-pages", type=int)

    backfill = commands.add_parser("backfill")
    backfill.add_argument("--start-month")
    backfill.add_argument("--end-month")
    backfill.add_argument("--index-pages", type=int)
    backfill.add_argument("--workers", type=int)
    backfill.add_argument("--train", action="store_true")

    features = commands.add_parser("build-features")
    features.add_argument("--target-month", required=True)
    features.add_argument("--as-of", required=True)
    features.add_argument("--output")

    train = commands.add_parser("train")
    train.add_argument("--training-file", required=True)
    train.add_argument("--output-dir", default="models/reconstructed-v1")

    forecast = commands.add_parser("forecast")
    forecast.add_argument("--target-month", required=True)
    forecast.add_argument("--as-of", required=True)
    forecast.add_argument("--bundle-dir", default="models/reconstructed-v1")

    run = commands.add_parser("run")
    run.add_argument("--target-month")
    run.add_argument("--as-of")

    commands.add_parser("status")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = _root(args.root)
    config = load_config(root)
    if args.command == "ingest":
        client = NBSClient(int(config["request_timeout_seconds"]), int(config["request_retries"]))
        result = ingest_nbs(
            root,
            str(config["nbs_index_url"]),
            pages=args.index_pages or int(config["index_pages"]),
            client=client,
            workers=int(config["download_workers"]),
        )
    elif args.command == "backfill":
        now_month = datetime.now().strftime("%Y-%m")
        client = NBSClient(int(config["request_timeout_seconds"]), int(config["request_retries"]))
        result = ingest_nbs_history(
            root,
            str(config["nbs_index_url"]),
            args.start_month or str(config["backfill_start_month"]),
            args.end_month or now_month,
            pages=args.index_pages or int(config["archive_index_pages"]),
            workers=args.workers or int(config["download_workers"]),
            client=client,
        )
        result["actual_registry_rebuild"] = rebuild_actuals_from_snapshots(root)
        result["failed"] = int(result["failed"]) + int(result["actual_registry_rebuild"]["failed"])
        if args.train:
            if int(result["failed"]):
                raise RuntimeError(f"backfill has {result['failed']} failed pages; rerun before training")
            result["training"] = train_project_bundles(
                root,
                root / str(config["model_bundle"]),
                float(config["first_survey_carry_weight"]),
            )
    elif args.command == "build-features":
        observations = pd.read_csv(root / "data" / "processed" / "nbs_ten_day_observations.csv")
        vintage = build_feature_vintage(
            observations, args.target_month, args.as_of, float(config["first_survey_carry_weight"])
        )
        output = root / (args.output or f"data/processed/vintages/{args.target_month}/{vintage.manifest['feature_hash'][:16]}")
        atomic_write_csv(output / "features.csv", vintage.frame)
        atomic_write_csv(output / "products.csv", vintage.product_changes)
        atomic_write_text(output / "manifest.json", json.dumps(vintage.manifest, indent=2, ensure_ascii=False) + "\n")
        result = vintage.manifest
    elif args.command == "train":
        training = pd.read_csv(root / args.training_file)
        result = train_bundle(training, root / args.output_dir)
    elif args.command == "forecast":
        result = create_forecast(
            root,
            args.target_month,
            args.as_of,
            root / args.bundle_dir,
            float(config["first_survey_carry_weight"]),
        )
    elif args.command == "run":
        result = run_pipeline(root, args.target_month, args.as_of)
    else:
        result = repository_status(root)
        write_status_report(root, result)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

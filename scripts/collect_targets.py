#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from china_ppi_nowcast.targets import write_headline_targets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=2013)
    parser.add_argument("--end-year", type=int)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    frame = write_headline_targets(
        args.root / "data/processed/targets",
        args.root / "data/raw/nbs_ppi",
        start_year=args.start_year,
        end_year=args.end_year,
    )
    print(frame.groupby("series_id")["month"].agg(["min", "max", "count"]))


if __name__ == "__main__":
    main()


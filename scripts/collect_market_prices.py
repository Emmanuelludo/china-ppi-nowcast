#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from china_ppi_nowcast.ingest import collect_market_price_releases


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--page-count", type=int, default=67)
    args = parser.parse_args()
    print(json.dumps(collect_market_price_releases(args.root, args.workers, args.page_count), indent=2))


if __name__ == "__main__":
    main()


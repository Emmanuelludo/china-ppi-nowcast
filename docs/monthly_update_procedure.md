# Monthly update procedure

1. Run `scripts/collect_market_prices.py` after each NBS ten-day release. Cache the page,
   record its hash and publication/availability timestamp, and never overwrite a prior
   source vintage.
2. Review the source, missing-release, duplicate/revision and parser-failure logs. A new
   specification is assigned a new exact-product ID before it enters harmonized features.
3. Update the product dictionary, lineage and conversion tables only through a reviewed,
   evidence-linked change. Discontinued products remain in history.
4. Ingest the latest official PPI target after release. Store first release separately
   from revised/current-database values.
5. Rebuild early, mid or final feature matrices with `available_at <= forecast_cutoff`.
   Generate monthly-average, end-to-end, day-weighted and direct ten-day variants.
6. Run `scripts/run_empirical_prototype.py`. Predictive coefficients and any statistical
   weights are re-estimated strictly inside each training window.
7. Run baseline, robust and event/shock sensitivities. A shock scenario changes the
   selected signal, not its economic weight, and never silently replaces the baseline.
8. Run `scripts/generate_report_assets.py`, `scripts/build_database.py`, and the full test
   suite. If product coverage or weight coverage falls below the configured gates, issue
   a fallback/no-forecast status rather than silently imputing.
9. Publish the vintage with cutoff, source hashes, model version, training sample,
   forecast interval, contributions, changes from the prior vintage and unresolved QA
   warnings.

## Reproduction commands

```bash
PYTHONPATH=src python scripts/collect_market_prices.py --workers 16 --page-count 67
PYTHONPATH=src python scripts/collect_targets.py --start-year 2013 --end-year 2026
python scripts/run_empirical_prototype.py
PYTHONPATH=src python scripts/generate_report_assets.py
python scripts/build_database.py
python -m pytest -q
```

The commands assume the dependencies in `pyproject.toml`. Network collection is separate
from transformations so cached raw sources can reproduce downstream outputs.


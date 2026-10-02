# Project maintenance notes

Start with [README](README.md), [operations](OPERATIONS.md) and
[methodology](docs/METHODOLOGY.md). The repository is the working state.

## Contracts to preserve

1. Target official China headline **PPI MoM**, not YoY.
2. Keep each timing specification and model version identifiable.
3. Enforce publication/retrieval cutoffs for prospective forecasts.
4. Preserve frozen forecasts, raw source snapshots and fitted artifacts.
5. Keep structural product missingness separate from collection/parser errors.
6. Label historical validation as pseudo-real-time; do not use in-sample backcasts
   as forecast-accuracy evidence.
7. Compare all models prospectively; do not promote a permanent winner from one month.
8. English presentation lives in `reporting.py` and `product_labels.json`.
   Translate display labels without changing the product identifiers or fitted contracts.

Active bundles are selected by `config/pipeline.json` and
`config/product_pipeline.json`. Run the test suite and clean-checkout verification
before publishing code changes. The GitHub workflow generates the reports used by
[Latest results](reports/README.md).

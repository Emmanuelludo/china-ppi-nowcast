# Saved models

[Latest forecasts](../reports/README.md) · [Model comparison](../reports/product_candidates.md)

## Find the active bundle

| Model family | Authoritative pointer |
|---|---|
| Product-price models | [`config/product_pipeline.json`](../config/product_pipeline.json) |
| Survey-aligned benchmarks | [`config/pipeline.json`](../config/pipeline.json) |

Older directories are retained because historical forecasts refer to those
versions. Use the configuration pointers rather than choosing a directory by name.

## Inside a product bundle

| File | Purpose |
|---|---|
| `manifest.json` | Version, feature contracts, hyperparameters, artifact hashes and metrics |
| `catalog.json` | Source product identities and basket membership |
| `environment.json` | Runtime/package versions |
| `canonical_prices.csv.gz` | Canonical absolute-price training snapshot |
| `twentieth/`, `final/`, `early/`, `early_carry/` | Fitted estimators and timing-specific matrices |
| `rolling_predictions.csv` | Monthly out-of-sample predictions |
| `historical_shap.csv.gz` | Historical product attributions |
| `paired_comparisons.json` | Paired forecast-loss comparisons |

Model objects and catalogs are fixed artifacts. English names are maintained in
the reporting layer so a presentation change never modifies a saved estimator.

# China PPI Nowcast

[![Daily pipeline](https://github.com/Emmanuelludo/china-ppi-nowcast/actions/workflows/nowcast.yml/badge.svg)](https://github.com/Emmanuelludo/china-ppi-nowcast/actions/workflows/nowcast.yml)

Forecasting China's **headline producer price inflation, month on month**, from
NBS production-material prices. The system collects releases, applies saved models,
and preserves each forecast before the official PPI announcement.

## Start here

| I want to… | Open |
|---|---|
| See the visual dashboard and projections | **[PPI dashboard](reports/README.md)** |
| Understand which products drive them | [Forecast explanations](reports/attributions.md) |
| Find a product in English | [Product glossary](docs/PRODUCTS.md) |
| Compare model accuracy | [Historical comparison](reports/product_candidates.md) · [Performance over time](reports/product_performance.md) |
| Understand the price dates and models | [Methodology](docs/METHODOLOGY.md) |
| Run or maintain the pipeline | [Operations guide](OPERATIONS.md) |

## What the system contains

- **29 active product-model variants**, including XGBoost, CatBoost, LightGBM,
  HistGradientBoosting, ridge, random forest and economic and sector benchmarks.
- **20th-to-20th, two-survey-period, early-month and carry-in specifications**,
  kept separate so forecasts reflect the information available at each date.
- **Survey-aligned benchmark models**, retained alongside the product models.
- Versioned fitted models, exact input rows, product/sector SHAP and immutable forecasts.
- Historical NBS prices from January 2014; [coverage gaps](reports/history_search.json)
  remain explicit.

All reported PPI predictions are **MoM percentages**: `+0.7` means `+0.7% MoM`.
The direct market-price tracker is an uncalibrated index and is displayed separately.
No permanent winning model or weighted ensemble has been selected.

## Run an update

The GitHub workflow runs daily. For an immediate update, open
[Actions → China PPI prospective nowcast](https://github.com/Emmanuelludo/china-ppi-nowcast/actions/workflows/nowcast.yml),
choose **Run workflow**, and leave the optional inputs blank.

For a local run with Python 3.12:

```sh
python -m pip install -e '.[product]'
python -m china_ppi_nowcast.cli --root . run
python -m china_ppi_nowcast.product ensure --root .
```

Read [Latest results](reports/README.md) after the run. Forecasts that require an
unpublished price window remain pending.

## Repository map

| Directory | Purpose |
|---|---|
| [`reports/`](reports/README.md) | Human-readable forecasts and evaluation |
| [`docs/`](docs/README.md) | Methodology, English product glossary and technical contracts |
| [`src/china_ppi_nowcast/`](src/china_ppi_nowcast/) | Ingestion, features, inference, evaluation and reporting |
| [`config/`](config/) | Active model pointers and pipeline settings |
| [`data/`](data/README.md) | Source snapshots, processed inputs and immutable forecast records |
| [`models/`](models/README.md) | Saved estimators, training matrices and validation results |
| [`tests/`](tests/) | Timing, leakage, ingestion, model and presentation checks |

English labels are used in reports. Original Chinese names and specifications are
retained in source data and the bilingual glossary for traceability. Translation
never changes product identities, model inputs or historical forecasts.

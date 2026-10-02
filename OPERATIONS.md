# Operations guide

[Project home](README.md) · [Latest results](reports/README.md) · [Methodology](docs/METHODOLOGY.md)

## Automatic and manual updates

The workflow **China PPI prospective nowcast** is scheduled daily at 02:35 UTC.
GitHub may start scheduled jobs later. To update immediately, use
[Actions → Run workflow](https://github.com/Emmanuelludo/china-ppi-nowcast/actions/workflows/nowcast.yml)
on `main` with the optional inputs left blank.

Each run tests the code, collects NBS releases, validates the data, loads the saved
models, appends new forecast vintages, refreshes the English reports, and verifies
saved-model inference from a clean checkout. An unchanged input/model combination
reuses its frozen forecast rather than creating duplicates.

## Local setup

Use Python 3.12:

```sh
python -m pip install -e '.[product]'
python -m unittest discover -s tests -v
python -m china_ppi_nowcast.cli --root . run
python -m china_ppi_nowcast.product ensure --root .
python scripts/verify_saved_deployment.py
```

Refresh presentation from existing saved forecasts, without downloading data,
refitting models or changing forecast records:

```sh
python -m china_ppi_nowcast.reporting --root .
```

## Active model versions

- `config/product_pipeline.json` points to the product-model bundle.
- `config/pipeline.json` points to the survey-aligned benchmark bundle.
- [Models guide](models/README.md) explains the saved artifacts.

Routine inference loads saved estimators. The product `ensure` command trains if
there is no configured bundle or the source history extends earlier than that
bundle's history. To deliberately train a new product version:

```sh
python -m china_ppi_nowcast.product train --root .
```

Review the new model comparison, bundle and configuration before adopting the new
version. Keep older versions and forecasts for reproducibility. The workflow's
`backfill_start_month` input invokes historical collection and benchmark training;
leave it blank for ordinary updates.

## Reading status and diagnostics

[Pipeline status](reports/latest.md) records data/model readiness.
[Actions logs](https://github.com/Emmanuelludo/china-ppi-nowcast/actions) show each step.
Network interruptions have bounded retries. Persistent download or schema errors
block a new forecast and retain diagnostics; they are not treated as structural
product missingness. Source checkpoints make collection resumable.

A pending forecast means a required release is not yet available. For example,
20th-to-20th requires the current and previous months' 11–20 prices.

To stop automation, disable the workflow in GitHub Actions. A manual run can later
be used to verify it before re-enabling the schedule.

## Forecast and data integrity

Raw snapshots are stored by content hash. Each forecast retains its timestamp,
model version, features, source references and code revision. Official results
are matched after publication. Frozen forecasts and saved model objects are not
rewritten when documentation, labels or reports change.

Historical validation is pseudo-real-time because the source pages were retrieved
later. Imported historical forecast records are distinguished from forecasts
produced by the active model versions. See [data provenance](docs/DATA.md).

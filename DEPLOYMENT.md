# China PPI nowcast operations

Verified 18 September 2026: [full training, artifact persistence and clean-checkout inference passed](https://github.com/Emmanuelludo/china-ppi-nowcast/actions/runs/35393132909). The saved product bundle is `product-v3-6ebe4ddbf8e9c7bc`.

The runtime is GitHub Actions. The scheduled workflow runs daily at 02:35 UTC;
GitHub can start scheduled jobs later than that time. Manual runs are available
under Actions → China PPI prospective nowcast → Run workflow.

## Reproduce a run

Use Python 3.12 and the pinned dependencies:

```sh
python -m pip install -e '.[product]'
python -m unittest discover -s tests -v
python -m china_ppi_nowcast.cli --root . run
python -m china_ppi_nowcast.product ensure --root .
python scripts/verify_saved_deployment.py
```

Ordinary runs load saved models. They append forecasts when the feature/model
vintage changes and retain the original records on identical reruns. Training a
new product bundle is an explicit `python -m china_ppi_nowcast.product train --root .`
operation; `ensure` also trains when the history extends earlier than the saved
bundle. Review and commit the resulting versioned artifacts and configuration.

## Where to inspect results

- `config/pipeline.json`: active retained benchmark bundle.
- `config/product_pipeline.json`: active additional product bundle.
- `models/`: fitted estimators, manifests, feature contracts, matrices, rolling
  predictions, package metadata and historical SHAP.
- `data/registry/forecasts.csv`: frozen August imports and retained-model vintages.
- `data/product/vintages/`: immutable additional forecasts, input rows and SHAP.
- `data/product/evaluations/`: subsequently matched official outcomes.
- `reports/product_latest.md`: current product-model forecasts and attributions.
- `reports/product_candidates.md`: nested rolling-origin comparison.
- `reports/product_performance.md`: prospective and historical performance.
- `reports/history_search.json`: source coverage and unresolved windows.

## Model and timing contracts

All previous fitted versions and frozen forecasts are retained. Corrected PPI
targets are used by the new `reconstructed-v3` benchmark bundle; they do not alter
past predictions. Earlier unrecoverable v0.4 forecasts remain historical imports,
not purported reproductions of recovered model objects.

There are 30 additional saved candidates: ten model families on 20th-to-20th
features, five stable-panel counterparts, and five product estimators for each
of final, early, and early-plus-carry timing. The ten families are ridge,
HistGradientBoosting, XGBoost, CatBoost, LightGBM, category-factor, sector-first,
random forest, NBS-only economic/ML hybrid, and the uncalibrated direct tracker.

20th-to-20th means `100 * log(current 11–20 price / previous 11–20 price)` for
each product. These are circulation-market period prices, not exact day-20
factory-gate transaction prices. The current 21–end release is not inserted into
this feature. A forecast waits until the required release is actually available.

The additional final variant compares the current and previous means of 1–10
and 11–20 prices. Early compares 1–10 with the prior month's 1–10; early-plus-carry
also includes prior 21–end to current 1–10 changes. The original carry-weighted
survey features remain in the retained benchmark family under separate identities.

Native tree missingness and training-fold preprocessing preserve structural
product additions/removals. Missing source releases and unreviewed units are QA
conditions, not fabricated price observations. Newly available features without
training history are recorded as unlearnable until a future model fit.

## Coverage and limitations

The recovered history has 22,200 product observations in 444 price releases,
starting January 2014, and 153 official monthly PPI outcomes. Thirteen historical
price windows remain absent; the audit lists each one, including May 2019's
11–20 window. September 2026's two later windows were not yet available at this
verification. An absent historical release is not automatically labelled a
confirmed holiday cancellation.

Historical validation is explicitly pseudo-real-time: publication cutoffs are
checked, but source pages were retrieved later. The original 12 August forecasts
remain unchanged. Product-level and grouped SHAP are predictive attributions,
not causal contributions. No model winner or performance-weighted ensemble has
been promoted from one month. Prospective evaluation still needs six or more
monthly outcomes.

External proxies, macro extensions and exact implied YoY remain separate research
work; the production target is official headline PPI MoM in percentage points.

## Failure handling

HTTP success is not proof of a valid NBS article. English and Chinese JavaScript
challenge responses are recognized and excluded from release parsing. Previously
captured valid snapshots support resumable history rebuilds. Raw response files
remain immutable. Flat headline PPI is parsed before later purchasing-price
changes, and target corrections are recorded in `data/registry/parser_corrections/`.

A failed ingestion blocks a new production forecast and records diagnostics.
Workflow checkpoints retain successful downloads before later model steps.
After fitting and committing artifacts, a fresh local Git clone on the runner
loads every saved candidate, checks artifact hashes and SHAP reconciliation, and
checks repeat-inference immutability. The workflow keeps failure logs and alerts.

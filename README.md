# Latest baseline: continuous survey-date alignment (v4)

Open **reports/v4/China_PPI_Survey_Aligned.html**. V4 supersedes calendar-month averaging for the official PPI nowcast. It preserves calendar averages as economic indicators and controls.

- Actual exact-specification prices form continuous 5th/20th survey proxies. Current late-month prices enter next-month carry-in, not the direct current PPI state.
- Timing candidates include nearest observations, midpoint interpolation, learned carry weights and one-sided extrapolation toward the20th. Weights are selected inside chronological training folds.
- Sector-first forecasts use individual product pass-through, explicit new-product coefficient priors and downstream AR fallbacks; estimated industry weights are dated and are not official PPI weights.
- Native-missing forests and boosting are challengers. The operational final state freezes the last survey-window prediction unless new target information is released.
- The reconstructed August mid-vintage product-ridge estimate is +0.410%, with prices available24August. Sector-first is +0.227%. Neither is the separate manual forecast.
- September carry updated with9September PPI: sector-first +0.289%, product ridge +0.641%, boosting +0.492%. These precede September circulation observations and are provisional.

See the paired19-month leaderboard, August vintage table and2026case table. Model-specific samples differ because of release gaps and minimum training history. Timing improves the controlled calendar comparison but does not resolve all April/May/June misses. No stable0.90correlation, immutable vintage replay, or deployed GitHub service is claimed.

Run `scripts/v4_timing.py`, `v4_compare.py`, `v4_sector.py`, `v4_live.py`, `v4_live_sector.py`, and `v4_publish.py` in order. Set `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1` for fitting. `v2_update.py --refresh` now orchestrates retained v2/v3 controls plus v4 and archives results; the input fingerprint includes model code changes. The supplied scheduled workflow emits v4 artifacts when deployed, but deployment remains outstanding.

---

# Latest: v3 feature and tree-model revision

Open **reports/v3/China_PPI_Model_Revision.html**. V3 audits the August signals, removes redundant transformations, separates input-price lags from target autoregression, and tests native-missing random forests and histogram boosting. A positive distributed-lag category bridge reaches **0.917** historical MoM correlation over 23 months, with **0.290 pp RMSE**; the old category bridge still has lower RMSE (**0.261 pp**). All August diagnostic forecasts are positive, but a close August fit does not establish general forecasting performance.

The August outcome and earlier test results were known when these specifications were developed. Nested chronological fitting does not make this redevelopment a pristine holdout. No automatic production promotion is claimed. Source-dated category mappings and comparator-gap audits are included. Run `python scripts/v3_experiments.py` then `python scripts/v3_publish.py` to reproduce the new results. The update workflow now emits both v2 and v3 results when deployed; hosted execution remains unavailable.

---

# China PPI nowcast — audited product and sector model

Open **reports/v2/China_PPI_Results.html** for actual results, charts, every final-vintage headline error, sector performance, and the August 2026 estimate. The HTML works offline.

The earlier v0.1 forecast claims are withdrawn. Legacy files remain as an audit trail and are not the current model.

## What the rebuilt implementation does

- Preserves 8,550 official circulation-price observations from 171 releases, September 2021–August 2026.
- Maps all observations into 69 exact specifications and 51 product families. Original names, specifications, prices and units are retained. No automatic cross-specification level splice.
- Fits individual product changes, multiple temporal transformations, lagged changes, family/category factors and available PPI lags. Predictor eligibility, imputation, scaling and penalty tuning use training data only.
- Uses 59 months of dated official headline, production-stage, purchasing and industry PPI tables, September 2021–July 2026.
- Produces early/mid/final forecasts, expanding and rolling headline backtests, separately fitted sector forecasts, historical-error intervals and additive attribution.
- Supplies three dated annual industry-revenue weight panels and a separate as-of revenue-weighted aggregation of covered sector forecasts. These are economic proxies, not official PPI weights.
- Includes a daily GitHub Actions update workflow. **It is not deployed; no new remote GitHub repository was created.**

## Acceptance result

The individual-product ridge has final-vintage MoM correlation **0.732** and RMSE **0.367 percentage points**, over **23** historical forecasts. The category bridge reaches **0.879** correlation and **0.261 pp** RMSE. The AR benchmark RMSE is **0.374 pp**.

The requested 0.90 headline MoM correlation has **not** been achieved by the individual-product model. More predictors do not automatically improve forecasting with this short sample. No model is promoted by selecting the most flattering result on the same test period. YoY skill is reported separately because known base effects account for much of its predictability.

## Reproduce

Python 3.12:

```sh
pip install -e '.[dev]'
python -m pytest -q
python scripts/v2_build_product_panel.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/v2_fit_models.py
python scripts/v2_collect_economic_weights.py
python scripts/v2_sector_aggregation.py
python scripts/v2_publish_results.py
```

To collect new releases, rebuild and archive results:

```sh
python scripts/v2_update.py --refresh
```

Long interrupted model runs can continue with `python scripts/v2_fit_models.py --resume` **only when the model code and inputs are unchanged**. Run without `--resume` after changing inputs or methodology. The scheduled workflow starts fresh.

## Data and outputs

- `data/raw/nbs_market_prices/html/`: original circulation-price source pages.
- `data/v2/products/`: mapped observations, exact specifications, unbalanced features and coverage audit.
- `data/interim/harmonization/`: documented lineage and historical harmonization evidence.
- `data/v2/targets/`: dated official PPI tables, source audit and cached pages.
- `data/v2/weights/`: official revenue sources and economic-weight proxy panel.
- `data/v2/models/`: every forecast, sample count, timestamp, score, interval and contribution.
- `reports/v2/`: standalone report, figures, headline errors, YoY scores and sector leaderboard.
- `.github/workflows/ppi-update.yml`: daily update configuration; requires deployment in an accessible GitHub repository.

## Material limitations

This is a publication-aware retrospective evaluation. Pages retrieved today cannot certify that every historical value equals its immutable first release. The collected circulation history starts in 2021; the series' earlier history is not claimed complete. The 22–23 month headline test set is too short for strong regime or turning-point conclusions. Economic weight coverage is incomplete and revenues are not official PPI weights. Consensus, external commodity/PMI comparisons, event-conditioned models, a validated state-space model and full historical basket reconstruction are not completed. Reported intervals are empirical and have limited calibration history. The implementation and results are reviewable; the original production-system success criterion remains unmet.

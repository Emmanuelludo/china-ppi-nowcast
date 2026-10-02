# China PPI nowcast

**Target: 2026-09 · Headline PPI month-on-month change**

Report refreshed: 2026-09-26T15:58:49.559435+08:00. Forecast timestamps remain fixed when inputs are unchanged.

Current-month price windows incorporated: **1-10, 11-20**.

[Model explanations](../docs/METHODOLOGY.md) · [English product glossary](../docs/PRODUCTS.md) · [Attributions](attributions.md) · [Performance](product_candidates.md)

## Product-price models

All values are predicted official PPI MoM percentages. A dash means that model/timing combination has no saved output.

| Model | 20th-to-20th | Two-survey period | Early month | Early + carry-in |
|---|---:|---:|---:|---:|
| XGBoost | +0.682% | +0.696% | +0.618% | +0.675% |
| CatBoost | +0.729% | +0.639% | +0.471% | +0.605% |
| LightGBM | +0.644% | +0.671% | +0.561% | +0.669% |
| HistGradientBoosting | +0.691% | +0.744% | +0.596% | +0.677% |
| Product ridge | -0.342% | +1.218% | +0.913% | +1.207% |
| Random forest | +0.614% | — | — | — |
| Sector-first regression | +1.261% | — | — | — |
| Economic / ML hybrid (NBS prices) | +0.945% | — | — | — |

## Survey-aligned benchmarks

These use the carry-weighted survey-date feature specification. Their estimates are separate from the product-price models above.

| Model | Timing | PPI MoM | Frozen at |
|---|---|---:|---|
| HistGradientBoosting | Final | +0.879% | 2026-09-24T15:48:16.589073+08:00 |
| Economic / ML hybrid (NBS prices) | Final | +0.743% | 2026-09-24T15:48:16.589073+08:00 |
| Product ridge | Final | +1.204% | 2026-09-24T15:48:16.589073+08:00 |
| Sector-first regression | Final | +0.662% | 2026-09-24T15:48:16.589073+08:00 |
| Random forest | Final | +0.646% | 2026-09-24T15:48:16.589073+08:00 |
| 20th-to-20th ridge | Final | +0.780% | 2026-09-24T15:48:16.589073+08:00 |

## Explore the results

| Report | Contents |
|---|---|
| [All product forecasts](product_latest.md) | Main models, stable-panel sensitivity, direct tracker and exact source releases |
| [Forecast explanations](attributions.md) | English product and sector SHAP tables |
| [Historical model comparison](product_candidates.md) | Rolling out-of-sample MAE, RMSE and bias |
| [Performance over time](product_performance.md) | Prospective results and 6/12/24-month historical summaries |
| [Survey-aligned benchmarks](latest_nowcast.md) | Benchmark estimates and model dispersion |
| [Pipeline status](latest.md) | Data and model readiness |
| [August 2026 forecast archive](august_2026_frozen.md) | Frozen historical forecast record |

No weighted ensemble has been adopted. Differences between models are not a calibrated confidence interval.

Advanced diagnostics: [source coverage audit](history_search.json), [benchmark validation](backfill_evaluation.md), [in-sample backcast](historical_backcast_2025_2026.md). The backcast is not forecast-accuracy evidence.

# China PPI nowcast

**Target: 2026-10 · Headline PPI month-on-month change**

Report refreshed: 2026-10-02T17:21:48.495892+08:00. Forecast timestamps remain fixed when inputs are unchanged.

Current-month price windows incorporated: **None yet**.

[Model explanations](../docs/METHODOLOGY.md) · [English product glossary](../docs/PRODUCTS.md) · [Attributions](attributions.md) · [Performance](product_candidates.md)

## Product-price models

All values are predicted official PPI MoM percentages. A dash means that model/timing combination has no saved output.

| Model | 20th-to-20th | Two-survey period | Early month | Early + carry-in |
|---|---:|---:|---:|---:|

## Survey-aligned benchmarks

These use the carry-weighted survey-date feature specification. Their estimates are separate from the product-price models above.

| Model | Timing | PPI MoM | Frozen at |
|---|---|---:|---|

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

# Forecast sense check

Latest saved target: **2026-11**. Checked: 2026-11-25.

Checks use frozen inputs and model artifacts. No forecasts or fitted models are changed. Current-month forecasts remain pending until their required price windows are available.

## Comparable forecasts

| Model | Timing | Panel | PPI MoM | Used product features | Outside training range | Features with <12 training months | Historical MAE | Recent MAE (N) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| CatBoost | 20th-to-20th | Stable products | -0.337% | 25 | 0 | 0 | 0.333 | 0.404 (10) |
| HistGradientBoosting | 20th-to-20th | Stable products | -0.344% | 25 | 0 | 0 | 0.335 | 0.405 (10) |
| LightGBM | 20th-to-20th | Stable products | -0.371% | 25 | 0 | 0 | 0.328 | 0.399 (10) |
| Product ridge | 20th-to-20th | Stable products | -0.364% | 25 | 0 | 0 | 0.282 | 0.317 (10) |
| XGBoost | 20th-to-20th | Stable products | -0.416% | 25 | 0 | 0 | 0.333 | 0.422 (10) |
| CatBoost | 20th-to-20th | All historical products | -0.396% | 50 | 5 | 8 | 0.343 | 0.496 (10) |
| Economic / ML hybrid (NBS prices) | 20th-to-20th | All historical products | -0.333% | 50 | 5 | 8 | 0.268 | 0.364 (10) |
| HistGradientBoosting | 20th-to-20th | All historical products | -0.155% | 50 | 5 | 8 | 0.349 | 0.456 (10) |
| LightGBM | 20th-to-20th | All historical products | -0.191% | 50 | 5 | 8 | 0.339 | 0.436 (10) |
| Random forest | 20th-to-20th | All historical products | -0.227% | 50 | 5 | 8 | 0.357 | 0.469 (10) |
| Product ridge | 20th-to-20th | All historical products | -0.233% | 42 | 0 | 0 | 0.276 | 0.334 (10) |
| Sector-first regression | 20th-to-20th | All historical products | -0.162% | 50 | 5 | 8 | 0.255 | 0.379 (10) |
| XGBoost | 20th-to-20th | All historical products | -0.260% | 50 | 5 | 8 | 0.348 | 0.449 (10) |

MAE is in percentage points. Recent means the last 12 calendar months in the stored rolling validation; missing-window months are excluded, so N can be less than 12. All accuracy statistics are pseudo-real-time, not prospective evidence.

## Interpretation

- 20th-to-20th: 4 product boosters span **-0.396% to -0.155%**; median **-0.226%**. This is descriptive agreement, not an ensemble or confidence interval.
- Ridge 20th-to-20th panel sensitivity: **0.131 pp** between all-product and stable-product versions. Compare both panels alongside their rolling errors; a sign reversal warrants investigation.
- Several product changes can lie outside the fitted training range. Linear models extrapolate; trees often saturate. Both require monitoring.
- Short-history product series and missingness indicators can encode basket/regime changes. Tight agreement among correlated boosters does not establish independent confirmation.
- Sector-first and hybrid models remain useful comparisons: judge their full and recent validation alongside the pure product models.
- The direct circulation-price index has no PPI weights or calibration and is excluded from all PPI summaries.
- Do not combine early forecasts with later forecasts into one mean. They represent different information sets.
- At least six prospective outcomes are still required before strong model-ranking claims.

## Sparse series and extrapolation


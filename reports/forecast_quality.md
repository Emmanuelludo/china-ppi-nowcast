# Forecast sense check

Latest saved target: **2026-09**. Checked: 2026-10-06.

Checks use frozen inputs and model artifacts. No forecasts or fitted models are changed. Current-month forecasts remain pending until their required price windows are available.

## Comparable forecasts

| Model | Timing | Panel | PPI MoM | Used product features | Outside training range | Features with <12 training months | Historical MAE | Recent MAE (N) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| CatBoost | Early month | All historical products | +0.471% | 50 | 2 | 8 | 0.329 | 0.494 (10) |
| HistGradientBoosting | Early month | All historical products | +0.596% | 50 | 2 | 8 | 0.341 | 0.409 (10) |
| LightGBM | Early month | All historical products | +0.561% | 50 | 2 | 8 | 0.327 | 0.410 (10) |
| Product ridge | Early month | All historical products | +0.913% | 50 | 2 | 8 | 0.342 | 1.111 (10) |
| XGBoost | Early month | All historical products | +0.618% | 50 | 2 | 8 | 0.332 | 0.442 (10) |
| CatBoost | Early + carry-in | All historical products | +0.605% | 100 | 6 | 16 | 0.340 | 0.457 (10) |
| HistGradientBoosting | Early + carry-in | All historical products | +0.677% | 100 | 6 | 16 | 0.348 | 0.410 (10) |
| LightGBM | Early + carry-in | All historical products | +0.669% | 100 | 6 | 16 | 0.334 | 0.390 (10) |
| Product ridge | Early + carry-in | All historical products | +1.207% | 100 | 6 | 16 | 0.362 | 0.572 (10) |
| XGBoost | Early + carry-in | All historical products | +0.675% | 100 | 6 | 16 | 0.340 | 0.439 (10) |
| CatBoost | Two-survey period | All historical products | +0.639% | 50 | 5 | 8 | 0.326 | 0.485 (8) |
| HistGradientBoosting | Two-survey period | All historical products | +0.744% | 50 | 5 | 8 | 0.328 | 0.498 (8) |
| LightGBM | Two-survey period | All historical products | +0.671% | 50 | 5 | 8 | 0.329 | 0.482 (8) |
| Product ridge | Two-survey period | All historical products | +1.218% | 50 | 5 | 8 | 0.322 | 1.169 (8) |
| XGBoost | Two-survey period | All historical products | +0.696% | 50 | 5 | 8 | 0.329 | 0.469 (8) |
| CatBoost | 20th-to-20th | Stable products | +0.802% | 25 | 1 | 0 | 0.333 | 0.404 (10) |
| HistGradientBoosting | 20th-to-20th | Stable products | +0.697% | 25 | 1 | 0 | 0.335 | 0.405 (10) |
| LightGBM | 20th-to-20th | Stable products | +0.719% | 25 | 1 | 0 | 0.328 | 0.399 (10) |
| Product ridge | 20th-to-20th | Stable products | +0.814% | 25 | 1 | 0 | 0.286 | 0.317 (10) |
| XGBoost | 20th-to-20th | Stable products | +0.652% | 25 | 1 | 0 | 0.333 | 0.422 (10) |
| CatBoost | 20th-to-20th | All historical products | +0.729% | 50 | 9 | 8 | 0.343 | 0.496 (10) |
| Economic / ML hybrid (NBS prices) | 20th-to-20th | All historical products | +0.945% | 50 | 9 | 8 | 0.268 | 0.364 (10) |
| HistGradientBoosting | 20th-to-20th | All historical products | +0.691% | 50 | 9 | 8 | 0.349 | 0.456 (10) |
| LightGBM | 20th-to-20th | All historical products | +0.644% | 50 | 9 | 8 | 0.339 | 0.436 (10) |
| Random forest | 20th-to-20th | All historical products | +0.614% | 50 | 9 | 8 | 0.357 | 0.469 (10) |
| Product ridge | 20th-to-20th | All historical products | -0.342% | 50 | 9 | 8 | 0.329 | 0.703 (10) |
| Sector-first regression | 20th-to-20th | All historical products | +1.261% | 50 | 9 | 8 | 0.255 | 0.379 (10) |
| XGBoost | 20th-to-20th | All historical products | +0.682% | 50 | 9 | 8 | 0.348 | 0.449 (10) |

MAE is in percentage points. Recent means the last 12 calendar months in the stored rolling validation; missing-window months are excluded, so N can be less than 12. All accuracy statistics are pseudo-real-time, not prospective evidence.

## Interpretation

- 20th-to-20th: 4 product boosters span **+0.644% to +0.729%**; median **+0.686%**. This is descriptive agreement, not an ensemble or confidence interval.
- Two-survey period: 4 product boosters span **+0.639% to +0.744%**; median **+0.683%**. This is descriptive agreement, not an ensemble or confidence interval.
- Early month: 4 product boosters span **+0.471% to +0.618%**; median **+0.579%**. This is descriptive agreement, not an ensemble or confidence interval.
- Early + carry-in: 4 product boosters span **+0.605% to +0.677%**; median **+0.672%**. This is descriptive agreement, not an ensemble or confidence interval.
- Ridge 20th-to-20th panel sensitivity: **1.156 pp** between all-product and stable-product versions. Treat the all-product estimate as sensitivity evidence; a sign reversal warrants investigation.
- Several product changes can lie outside the fitted training range. Linear models extrapolate; trees often saturate. Both require monitoring.
- Short-history product series and missingness indicators can encode basket/regime changes. Tight agreement among correlated boosters does not establish independent confirmation.
- Sector-first and hybrid models remain useful comparisons: judge their full and recent validation alongside the pure product models.
- The direct circulation-price index has no PPI weights or calibration and is excluded from all PPI summaries.
- Do not combine early forecasts with later forecasts into one mean. They represent different information sets.
- At least six prospective outcomes are still required before strong model-ranking claims.

## Sparse series and extrapolation

- Float glass (5/6mm): live change outside this feature’s fitted historical range.
- Polyester filament yarn (POY150D/48F): live change outside this feature’s fitted historical range.
- Polysilicon (dense grade): live change outside this feature’s fitted historical range.
- Polyethylene (LLDPE,film grade, melt index 2): live change outside this feature’s fitted historical range.
- Polypropylene (raffia grade): live change outside this feature’s fitted historical range.
- Lithium iron phosphate (LFP) (standard battery grade): live change outside this feature’s fitted historical range.
- Metallurgical coke (quasi-grade 1): live change outside this feature’s fitted historical range.
- Phosphate fertilizer (55%monoammonium phosphate): live change outside this feature’s fitted historical range.
- Methanol (premium grade): live change outside this feature’s fitted historical range.

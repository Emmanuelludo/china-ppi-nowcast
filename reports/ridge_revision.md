# Ridge specification revision

Ridge v2 scales price changes using genuinely observed training values, with a fixed minimum scale of one log percentage point. Missing values map to the observed training mean. Basket-era missingness indicators are removed.

Each expanding outer training window selects alpha from 10, 25, 100, 400, 1600 and minimum observed history from 2, 12, 24 months using three chronological inner folds. Stable panels require complete training coverage. Preprocessing and eligibility are refitted within every fold. No prediction clipping is applied.

**Caution:** this revision was designed after inspecting August/September instability. August outcomes were excluded from its fitting and tuning, but it is not an untouched validation experiment. Historical scores are exploratory pseudo-real-time evidence; prospective evaluation remains necessary.

All non-ridge artifacts are unchanged. Earlier September forecasts and the original frozen August +0.410% ridge record remain immutable. New September estimates are issued at the actual rerun timestamp, not backdated.

## Matched rolling validation

| Timing | Panel | N | Old MAE | Revised MAE | Old RMSE | Revised RMSE | Old recent MAE | Revised recent MAE | Final alpha | Minimum history | Learned products |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20th-to-20th | All historical products | 115 | 0.329 | 0.276 | 0.495 | 0.366 | 0.703 | 0.334 | 25 | 12 | 78 |
| 20th-to-20th | Stable products | 115 | 0.286 | 0.282 | 0.377 | 0.371 | 0.317 | 0.317 | 100 | 2 | 25 |
| Two-survey period | All historical products | 107 | 0.322 | 0.246 | 0.601 | 0.328 | 1.169 | 0.337 | 25 | 24 | 69 |
| Early month | All historical products | 119 | 0.342 | 0.253 | 0.745 | 0.336 | 1.111 | 0.301 | 100 | 24 | 75 |
| Early + carry-in | All historical products | 116 | 0.362 | 0.280 | 0.542 | 0.380 | 0.572 | 0.361 | 25 | 24 | 148 |

Recent means the last 12 calendar months with eligible observations, not necessarily 12 forecasts. Errors are percentage points.

## August 2026 reconstructed forecasts

| Timing | Panel | Prediction | Actual | Error | Training through |
|---|---|---:|---:|---:|---|
| 20th-to-20th | All historical products | +0.319% | +0.400% | -0.081 | 2026-07 |
| 20th-to-20th | Stable products | +0.234% | +0.400% | -0.166 | 2026-07 |
| Two-survey period | All historical products | +0.436% | +0.400% | +0.036 | 2026-07 |
| Early month | All historical products | +0.379% | +0.400% | -0.021 | 2026-07 |
| Early + carry-in | All historical products | +0.422% | +0.400% | +0.022 | 2026-07 |

## September replacement vintages

| Timing | Panel | Prediction | Issued |
|---|---|---:|---|
| Early month | All historical products | +0.913% | 2026-10-07T04:35:54.229179+08:00 |
| Two-survey period | All historical products | +1.042% | 2026-10-07T04:35:54.229179+08:00 |
| Early + carry-in | All historical products | +1.196% | 2026-10-07T04:35:54.229179+08:00 |
| 20th-to-20th | All historical products | +0.979% | 2026-10-07T04:35:54.229179+08:00 |
| 20th-to-20th | Stable products | +0.781% | 2026-10-07T04:35:54.229179+08:00 |

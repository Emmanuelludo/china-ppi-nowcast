# Historical model comparison

[Latest forecasts](README.md) · [Evaluation methodology](../docs/METHODOLOGY.md)

Expanding-window, nested chronological validation. These results are **pseudo-real-time**: release dates are respected, but historical pages were retrieved later.

MAE, RMSE and bias are in percentage points. Compare models within the same timing and panel; the eligible forecast months differ across timing specifications. The direct tracker is an uncalibrated price index.

| Timing | Product panel | Model | Forecast months | MAE | RMSE | Bias |
|---|---|---|---:|---:|---:|---:|
| 20th-to-20th | All historical products | Product ridge | 115 | 0.329 | 0.495 | -0.015 |
| 20th-to-20th | All historical products | HistGradientBoosting | 115 | 0.349 | 0.464 | -0.067 |
| 20th-to-20th | All historical products | XGBoost | 115 | 0.348 | 0.460 | -0.085 |
| 20th-to-20th | All historical products | CatBoost | 115 | 0.343 | 0.462 | -0.097 |
| 20th-to-20th | All historical products | LightGBM | 115 | 0.339 | 0.454 | -0.066 |
| 20th-to-20th | All historical products | Sector-first regression | 115 | 0.255 | 0.361 | -0.001 |
| 20th-to-20th | All historical products | Random forest | 115 | 0.357 | 0.475 | -0.070 |
| 20th-to-20th | All historical products | Economic / ML hybrid (NBS prices) | 115 | 0.268 | 0.366 | -0.024 |
| 20th-to-20th | All historical products | Direct price tracker | 115 | 2.038 | 2.805 | 0.233 |
| 20th-to-20th | Stable products | Product ridge | 115 | 0.286 | 0.377 | -0.049 |
| 20th-to-20th | Stable products | HistGradientBoosting | 115 | 0.335 | 0.443 | -0.088 |
| 20th-to-20th | Stable products | XGBoost | 115 | 0.333 | 0.446 | -0.098 |
| 20th-to-20th | Stable products | CatBoost | 115 | 0.333 | 0.447 | -0.088 |
| 20th-to-20th | Stable products | LightGBM | 115 | 0.328 | 0.436 | -0.078 |
| Two-survey period | All historical products | Product ridge | 107 | 0.322 | 0.601 | -0.001 |
| Two-survey period | All historical products | HistGradientBoosting | 107 | 0.328 | 0.431 | -0.052 |
| Two-survey period | All historical products | XGBoost | 107 | 0.329 | 0.437 | -0.075 |
| Two-survey period | All historical products | CatBoost | 107 | 0.326 | 0.440 | -0.080 |
| Two-survey period | All historical products | LightGBM | 107 | 0.329 | 0.433 | -0.076 |
| Early month | All historical products | Product ridge | 119 | 0.342 | 0.745 | 0.013 |
| Early month | All historical products | HistGradientBoosting | 119 | 0.341 | 0.449 | -0.097 |
| Early month | All historical products | XGBoost | 119 | 0.332 | 0.441 | -0.106 |
| Early month | All historical products | CatBoost | 119 | 0.329 | 0.443 | -0.111 |
| Early month | All historical products | LightGBM | 119 | 0.327 | 0.437 | -0.101 |
| Early + carry-in | All historical products | Product ridge | 116 | 0.362 | 0.542 | -0.061 |
| Early + carry-in | All historical products | HistGradientBoosting | 116 | 0.348 | 0.449 | -0.098 |
| Early + carry-in | All historical products | XGBoost | 116 | 0.340 | 0.455 | -0.118 |
| Early + carry-in | All historical products | CatBoost | 116 | 0.340 | 0.458 | -0.128 |
| Early + carry-in | All historical products | LightGBM | 116 | 0.334 | 0.446 | -0.112 |

Model version: `product-v3-6ebe4ddbf8e9c7bc`. Training-source coverage: 2014-01-01 to 2026-09-10.

Stable product panels and preprocessing are selected within each training fold. At least six genuinely prospective monthly releases are needed before making strong model-ranking claims.

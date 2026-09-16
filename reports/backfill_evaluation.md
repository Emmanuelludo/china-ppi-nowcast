# Reconstructed-model backfill evaluation

All results below are **pseudo-real-time**. Publication timestamps were used as cutoffs,
but the NBS pages were retrieved later and revision-vintage correctness is not claimed.
Operational validation means that the artifacts, leakage guards, chronology, and model
interfaces passed; it is not a claim that any model is superior.

| Vintage | Model | OOF n | MAE | RMSE | Bias | Direction | 10% mask MAE |
|---|---|---:|---:|---:|---:|---:|---:|

| Vintage | Model | OOF n | MAE | RMSE | Bias | Direction | 10% mask MAE |
|---|---|---:|---:|---:|---:|---:|---:|
| early | Category-factor regression | 45 | 0.356 | 0.503 | 0.140 | 0.711 | 0.363 |
| early | Gradient boosting | 45 | 0.333 | 0.442 | 0.063 | 0.600 | 0.331 |
| early | Economic + ML hybrid | 45 | 0.281 | 0.375 | 0.041 | 0.756 | 0.275 |
| early | Product-level ridge | 45 | 0.281 | 0.388 | -0.077 | 0.667 | 0.262 |
| early | Sector-first aggregation | 45 | 0.367 | 0.531 | 0.025 | 0.689 | 0.360 |
| early | Random forest | 45 | 0.356 | 0.475 | 0.083 | 0.600 | 0.370 |

**early baselines**

- `no_change`: MAE 0.358, RMSE 0.474, bias 0.079, direction 0.047.
- `prior_month_persistence`: MAE 0.284, RMSE 0.406, bias -0.005, direction 0.744.
- `expanding_historical_mean`: MAE 0.357, RMSE 0.486, bias 0.026, direction 0.535.

Panel: 88 product columns; 0 observed in at least 90% of months; median coverage 73.6%; median monthly entry/exit count 0.0.


| Vintage | Model | OOF n | MAE | RMSE | Bias | Direction | 10% mask MAE |
|---|---|---:|---:|---:|---:|---:|---:|
| final | Category-factor regression | 40 | 0.355 | 0.508 | 0.127 | 0.725 | 0.364 |
| final | Gradient boosting | 40 | 0.367 | 0.482 | 0.051 | 0.575 | 0.364 |
| final | Economic + ML hybrid | 40 | 0.343 | 0.439 | 0.093 | 0.700 | 0.346 |
| final | Product-level ridge | 40 | 0.342 | 0.469 | 0.007 | 0.650 | 0.367 |
| final | Sector-first aggregation | 40 | 0.352 | 0.489 | 0.097 | 0.675 | 0.352 |
| final | Random forest | 40 | 0.363 | 0.474 | 0.086 | 0.625 | 0.376 |
| final | 20th-to-20th direct trimmed index | 40 | 1.247 | 1.566 | -0.355 | 0.775 | 1.313 |
| final | 20th-to-20th product ridge | 40 | 0.307 | 0.444 | -0.170 | 0.600 | 0.307 |

**final baselines**

- `no_change`: MAE 0.361, RMSE 0.480, bias 0.088, direction 0.049.
- `prior_month_persistence`: MAE 0.298, RMSE 0.416, bias -0.005, direction 0.732.
- `expanding_historical_mean`: MAE 0.360, RMSE 0.493, bias 0.036, direction 0.537.

Panel: 88 product columns; 0 observed in at least 90% of months; median coverage 73.6%; median monthly entry/exit count 0.0.


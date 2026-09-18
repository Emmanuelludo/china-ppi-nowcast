# Reconstructed-model backfill evaluation

All results below are **pseudo-real-time**. Publication timestamps were used as cutoffs,
but the NBS pages were retrieved later and revision-vintage correctness is not claimed.
Operational validation means that the artifacts, leakage guards, chronology, and model
interfaces passed; it is not a claim that any model is superior.

| Vintage | Model | OOF n | MAE | RMSE | Bias | Direction | 10% mask MAE |
|---|---|---:|---:|---:|---:|---:|---:|

| Vintage | Model | OOF n | MAE | RMSE | Bias | Direction | 10% mask MAE |
|---|---|---:|---:|---:|---:|---:|---:|
| early | Category-factor regression | 120 | 0.356 | 0.476 | -0.138 | 0.650 | 0.370 |
| early | Gradient boosting | 120 | 0.467 | 0.635 | -0.193 | 0.608 | 0.483 |
| early | Economic + ML hybrid | 120 | 0.377 | 0.517 | -0.158 | 0.625 | 0.382 |
| early | Product-level ridge | 120 | 0.641 | 0.960 | -0.380 | 0.533 | 0.644 |
| early | Sector-first aggregation | 120 | 0.340 | 0.461 | -0.135 | 0.675 | 0.347 |
| early | Random forest | 120 | 0.481 | 0.644 | -0.155 | 0.583 | 0.484 |

**early baselines**

- `no_change`: MAE 0.475, RMSE 0.638, bias -0.078, direction 0.068.
- `prior_month_persistence`: MAE 0.380, RMSE 0.536, bias -0.011, direction 0.735.
- `expanding_historical_mean`: MAE 0.478, RMSE 0.651, bias -0.106, direction 0.432.

Panel: 114 product columns; 13 observed in at least 90% of months; median coverage 36.1%; median monthly entry/exit count 0.0.


| Vintage | Model | OOF n | MAE | RMSE | Bias | Direction | 10% mask MAE |
|---|---|---:|---:|---:|---:|---:|---:|
| final | Category-factor regression | 115 | 0.335 | 0.462 | -0.136 | 0.678 | 0.358 |
| final | Gradient boosting | 115 | 0.452 | 0.627 | -0.162 | 0.626 | 0.459 |
| final | Economic + ML hybrid | 115 | 0.364 | 0.499 | -0.138 | 0.661 | 0.370 |
| final | Product-level ridge | 115 | 0.616 | 0.846 | -0.334 | 0.530 | 0.618 |
| final | Sector-first aggregation | 115 | 0.312 | 0.424 | -0.124 | 0.739 | 0.323 |
| final | Random forest | 115 | 0.476 | 0.641 | -0.143 | 0.609 | 0.482 |
| final | 20th-to-20th direct trimmed index | 110 | 1.734 | 2.404 | 0.218 | 0.791 | 1.775 |
| final | 20th-to-20th product ridge | 110 | 0.580 | 0.770 | -0.312 | 0.482 | 0.606 |

**final baselines**

- `no_change`: MAE 0.479, RMSE 0.645, bias -0.079, direction 0.071.
- `prior_month_persistence`: MAE 0.394, RMSE 0.551, bias -0.012, direction 0.722.
- `expanding_historical_mean`: MAE 0.483, RMSE 0.658, bias -0.098, direction 0.437.

Panel: 114 product columns; 0 observed in at least 90% of months; median coverage 35.9%; median monthly entry/exit count 0.0.


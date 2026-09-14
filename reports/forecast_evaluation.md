# Prospective forecast evaluation

Forecast rows are joined to official results without altering the frozen registry.
With fewer than six prospective target months, individual errors should be read directly
and aggregate ranking should not be treated as decisive.

| Model | Vintage | n | MAE | RMSE | Bias | Direction |
|---|---|---:|---:|---:|---:|---:|
| category_factor_regression | early | 1 | 0.213 | 0.213 | -0.213 | 1.000 |
| category_factor_regression | final | 1 | 0.121 | 0.121 | -0.121 | 1.000 |
| economic_ml_hybrid | early | 1 | 0.089 | 0.089 | -0.089 | 1.000 |
| economic_ml_hybrid | final | 1 | 0.030 | 0.030 | -0.030 | 1.000 |
| gradient_boosting | early | 1 | 0.003 | 0.003 | -0.003 | 1.000 |
| gradient_boosting | final | 1 | 0.053 | 0.053 | 0.053 | 1.000 |
| product_level_ridge | early | 1 | 0.012 | 0.012 | 0.012 | 1.000 |
| product_level_ridge | final | 1 | 0.010 | 0.010 | 0.010 | 1.000 |
| random_forest | early | 1 | 0.038 | 0.038 | 0.038 | 1.000 |
| random_forest | final | 1 | 0.109 | 0.109 | 0.109 | 1.000 |
| sector_first_aggregation | early | 1 | 0.212 | 0.212 | -0.212 | 1.000 |
| sector_first_aggregation | final | 1 | 0.173 | 0.173 | -0.173 | 1.000 |

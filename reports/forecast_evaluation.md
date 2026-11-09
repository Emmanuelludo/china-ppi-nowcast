# Forecast archive evaluation

Forecast rows are joined to official results without altering the frozen registry.
With fewer than six prospective target months, individual errors should be read directly
and aggregate ranking should not be treated as decisive.

| Model | Vintage | n | MAE | RMSE | Bias | Direction |
|---|---|---:|---:|---:|---:|---:|
| Category-factor regression | early | 4 | 0.923 | 1.010 | -0.923 | 1.000 |
| Category-factor regression | final | 2 | 0.364 | 0.437 | -0.364 | 1.000 |
| Economic / ML hybrid (NBS prices) | early | 4 | 0.604 | 0.699 | -0.604 | 1.000 |
| Economic / ML hybrid (NBS prices) | final | 3 | 0.314 | 0.373 | -0.314 | 1.000 |
| HistGradientBoosting | early | 4 | 0.464 | 0.547 | -0.464 | 1.000 |
| HistGradientBoosting | final | 3 | 0.240 | 0.274 | -0.205 | 1.000 |
| Product ridge | early | 4 | 0.286 | 0.328 | -0.280 | 1.000 |
| Product ridge | final | 3 | 0.101 | 0.167 | 0.101 | 1.000 |
| Random forest | early | 4 | 0.499 | 0.567 | -0.480 | 1.000 |
| Random forest | final | 3 | 0.329 | 0.376 | -0.256 | 1.000 |
| Sector-first regression | early | 4 | 0.824 | 0.929 | -0.824 | 0.500 |
| Sector-first regression | final | 3 | 0.387 | 0.417 | -0.387 | 1.000 |
| Direct trimmed price tracker | final | 2 | 2.209 | 2.749 | 1.636 | 1.000 |
| 20th-to-20th ridge | final | 2 | 0.444 | 0.444 | -0.444 | 1.000 |

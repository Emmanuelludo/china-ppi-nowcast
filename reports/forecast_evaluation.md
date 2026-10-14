# Forecast archive evaluation

Forecast rows are joined to official results without altering the frozen registry.
With fewer than six prospective target months, individual errors should be read directly
and aggregate ranking should not be treated as decisive.

| Model | Vintage | n | MAE | RMSE | Bias | Direction |
|---|---|---:|---:|---:|---:|---:|
| Category-factor regression | early | 4 | 0.923 | 1.010 | -0.923 | 1.000 |
| Category-factor regression | final | 2 | 0.364 | 0.437 | -0.364 | 1.000 |
| Economic / ML hybrid (NBS prices) | early | 4 | 0.604 | 0.699 | -0.604 | 1.000 |
| Economic / ML hybrid (NBS prices) | final | 2 | 0.244 | 0.324 | -0.244 | 1.000 |
| HistGradientBoosting | early | 4 | 0.464 | 0.547 | -0.464 | 1.000 |
| HistGradientBoosting | final | 2 | 0.187 | 0.230 | -0.134 | 1.000 |
| Product ridge | early | 4 | 0.286 | 0.328 | -0.280 | 1.000 |
| Product ridge | final | 2 | 0.007 | 0.008 | 0.007 | 1.000 |
| Random forest | early | 4 | 0.499 | 0.567 | -0.480 | 1.000 |
| Random forest | final | 2 | 0.332 | 0.399 | -0.223 | 1.000 |
| Sector-first regression | early | 4 | 0.824 | 0.929 | -0.824 | 0.500 |
| Sector-first regression | final | 2 | 0.355 | 0.399 | -0.355 | 1.000 |
| Direct trimmed price tracker | final | 1 | 3.846 | 3.846 | 3.846 | 1.000 |
| 20th-to-20th ridge | final | 1 | 0.420 | 0.420 | -0.420 | 1.000 |

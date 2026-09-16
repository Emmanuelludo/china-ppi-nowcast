# Model and training-data contract

The lost v0.4 fitted objects are not reproducible from the surviving evidence.
Version `reconstructed-v1` therefore defines six new candidate estimators under
the old family labels.

## Training matrix

One row per target month and forecast vintage, sorted chronologically:

| Column | Meaning |
|---|---|
| `target_month` | `YYYY-MM` target identifier |
| `target_mom_pct` | Official headline PPI MoM percentage |
| `vintage` | `early` or `final`; train/evaluate separately where feasible |
| `global__*` | Survey-aligned panel summaries |
| `category__*` | Category summaries and missingness |
| `product__*` | Product-level survey-aligned changes |
| `missing__*` | Product missingness indicators |
| `econ__*` | Optional, explicitly reviewed auxiliary features |

Features must be constructed using only snapshots whose `published_at` and
`retrieved_at` are no later than the row's cutoff. A backtest built from pages
first retrieved later must be labeled pseudo-real-time.

## Reconstructed candidates

| Family label | Reconstructed implementation |
|---|---|
| Category-factor regression | Median imputation + scaling + PCA + ridge |
| Gradient boosting | `HistGradientBoostingRegressor` with native NaNs |
| Economic + ML hybrid | Equal-weight ridge/histogram-boosting voting regressor; currently NBS-only because no reviewed economic inputs were recovered |
| Product-level ridge | Median imputation + missing indicators + ridge |
| Sector-first aggregation | Ridge on global/category summaries |
| Random forest | Median imputation + missing indicators + random forest |

These are transparent defaults for prospective comparison, not assertions about
the lost archive. A bundle becomes operationally validated only after the
minimum-history, chronology, finite-metric, six-artifact, and pseudo-real-time
label checks pass. This gate does not assert model superiority.

## Minimum evaluation

Use expanding-window splits and report MAE, RMSE, bias, directional accuracy,
the individual monthly error sequence, panel-dropout sensitivity, and early vs
final vintage performance. Do not select a permanent winner from six months.


## Version 2: two final-vintage timing benchmarks

The six original candidates continue to use survey-aligned features. For September:

| Level | Price windows used |
|---|---|
| September first survey proxy | August 21–end and September 1–10, equal log weights |
| September second survey proxy | September 11–20 |
| August comparison level | July 21–end, August 1–10 and August 11–20 |
| Early change | September first survey proxy versus August monthly proxy |
| Final change | Mean of September first/second log proxies versus August monthly proxy |
| New 20th-to-20th change | September 11–20 versus August 11–20 only |

Dates are used to construct and gate the features, rather than as numerical calendar predictors.
The ten-day observations are window averages of circulation-market prices, not prices observed
at exactly the 20th or confidential factory-gate survey microdata.

`twentieth_to_twentieth_direct` calculates product level ratios, then removes floor(10% × n)
products from each tail and equally averages the remaining changes. It has no learned weights,
no category weights and no calibration to headline PPI. It is an uncalibrated circulation-price
proxy; it should not be treated as the official PPI basket.

`twentieth_to_twentieth_ridge` regresses those product changes on headline PPI, using fold-local
median imputation, missing indicators, scaling and ridge regularisation. Both candidates require
at least one observed comparable product and are withheld when the current 11–20 release is
unavailable. Early bundles contain six candidates; final bundles contain eight. The original
v1 artifacts and all frozen forecasts remain preserved. The v2 feature hash includes a schema
version to prevent overwriting v1 feature vintages. Historical performance is pseudo-real-time.

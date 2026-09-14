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

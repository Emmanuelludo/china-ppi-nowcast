# Methodology

[Project home](../README.md) · [Latest results](../reports/README.md)

## Target and source

Predict the NBS headline producer price index **month-on-month percentage change**.
A forecast of `+0.7` means `+0.7% MoM`. The inputs are absolute prices in the NBS
*Market Prices of Important Means of Production in Circulation* releases.
These are wholesale/distribution prices, not confidential factory-gate PPI microdata.

## Price timing

| Specification | Product price comparison | Available after |
|---|---|---|
| 20th-to-20th | Current 11–20 period / previous 11–20 period | Current 11–20 release |
| Two-survey period | Mean of current 1–10 and 11–20 levels / corresponding previous mean | Current 11–20 release |
| Early month | Current 1–10 / previous 1–10 | Current 1–10 release |
| Early + carry-in | Early features plus current 1–10 / previous 21–end | Current 1–10 release |

Product changes are `100 × ln(current level / comparison level)`. They are
predictors; the fitted target remains official PPI MoM in percentage points.
Current 21–end prices primarily carry into the next month and are not silently
included in the current two-survey or 20th-to-20th feature.

Separate survey-aligned benchmarks combine the prior 21–end and current 1–10
prices to approximate the first survey date, then use 11–20 for the second.
Their different feature construction explains why similarly named estimators
can produce different forecasts. See the [benchmark contract](MODEL_CONTRACT.md).

## Models

| Family | Role |
|---|---|
| XGBoost, CatBoost, LightGBM, HistGradientBoosting | Nonlinear models using individual product changes |
| Product ridge | Regularized linear comparison |
| Random forest | Alternative tree ensemble |
| Sector-first regression | Regression on grouped price signals |
| Economic / ML hybrid | NBS-price-based linear and boosting combination |
| Direct market-price tracker | Uncalibrated index; displayed separately from PPI forecasts |

All nine active families have 20th-to-20th variants. Five core product estimators also
have early, early-plus-carry and two-survey variants. Five stable-panel
20th-to-20th counterparts provide sensitivity checks: **29 active product-model
variants** in total, alongside the survey-aligned benchmark family.

## Missingness and product definitions

Product identities include name, specification and unit. Structural absence
before introduction or after retirement remains missing. Trees use native missing
handling; linear/factor pipelines fit imputation, missingness indicators and
scaling inside the training fold. Stable panels use training-fold coverage only.
A newly introduced series cannot influence a saved model that has never learned
from it; the forecast metadata records these features.

The [bilingual glossary](PRODUCTS.md) translates display names only. Specification
and footnote variants retain separate historical IDs. Neither labels nor source
units are silently merged. Missing releases, duplicate products and unreviewed
units require QA, rather than invented observations.

## Validation and interpretation

Product models use monthly expanding-window validation with chronological inner
hyperparameter selection. Historical pages were retrieved later, so this is
**pseudo-real-time**, not a fully revision-correct vintage backtest. Compare
models over common forecast months within a timing specification.

Read MAE, RMSE, bias and directional accuracy together with individual errors,
panel sensitivity and market regimes. Accumulate at least six genuinely
prospective releases before making strong model-ranking claims.

SHAP decomposes a tree model's prediction into its baseline and product
attributions. Sector attributions sum the product values **after prediction**.
These are predictive attributions, not causal economic contributions; correlated
prices can redistribute attribution across products.

No permanent winner or weighted ensemble is currently adopted. Model dispersion
is not a calibrated prediction interval. Exact implied YoY and external price
proxies are not part of the current production forecast.

Category-factor models are retired from active inference and comparison tables. Their saved objects and immutable historical forecasts remain in the archive.

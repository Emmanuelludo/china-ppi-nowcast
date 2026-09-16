# Additive product-price models

Existing reconstructed-v1/v2 objects, model identities and frozen forecasts remain unchanged.
The product-v3 family is additional; none of the existing models is removed or promoted away.

## Timing and model coverage

| Specification | Absolute-price comparison | Models |
|---|---|---|
| 20th-to-20th proxy | Current 11–20 / previous 11–20 | XGBoost, CatBoost, LightGBM, HistGB, ridge, random forest, category-factor, sector-first, economic/ML hybrid, direct tracker |
| Final two-survey proxy | Mean(current 1–10, 11–20) / mean(previous 1–10, 11–20) | Five product-level candidates |
| Early | Current 1–10 / previous 1–10 | Five product-level candidates |
| Early plus carry | Early changes plus current 1–10 / previous 21–end | Five product-level candidates |

Predictors are 100 × natural log of these ratios. Final level means are arithmetic;
missing either required product observation leaves the feature missing. Current 21–end
never enters the current final or 20th-to-20th specification.

All-price models use individual product changes. Category/sector benchmarks retain their
aggregation, using all comparable prices within groups. The hybrid combines group ridge
and HistGB; no unverified external macro series is added. The direct tracker is an
uncalibrated geometric circulation-price proxy, not an estimate with official PPI weights.

## Identity and missingness

Unicode/whitespace formatting is normalised. Name/specification and unit define identity;
row order and category labels do not. Replacements are separate series, never invisibly
spliced. A saved catalog records membership epochs and source evidence, including January
2026. Observed epoch dates are bounded by the retrieved releases, not asserted official
revision announcements. Raw Chinese labels are preserved.

The historical union remains in the feature contract. Structural missing values stay NaN
in raw prices/features. Trees handle NaN natively. Ridge/factor pipelines fit median
imputation, indicators and scaling only on each training fold. All-missing training
columns are unlearnable and excluded from that fit; the forecast records any newly observed
features not yet learnable by its saved model. Stable-basket sensitivity uses only columns
complete in its training fold. Missing releases, duplicate series, changed units, and
unexpected missing active products are QA conditions, not structural NaN.

## Validation and interpretation

Each model uses the same eligible monthly expanding outer origins within each specification.
Outer training targets must have been released before the forecast cutoff. Two expanding
inner splits select between two conservative regularization settings. This is a deliberately
small initial search; it is not exhaustive tuning. Historical sources were retrieved later,
so results are pseudo-real-time and not revision-vintage-correct.

Every tree OOS/live forecast saves reconciled SHAP by product; grouped attribution is
calculated afterward. SHAP is model attribution, not causality. Correlated product attribution
can differ between estimators. Pairwise moving-block bootstrap intervals describe uncertainty
in mean absolute loss differences; no automatic winner selection or ensemble promotion occurs.

## Commands and artifacts

Install `python -m pip install -e '.[product]'`.
Train: `python -m china_ppi_nowcast.product train --root .`.
Run: `python -m china_ppi_nowcast.product run --root .`.
Optional `--target-month YYYY-MM --as-of ISO_TIMESTAMP` freezes the information cutoff.
The scheduled workflow calls `ensure`, training only if no product bundle has been configured.
CatBoost requires a normal Linux runtime; it cannot train in a sandbox without `/proc/self/statm`.

Versioned `models/product-v3-*/` contains estimators, canonical prices, catalog, exact training
matrices, package versions, hyperparameters, monthly OOS errors and historical SHAP.
`data/product/vintages/` stores write-once forecasts, feature values/source snapshots and SHAP.
Reports are `reports/product_candidates.md` and `reports/product_latest.md`.
No 20th-to-20th forecast is published before the current 11–20 release.

## Remaining work — not claimed complete

The verified source history currently starts September 2021. Recovering January 2014 onward
is still required; empty earlier rows are not fabricated. NBS states this series began
January 2014, so 2013 is not assumed available:
https://www.stats.gov.cn/hd/cjwtjd/202302/t20230207_1902269.html

Historical proxy sourcing/splicing, additional macro/breadth experiments, prospective ensemble
promotion, exact-index YoY derivation and the full regime/performance dashboard remain separate
follow-up work. YoY is explicitly null until a verified official index path is available.

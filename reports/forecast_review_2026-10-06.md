# China PPI forecast review — 6 October 2026

**Latest available target: September 2026. October has no model forecast yet.**

The pure product boosters give a provisional September reading of **about +0.7%
headline PPI month on month**. Their 20th-to-20th estimates span +0.644% to +0.729%;
the two-survey-period counterparts span +0.639% to +0.744%. These are descriptive
model ranges, not confidence intervals and not a newly selected ensemble.

## Comparable saved forecasts

| Model | 20th-to-20th, all products | Two-survey period, all products | 20th-to-20th, stable products | Historical 20th-to-20th MAE, all products |
|---|---:|---:|---:|---:|
| XGBoost | +0.682% | +0.696% | +0.652% | 0.348 pp |
| CatBoost | +0.729% | +0.639% | +0.802% | 0.343 pp |
| LightGBM | +0.644% | +0.671% | +0.719% | 0.339 pp |
| HistGradientBoosting | +0.691% | +0.744% | +0.697% | 0.349 pp |
| Product ridge | −0.342% | +1.218% | +0.814% | 0.329 pp |
| Random forest | +0.614% | — | — | 0.357 pp |
| Sector-first regression | +1.261% | — | — | 0.255 pp |
| Economic / ML hybrid | +0.945% | — | — | 0.268 pp |

A dash denotes an unimplemented model/timing/panel combination, not a zero.
The stable panel uses 25 live product features. All-product forecasts use 50 live
prices, while retaining historical product identities separately. The comparison
above keeps timing and product panel explicit. MAE covers 115 chronological,
nested pseudo-real-time forecast months; it is not prospective performance.
Category-factor models are retired. The +6.123% direct market-price index is an
uncalibrated circulation-price measure and is excluded from the PPI comparison.

## Does the economic signal make sense?

The [official September 11–20 release](https://www.stats.gov.cn/sj/zxfbhjd/202609/t20260923_1965403.html)
shows chemical and fuel strength alongside softer steel and several metals versus
early September. The saved price levels match the checked official values: methanol
CNY 3,695.9/tonne; LPG CNY 7,488.8/tonne; copper CNY 108,770.0/tonne;
rebar CNY 3,165.1/tonne; LFP CNY 51,881.1/tonne. From the repository's absolute
prices, methanol is approximately 40.2% above August's 11–20 level and LPG 28.9%
higher. These comparisons make positive monthly price pressure plausible.

The survey measures circulation-market prices, which include distribution costs,
profits and taxes. It does not measure the full industrial producer-price basket.
A +0.7% headline PPI model estimate is therefore a fitted translation of these
signals, not their arithmetic average or a causal commodity-weight decomposition.

## Why ridge needs caution

The full-panel 20th-to-20th ridge estimate is −0.342%, compared with +0.814% from
the stable panel: a **1.156 percentage-point sign-changing difference**. Its
all-product two-survey estimate is +1.218%, another material specification change.

Eight current series have only **five usable monthly rows** in the fitted
20th-to-20th matrix: sugar, float glass, polysilicon, acetic acid, ethanol, LFP,
potash and phosphate fertilizer. Nine live product changes fall outside their
individual fitted ranges. This combination makes a high-dimensional linear
estimate sensitive to sparse columns, imputation/missingness terms and
extrapolation. It is not evidence that the broad price process turned negative.
Retain it as a diagnostic; do not erase or repair its frozen estimate after seeing it.

The stable-panel ridge's historical MAE is 0.286 pp, and its latest 12-calendar-month
MAE is 0.317 pp over 10 available forecast months. The corresponding all-product
ridge values are 0.329 pp and 0.703 pp. That deterioration is a substantive reason
to show the stable version alongside the full panel.

## How much confidence is justified?

The four boosters' 20th-to-20th historical MAEs are roughly 0.34–0.35 pp, with
RMSEs around 0.45–0.46 pp. Over the latest 12 calendar months, MAEs are approximately
0.44–0.50 pp across only 10 eligible forecast months. The no-change baseline's
MAE on that same recent sequence is 0.440 pp. Tight booster agreement is therefore
not evidence of a similarly tight uncertainty interval.

Sector-first and hybrid models remain useful, with stronger full-history and recent
MAE comparisons. Their higher September estimates broaden the plausible model
picture and should not be hidden merely because they disagree with the boosters.
No permanent winner, confidence interval or retrospectively optimized ensemble
has been adopted. Continue collecting prospective monthly outcomes.

## Reproducibility and monitoring

[Live quality diagnostics](forecast_quality.md) track panel sensitivity, sparse
series, extrapolation and recent errors. The clean-checkout workflow additionally
reparses raw source snapshots, reconstructs the frozen input vectors, reloads the
saved fitted objects, reproduces the latest model forecasts and checks saved SHAP
reconciliation. Frozen forecasts, raw sources and model objects are preserved.

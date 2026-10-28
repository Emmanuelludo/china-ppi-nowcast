# China PPI nowcast

**Target: 2026-10 · Headline PPI month-on-month change**

Report refreshed: 2026-10-28T16:57:07.991148+08:00. Forecast timestamps remain fixed when inputs are unchanged.

Current-month price windows incorporated: **11-20**.

[Model explanations](../docs/METHODOLOGY.md) · [English product glossary](../docs/PRODUCTS.md) · [Attributions](attributions.md) · [Performance](product_candidates.md)

## Product-price models

All values are predicted official PPI MoM percentages. A dash means that model/timing combination has no saved output.

**Holiday-imputed scenario:** the cancelled first ten-day window is estimated separately for each product as the midpoint of the prior 21–end and current 11–20 observed price levels. This estimate uses information released on the later date; the early-labelled model variants are NOT genuine early-month vintages.

| Model | 20th-to-20th | Two-survey period | Early month | Early + carry-in |
|---|---:|---:|---:|---:|
| XGBoost | +0.279% | +0.454% | +0.576% | +0.442% |
| CatBoost | +0.096% | +0.206% | +0.357% | +0.389% |
| LightGBM | +0.232% | +0.472% | +0.602% | +0.593% |
| HistGradientBoosting | +0.112% | +0.595% | +0.544% | +0.461% |
| Product ridge | +0.271% | +0.264% | +0.335% | +0.404% |
| Random forest | +0.137% | — | — | — |
| Sector-first regression | +0.345% | — | — | — |
| Economic / ML hybrid (NBS prices) | +0.154% | — | — | — |

## Stable-product sensitivity

These models use only series with complete coverage in their training sample.

| Model | 20th-to-20th | Two-survey period | Early month | Early + carry-in |
|---|---:|---:|---:|---:|
| XGBoost | +0.256% | — | — | — |
| CatBoost | +0.170% | — | — | — |
| LightGBM | +0.187% | — | — | — |
| HistGradientBoosting | -0.017% | — | — | — |
| Product ridge | +0.280% | — | — | — |

## Direct market-price tracker

This is an uncalibrated circulation-market price index, **not an official PPI forecast**. It is excluded from forecast summaries.

- 20th-to-20th: **-0.174%**.

## How to read the timings

- **20th-to-20th:** current versus previous month’s 11–20 period prices.
- **Two-survey period:** average of 1–10 and 11–20 prices versus the same previous-month periods.
- **Early month:** current versus previous 1–10 prices.
- **Early + carry-in:** early-month features plus the change from the previous 21–end period.

Active models are retained for comparison. Category-factor models are retired; historical records remain archived. No permanent winner or weighted ensemble has been selected.

Training-source coverage: 2014-01-01 to 2026-09-10. This is the fitted model's training snapshot, not the latest live-data cutoff.

## Source releases used

| Price window | Publication time | Official source |
|---|---|---|
| 2026-09 / 1-10 | 2026-09-14 01:30:00+00:00 | [NBS release](https://www.stats.gov.cn/sj/zxfb/202609/t20260914_1965293.html) |
| 2026-09 / 11-20 | 2026-09-24 01:30:00+00:00 | [NBS release](https://www.stats.gov.cn/sj/zxfb/202609/t20260923_1965403.html) |
| 2026-09 / 21-end | 2026-10-09 01:30:00+00:00 | [NBS release](https://www.stats.gov.cn/sj/zxfb/202610/t20261008_1965465.html) |
| 2026-10 / 11-20 | 2026-10-24 01:30:00+00:00 | [NBS release](https://www.stats.gov.cn/zwfwck/sjfb/202610/t20261023_1965679.html) |

## Forecast archive

[Immutable forecasts and input rows](../data/product/vintages/) · [Saved model objects](../models/)

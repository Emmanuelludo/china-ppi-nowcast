# China PPI nowcast

**Target: 2026-11 · Headline PPI month-on-month change**

Report refreshed: 2026-11-28T18:49:02.815863+08:00. Forecast timestamps remain fixed when inputs are unchanged.

Current-month price windows incorporated: **11-20**.

[Model explanations](../docs/METHODOLOGY.md) · [English product glossary](../docs/PRODUCTS.md) · [Attributions](attributions.md) · [Performance](product_candidates.md)

## Product-price models

All values are predicted official PPI MoM percentages. A dash means that model/timing combination has no saved output.

| Model | 20th-to-20th | Two-survey period | Early month | Early + carry-in |
|---|---:|---:|---:|---:|
| XGBoost | -0.260% | — | — | — |
| CatBoost | -0.396% | — | — | — |
| LightGBM | -0.191% | — | — | — |
| HistGradientBoosting | -0.155% | — | — | — |
| Product ridge | -0.233% | — | — | — |
| Random forest | -0.227% | — | — | — |
| Sector-first regression | -0.162% | — | — | — |
| Economic / ML hybrid (NBS prices) | -0.333% | — | — | — |

## Stable-product sensitivity

These models use only series with complete coverage in their training sample.

| Model | 20th-to-20th | Two-survey period | Early month | Early + carry-in |
|---|---:|---:|---:|---:|
| XGBoost | -0.416% | — | — | — |
| CatBoost | -0.337% | — | — | — |
| LightGBM | -0.371% | — | — | — |
| HistGradientBoosting | -0.344% | — | — | — |
| Product ridge | -0.364% | — | — | — |

## Direct market-price tracker

This is an uncalibrated circulation-market price index, **not an official PPI forecast**. It is excluded from forecast summaries.

- 20th-to-20th: **-3.458%**.

## Awaiting data

- Two-survey period: awaiting price release 2026-10:1-10.
- Early month: awaiting price release 2026-10:1-10.
- Early + carry-in: awaiting price release 2026-10:1-10.

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
| 2026-10 / 11-20 | 2026-10-24 01:30:00+00:00 | [NBS release](https://www.stats.gov.cn/zwfwck/sjfb/202610/t20261023_1965679.html) |
| 2026-11 / 11-20 | 2026-11-24 01:30:00+00:00 | [NBS release](https://www.stats.gov.cn/sj/zxfb/202611/t20261123_1965935.html) |

## Forecast archive

[Immutable forecasts and input rows](../data/product/vintages/) · [Saved model objects](../models/)

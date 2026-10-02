# China PPI nowcast

**Target: 2026-09 · Headline PPI month-on-month change**

Report refreshed: 2026-09-26T15:58:49.559435+08:00. Forecast timestamps remain fixed when inputs are unchanged.

Current-month price windows incorporated: **1-10, 11-20**.

[Model explanations](../docs/METHODOLOGY.md) · [English product glossary](../docs/PRODUCTS.md) · [Attributions](attributions.md) · [Performance](product_candidates.md)

## Product-price models

All values are predicted official PPI MoM percentages. A dash means that model/timing combination has no saved output.

| Model | 20th-to-20th | Two-survey period | Early month | Early + carry-in |
|---|---:|---:|---:|---:|
| XGBoost | +0.682% | +0.696% | +0.618% | +0.675% |
| CatBoost | +0.729% | +0.639% | +0.471% | +0.605% |
| LightGBM | +0.644% | +0.671% | +0.561% | +0.669% |
| HistGradientBoosting | +0.691% | +0.744% | +0.596% | +0.677% |
| Product ridge | -0.342% | +1.218% | +0.913% | +1.207% |
| Random forest | +0.614% | — | — | — |
| Sector-first regression | +1.261% | — | — | — |
| Economic / ML hybrid (NBS prices) | +0.945% | — | — | — |

## Stable-product sensitivity

These models use only series with complete coverage in their training sample.

| Model | 20th-to-20th | Two-survey period | Early month | Early + carry-in |
|---|---:|---:|---:|---:|
| XGBoost | +0.652% | — | — | — |
| CatBoost | +0.802% | — | — | — |
| LightGBM | +0.719% | — | — | — |
| HistGradientBoosting | +0.697% | — | — | — |
| Product ridge | +0.814% | — | — | — |

## Direct market-price tracker

This is an uncalibrated circulation-market price index, **not an official PPI forecast**. It is excluded from forecast summaries.

- 20th-to-20th: **+6.123%**.

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
| 2026-08 / 1-10 | 2026-08-14 01:30:00+00:00 | [NBS release](https://www.stats.gov.cn/sj/zxfb/202608/t20260813_1965025.html) |
| 2026-08 / 11-20 | 2026-08-24 01:30:00+00:00 | [NBS release](https://www.stats.gov.cn/sj/zxfb/202608/t20260821_1965093.html) |
| 2026-08 / 21-end | 2026-09-04 01:30:00+00:00 | [NBS release](https://www.stats.gov.cn/sj/zxfb/202609/t20260903_1965182.html) |
| 2026-09 / 1-10 | 2026-09-14 01:30:00+00:00 | [NBS release](https://www.stats.gov.cn/sj/zxfb/202609/t20260914_1965293.html) |
| 2026-09 / 11-20 | 2026-09-24 01:30:00+00:00 | [NBS release](https://www.stats.gov.cn/sj/zxfb/202609/t20260923_1965403.html) |

## Forecast archive

[Immutable forecasts and input rows](../data/product/vintages/) · [Saved model objects](../models/)

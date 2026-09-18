# Latest China headline PPI MoM nowcast

- Target month: **2026-09**
- Frozen cutoff: **2026-09-19T04:46:48.549295+08:00**
- Information set: **early**
- Comparable products: **50**
- Model median: **+0.670% MoM**
- Model range: **+0.024% to +0.880% MoM**

| Model | Estimate (% MoM) | Provenance |
|---|---:|---|
| Category-factor regression | +0.024 | reconstructed |
| Gradient boosting | +0.770 | reconstructed |
| Economic + ML hybrid | +0.728 | reconstructed |
| Product-level ridge | +0.880 | reconstructed |
| Sector-first aggregation | +0.569 | reconstructed |
| Random forest | +0.611 | reconstructed |

The cross-model range is descriptive dispersion, not a calibrated prediction interval.
The direct 20th-to-20th index is an uncalibrated circulation-price proxy and is excluded from the model median/range.
Both 20th-to-20th benchmarks require the current and prior months’ 11–20 releases; unavailable early in the month.
All candidates are reconstructed because the original v0.4 fitted objects were not recovered.
No permanent model winner is selected from this backfill.

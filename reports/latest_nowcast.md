# Latest China headline PPI MoM nowcast

- Target month: **2026-09**
- Frozen cutoff: **2026-09-24T15:48:16.589073+08:00**
- Information set: **final**
- Comparable products: **50**
- Model median: **+0.743% MoM**
- Model range: **+0.594% to +1.204% MoM**

| Model | Estimate (% MoM) | Provenance |
|---|---:|---|
| Category-factor regression | +0.594 | reconstructed |
| Gradient boosting | +0.879 | reconstructed |
| Economic + ML hybrid | +0.743 | reconstructed |
| Product-level ridge | +1.204 | reconstructed |
| Sector-first aggregation | +0.662 | reconstructed |
| Random forest | +0.646 | reconstructed |
| 20th-to-20th direct trimmed index | +5.046 | reconstructed |
| 20th-to-20th product ridge | +0.780 | reconstructed |

The cross-model range is descriptive dispersion, not a calibrated prediction interval.
The direct 20th-to-20th index is an uncalibrated circulation-price proxy and is excluded from the model median/range.
Both 20th-to-20th benchmarks require the current and prior months’ 11–20 releases; unavailable early in the month.
All candidates are reconstructed because the original v0.4 fitted objects were not recovered.
No permanent model winner is selected from this backfill.

# Adaptive model monitoring

Updated: 2026-10-10T16:54:29.388312+08:00. Monitoring started: 2026-10-07T05:03:46.644079+08:00.

Four newly released monthly outcomes form the default monitoring window. Triggered models receive independently fitted challengers. Each frozen champion/challenger pair uses identical source snapshots, and six future matched monthly outcomes determine a provisional promotion. No historical forecast is rewritten.

Diagnostics describe residual bias, sparse histories, extrapolation and model attributions; they do not establish an economic cause. Source QA failures stop the pipeline. Historical tuning is pseudo-real-time; promotion evidence is prospective.

| Model | Timing | Panel | Released outcomes | Status / trigger |
|---|---|---|---:|---|
| CatBoost | Early month | All historical products | 0 | awaiting released prospective outcomes |
| HistGradientBoosting | Early month | All historical products | 0 | awaiting released prospective outcomes |
| LightGBM | Early month | All historical products | 0 | awaiting released prospective outcomes |
| Product ridge | Early month | All historical products | 0 | awaiting released prospective outcomes |
| XGBoost | Early month | All historical products | 0 | awaiting released prospective outcomes |
| CatBoost | Early + carry-in | All historical products | 0 | awaiting released prospective outcomes |
| HistGradientBoosting | Early + carry-in | All historical products | 0 | awaiting released prospective outcomes |
| LightGBM | Early + carry-in | All historical products | 0 | awaiting released prospective outcomes |
| Product ridge | Early + carry-in | All historical products | 0 | awaiting released prospective outcomes |
| XGBoost | Early + carry-in | All historical products | 0 | awaiting released prospective outcomes |
| CatBoost | Two-survey period | All historical products | 0 | awaiting released prospective outcomes |
| HistGradientBoosting | Two-survey period | All historical products | 0 | awaiting released prospective outcomes |
| LightGBM | Two-survey period | All historical products | 0 | awaiting released prospective outcomes |
| Product ridge | Two-survey period | All historical products | 0 | awaiting released prospective outcomes |
| XGBoost | Two-survey period | All historical products | 0 | awaiting released prospective outcomes |
| CatBoost | 20th-to-20th | Stable products | 0 | awaiting released prospective outcomes |
| HistGradientBoosting | 20th-to-20th | Stable products | 0 | awaiting released prospective outcomes |
| LightGBM | 20th-to-20th | Stable products | 0 | awaiting released prospective outcomes |
| Product ridge | 20th-to-20th | Stable products | 0 | awaiting released prospective outcomes |
| XGBoost | 20th-to-20th | Stable products | 0 | awaiting released prospective outcomes |
| CatBoost | 20th-to-20th | All historical products | 0 | awaiting released prospective outcomes |
| Economic / ML hybrid (NBS prices) | 20th-to-20th | All historical products | 0 | awaiting released prospective outcomes |
| HistGradientBoosting | 20th-to-20th | All historical products | 0 | awaiting released prospective outcomes |
| LightGBM | 20th-to-20th | All historical products | 0 | awaiting released prospective outcomes |
| Random forest | 20th-to-20th | All historical products | 0 | awaiting released prospective outcomes |
| Product ridge | 20th-to-20th | All historical products | 0 | awaiting released prospective outcomes |
| Sector-first regression | 20th-to-20th | All historical products | 0 | awaiting released prospective outcomes |
| XGBoost | 20th-to-20th | All historical products | 0 | awaiting released prospective outcomes |

## Challenger trials

| Model / specification | State | Completed comparison months | Champion MAE | Challenger MAE | Decision |
|---|---|---:|---:|---:|---|
| No trials yet | Armed | 0 | — | — | Awaiting genuinely prospective outcomes |

## Latest matched trial forecasts

| Model / specification | Target month | Incumbent | Refit challenger | Frozen |
|---|---|---:|---:|---|

## Diagnostic evidence for registered trials


A challenger must improve MAE by at least 5% and 0.02 pp, avoid more than 5% RMSE deterioration or 0.05 pp bias deterioration, and win at least half the paired months. These thresholds are operational defaults; six outcomes do not prove permanent superiority.

After a trial, four fresh incumbent outcomes are needed for a new deviation-triggered cycle. A 12-outcome periodic refresh also prevents indefinite staleness. Training and comparison rules are frozen when each trial is registered.

[Monitoring configuration](../config/adaptive.json) · [Append-only decision journal](../data/adaptive/events) · [Matched forecast archive](../data/adaptive/forecasts) · [Technical method](../docs/ADAPTIVE.md)

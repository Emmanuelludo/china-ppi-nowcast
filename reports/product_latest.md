# Additional product PPI forecasts

Target: 2026-09; as of 2026-09-16T23:37:11.005700+08:00

Existing models remain active. These additional candidates do not replace them.
20th-to-20th waits for the current 11–20 release; it is a period-price proxy.

|Timing|Panel|Model|MoM (%)|
|---|---|---|---:|
|early|union|ridge|+0.768|
|early|union|histgb|+0.297|
|early|union|xgboost|+0.465|
|early|union|catboost|+0.395|
|early|union|lightgbm|+0.516|
|early_carry|union|ridge|+0.968|
|early_carry|union|histgb|+0.273|
|early_carry|union|xgboost|+0.578|
|early_carry|union|catboost|+0.551|
|early_carry|union|lightgbm|+0.330|

Pending twentieth: QA: unavailable source release 2026-09:11-20

Pending final: QA: unavailable source release 2026-09:11-20

Direct tracker is uncalibrated. No ensemble weights or model winner have been promoted.
Individual and grouped SHAP files are stored beside each tree forecast. They are model attributions, not causal contributions.
Earlier-than-2021 historical recovery remains outstanding. See the bundle for exact coverage.

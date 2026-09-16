# Additional product models

Bundle: `product-v3-f62708ba53ea7b1d`

Existing models and forecasts are preserved. No permanent winner or ensemble promotion.
Verified history: 2021-09-21–2026-09-10; earlier official history remains outstanding.
20th-to-20th uses current versus previous 11–20 period prices, not exact day-20 factory-gate prices.
All models share eligible monthly OOS origins within a timing specification. Results are pseudo-real-time.

|Timing|Panel|Model|OOS n|MAE|RMSE|Bias|
|---|---|---|---:|---:|---:|---:|
|twentieth|union|ridge|30|0.360|0.593|0.068|
|twentieth|union|histgb|30|0.324|0.449|-0.108|
|twentieth|union|xgboost|30|0.297|0.414|-0.061|
|twentieth|union|catboost|30|0.297|0.426|-0.058|
|twentieth|union|lightgbm|30|0.302|0.443|-0.074|
|twentieth|union|category_factor|30|0.269|0.373|-0.036|
|twentieth|union|sector_first|30|0.276|0.390|0.033|
|twentieth|union|random_forest|30|0.308|0.430|-0.013|
|twentieth|union|economic_ml_hybrid|30|0.287|0.410|-0.000|
|twentieth|union|direct_tracker|30|1.075|1.252|-0.329|
|twentieth|stable|ridge|30|0.296|0.422|-0.036|
|twentieth|stable|histgb|30|0.334|0.436|-0.041|
|twentieth|stable|xgboost|30|0.304|0.401|-0.049|
|twentieth|stable|catboost|30|0.293|0.414|-0.072|
|twentieth|stable|lightgbm|30|0.317|0.425|-0.052|
|final|union|ridge|26|0.371|0.576|0.117|
|final|union|histgb|26|0.351|0.493|-0.106|
|final|union|xgboost|26|0.341|0.491|-0.119|
|final|union|catboost|26|0.314|0.438|-0.023|
|final|union|lightgbm|26|0.343|0.492|-0.126|
|early|union|ridge|30|0.436|1.166|0.252|
|early|union|histgb|30|0.306|0.438|-0.078|
|early|union|xgboost|30|0.295|0.406|-0.061|
|early|union|catboost|30|0.248|0.364|-0.025|
|early|union|lightgbm|30|0.303|0.427|-0.080|
|early_carry|union|ridge|28|0.417|0.813|0.199|
|early_carry|union|histgb|28|0.323|0.459|-0.053|
|early_carry|union|xgboost|28|0.313|0.431|-0.068|
|early_carry|union|catboost|28|0.278|0.377|-0.030|
|early_carry|union|lightgbm|28|0.304|0.439|-0.095|

Tree SHAP values are saved per product and origin, with numerical reconciliation. They are not causal contributions.
Category/sector/hybrid models retain their own aggregation. The hybrid has no unverified external economic inputs.
The direct tracker is an uncalibrated circulation-price index. Stable panels are selected within each training fold.

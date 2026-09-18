# Additional product models

Bundle: `product-v3-6ebe4ddbf8e9c7bc`

Existing models and forecasts are preserved. No permanent winner or ensemble promotion.
Verified history: 2014-01-01–2026-09-10; see the historical discovery audit for remaining gaps.
20th-to-20th uses current versus previous 11–20 period prices, not exact day-20 factory-gate prices.
All models share eligible monthly OOS origins within a timing specification. Results are pseudo-real-time.

|Timing|Panel|Model|OOS n|MAE|RMSE|Bias|
|---|---|---|---:|---:|---:|---:|
|twentieth|union|ridge|115|0.329|0.495|-0.015|
|twentieth|union|histgb|115|0.349|0.464|-0.067|
|twentieth|union|xgboost|115|0.348|0.460|-0.085|
|twentieth|union|catboost|115|0.343|0.462|-0.097|
|twentieth|union|lightgbm|115|0.339|0.454|-0.066|
|twentieth|union|category_factor|115|0.245|0.364|-0.041|
|twentieth|union|sector_first|115|0.255|0.361|-0.001|
|twentieth|union|random_forest|115|0.357|0.475|-0.070|
|twentieth|union|economic_ml_hybrid|115|0.268|0.366|-0.024|
|twentieth|union|direct_tracker|115|2.038|2.805|0.233|
|twentieth|stable|ridge|115|0.286|0.377|-0.049|
|twentieth|stable|histgb|115|0.335|0.443|-0.088|
|twentieth|stable|xgboost|115|0.333|0.446|-0.098|
|twentieth|stable|catboost|115|0.333|0.447|-0.088|
|twentieth|stable|lightgbm|115|0.328|0.436|-0.078|
|final|union|ridge|107|0.322|0.601|-0.001|
|final|union|histgb|107|0.328|0.431|-0.052|
|final|union|xgboost|107|0.329|0.437|-0.075|
|final|union|catboost|107|0.326|0.440|-0.080|
|final|union|lightgbm|107|0.329|0.433|-0.076|
|early|union|ridge|119|0.342|0.745|0.013|
|early|union|histgb|119|0.341|0.449|-0.097|
|early|union|xgboost|119|0.332|0.441|-0.106|
|early|union|catboost|119|0.329|0.443|-0.111|
|early|union|lightgbm|119|0.327|0.437|-0.101|
|early_carry|union|ridge|116|0.362|0.542|-0.061|
|early_carry|union|histgb|116|0.348|0.449|-0.098|
|early_carry|union|xgboost|116|0.340|0.455|-0.118|
|early_carry|union|catboost|116|0.340|0.458|-0.128|
|early_carry|union|lightgbm|116|0.334|0.446|-0.112|

Tree SHAP values are saved per product and origin, with numerical reconciliation. They are not causal contributions.
Category/sector/hybrid models retain their own aggregation. The hybrid has no unverified external economic inputs.
The direct tracker is an uncalibrated circulation-price index. Stable panels are selected within each training fold.

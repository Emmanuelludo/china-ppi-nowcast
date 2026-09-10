"""Naive and autoregressive forecast benchmarks."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .linear import FittedLinearModel, fit_linear


def naive_forecast(history: pd.Series, *, rule: str = "zero_mom") -> float:
    clean = pd.to_numeric(history, errors="coerce").dropna()
    if rule == "zero_mom":
        return 0.0
    if rule == "last_value":
        if clean.empty:
            raise ValueError("last_value naive forecast requires history")
        return float(clean.iloc[-1])
    raise ValueError("rule must be zero_mom or last_value")


def autoregressive_design(target: pd.Series, lags: int = 1) -> tuple[pd.DataFrame, pd.Series]:
    if not 1 <= lags <= 6:
        raise ValueError("lags must be between 1 and 6")
    values = pd.to_numeric(target, errors="coerce")
    X = pd.concat({f"ppi_lag_{lag}": values.shift(lag) for lag in range(1, lags + 1)}, axis=1)
    valid = X.notna().all(axis=1) & values.notna()
    return X.loc[valid], values.loc[valid]


def fit_autoregression(target: pd.Series, lags: int = 1) -> FittedLinearModel:
    X, y = autoregressive_design(target, lags)
    return fit_linear(X, y, feature_names=list(X.columns), family="ar", model_id=f"ar_{lags}")


def forecast_autoregression(model: FittedLinearModel, history: pd.Series) -> float:
    clean = pd.to_numeric(history, errors="coerce").dropna()
    lag_count = len(model.feature_names)
    if len(clean) < lag_count:
        raise ValueError("insufficient target lags")
    row = pd.DataFrame(
        [[clean.iloc[-lag] for lag in range(1, lag_count + 1)]],
        columns=model.feature_names,
    )
    return float(model.predict(row)[0])

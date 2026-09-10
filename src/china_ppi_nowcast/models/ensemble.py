"""Transparent forecast ensembles."""

from __future__ import annotations

import numpy as np
import pandas as pd


def inverse_error_weights(
    error_history: pd.DataFrame,
    *,
    metric: str = "mae",
    floor: float = 1e-6,
) -> pd.Series:
    """Weights based only on errors supplied by the caller's prior-data window."""

    if not {"model_id", "error"}.issubset(error_history.columns):
        raise ValueError("error_history requires model_id and error")
    errors = error_history.copy()
    errors["error"] = pd.to_numeric(errors["error"], errors="coerce")
    if metric == "mae":
        scores = errors.groupby("model_id")["error"].apply(lambda values: values.abs().mean())
    elif metric == "rmse":
        scores = errors.groupby("model_id")["error"].apply(lambda values: np.sqrt(np.mean(values**2)))
    else:
        raise ValueError("metric must be mae or rmse")
    inverse = 1 / scores.clip(lower=floor)
    return inverse / inverse.sum()


def combine_forecasts(forecasts: pd.Series, weights: pd.Series) -> float:
    common = forecasts.dropna().index.intersection(weights.dropna().index)
    if common.empty:
        raise ValueError("no common forecasts and weights")
    normalized = weights.loc[common] / weights.loc[common].sum()
    return float((forecasts.loc[common] * normalized).sum())

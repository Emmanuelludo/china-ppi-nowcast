"""Latent producer-price-pressure state-space bridge."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from .base import validate_sample_size


@dataclass
class FittedStateSpaceModel:
    feature_names: tuple[str, ...]
    imputer: SimpleImputer
    scaler: StandardScaler
    result: object
    residuals: np.ndarray

    def forecast(self, row: pd.DataFrame) -> float:
        exog = self.scaler.transform(self.imputer.transform(row.loc[:, self.feature_names]))
        return float(np.asarray(self.result.forecast(1, exog=exog)).reshape(-1)[0])


def fit_state_space(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    feature_names: list[str],
) -> FittedStateSpaceModel:
    try:
        from statsmodels.tsa.statespace.structural import UnobservedComponents
    except ImportError as exc:  # optional at runtime; declared by the project package
        raise RuntimeError("state-space model requires statsmodels") from exc
    target = pd.to_numeric(y, errors="coerce")
    valid = target.notna()
    validate_sample_size("state_space", int(valid.sum()), len(feature_names) + 2, regularized=True)
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    exog = scaler.fit_transform(imputer.fit_transform(X.loc[valid, feature_names]))
    model = UnobservedComponents(
        target.loc[valid].to_numpy(),
        level="local level",
        autoregressive=1,
        exog=exog,
    )
    result = model.fit(disp=False, maxiter=500)
    residuals = np.asarray(result.resid, dtype=float)
    return FittedStateSpaceModel(tuple(feature_names), imputer, scaler, result, residuals)

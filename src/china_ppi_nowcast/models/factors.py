"""Principal-component price factor bridge."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from .base import validate_sample_size


@dataclass
class FittedFactorModel:
    feature_names: tuple[str, ...]
    imputer: SimpleImputer
    scaler: StandardScaler
    pca: PCA
    regression: Ridge
    residuals: np.ndarray

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        values = self.imputer.transform(frame.loc[:, self.feature_names])
        factors = self.pca.transform(self.scaler.transform(values))
        return self.regression.predict(factors)

    def factor_contributions(self, row: pd.DataFrame) -> dict[str, float]:
        values = self.imputer.transform(row.loc[:, self.feature_names])
        factors = self.pca.transform(self.scaler.transform(values))[0]
        result = {
            f"factor_{index + 1}": float(value * coefficient)
            for index, (value, coefficient) in enumerate(zip(factors, self.regression.coef_))
        }
        result["intercept"] = float(self.regression.intercept_)
        return result


def fit_factor_model(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    feature_names: list[str],
    n_factors: int = 1,
    alpha: float = 1.0,
) -> FittedFactorModel:
    target = pd.to_numeric(y, errors="coerce")
    valid = target.notna()
    validate_sample_size("factor", int(valid.sum()), n_factors + 1, regularized=True)
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    values = scaler.fit_transform(imputer.fit_transform(X.loc[valid, feature_names]))
    components = min(n_factors, values.shape[0], values.shape[1])
    if components < 1:
        raise ValueError("factor model needs at least one usable feature")
    pca = PCA(n_components=components).fit(values)
    factors = pca.transform(values)
    regression = Ridge(alpha=alpha).fit(factors, target.loc[valid])
    residuals = target.loc[valid].to_numpy() - regression.predict(factors)
    return FittedFactorModel(tuple(feature_names), imputer, scaler, pca, regression, residuals)

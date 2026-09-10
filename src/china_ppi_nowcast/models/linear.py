"""OLS, ridge and elastic-net bridges with exact linear attribution."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler

from .base import validate_sample_size


@dataclass
class FittedLinearModel:
    model_id: str
    family: str
    feature_names: tuple[str, ...]
    imputer: SimpleImputer
    scaler: StandardScaler
    estimator: object
    residuals: np.ndarray

    def _transform(self, frame: pd.DataFrame) -> np.ndarray:
        return self.scaler.transform(self.imputer.transform(frame.loc[:, self.feature_names]))

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        return np.asarray(self.estimator.predict(self._transform(frame)), dtype=float)

    def contributions(self, row: pd.DataFrame) -> dict[str, float]:
        """Contributions sum exactly to the model prediction (within floating error)."""

        transformed = self._transform(row)[0]
        coefficients = np.asarray(self.estimator.coef_, dtype=float).reshape(-1)
        result = {
            name: float(value * coefficient)
            for name, value, coefficient in zip(self.feature_names, transformed, coefficients)
        }
        result["intercept"] = float(np.asarray(self.estimator.intercept_).reshape(-1)[0])
        return result


def fit_linear(
    X: pd.DataFrame,
    y: pd.Series | np.ndarray,
    *,
    feature_names: list[str] | tuple[str, ...],
    family: str = "bridge",
    model_id: str | None = None,
    alpha: float = 1.0,
    l1_ratio: float = 0.5,
) -> FittedLinearModel:
    names = tuple(feature_names)
    target = np.asarray(y, dtype=float)
    finite_target = np.isfinite(target)
    X_fit = X.loc[finite_target, names]
    y_fit = target[finite_target]
    regularized = family in {"ridge", "elastic_net"}
    validate_sample_size(family, len(y_fit), len(names) + 1, regularized=regularized)
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    transformed = scaler.fit_transform(imputer.fit_transform(X_fit))
    if family in {"bridge", "ar"}:
        estimator = LinearRegression()
    elif family == "ridge":
        estimator = Ridge(alpha=alpha)
    elif family == "elastic_net":
        estimator = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=20000)
    else:
        raise ValueError("family must be ar, bridge, ridge or elastic_net")
    estimator.fit(transformed, y_fit)
    residuals = y_fit - estimator.predict(transformed)
    return FittedLinearModel(
        model_id=model_id or family,
        family=family,
        feature_names=names,
        imputer=imputer,
        scaler=scaler,
        estimator=estimator,
        residuals=np.asarray(residuals, dtype=float),
    )

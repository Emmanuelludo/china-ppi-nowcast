"""Recursive time-varying-parameter regression."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from .base import validate_sample_size


@dataclass
class FittedTVPModel:
    feature_names: tuple[str, ...]
    imputer: SimpleImputer
    scaler: StandardScaler
    coefficients: np.ndarray
    covariance: np.ndarray
    forgetting_factor: float
    residuals: np.ndarray

    def forecast(self, row: pd.DataFrame) -> float:
        transformed = self.scaler.transform(self.imputer.transform(row.loc[:, self.feature_names]))[0]
        design = np.r_[1.0, transformed]
        return float(design @ self.coefficients)

    def contributions(self, row: pd.DataFrame) -> dict[str, float]:
        transformed = self.scaler.transform(self.imputer.transform(row.loc[:, self.feature_names]))[0]
        values = {
            name: float(value * coefficient)
            for name, value, coefficient in zip(self.feature_names, transformed, self.coefficients[1:])
        }
        values["intercept"] = float(self.coefficients[0])
        return values


def fit_tvp(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    feature_names: list[str],
    forgetting_factor: float = 0.98,
    initial_variance: float = 100.0,
) -> FittedTVPModel:
    if not 0.90 <= forgetting_factor <= 1.0:
        raise ValueError("forgetting_factor must be in [0.90, 1]")
    target = pd.to_numeric(y, errors="coerce")
    valid = target.notna()
    validate_sample_size("tvp", int(valid.sum()), len(feature_names) + 1, regularized=True)
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    values = scaler.fit_transform(imputer.fit_transform(X.loc[valid, feature_names]))
    design = np.column_stack([np.ones(len(values)), values])
    coefficient = np.zeros(design.shape[1])
    covariance = np.eye(design.shape[1]) * initial_variance
    residuals: list[float] = []
    for row, actual in zip(design, target.loc[valid].to_numpy(dtype=float)):
        covariance_prior = covariance / forgetting_factor
        denominator = 1.0 + row @ covariance_prior @ row
        gain = covariance_prior @ row / denominator
        error = float(actual - row @ coefficient)
        coefficient = coefficient + gain * error
        covariance = covariance_prior - np.outer(gain, row) @ covariance_prior
        residuals.append(error)
    return FittedTVPModel(
        tuple(feature_names), imputer, scaler, coefficient, covariance,
        forgetting_factor, np.asarray(residuals),
    )

"""Regularized direct-MIDAS bridge for ten-day feature slots."""

from __future__ import annotations

import pandas as pd

from .linear import FittedLinearModel, fit_linear


def fit_midas_bridge(
    matrix: pd.DataFrame,
    target: pd.Series,
    *,
    alpha: float = 1.0,
) -> FittedLinearModel:
    features = [column for column in matrix if column.startswith("midas__")]
    if not features:
        raise ValueError("matrix has no midas__ feature columns")
    # MIDAS is regularized because slot/product dimensionality is large relative to
    # the monthly sample.  Tuning alpha belongs inside rolling validation.
    return fit_linear(
        matrix,
        target,
        feature_names=features,
        family="ridge",
        model_id="direct_midas_ridge",
        alpha=alpha,
    )

"""Regression checks for the legacy diagnostic's disclosed audit defects."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location("legacy", Path(__file__).parents[1] / "scripts/run_empirical_prototype.py")
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)


def test_interval_inverts_positive_forecast_bias():
    lo, hi = legacy.error_interval(2., np.array([1., 1., 1., 1.]))
    assert (lo, hi) == (1., 1.)


def test_snapshot_rejected_without_explicit_optin(tmp_path):
    path = tmp_path / "targets.csv"
    pd.DataFrame([dict(month="2020-01-01", series_id="headline_ppi_mom", value=1., vintage="current_snapshot_2026", available_at="2020-02-16")]).to_csv(path, index=False)
    with pytest.raises(ValueError, match="Current-snapshot"):
        legacy.load_target(path)


def test_unpublished_training_actual_excluded():
    months = pd.date_range("2020-01-01", periods=6, freq="MS")
    frame = pd.DataFrame(dict(month=months, headline_ppi_mom=np.arange(6.),
        headline_ppi_mom_available_at=pd.to_datetime(["2030-01-01"] * 6, utc=True),
        latest_available_at=pd.to_datetime(months, utc=True), forecast_vintage="early", aggregation_method="test"))
    assert legacy.expanding_backtest(frame, "naive_zero", [], min_train=2).empty


def test_unavailable_lag_masked():
    months = pd.date_range("2020-01-01", periods=3, freq="MS")
    target = pd.DataFrame(dict(month=months, headline_ppi_mom=[1.,2.,3.], headline_ppi_yoy=[1.,2.,3.],
        headline_ppi_mom_available_at=pd.to_datetime(["2030-01-01"] * 3, utc=True)))
    features = pd.DataFrame(dict(month=months, forecast_vintage="early", aggregation_method="test", market_price_factor=1., latest_available_at=pd.to_datetime(months, utc=True)))
    assert legacy.design_frame(features, target, "early", "test").ppi_mom_lag1.isna().all()

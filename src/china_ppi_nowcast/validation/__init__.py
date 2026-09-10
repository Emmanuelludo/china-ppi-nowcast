"""Pseudo-real-time validation primitives for the China PPI nowcast."""

from .backtest import BacktestFold, build_backtest_folds
from .intervals import add_pseudo_realtime_intervals
from .metrics import forecast_metrics, performance_leaderboard
from .realtime import (
    ASIA_SHANGHAI,
    as_of,
    attach_evaluation_targets,
    resolve_available_at,
    select_evaluation_targets,
)
from .scorecard import CriterionSpec, build_model_scorecard
from .turning_points import (
    sign_reversal_flags,
    turning_point_metrics,
    turning_point_table,
)

__all__ = [
    "ASIA_SHANGHAI",
    "BacktestFold",
    "CriterionSpec",
    "add_pseudo_realtime_intervals",
    "as_of",
    "attach_evaluation_targets",
    "build_backtest_folds",
    "build_model_scorecard",
    "forecast_metrics",
    "performance_leaderboard",
    "resolve_available_at",
    "select_evaluation_targets",
    "sign_reversal_flags",
    "turning_point_metrics",
    "turning_point_table",
]

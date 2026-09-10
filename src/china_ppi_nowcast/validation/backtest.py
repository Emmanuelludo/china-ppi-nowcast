"""Construction of leakage-safe pseudo-real-time backtest folds."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .realtime import as_of, select_evaluation_targets


@dataclass(frozen=True)
class BacktestFold:
    target_month: pd.Timestamp
    forecast_vintage: str
    forecast_cutoff: pd.Timestamp
    train_features: pd.DataFrame
    train_targets: pd.DataFrame
    nowcast_features: pd.DataFrame


def build_backtest_folds(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    schedule: pd.DataFrame,
    *,
    feature_month_col: str = "month",
    schedule_month_col: str = "target_month",
    vintage_col: str = "forecast_vintage",
    cutoff_col: str = "forecast_cutoff",
    min_train_months: int = 24,
    rolling_months: int | None = None,
) -> list[BacktestFold]:
    """Build expanding or rolling folds using only values available at each cutoff."""

    required_schedule = {schedule_month_col, vintage_col, cutoff_col}
    missing = required_schedule.difference(schedule.columns)
    if missing:
        raise ValueError(f"schedule missing required columns: {sorted(missing)}")
    selected_targets = select_evaluation_targets(targets)
    selected_targets = selected_targets.rename(columns={"month": feature_month_col})
    selected_targets[feature_month_col] = pd.to_datetime(
        selected_targets[feature_month_col]
    ).dt.to_period("M").dt.to_timestamp()
    work_features = features.copy()
    work_features[feature_month_col] = pd.to_datetime(
        work_features[feature_month_col]
    ).dt.to_period("M").dt.to_timestamp()
    folds: list[BacktestFold] = []
    for _, row in schedule.sort_values(cutoff_col).iterrows():
        target_month = pd.Timestamp(row[schedule_month_col]).to_period("M").to_timestamp()
        cutoff = pd.Timestamp(row[cutoff_col])
        feature_snapshot = as_of(work_features, cutoff)
        target_snapshot = selected_targets.loc[
            selected_targets["primary_actual_available_at"].le(
                pd.Timestamp(cutoff).tz_localize("Asia/Shanghai")
                if pd.Timestamp(cutoff).tzinfo is None
                else pd.Timestamp(cutoff)
            )
        ].copy()
        train_features = feature_snapshot.loc[
            feature_snapshot[feature_month_col].lt(target_month)
        ].copy()
        train_targets = target_snapshot.loc[
            target_snapshot[feature_month_col].lt(target_month)
        ].copy()
        common = sorted(
            set(train_features[feature_month_col]).intersection(
                train_targets[feature_month_col]
            )
        )
        if rolling_months is not None:
            common = common[-rolling_months:]
        if len(common) < min_train_months:
            continue
        train_features = train_features.loc[
            train_features[feature_month_col].isin(common)
        ]
        train_targets = train_targets.loc[train_targets[feature_month_col].isin(common)]
        nowcast = feature_snapshot.loc[
            feature_snapshot[feature_month_col].eq(target_month)
            & feature_snapshot[vintage_col].eq(row[vintage_col])
        ].copy()
        folds.append(
            BacktestFold(
                target_month=target_month,
                forecast_vintage=str(row[vintage_col]),
                forecast_cutoff=cutoff,
                train_features=train_features,
                train_targets=train_targets,
                nowcast_features=nowcast,
            )
        )
    return folds

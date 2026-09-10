from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from china_ppi_nowcast.reporting import FIGURE_SPECS, build_required_figures
from china_ppi_nowcast.validation import (
    CriterionSpec,
    add_pseudo_realtime_intervals,
    as_of,
    attach_evaluation_targets,
    build_model_scorecard,
    select_evaluation_targets,
    sign_reversal_flags,
    turning_point_metrics,
)


def test_date_only_availability_is_next_local_midnight() -> None:
    frame = pd.DataFrame(
        {
            "row": ["date_only", "exact"],
            "available_at": [None, "2024-02-08 09:30:00+08:00"],
            "publication_date": ["2024-02-08", "2024-02-08"],
        }
    )
    before_next_midnight = as_of(frame, "2024-02-08 23:59:59+08:00")
    assert before_next_midnight.row.tolist() == ["exact"]
    at_next_midnight = as_of(frame, "2024-02-09 00:00:00+08:00")
    assert at_next_midnight.row.tolist() == ["date_only", "exact"]


def test_schema_publication_datetime_honors_date_precision() -> None:
    frame = pd.DataFrame(
        {
            "row": ["schema_date"],
            "available_at": [None],
            "publication_datetime": ["2024-02-08 00:00:00"],
            "publication_date_precision": ["date"],
        }
    )
    assert as_of(frame, "2024-02-08 12:00:00+08:00").empty
    assert as_of(frame, "2024-02-09 00:00:00+08:00").row.tolist() == ["schema_date"]


def test_first_release_is_primary_and_latest_settled_is_diagnostic() -> None:
    targets = pd.DataFrame(
        {
            "month": ["2024-01-01", "2024-01-01"],
            "series_id": ["headline_mom", "headline_mom"],
            "value": [0.2, 0.3],
            "vintage": ["first", "revised"],
            "available_at": ["2024-02-08 09:30+08:00", "2024-03-01 09:00+08:00"],
        }
    )
    selected = select_evaluation_targets(targets).iloc[0]
    assert selected.primary_actual == 0.2
    assert selected.latest_settled_actual == 0.3
    assert np.isclose(selected.settled_revision, 0.1)
    assert selected.evaluation_target_policy == "official_first_release"
    assert selected.settled_value_role == "diagnostic_only"

    forecasts = pd.DataFrame(
        {
            "target_month": ["2024-01-01"],
            "target_series_id": ["headline_mom"],
            "forecast": [0.1],
        }
    )
    evaluated = attach_evaluation_targets(forecasts, targets).iloc[0]
    assert evaluated.actual == 0.2
    assert np.isclose(evaluated.error, -0.1)
    assert np.isclose(evaluated.settled_diagnostic_error, -0.2)


def test_interval_calibration_is_vintage_specific_then_explicitly_pooled() -> None:
    frame = pd.DataFrame(
        {
            "model_id": ["m"] * 5,
            "target_series_id": ["headline_mom"] * 5,
            "shock_scenario": ["baseline"] * 5,
            "forecast_vintage": ["early", "early", "final", "final", "final"],
            "forecast": [0.0, 0.0, 0.0, 0.0, 1.0],
            "actual": [0.1, -0.1, 0.2, -0.2, np.nan],
            "forecast_cutoff": [
                "2024-02-01", "2024-03-01", "2024-04-01", "2024-05-01", "2024-06-01"
            ],
            "primary_actual_available_at": [
                "2024-02-10", "2024-03-10", "2024-04-10", "2024-05-10", "2024-06-10"
            ],
        }
    )
    result = add_pseudo_realtime_intervals(
        frame, min_vintage_n=3, min_pooled_n=4, alpha=0.2
    )
    current = result.iloc[-1]
    assert current.interval_calibration_scope == "pooled_vintages"
    assert current.interval_calibration_n == 4
    assert current.lower_bound < current.forecast < current.upper_bound


def test_interval_excludes_errors_not_released_by_cutoff() -> None:
    frame = pd.DataFrame(
        {
            "model_id": ["m", "m"],
            "target_series_id": ["s", "s"],
            "shock_scenario": ["baseline", "baseline"],
            "forecast_vintage": ["early", "early"],
            "forecast": [0.0, 0.0],
            "actual": [10.0, np.nan],
            "forecast_cutoff": ["2024-01-01", "2024-02-01"],
            "primary_actual_available_at": ["2024-02-02", "2024-03-02"],
        }
    )
    result = add_pseudo_realtime_intervals(frame, min_vintage_n=1, min_pooled_n=1)
    assert result.iloc[1].interval_calibration_scope == "unavailable"
    assert np.isnan(result.iloc[1].lower_bound)


def test_sign_reversal_is_primary_turning_point_definition() -> None:
    values = pd.Series([0.2, 0.0, -0.1, -0.2, 0.3])
    assert sign_reversal_flags(values).tolist() == [False, False, True, False, True]
    frame = pd.DataFrame(
        {
            "target_month": pd.date_range("2024-01-01", periods=5, freq="MS"),
            "actual": values,
            "forecast": [0.1, 0.0, -0.2, -0.1, 0.2],
        }
    )
    metrics = turning_point_metrics(frame)
    assert metrics["turn_definition"] == "sign_reversal"
    assert metrics["turn_true_positives"] == 2
    assert sign_reversal_flags(pd.Series([0.2, np.nan, -0.1])).tolist() == [False, False, False]


def test_scorecard_never_reweights_around_missing_criteria() -> None:
    metrics = pd.DataFrame(
        {
            "model_id": ["complete", "missing"],
            "rmse": [0.2, 0.1],
            "directional_accuracy": [0.7, np.nan],
        }
    )
    result = build_model_scorecard(
        metrics,
        [
            CriterionSpec("rmse", 0.6, "lower"),
            CriterionSpec("directional_accuracy", 0.4, "higher"),
        ],
    ).set_index("model_id")
    assert bool(result.loc["complete", "scorecard_eligible"])
    assert not bool(result.loc["missing", "scorecard_eligible"])
    assert np.isnan(result.loc["missing", "model_score"])
    assert result.loc["missing", "missing_criteria"] == "directional_accuracy"
    assert result.loc["missing", "missing_criteria_policy"] == "ineligible_no_weight_redistribution"


def test_required_figure_dispatcher_audits_all_fifteen_panels() -> None:
    figures, manifest = build_required_figures({})
    assert len(FIGURE_SPECS) == 15
    assert len(figures) == 15
    assert len(manifest) == 15
    assert set(manifest.status) == {"input_unavailable"}
    for figure in figures.values():
        plt.close(figure)

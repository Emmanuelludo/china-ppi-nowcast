"""Multi-criterion model scorecards with strict missing-data treatment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CriterionSpec:
    """Definition of one scorecard criterion."""

    column: str
    weight: float
    direction: Literal["higher", "lower"]

    def __post_init__(self) -> None:
        if self.weight <= 0:
            raise ValueError("criterion weights must be positive")


def _minmax_score(values: pd.Series, direction: str) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    valid = numeric.dropna()
    score = pd.Series(np.nan, index=values.index, dtype="float64")
    if valid.empty:
        return score
    lo, hi = valid.min(), valid.max()
    if np.isclose(lo, hi):
        score.loc[valid.index] = 1.0
    else:
        score.loc[valid.index] = (valid - lo) / (hi - lo)
        if direction == "lower":
            score.loc[valid.index] = 1.0 - score.loc[valid.index]
    return score


def build_model_scorecard(
    metrics: pd.DataFrame,
    criteria: list[CriterionSpec],
    *,
    model_col: str = "model_id",
) -> pd.DataFrame:
    """Normalize criteria, aggregate fixed weights, and rank eligible models.

    A model missing any criterion is ineligible and receives ``NaN`` total score.
    Weights are normalized once across the full criterion set and are never
    reweighted model-by-model to hide missing evidence.
    """

    if not criteria:
        raise ValueError("at least one criterion is required")
    required = {model_col, *(criterion.column for criterion in criteria)}
    missing = required.difference(metrics.columns)
    if missing:
        raise ValueError(f"metrics missing scorecard columns: {sorted(missing)}")
    out = metrics.copy()
    total_weight = sum(criterion.weight for criterion in criteria)
    score_cols: list[str] = []
    for criterion in criteria:
        score_col = f"score__{criterion.column}"
        out[score_col] = _minmax_score(out[criterion.column], criterion.direction)
        score_cols.append(score_col)
    out["missing_criteria"] = out.apply(
        lambda row: ",".join(
            criterion.column
            for criterion, score_col in zip(criteria, score_cols, strict=True)
            if pd.isna(row[score_col])
        ),
        axis=1,
    )
    out["scorecard_eligible"] = out["missing_criteria"].eq("")
    weighted = sum(
        out[score_col] * (criterion.weight / total_weight)
        for criterion, score_col in zip(criteria, score_cols, strict=True)
    )
    out["model_score"] = weighted.where(out["scorecard_eligible"])
    out["model_rank"] = out["model_score"].rank(
        method="min", ascending=False, na_option="bottom"
    )
    out.loc[~out["scorecard_eligible"], "model_rank"] = np.nan
    out["missing_criteria_policy"] = "ineligible_no_weight_redistribution"
    return out.sort_values(
        ["scorecard_eligible", "model_score"], ascending=[False, False], na_position="last"
    ).reset_index(drop=True)

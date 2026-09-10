"""Shared model contracts and complexity gates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


MINIMUM_HISTORY = {
    "naive": 1,
    "ar": 36,
    "bridge": 36,
    "ridge": 60,
    "elastic_net": 60,
    "factor": 60,
    "midas": 60,
    "state_space": 72,
    "tvp": 72,
    "ensemble": 36,
}


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    family: str
    feature_columns: tuple[str, ...] = ()
    parameters: dict[str, Any] = field(default_factory=dict)
    target_series_id: str = "headline_ppi_mom"


@dataclass
class ForecastEstimate:
    model_id: str
    forecast: float
    lower_bound: float | None = None
    upper_bound: float | None = None
    contributions: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


def minimum_history(family: str) -> int:
    try:
        return MINIMUM_HISTORY[family]
    except KeyError as exc:
        raise ValueError(f"unknown model family: {family}") from exc


def validate_sample_size(family: str, n_observations: int, n_parameters: int, *, regularized: bool) -> None:
    """Enforce lead-adjudicated history and degrees-of-freedom gates."""

    required = minimum_history(family)
    if not regularized:
        required = max(required, 3 * n_parameters, 36 if family != "naive" else 1)
    if n_observations < required:
        raise ValueError(
            f"insufficient history for {family}: n={n_observations}, required={required}, "
            f"p={n_parameters}"
        )

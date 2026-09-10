"""Signal-level shock scenarios."""

from __future__ import annotations

import pandas as pd


def apply_signal_scenario(
    frame: pd.DataFrame,
    signal_columns: list[str],
    *,
    scenario: str,
    multiplier_column: str = "signal_multiplier",
) -> pd.DataFrame:
    """Return a scenario copy, never modifying economic-weight columns."""

    if scenario not in {"baseline", "shock_adjusted"}:
        raise ValueError("scenario must be baseline or shock_adjusted")
    result = frame.copy()
    if scenario == "baseline":
        return result
    if multiplier_column not in result:
        raise ValueError(f"frame missing {multiplier_column}")
    for column in signal_columns:
        if column not in result:
            raise ValueError(f"frame missing signal column {column}")
        result[column] = result[column] * result[multiplier_column]
    return result

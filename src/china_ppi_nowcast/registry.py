"""Append-only forecast and actual registries."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .schema import ACTUAL_COLUMNS, FORECAST_COLUMNS
from .storage import atomic_write_csv, read_csv_or_empty, stable_hash


FORECAST_LOGICAL_KEY = ["target_month", "vintage", "model_key", "model_version", "feature_hash"]


def append_forecasts(path: Path, rows: list[dict[str, object]]) -> int:
    current = read_csv_or_empty(path, FORECAST_COLUMNS)
    additions: list[dict[str, object]] = []
    for raw in rows:
        row = {column: raw.get(column, "") for column in FORECAST_COLUMNS}
        logical = {key: str(row[key]) for key in FORECAST_LOGICAL_KEY}
        row["forecast_id"] = row["forecast_id"] or stable_hash(
            {**logical, "estimate_mom_pct": str(row["estimate_mom_pct"])}
        )[:24]
        if not current.empty:
            mask = pd.Series(True, index=current.index)
            for key, value in logical.items():
                mask &= current[key].astype(str).eq(value)
            matches = current.loc[mask]
            if not matches.empty:
                stored = pd.to_numeric(matches["estimate_mom_pct"], errors="raise").to_numpy(dtype=float)
                incoming = float(row["estimate_mom_pct"])
                same = bool(np.isclose(stored, incoming, rtol=0.0, atol=1e-12).all())
                if not same:
                    raise ValueError(f"immutable forecast conflict for {logical}")
                continue
        additions.append(row)
        current = pd.DataFrame([row]) if current.empty else pd.concat([current, pd.DataFrame([row])], ignore_index=True)
    if additions:
        atomic_write_csv(path, current[FORECAST_COLUMNS])
    return len(additions)


def append_actuals(path: Path, rows: list[dict[str, object]]) -> int:
    current = read_csv_or_empty(path, ACTUAL_COLUMNS)
    additions = 0
    for raw in rows:
        row = {column: raw.get(column, "") for column in ACTUAL_COLUMNS}
        if not current.empty:
            exact = (
                current["target_month"].eq(str(row["target_month"]))
                & current["content_sha256"].eq(str(row["content_sha256"]))
            )
            if exact.any():
                continue
        current = pd.DataFrame([row]) if current.empty else pd.concat([current, pd.DataFrame([row])], ignore_index=True)
        additions += 1
    if additions:
        atomic_write_csv(path, current[ACTUAL_COLUMNS])
    return additions

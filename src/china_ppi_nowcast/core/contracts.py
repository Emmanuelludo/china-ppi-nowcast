"""Runtime checks for tabular hand-offs."""

from __future__ import annotations

from collections.abc import Iterable
import pandas as pd


def require_columns(frame: pd.DataFrame, columns: Iterable[str], table: str) -> None:
    missing = sorted(set(["schema_version", *columns]).difference(frame.columns))
    if missing:
        raise ValueError(f"{table}: missing required columns: {', '.join(missing)}")


def require_unique(frame: pd.DataFrame, keys: Iterable[str], table: str) -> None:
    if frame.duplicated(list(keys), keep=False).any():
        raise ValueError(f"{table}: duplicate primary keys")


def require_unit_interval(frame: pd.DataFrame, columns: Iterable[str], table: str) -> None:
    for column in columns:
        values = pd.to_numeric(frame[column], errors="coerce")
        if (values.notna() & ~values.between(0, 1)).any():
            raise ValueError(f"{table}.{column}: values outside [0, 1]")


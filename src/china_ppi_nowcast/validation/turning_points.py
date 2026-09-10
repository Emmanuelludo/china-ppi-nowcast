"""Turning-point definitions and scoring."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _carried_sign(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    signs = pd.Series(np.sign(numeric), index=values.index, dtype="float64")
    carried = pd.Series(np.nan, index=values.index, dtype="float64")
    prior = np.nan
    for idx, sign in signs.items():
        if pd.isna(sign):
            prior = np.nan
            continue
        if sign == 0:
            carried.loc[idx] = prior
            continue
        prior = sign
        carried.loc[idx] = sign
    return carried


def sign_reversal_flags(values: pd.Series) -> pd.Series:
    """Primary turning-point flag: a reversal between non-zero signs.

    Zeros inherit the most recent non-zero sign, so ``+ -> 0 -> -`` is one reversal
    when the negative value arrives. Missing values break evaluation until a new sign
    is observed but never count as a reversal themselves.
    """

    signs = _carried_sign(values)
    flags = signs.notna() & signs.shift(1).notna() & signs.ne(signs.shift(1))
    return flags.astype(bool)


def turning_point_table(
    frame: pd.DataFrame,
    *,
    actual_col: str = "actual",
    forecast_col: str = "forecast",
    date_col: str = "target_month",
) -> pd.DataFrame:
    """Return actual and predicted sign-reversal flags by date."""

    required = {actual_col, forecast_col, date_col}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"frame missing required columns: {sorted(missing)}")
    out = frame[[date_col, actual_col, forecast_col]].copy().sort_values(date_col)
    out["actual_turn"] = sign_reversal_flags(out[actual_col])
    out["predicted_turn"] = sign_reversal_flags(out[forecast_col])
    out["turn_hit"] = out["actual_turn"] & out["predicted_turn"]
    out["turn_definition"] = "sign_reversal"
    return out


def turning_point_metrics(
    frame: pd.DataFrame,
    *,
    actual_col: str = "actual",
    forecast_col: str = "forecast",
    date_col: str = "target_month",
) -> dict[str, float | int | str]:
    """Score exact-month sign-reversal detection."""

    table = turning_point_table(
        frame, actual_col=actual_col, forecast_col=forecast_col, date_col=date_col
    )
    tp = int((table.actual_turn & table.predicted_turn).sum())
    fp = int((~table.actual_turn & table.predicted_turn).sum())
    fn = int((table.actual_turn & ~table.predicted_turn).sum())
    precision = tp / (tp + fp) if tp + fp else np.nan
    recall = tp / (tp + fn) if tp + fn else np.nan
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else np.nan
    return {
        "turn_definition": "sign_reversal",
        "turn_true_positives": tp,
        "turn_false_positives": fp,
        "turn_false_negatives": fn,
        "turn_precision": float(precision),
        "turn_recall": float(recall),
        "turn_f1": float(f1),
    }

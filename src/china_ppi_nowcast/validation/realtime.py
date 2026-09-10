"""Availability and evaluation-target rules.

All comparisons occur in UTC after interpreting naive timestamps in China Standard
Time.  A publication represented by a date but no timestamp is conservatively
available at 00:00 on the *following* local day.  This prevents a midnight value
from leaking into a forecast made earlier on an unknown release day.
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd

ASIA_SHANGHAI = ZoneInfo("Asia/Shanghai")
UTC = ZoneInfo("UTC")


def _one_timestamp_utc(value: object, *, date_only: bool = False) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if pd.isna(ts):
        return pd.NaT
    if date_only:
        ts = ts.normalize() + pd.Timedelta(days=1)
    if ts.tzinfo is None:
        ts = ts.tz_localize(ASIA_SHANGHAI)
    return ts.tz_convert(UTC)


def resolve_available_at(
    frame: pd.DataFrame,
    *,
    available_at_col: str = "available_at",
    publication_date_col: str = "publication_date",
    publication_datetime_col: str = "publication_datetime",
    precision_col: str = "publication_date_precision",
) -> pd.Series:
    """Return a timezone-aware UTC availability series.

    Exact ``available_at`` values take precedence. Missing exact values fall back
    to the next midnight after ``publication_date`` in Asia/Shanghai. Rows with
    neither field remain ``NaT`` and therefore cannot enter an as-of dataset.
    """

    resolved = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns, UTC]")
    if available_at_col in frame:
        mask = frame[available_at_col].notna()
        if mask.any():
            resolved.loc[mask] = frame.loc[mask, available_at_col].map(
                _one_timestamp_utc
            )
    if publication_datetime_col in frame:
        mask = resolved.isna() & frame[publication_datetime_col].notna()
        if mask.any():
            def resolve_publication(row: pd.Series) -> pd.Timestamp:
                value = row[publication_datetime_col]
                precision = str(row.get(precision_col, "")).strip().lower()
                inferred_date_only = (
                    isinstance(value, date)
                    and not isinstance(value, datetime)
                    or isinstance(value, str)
                    and len(value.strip()) == 10
                )
                date_only = precision in {"date", "day", "date_only"} or inferred_date_only
                return _one_timestamp_utc(value, date_only=date_only)

            resolved.loc[mask] = frame.loc[mask].apply(resolve_publication, axis=1)
    if publication_date_col in frame:
        mask = resolved.isna() & frame[publication_date_col].notna()
        if mask.any():
            resolved.loc[mask] = frame.loc[mask, publication_date_col].map(
                lambda value: _one_timestamp_utc(value, date_only=True)
            )
    return resolved


def as_of(
    frame: pd.DataFrame,
    cutoff: object,
    *,
    available_at_col: str = "available_at",
    publication_date_col: str = "publication_date",
    publication_datetime_col: str = "publication_datetime",
    precision_col: str = "publication_date_precision",
    keep_resolved_column: bool = False,
) -> pd.DataFrame:
    """Filter rows to values that were knowable at ``cutoff``.

    Rows with unresolved availability are excluded, never silently treated as old.
    """

    cutoff_utc = _one_timestamp_utc(cutoff)
    available = resolve_available_at(
        frame,
        available_at_col=available_at_col,
        publication_date_col=publication_date_col,
        publication_datetime_col=publication_datetime_col,
        precision_col=precision_col,
    )
    result = frame.loc[available.notna() & available.le(cutoff_utc)].copy()
    if keep_resolved_column:
        result["resolved_available_at"] = available.loc[result.index]
    return result


def select_evaluation_targets(
    targets: pd.DataFrame,
    *,
    month_col: str = "month",
    series_col: str = "series_id",
    value_col: str = "value",
    vintage_col: str = "vintage",
    available_at_col: str = "available_at",
    publication_date_col: str = "publication_date",
    publication_datetime_col: str = "publication_datetime",
    precision_col: str = "publication_date_precision",
    settled_cutoff: object | None = None,
) -> pd.DataFrame:
    """Select first-release primary actuals and latest-settled diagnostics.

    The primary forecast target is always the earliest available official release.
    The most recently available value is returned under ``latest_settled_*`` and
    must not be used for model ranking. ``settled_cutoff`` recreates an historical
    diagnostic vintage; with ``None``, the latest row in the supplied snapshot wins.
    """

    required = {month_col, series_col, value_col, vintage_col}
    missing = required.difference(targets.columns)
    if missing:
        raise ValueError(f"targets missing required columns: {sorted(missing)}")
    work = targets.copy()
    work["_available"] = resolve_available_at(
        work,
        available_at_col=available_at_col,
        publication_date_col=publication_date_col,
        publication_datetime_col=publication_datetime_col,
        precision_col=precision_col,
    )
    work = work.loc[work["_available"].notna()].copy()
    if settled_cutoff is not None:
        work = work.loc[work["_available"].le(_one_timestamp_utc(settled_cutoff))]
    work[month_col] = pd.to_datetime(work[month_col]).dt.to_period("M").dt.to_timestamp()
    keys = [month_col, series_col]
    work = work.sort_values(keys + ["_available", vintage_col], kind="stable")
    first = work.groupby(keys, sort=False, as_index=False).first()
    latest = work.groupby(keys, sort=False, as_index=False).last()
    first = first[keys + [value_col, vintage_col, "_available"]].rename(
        columns={
            value_col: "primary_actual",
            vintage_col: "primary_actual_vintage",
            "_available": "primary_actual_available_at",
        }
    )
    latest = latest[keys + [value_col, vintage_col, "_available"]].rename(
        columns={
            value_col: "latest_settled_actual",
            vintage_col: "latest_settled_vintage",
            "_available": "latest_settled_available_at",
        }
    )
    result = first.merge(latest, on=keys, how="outer", validate="one_to_one")
    result["settled_revision"] = (
        result["latest_settled_actual"] - result["primary_actual"]
    )
    result["evaluation_target_policy"] = "official_first_release"
    result["settled_value_role"] = "diagnostic_only"
    return result.sort_values(keys).reset_index(drop=True)


def attach_evaluation_targets(
    forecasts: pd.DataFrame,
    targets: pd.DataFrame,
    *,
    forecast_month_col: str = "target_month",
    forecast_series_col: str = "target_series_id",
    target_month_col: str = "month",
    target_series_col: str = "series_id",
    settled_cutoff: object | None = None,
) -> pd.DataFrame:
    """Attach first-release actuals and separate latest-settled diagnostics."""

    selected = select_evaluation_targets(
        targets,
        month_col=target_month_col,
        series_col=target_series_col,
        settled_cutoff=settled_cutoff,
    ).rename(
        columns={
            target_month_col: forecast_month_col,
            target_series_col: forecast_series_col,
        }
    )
    result = forecasts.copy()
    result[forecast_month_col] = (
        pd.to_datetime(result[forecast_month_col]).dt.to_period("M").dt.to_timestamp()
    )
    result = result.merge(
        selected,
        on=[forecast_month_col, forecast_series_col],
        how="left",
        validate="many_to_one",
    )
    result["actual"] = result["primary_actual"]
    result["error"] = result["forecast"] - result["primary_actual"]
    result["settled_diagnostic_error"] = (
        result["forecast"] - result["latest_settled_actual"]
    )
    return result

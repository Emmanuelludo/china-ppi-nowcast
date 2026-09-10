"""Convert event intervals to model-ready flags without look-ahead."""

from __future__ import annotations

import pandas as pd


def _utc(value: str | pd.Timestamp) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    return stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")


def events_available_at(events: pd.DataFrame, cutoff: str | pd.Timestamp) -> pd.DataFrame:
    """Return only events known by the forecast cutoff."""

    known = pd.to_datetime(events["available_at"], utc=True) <= _utc(cutoff)
    return events.loc[known].copy()


def expand_event_flags(events: pd.DataFrame, dates: pd.Series | list[object], cutoff: str | pd.Timestamp) -> pd.DataFrame:
    """Create a date/entity panel for events both active and known at cutoff."""

    known = events_available_at(events, cutoff)
    date_frame = pd.DataFrame({"date": pd.to_datetime(pd.Series(dates)).dt.normalize()}).drop_duplicates()
    rows: list[dict[str, object]] = []
    for event in known.itertuples(index=False):
        start = pd.Timestamp(event.start_date)
        end = pd.Timestamp(event.end_date) if pd.notna(event.end_date) else pd.Timestamp.max.normalize()
        for date in date_frame.loc[date_frame["date"].between(start, end), "date"]:
            rows.append({
                "date": date, "event_id": event.event_id, "entity_level": event.entity_level, "entity_id": event.entity_id,
                "shock_type": event.shock_type, "expected_direction": event.expected_direction, "confidence": event.confidence,
                "event_active": 1, "available_at": event.available_at,
            })
    return pd.DataFrame(rows, columns=["date", "event_id", "entity_level", "entity_id", "shock_type", "expected_direction", "confidence", "event_active", "available_at"])

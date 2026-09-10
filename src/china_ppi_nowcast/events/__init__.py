"""Structural-shock registry and pseudo-real-time event flags."""

from .catalog import build_event_catalog
from .flags import events_available_at, expand_event_flags

__all__ = ["build_event_catalog", "events_available_at", "expand_event_flags"]

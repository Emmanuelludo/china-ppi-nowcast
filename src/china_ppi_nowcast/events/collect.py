"""Write the curated event registry and source audit."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .catalog import build_event_catalog


def collect_events(root: Path) -> dict[str, int]:
    output = root / "data/interim/events"
    output.mkdir(parents=True, exist_ok=True)
    events = build_event_catalog()
    events.to_csv(output / "event_flags.csv", index=False)
    source_audit = events[["source_url", "source_quality"]].drop_duplicates().copy()
    source_audit["primary_source_followup_required"] = source_audit["source_quality"].isin(["official_agency_home_archive_needed", "reputable_secondary_government_report"])
    source_audit.to_csv(output / "event_source_audit.csv", index=False)
    return {"event_entity_rows": len(events), "events": events["event_id"].nunique(), "entities": events["entity_id"].nunique()}

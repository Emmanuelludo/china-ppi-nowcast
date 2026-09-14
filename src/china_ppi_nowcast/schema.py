"""Canonical schemas and validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Window(str, Enum):
    FIRST = "1-10"
    SECOND = "11-20"
    THIRD = "21-end"


OBSERVATION_COLUMNS = [
    "release_id",
    "release_month",
    "window",
    "category_cn",
    "product_name_cn",
    "unit_cn",
    "price_cny",
    "change_cny",
    "change_pct",
    "published_at",
    "retrieved_at",
    "source_url",
    "content_sha256",
]

FORECAST_COLUMNS = [
    "forecast_id",
    "target_month",
    "as_of",
    "as_of_precision",
    "vintage",
    "model_key",
    "model_label",
    "model_version",
    "model_provenance",
    "estimate_mom_pct",
    "data_cutoff",
    "feature_hash",
    "code_commit",
    "status",
    "created_at",
    "actual_mom_pct",
    "notes",
]

ACTUAL_COLUMNS = [
    "target_month",
    "actual_mom_pct",
    "published_at",
    "retrieved_at",
    "source_url",
    "content_sha256",
    "notes",
]


@dataclass(frozen=True)
class ReleaseIdentity:
    release_month: str
    window: Window
    published_at: datetime
    source_url: str

    @property
    def release_id(self) -> str:
        return f"{self.release_month}:{self.window.value}:{self.published_at.isoformat()}"

"""Identity resolution and validation for the product ontology.

Names are normalized only to resolve spelling, Unicode, and punctuation variants of an
already-curated exact product.  Fuzzy matching is intentionally absent: similarity is
not evidence of comparability.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


SCHEMA_VERSION = "0.1.0"
COMPARABILITY_TYPES = {
    "identical",
    "directly_comparable",
    "comparable_with_scaling",
    "partially_comparable",
    "successor_predecessor",
    "non_comparable",
}


def normalize_identity_text(value: object) -> str:
    """Return a deterministic comparison form without semantic substitutions."""

    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = unicodedata.normalize("NFKC", str(value)).strip().lower()
    translations = str.maketrans({
        "（": "(", "）": ")", "，": ",", "；": ";", "：": ":",
        "×": "*", "–": "-", "—": "-", "−": "-", "＃": "#",
    })
    text = text.translate(translations)
    text = re.sub(r"\s+", "", text)
    return text


def normalize_unit(value: object) -> str:
    """Normalize only exact unit synonyms, not physical dimensions or quote bases."""

    unit = normalize_identity_text(value)
    aliases = {
        "ton": "tonne", "tons": "tonne", "metricton": "tonne", "吨": "tonne", "公吨": "tonne",
        "kilogram": "kg", "kilograms": "kg", "千克": "kg", "公斤": "kg",
    }
    return aliases.get(unit, unit)


def _slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    if not value:
        raise ValueError("ID slug cannot be empty")
    return value


def make_exact_product_id(name_zh: str, specification: str, unit: str, slug: str) -> str:
    """Apply the master-schema exact-product ID rule."""

    identity = "|".join(
        normalize_identity_text(part) for part in (name_zh, specification, unit)
    )
    suffix = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:8]
    return f"EP_{_slug(slug)}_{suffix}"


def make_lineage_id(predecessor_id: str, successor_id: str, relationship_type: str) -> str:
    payload = f"{predecessor_id}|{successor_id}|{relationship_type}"
    return "LIN_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class MatchResult:
    exact_product_id: str | None
    mapping_status: str
    matched_alias: str | None = None


class HarmonizationRegistry:
    """Read-only registry for exact matching and as-of basket membership."""

    def __init__(
        self,
        product_dictionary: pd.DataFrame,
        aliases: pd.DataFrame,
        basket_membership: pd.DataFrame | None = None,
    ) -> None:
        self.products = product_dictionary.copy()
        self.aliases = aliases.copy()
        self.basket_membership = (
            basket_membership.copy() if basket_membership is not None else pd.DataFrame()
        )
        validate_product_dictionary(self.products)
        self._alias_index: dict[tuple[str, str], set[str]] = {}
        for row in self.aliases.itertuples(index=False):
            key = (normalize_identity_text(row.alias), normalize_unit(row.unit))
            self._alias_index.setdefault(key, set()).add(row.exact_product_id)

    @classmethod
    def from_directory(cls, directory: str | Path) -> "HarmonizationRegistry":
        root = Path(directory)
        membership_path = root / "basket_membership.csv"
        membership = pd.read_csv(membership_path) if membership_path.exists() else None
        return cls(
            pd.read_csv(root / "product_dictionary.csv"),
            pd.read_csv(root / "product_aliases.csv"),
            membership,
        )

    def match_exact(self, raw_name: object, specification: object = "", unit: object = "") -> MatchResult:
        """Match only curated exact aliases; never fuzzy-match or infer a splice."""

        name = "" if raw_name is None else str(raw_name)
        spec = "" if specification is None else str(specification)
        candidates = [name]
        if normalize_identity_text(spec):
            candidates.insert(0, f"{name}({spec})")
            candidates.insert(1, f"{name}{spec}")
        ids: set[str] = set()
        matched: list[str] = []
        for alias in candidates:
            key = (normalize_identity_text(alias), normalize_unit(unit))
            exact = self._alias_index.get(key, set())
            if exact:
                ids.update(exact)
                matched.append(alias)
        if len(ids) == 1:
            return MatchResult(next(iter(ids)), "exact_curated_alias", matched[0])
        if len(ids) > 1:
            return MatchResult(None, "ambiguous_curated_alias", matched[0] if matched else None)
        return MatchResult(None, "unmatched", None)

    def map_frame(
        self,
        frame: pd.DataFrame,
        name_column: str = "raw_product_name",
        specification_column: str = "specification",
        unit_column: str = "original_unit",
    ) -> pd.DataFrame:
        """Append mapping metadata while preserving every input observation."""

        rows: list[dict[str, object]] = []
        for row in frame.to_dict("records"):
            result = self.match_exact(
                row.get(name_column, ""), row.get(specification_column, ""), row.get(unit_column, "")
            )
            mapped = dict(row)
            mapped["exact_product_id"] = result.exact_product_id
            mapped["mapping_status"] = result.mapping_status
            rows.append(mapped)
        output = pd.DataFrame(rows)
        lookup = self.products.set_index("exact_product_id")
        for column in ("harmonized_product_id", "product_family_id", "category_id", "ppi_industry_id"):
            output[column] = output["exact_product_id"].map(lookup[column])
        return output

    def active_products(self, as_of: object) -> pd.DataFrame:
        """Return the documented basket visible on an as-of date."""

        if self.basket_membership.empty:
            return self.products.iloc[0:0].copy()
        date = pd.Timestamp(as_of).normalize()
        membership = self.basket_membership.copy()
        starts = pd.to_datetime(membership["effective_start"]).dt.normalize()
        ends = pd.to_datetime(membership["effective_end"], errors="coerce").dt.normalize()
        visible = membership.loc[(starts <= date) & (ends.isna() | (ends >= date))]
        return visible.merge(self.products, on="exact_product_id", how="left", validate="many_to_one")


def validate_product_dictionary(frame: pd.DataFrame) -> None:
    required = {
        "exact_product_id", "harmonized_product_id", "product_family_id", "category_id",
        "normalized_name_zh", "normalized_specification", "original_unit", "quality_score",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"product_dictionary missing columns: {sorted(missing)}")
    if frame["exact_product_id"].isna().any() or frame["exact_product_id"].duplicated().any():
        raise ValueError("exact_product_id must be populated and unique")
    if not frame["exact_product_id"].str.match(r"^EP_[a-z0-9_]+_[0-9a-f]{8}$").all():
        raise ValueError("invalid exact_product_id format")
    scores = pd.to_numeric(frame["quality_score"], errors="coerce")
    if scores.isna().any() or not scores.between(0, 1).all():
        raise ValueError("quality_score must lie in [0, 1]")


def validate_lineage(frame: pd.DataFrame, known_exact_ids: Iterable[str]) -> None:
    known = set(known_exact_ids)
    if frame["lineage_id"].duplicated().any():
        raise ValueError("lineage_id must be unique")
    if not set(frame["relationship_type"]).issubset(COMPARABILITY_TYPES):
        raise ValueError("unknown lineage relationship_type")
    referenced = set(frame["predecessor_id"]) | set(frame["successor_id"])
    if not referenced.issubset(known):
        raise ValueError(f"lineage references unknown exact products: {sorted(referenced - known)}")
    confidence = pd.to_numeric(frame["confidence"], errors="coerce")
    if confidence.isna().any() or not confidence.between(0, 1).all():
        raise ValueError("lineage confidence must lie in [0, 1]")
    invalid_factor = frame["relationship_type"].ne("comparable_with_scaling") & frame["adjustment_factor"].notna()
    if invalid_factor.any():
        raise ValueError("adjustment_factor is allowed only for comparable_with_scaling")

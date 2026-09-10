"""Deterministic identifier construction."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable

_SPACE = re.compile(r"\s+")


def normalize_key_part(value: object) -> str:
    if value is None:
        return ""
    return _SPACE.sub(" ", unicodedata.normalize("NFKC", str(value)).strip())


def stable_hash(parts: Iterable[object], length: int | None = None) -> str:
    payload = "|".join(normalize_key_part(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return digest if length is None else digest[:length]


def stable_id(prefix: str, parts: Iterable[object], hash_length: int = 16) -> str:
    clean = re.sub(r"[^A-Z0-9_]", "_", prefix.upper()).strip("_")
    if not clean:
        raise ValueError("prefix must contain an alphanumeric character")
    return f"{clean}_{stable_hash(parts, hash_length)}"


def observation_id(source_release_id: str, source_row_number: int, raw_product_name: str,
                   specification: str | None, original_unit: str | None) -> str:
    return stable_hash([source_release_id, source_row_number, raw_product_name, specification, original_unit])


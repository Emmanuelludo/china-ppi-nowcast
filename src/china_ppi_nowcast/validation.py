"""Validation rules for parsed NBS product releases."""

from __future__ import annotations

import pandas as pd

from .schema import OBSERVATION_COLUMNS


def validate_release(frame: pd.DataFrame, minimum_products: int = 40) -> list[str]:
    missing_columns = set(OBSERVATION_COLUMNS) - set(frame.columns)
    if missing_columns:
        raise ValueError(f"observation schema missing columns: {sorted(missing_columns)}")
    if frame.empty:
        raise ValueError("release contains no product observations")
    numeric = frame[["price_cny", "change_cny", "change_pct"]].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        raise ValueError("release contains non-numeric price/change fields")
    if (numeric["price_cny"] <= 0).any():
        raise ValueError("release contains non-positive product prices")
    for column in ("category_cn", "product_name_cn", "unit_cn", "source_url", "content_sha256"):
        if frame[column].astype(str).str.strip().eq("").any():
            raise ValueError(f"release contains blank {column}")
    if frame.duplicated(["release_month", "window", "product_name_cn", "unit_cn"]).any():
        raise ValueError("release contains duplicate product/unit rows")
    prior = numeric["price_cny"] - numeric["change_cny"]
    valid_prior = prior > 0
    implied = 100 * numeric.loc[valid_prior, "change_cny"] / prior[valid_prior]
    discrepancy = (implied - numeric.loc[valid_prior, "change_pct"]).abs()
    if (discrepancy > 1.0).any():
        raise ValueError("reported price change is inconsistent with price levels beyond rounding tolerance")
    warnings: list[str] = []
    if (discrepancy > 0.25).any():
        warnings.append(
            f"{int((discrepancy > 0.25).sum())} reported changes differ from level-implied changes by 0.25-1.0 pp"
        )
    if len(frame) < minimum_products:
        warnings.append(f"product count {len(frame)} is below warning threshold {minimum_products}")
    return warnings

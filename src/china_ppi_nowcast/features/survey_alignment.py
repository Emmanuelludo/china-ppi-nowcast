"""Leakage-safe features aligned to the approximate 5th/20th PPI survey dates."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

from ..storage import stable_hash
from ..time import Window, parse_as_of, parse_target_month, target_vintage


@dataclass(frozen=True)
class FeatureVintage:
    frame: pd.DataFrame
    product_changes: pd.DataFrame
    manifest: dict[str, object]


def select_available_observations(observations: pd.DataFrame, as_of: str | datetime) -> pd.DataFrame:
    """Return the latest immutable source snapshot genuinely available at cutoff."""
    if observations.empty:
        return observations.copy()
    cutoff = pd.Timestamp(parse_as_of(as_of)).tz_convert("UTC")
    frame = observations.copy()
    frame["published_at"] = pd.to_datetime(frame["published_at"], utc=True, errors="raise")
    frame["retrieved_at"] = pd.to_datetime(frame["retrieved_at"], utc=True, errors="raise")
    frame = frame[(frame["published_at"] <= cutoff) & (frame["retrieved_at"] <= cutoff)]
    if frame.empty:
        return frame
    snapshot_keys = ["release_month", "window", "source_url", "content_sha256"]
    snapshots = frame[snapshot_keys + ["retrieved_at"]].drop_duplicates()
    latest = snapshots.sort_values("retrieved_at").drop_duplicates(
        ["release_month", "window", "source_url"], keep="last"
    )
    return frame.merge(latest[snapshot_keys], on=snapshot_keys, how="inner")


def _log_price_table(frame: pd.DataFrame) -> pd.DataFrame:
    working = frame.copy()
    working["price_cny"] = pd.to_numeric(working["price_cny"], errors="coerce")
    working = working[working["price_cny"] > 0]
    working["log_price"] = np.log(working["price_cny"])
    return working.pivot_table(
        index=["product_name_cn", "unit_cn", "category_cn"],
        columns=["release_month", "window"],
        values="log_price",
        aggfunc="last",
    )


def _column(table: pd.DataFrame, month: str, window: Window) -> pd.Series:
    key = (month, window.value)
    if key not in table.columns:
        return pd.Series(np.nan, index=table.index, dtype=float)
    return table[key].astype(float)


def _month_log_level(
    table: pd.DataFrame,
    month: pd.Period,
    carry_weight: float,
    allow_first_only: bool,
) -> tuple[pd.Series, pd.DataFrame]:
    prior = str(month - 1)
    current = str(month)
    carry = _column(table, prior, Window.THIRD)
    first_window = _column(table, current, Window.FIRST)
    second = _column(table, current, Window.SECOND)
    first_survey = carry_weight * carry + (1.0 - carry_weight) * first_window
    monthly = (first_survey + second) / 2.0
    if allow_first_only:
        monthly = monthly.where(second.notna(), first_survey)
    components = pd.DataFrame(
        {
            "carry_log_price": carry,
            "first_window_log_price": first_window,
            "first_survey_log_price": first_survey,
            "second_survey_log_price": second,
            "month_log_price": monthly,
        }
    )
    return monthly, components


def _trimmed_mean(values: pd.Series, fraction: float = 0.1) -> float:
    clean = np.sort(values.dropna().to_numpy(dtype=float))
    if len(clean) == 0:
        return math.nan
    cut = int(len(clean) * fraction)
    kept = clean[cut : len(clean) - cut] if cut and len(clean) > 2 * cut else clean
    return float(np.mean(kept))


def build_feature_vintage(
    observations: pd.DataFrame,
    target_month: str,
    as_of: str | datetime,
    carry_weight: float = 0.5,
) -> FeatureVintage:
    if not 0 <= carry_weight <= 1:
        raise ValueError("carry_weight must lie in [0, 1]")
    cutoff = parse_as_of(as_of)
    month = parse_target_month(target_month)
    available = select_available_observations(observations, cutoff)
    windows = set(zip(available.get("release_month", []), available.get("window", [])))
    vintage = target_vintage(target_month, windows)
    if vintage == "not_ready":
        raise ValueError("target month lacks prior 21-end carry and current 1-10 release")
    relevant_windows = {
        (str(month - 2), Window.THIRD.value),
        (str(month - 1), Window.FIRST.value),
        (str(month - 1), Window.SECOND.value),
        (str(month - 1), Window.THIRD.value),
        (str(month), Window.FIRST.value),
        (str(month), Window.SECOND.value),
    }
    available = available[
        pd.Series(list(zip(available["release_month"], available["window"])), index=available.index).isin(relevant_windows)
    ].copy()
    table = _log_price_table(available)
    current_level, current_components = _month_log_level(
        table, month, carry_weight, allow_first_only=vintage == "early"
    )
    prior_level, _ = _month_log_level(table, month - 1, carry_weight, allow_first_only=False)
    pct_change = 100.0 * np.expm1(current_level - prior_level)
    product = current_components.copy()
    product["prior_month_log_price"] = prior_level
    product["survey_aligned_change_pct"] = pct_change
    product["second_window_missing"] = product["second_survey_log_price"].isna().astype(int)
    product = product.reset_index()

    valid = product["survey_aligned_change_pct"].dropna()
    features: dict[str, object] = {
        "target_month": target_month,
        "as_of": cutoff.isoformat(),
        "vintage": vintage,
        "global__mean": float(valid.mean()) if len(valid) else math.nan,
        "global__median": float(valid.median()) if len(valid) else math.nan,
        "global__trimmed_mean": _trimmed_mean(valid),
        "global__std": float(valid.std(ddof=1)) if len(valid) > 1 else math.nan,
        "global__n_products": int(valid.size),
        "global__missing_fraction": float(1.0 - valid.size / max(len(product), 1)),
        "global__second_window_missing_fraction": float(product["second_window_missing"].mean()),
    }
    for category, group in product.groupby("category_cn", dropna=False):
        values = group["survey_aligned_change_pct"]
        features[f"category__{category}__mean"] = float(values.mean())
        features[f"category__{category}__missing"] = float(values.isna().mean())
    for _, row in product.iterrows():
        name = row["product_name_cn"]
        features[f"product__{name}"] = row["survey_aligned_change_pct"]
        features[f"missing__{name}"] = int(pd.isna(row["survey_aligned_change_pct"]))

    source_vintages = (
        available[["release_month", "window", "published_at", "retrieved_at", "source_url", "content_sha256"]]
        .drop_duplicates()
        .sort_values(["release_month", "window", "retrieved_at"])
        .astype(str)
        .to_dict(orient="records")
    )
    feature_hash = stable_hash({"settings": {"carry_weight": carry_weight}, "sources": source_vintages})
    features["feature_hash"] = feature_hash
    manifest = {
        "target_month": target_month,
        "as_of": cutoff.isoformat(),
        "vintage": vintage,
        "carry_weight": carry_weight,
        "first_survey_formula": "carry_weight*log(M-1:21-end)+(1-carry_weight)*log(M:1-10)",
        "second_survey_formula": "log(M:11-20)",
        "current_21_end_used": False,
        "feature_hash": feature_hash,
        "sources": source_vintages,
        "n_products": int(valid.size),
    }
    return FeatureVintage(pd.DataFrame([features]), product, manifest)

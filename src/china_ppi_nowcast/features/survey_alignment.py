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


def select_available_observations(
    observations: pd.DataFrame,
    as_of: str | datetime,
    availability_basis: str = "strict",
) -> pd.DataFrame:
    """Return the latest eligible immutable source snapshot.

    ``strict`` requires both publication and retrieval by the cutoff and is the
    only permitted mode for live forecasts. ``publication`` is explicitly for
    pseudo-real-time historical training when pages were retrieved later.
    """
    if availability_basis not in {"strict", "publication"}:
        raise ValueError("availability_basis must be 'strict' or 'publication'")
    if observations.empty:
        return observations.copy()
    cutoff = pd.Timestamp(parse_as_of(as_of)).tz_convert("UTC")
    frame = observations.copy()
    frame["published_at"] = pd.to_datetime(frame["published_at"], utc=True, errors="raise")
    frame["retrieved_at"] = pd.to_datetime(frame["retrieved_at"], utc=True, errors="raise")
    eligible = frame["published_at"] <= cutoff
    if availability_basis == "strict":
        eligible &= frame["retrieved_at"] <= cutoff
    frame = frame[eligible]
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
    availability_basis: str = "strict",
) -> FeatureVintage:
    if not 0 <= carry_weight <= 1:
        raise ValueError("carry_weight must lie in [0, 1]")
    cutoff = parse_as_of(as_of)
    month = parse_target_month(target_month)
    available = select_available_observations(observations, cutoff, availability_basis)
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
    twentieth_change = 100.0 * np.expm1(
        _column(table, str(month), Window.SECOND)
        - _column(table, str(month - 1), Window.SECOND)
    )
    product = current_components.copy()
    product["prior_month_log_price"] = prior_level
    product["survey_aligned_change_pct"] = pct_change
    product["twentieth_to_twentieth_change_pct"] = twentieth_change
    product["second_window_missing"] = product["second_survey_log_price"].isna().astype(int)
    product = product.reset_index()

    valid = product["survey_aligned_change_pct"].dropna()
    twentieth_valid = product["twentieth_to_twentieth_change_pct"].dropna()
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
        "twentieth__mean": float(twentieth_valid.mean()) if len(twentieth_valid) else math.nan,
        "twentieth__median": float(twentieth_valid.median()) if len(twentieth_valid) else math.nan,
        "twentieth__trimmed_mean": _trimmed_mean(twentieth_valid),
        "twentieth__std": float(twentieth_valid.std(ddof=1)) if len(twentieth_valid) > 1 else math.nan,
        "twentieth__n_products": int(twentieth_valid.size),
        "twentieth__missing_fraction": float(1.0 - twentieth_valid.size / max(len(product), 1)),
    }
    for category, group in product.groupby("category_cn", dropna=False):
        values = group["survey_aligned_change_pct"]
        features[f"category__{category}__mean"] = float(values.mean())
        features[f"category__{category}__missing"] = float(values.isna().mean())
        twentieth_values = group["twentieth_to_twentieth_change_pct"]
        features[f"twentieth_category__{category}__mean"] = float(twentieth_values.mean())
        features[f"twentieth_category__{category}__missing"] = float(twentieth_values.isna().mean())
    for _, row in product.iterrows():
        name = row["product_name_cn"]
        features[f"product__{name}"] = row["survey_aligned_change_pct"]
        features[f"missing__{name}"] = int(pd.isna(row["survey_aligned_change_pct"]))
        features[f"twentieth_product__{name}"] = row["twentieth_to_twentieth_change_pct"]
        features[f"twentieth_missing__{name}"] = int(pd.isna(row["twentieth_to_twentieth_change_pct"]))

    source_vintages = (
        available[["release_month", "window", "published_at", "retrieved_at", "source_url", "content_sha256"]]
        .drop_duplicates()
        .sort_values(["release_month", "window", "retrieved_at"])
        .astype(str)
        .to_dict(orient="records")
    )
    feature_hash = stable_hash({"schema": "survey-plus-twentieth-v2", "target_month": target_month, "vintage": vintage, "settings": {"carry_weight": carry_weight}, "sources": source_vintages})
    features["feature_hash"] = feature_hash
    manifest = {
        "target_month": target_month,
        "as_of": cutoff.isoformat(),
        "vintage": vintage,
        "carry_weight": carry_weight,
        "first_survey_formula": "carry_weight*log(M-1:21-end)+(1-carry_weight)*log(M:1-10)",
        "second_survey_formula": "log(M:11-20)",
        "twentieth_to_twentieth_formula": "100*(exp(log(M:11-20)-log(M-1:11-20))-1)",
        "current_21_end_used": False,
        "feature_hash": feature_hash,
        "sources": source_vintages,
        "n_products": int(valid.size),
        "n_twentieth_to_twentieth_products": int(twentieth_valid.size),
        "availability_basis": availability_basis,
        "realtime_status": "prospective" if availability_basis == "strict" else "pseudo_real_time",
        "historical_snapshot_caveat": (
            None if availability_basis == "strict"
            else "Publication-time cutoff applied to pages retrieved later; revision-vintage correctness is not claimed."
        ),
    }
    return FeatureVintage(pd.DataFrame([features]), product, manifest)

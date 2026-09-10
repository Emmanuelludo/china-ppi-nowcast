"""Construct weight variants without inventing official PPI weights."""

from __future__ import annotations

import numpy as np
import pandas as pd


SCHEMA_VERSION = "0.1.0"
METHODOLOGY_VERSION = "weights_v0.1.0"


def _normalise_nonnegative(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce").clip(lower=0)
    total = numeric.sum(min_count=1)
    if pd.isna(total) or total <= 0:
        raise ValueError("weights must contain at least one positive observed value")
    return numeric / total


def build_equal_weight_panel(
    product_dictionary: pd.DataFrame,
    basket_membership: pd.DataFrame,
    basket_snapshots: pd.DataFrame,
) -> pd.DataFrame:
    """Create equal-product and equal-category weights for each observed basket.

    Exact specifications are first mapped to harmonized products.  If two exact
    specifications map to one harmonized product in a snapshot, it receives one
    product vote, preventing accidental double weighting after a specification
    transition.
    """

    required_dictionary = {"exact_product_id", "harmonized_product_id", "category_id", "quality_score"}
    required_membership = {"basket_snapshot_id", "exact_product_id", "membership_status"}
    required_snapshots = {"basket_snapshot_id", "effective_start", "available_at", "source_url"}
    for required, frame, name in ((required_dictionary, product_dictionary, "product_dictionary"), (required_membership, basket_membership, "basket_membership"), (required_snapshots, basket_snapshots, "basket_snapshots")):
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{name} missing {sorted(missing)}")
    active = basket_membership.loc[basket_membership["membership_status"].eq("active")].merge(
        product_dictionary[list(required_dictionary)], on="exact_product_id", how="left", validate="many_to_one"
    )
    if active[["harmonized_product_id", "category_id"]].isna().any().any():
        raise ValueError("active exact products must be mapped before weighting")
    # One harmonized product per basket. Quality is conservatively the weakest link.
    active = active.groupby(["basket_snapshot_id", "harmonized_product_id", "category_id"], as_index=False).agg(data_quality_weight=("quality_score", "min"))
    active = active.merge(basket_snapshots[list(required_snapshots)], on="basket_snapshot_id", how="left", validate="many_to_one")
    results: list[pd.DataFrame] = []
    for _, group in active.groupby("basket_snapshot_id", sort=True):
        work = group.copy()
        work["effective_date"] = pd.to_datetime(work["effective_start"]).dt.date
        work["available_at"] = pd.to_datetime(work["available_at"], utc=True)
        work["economic_weight"] = np.nan
        work["ppi_weight"] = np.nan
        work["predictive_weight"] = np.nan

        product = work.copy()
        product["weight_variant"] = "equal_product"
        product["composite_weight"] = 1.0 / len(product)
        product["weight_basis"] = "one vote per active harmonized product"

        category = work.copy()
        counts = category.groupby("category_id")["harmonized_product_id"].transform("count")
        category_count = category["category_id"].nunique()
        category["weight_variant"] = "equal_category"
        category["composite_weight"] = 1.0 / category_count / counts
        category["weight_basis"] = "equal category share, then equal active harmonized products within category"
        results.extend([product, category])
    output = pd.concat(results, ignore_index=True)
    output["schema_version"] = SCHEMA_VERSION
    output["methodology_version"] = METHODOLOGY_VERSION
    output["is_official_weight"] = False
    output["strict_backtest_eligible"] = True
    columns = ["schema_version", "effective_date", "available_at", "harmonized_product_id", "category_id", "weight_variant", "economic_weight", "ppi_weight", "predictive_weight", "data_quality_weight", "composite_weight", "source_url", "methodology_version", "basket_snapshot_id", "weight_basis", "is_official_weight", "strict_backtest_eligible"]
    return output[columns].sort_values(["effective_date", "weight_variant", "harmonized_product_id"]).reset_index(drop=True)


def latest_available_weights(panel: pd.DataFrame, cutoff: str | pd.Timestamp, effective_date: str | pd.Timestamp) -> pd.DataFrame:
    """Select the latest released weight per product without future information."""

    cutoff_ts = pd.Timestamp(cutoff)
    if cutoff_ts.tzinfo is None:
        cutoff_ts = cutoff_ts.tz_localize("UTC")
    else:
        cutoff_ts = cutoff_ts.tz_convert("UTC")
    target_date = pd.Timestamp(effective_date).date()
    work = panel.copy()
    available = pd.to_datetime(work["available_at"], utc=True)
    effective = pd.to_datetime(work["effective_date"]).dt.date
    work = work.loc[(available <= cutoff_ts) & (effective <= target_date)].copy()
    if work.empty:
        return work
    work["_effective"] = pd.to_datetime(work["effective_date"])
    return work.sort_values("_effective").groupby(["harmonized_product_id", "weight_variant"], as_index=False).tail(1).drop(columns="_effective")


def combine_hybrid_weights(
    panel: pd.DataFrame,
    economic_column: str = "economic_weight",
    predictive_column: str = "predictive_weight",
    quality_column: str = "data_quality_weight",
) -> pd.DataFrame:
    """Multiply explicit inputs and normalise; missing inputs are never imputed.

    Predictive weights may be signed.  Their absolute magnitude determines basket
    importance; the original sign is retained in ``predictive_sign`` for attribution.
    """

    required = {"harmonized_product_id", economic_column, predictive_column, quality_column}
    missing = required.difference(panel.columns)
    if missing:
        raise ValueError(f"hybrid inputs missing {sorted(missing)}")
    output = panel.copy()
    if output[[economic_column, predictive_column, quality_column]].isna().any().any():
        raise ValueError("hybrid weights require observed economic, predictive, and quality inputs; no silent fill")
    output["predictive_sign"] = np.sign(output[predictive_column])
    raw = output[economic_column].clip(lower=0) * output[predictive_column].abs() * output[quality_column].clip(lower=0, upper=1)
    output["composite_weight"] = _normalise_nonnegative(raw)
    output["weight_variant"] = "hybrid"
    output["is_official_weight"] = False
    return output

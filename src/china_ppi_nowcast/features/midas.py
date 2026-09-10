"""Direct intra-month (MIDAS-ready) feature matrix."""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_midas_matrix(
    observations: pd.DataFrame,
    *,
    cutoff: str | pd.Timestamp,
    transformation_version: str = "midas_price_changes_v1",
) -> pd.DataFrame:
    """Pivot public ten-day changes into slot-specific product columns.

    Missing product/slot observations stay missing; the panel is intentionally
    unbalanced and can be imputed inside a rolling model pipeline.
    """

    required = {
        "harmonized_product_id", "reference_period_start", "reference_period_end",
        "available_at",
    }
    missing = required.difference(observations.columns)
    if missing:
        raise ValueError(f"observations missing required columns: {sorted(missing)}")
    price_column = "standardized_price" if "standardized_price" in observations else "raw_price"
    if price_column not in observations:
        raise ValueError("observations require standardized_price or raw_price")
    boundary = pd.Timestamp(cutoff)
    boundary = boundary.tz_localize("UTC") if boundary.tzinfo is None else boundary.tz_convert("UTC")
    frame = observations.copy()
    frame["available_at"] = pd.to_datetime(frame["available_at"], utc=True)
    frame = frame.loc[frame["available_at"].le(boundary)].copy()
    frame["reference_period_end"] = pd.to_datetime(frame["reference_period_end"])
    frame["month"] = frame["reference_period_end"].dt.to_period("M").dt.to_timestamp()
    frame["day"] = frame["reference_period_end"].dt.day
    frame["slot"] = np.select(
        [frame["day"].le(10), frame["day"].le(20)], ["d10", "d20"], default="d30"
    )
    frame["price"] = pd.to_numeric(frame[price_column], errors="coerce")
    frame = frame.sort_values(["harmonized_product_id", "reference_period_end", "available_at"])
    frame = frame.drop_duplicates(["harmonized_product_id", "reference_period_end"], keep="last")
    frame["slot_change"] = frame.groupby("harmonized_product_id")["price"].pct_change(fill_method=None).mul(100)
    wide = frame.pivot_table(
        index="month", columns=["harmonized_product_id", "slot"], values="slot_change", aggfunc="last"
    )
    wide.columns = [f"midas__{product}__{slot}" for product, slot in wide.columns]
    wide = wide.reset_index()
    public = frame.groupby("month")["available_at"].max().rename("available_at")
    wide = wide.merge(public, on="month", how="left")
    wide["forecast_cutoff"] = boundary
    wide["aggregation_method"] = "direct_midas"
    wide["transformation_version"] = transformation_version
    return wide.sort_values("month").reset_index(drop=True)

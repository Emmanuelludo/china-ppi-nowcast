"""Model matrices with explicit method/version selection."""

from __future__ import annotations

import pandas as pd


def category_feature_matrix(
    category_features: pd.DataFrame,
    *,
    aggregation_method: str,
    transformation_version: str,
    value_columns: tuple[str, ...] = ("weighted_mean_change", "diffusion"),
) -> pd.DataFrame:
    """Create one row per month/vintage and reject implicit method mixing."""

    required = {
        "month", "forecast_vintage", "category_id", "available_at",
        "aggregation_method", "transformation_version", *value_columns,
    }
    missing = required.difference(category_features.columns)
    if missing:
        raise ValueError(f"category_features missing columns: {sorted(missing)}")
    frame = category_features.loc[
        category_features["aggregation_method"].eq(aggregation_method)
        & category_features["transformation_version"].eq(transformation_version)
    ].copy()
    if frame.empty:
        raise ValueError("no rows match aggregation_method/transformation_version")
    indices = ["month", "forecast_vintage"]
    parts: list[pd.DataFrame] = []
    for value in value_columns:
        part = frame.pivot_table(index=indices, columns="category_id", values=value, aggfunc="last")
        part.columns = [f"{value}__{category}" for category in part.columns]
        parts.append(part)
    result = pd.concat(parts, axis=1).reset_index()
    availability = frame.groupby(indices)["available_at"].max().reset_index()
    result = result.merge(availability, on=indices, how="left")
    result["aggregation_method"] = aggregation_method
    result["transformation_version"] = transformation_version
    for column in ("forecast_cutoff", "processed_at", "schema_version", "source_snapshot_hash"):
        if column in frame:
            meta = frame.groupby(indices)[column].last().reset_index()
            result = result.merge(meta, on=indices, how="left")
    return result.sort_values(indices).reset_index(drop=True)

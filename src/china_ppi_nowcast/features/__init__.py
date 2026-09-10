"""Vintage-safe transformations for NBS circulation-price observations."""

from .engineering import (
    FeatureConfig,
    aggregate_monthly_prices,
    build_category_features,
    build_feature_panel,
    build_product_features,
    classify_regime,
)

__all__ = [
    "FeatureConfig",
    "aggregate_monthly_prices",
    "build_category_features",
    "build_feature_panel",
    "build_product_features",
    "classify_regime",
]

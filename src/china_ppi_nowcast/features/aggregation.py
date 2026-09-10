"""Monthly temporal aggregation contracts."""

from .engineering import FeatureConfig, aggregate_monthly_prices

AGGREGATION_METHODS = ("monthly_average", "end_to_end", "day_weighted_average")

__all__ = ["AGGREGATION_METHODS", "FeatureConfig", "aggregate_monthly_prices"]

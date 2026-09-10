"""Declared model ladder; tuning occurs only inside rolling validation."""

from __future__ import annotations

from .base import ModelSpec


def default_model_registry(
    category_features: list[str] | tuple[str, ...] = (),
    midas_features: list[str] | tuple[str, ...] = (),
) -> list[ModelSpec]:
    features = tuple(category_features)
    registry = [
        ModelSpec("naive_zero_mom", "naive", parameters={"rule": "zero_mom"}),
        ModelSpec("naive_last_mom", "naive", parameters={"rule": "last_value"}),
        ModelSpec("ar_1", "ar", ("ppi_lag_1",)),
        ModelSpec("category_bridge", "bridge", features),
        ModelSpec("ridge", "ridge", features, {"alpha": 1.0}),
        ModelSpec("elastic_net", "elastic_net", features, {"alpha": 0.1, "l1_ratio": 0.5}),
        ModelSpec("price_factor_1", "factor", features, {"n_factors": 1, "alpha": 1.0}),
        ModelSpec("state_space", "state_space", features),
        ModelSpec("tvp", "tvp", features, {"forgetting_factor": 0.98}),
    ]
    if midas_features:
        registry.insert(
            7,
            ModelSpec("direct_midas_ridge", "midas", tuple(midas_features), {"alpha": 1.0}),
        )
    return registry

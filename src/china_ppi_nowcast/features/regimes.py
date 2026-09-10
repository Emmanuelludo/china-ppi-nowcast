"""Rule-based regime labels that complement continuous price features."""

from .engineering import classify_regime

REGIMES = (
    "persistent_structural_uplift",
    "elevated_level_reacceleration",
    "cyclical_rebound",
    "shock_normalization",
    "persistent_weakness",
    "policy_induced_repricing",
    "mixed_uncertain",
)

__all__ = ["REGIMES", "classify_regime"]

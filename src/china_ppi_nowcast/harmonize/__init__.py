"""Conservative product harmonization for NBS circulation-price observations.

The public API deliberately separates exact-product matching from lineage.  A matched
observation may receive an exact and harmonized product ID, but no cross-specification
price splice is performed unless a reviewed lineage decision explicitly permits it.
"""

from .build import build_harmonization_artifacts
from .ontology import HarmonizationRegistry, make_exact_product_id, normalize_identity_text
from .units import convert_price

__all__ = [
    "HarmonizationRegistry",
    "build_harmonization_artifacts",
    "convert_price",
    "make_exact_product_id",
    "normalize_identity_text",
]

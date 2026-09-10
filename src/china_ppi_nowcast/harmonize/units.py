"""Audited unit conversions for exact products."""

from __future__ import annotations

import pandas as pd


def convert_price(
    value: float,
    exact_product_id: str,
    from_unit: str,
    to_unit: str,
    conversions: pd.DataFrame,
    as_of: object | None = None,
) -> tuple[float | None, str]:
    """Convert a price only when one unambiguous reviewed rule applies.

    The factor transforms a quoted price, e.g. CNY/kg to CNY/tonne uses 1,000.
    No conversion is guessed from the unit strings.
    """

    rules = conversions.loc[
        conversions["from_unit"].eq(from_unit)
        & conversions["to_unit"].eq(to_unit)
        & (conversions["exact_product_id"].eq(exact_product_id) | conversions["exact_product_id"].isna())
    ].copy()
    if as_of is not None and not rules.empty:
        date = pd.Timestamp(as_of).normalize()
        starts = pd.to_datetime(rules["valid_from"], errors="coerce").dt.normalize()
        ends = pd.to_datetime(rules["valid_to"], errors="coerce").dt.normalize()
        rules = rules.loc[(starts.isna() | (starts <= date)) & (ends.isna() | (ends >= date))]
    exact = rules.loc[rules["exact_product_id"].eq(exact_product_id)]
    if not exact.empty:
        rules = exact
    if len(rules) != 1:
        return None, "missing_or_ambiguous_conversion"
    factor = pd.to_numeric(rules.iloc[0]["factor"], errors="coerce")
    if pd.isna(factor):
        return None, "non_multiplicative_conversion_requires_review"
    return float(value) * float(factor), "converted_reviewed_rule"

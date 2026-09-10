"""Auditable catalog of external variables used in benchmark models.

The six collected public series are current-vintage observations distributed by
FRED.  The commodity series are sourced by the IMF and mirrored by FRED.  A
current-vintage download is useful for exploratory/current models but is not a
valid substitute for an archived vintage in a strict pseudo-real-time backtest.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExternalSeries:
    series_id: str
    source_series_id: str
    name: str
    raw_frequency: str
    unit: str
    source_agency: str
    source_url: str
    aggregation: str
    availability_lag_days: int
    strict_backtest_eligible: bool = False


FRED_GRAPH = "https://fred.stlouisfed.org/graph/fredgraph.csv"

PUBLIC_SERIES: tuple[ExternalSeries, ...] = (
    ExternalSeries("brent_usd_bbl", "DCOILBRENTEU", "Brent crude oil", "daily", "USD/barrel", "U.S. EIA via FRED", "https://fred.stlouisfed.org/series/DCOILBRENTEU", "monthly_mean", 1),
    ExternalSeries("wti_usd_bbl", "DCOILWTICO", "WTI crude oil", "daily", "USD/barrel", "U.S. EIA via FRED", "https://fred.stlouisfed.org/series/DCOILWTICO", "monthly_mean", 1),
    ExternalSeries("cny_per_usd", "DEXCHUS", "China/U.S. exchange rate", "daily", "CNY/USD", "Federal Reserve Board via FRED", "https://fred.stlouisfed.org/series/DEXCHUS", "monthly_mean", 1),
    ExternalSeries("copper_usd_mt", "PCOPPUSDM", "Copper price", "monthly", "USD/metric tonne", "IMF Primary Commodity Prices via FRED", "https://fred.stlouisfed.org/series/PCOPPUSDM", "as_reported", 45),
    ExternalSeries("iron_ore_usd_dmt", "PIORECRUSDM", "Iron ore price", "monthly", "USD/dry metric tonne", "IMF Primary Commodity Prices via FRED", "https://fred.stlouisfed.org/series/PIORECRUSDM", "as_reported", 45),
    ExternalSeries("australian_coal_usd_mt", "PCOALAUUSDM", "Australian thermal coal price", "monthly", "USD/metric tonne", "IMF Primary Commodity Prices via FRED", "https://fred.stlouisfed.org/series/PCOALAUUSDM", "as_reported", 45),
)


UNCOLLECTED_SERIES: tuple[dict[str, str], ...] = (
    {"series_id": "nbs_pmi_input_prices", "status": "uncollected", "reason": "No vintage-preserving public machine-readable history established."},
    {"series_id": "nbs_pmi_output_prices", "status": "uncollected", "reason": "No vintage-preserving public machine-readable history established."},
    {"series_id": "private_manufacturing_pmi_prices", "status": "uncollected", "reason": "Proprietary/licensed history; must not be imputed."},
    {"series_id": "global_manufacturing_pmi_prices", "status": "uncollected", "reason": "Proprietary/licensed history; must not be imputed."},
)

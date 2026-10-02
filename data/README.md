# Data directory

For readable results, start at **[Latest forecasts](../reports/README.md)**.
For product names and units, use the **[English glossary](../docs/PRODUCTS.md)**.

| Path | Contents |
|---|---|
| `raw/nbs/objects/` | Immutable source pages and URL/retrieval metadata, keyed by content hash |
| `raw/nbs/search/` | Historical release-discovery snapshots |
| `processed/nbs_ten_day_observations.csv.gz` | Parsed price observations with source names and units |
| `processed/training/` | Versioned benchmark training matrices |
| `processed/vintages/` | Frozen benchmark feature inputs |
| `registry/forecasts.csv` | Benchmark forecasts and imported historical records |
| `registry/actuals.csv` | Official headline PPI MoM outcomes |
| `registry/parser_corrections/` | Audited target-parser corrections |
| `product/vintages/` | Product forecasts, exact features and SHAP, grouped by month and vintage ID |
| `product/evaluations/` | Forecast/outcome matches appended after official release |

Hashed filenames preserve identity and reproducibility. Human-readable English
reports are generated from these records; the raw Chinese evidence is not renamed.

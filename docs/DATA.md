# Data and provenance

[Project home](../README.md) · [Product glossary](PRODUCTS.md)

## Sources and coverage

Source: [NBS data releases](https://www.stats.gov.cn/sj/zxfb/index.html).
The price history starts in January 2014. The live dataset grows with new releases;
[the historical audit](../reports/history_search.json) documents the backfill and gaps.
Absence of a historical window is not automatically assumed to be a holiday cancellation.

Absolute product prices are the modeling input. Published ten-day percentage
changes are retained for validation. Chinese source names, specifications, units,
URLs and timestamps are preserved. English labels are a presentation layer.

## Three kinds of records

| Record | Interpretation |
|---|---|
| Live forecast vintage | Saved before official PPI publication, using only data released and retrieved by its cutoff |
| Historical validation prediction | Expanding-window result with publication cutoffs; explicitly pseudo-real-time |
| Imported historical forecast | Frozen archival value, with its original provenance and timestamp precision retained |

The [August 2026 table](../reports/august_2026_frozen.md) is an imported historical
record, separate from the active models' prospective validation. Its date-level
cutoffs must not be interpreted as verified intraday timestamps.

## Storage and revisions

Raw pages and metadata are immutable and content-addressed. Corrections create
new snapshots and audit entries. Forecasts retain their feature inputs, model
version, source references and code revision; later actuals do not change forecasts.

[Data directory guide](../data/README.md) · [Model directory guide](../models/README.md)

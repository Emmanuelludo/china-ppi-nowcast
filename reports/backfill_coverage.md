# NBS backfill coverage

The reproducible crawl scanned all 67 pages of the current NBS data-release
index on 2026-09-14. That index enumerated 233 relevant source pages from
September 2021 through September 2026:

- 173 ten-day price releases, containing 8,650 product observations;
- 60 official headline PPI result pages, through August 2026;
- 61 calendar months represented in the high-frequency data;
- zero unresolved fetch or parse failures after the validated retry.

Against a mechanical three-windows-per-month grid through August 2026, the
following entries are absent from the official index:

| Month | Window | Treatment |
|---|---|---|
| 2021-09 | 1-10, 11-20 | Archive boundary; training begins only when required carry and comparison windows exist |
| 2022-02 | 1-10 | No release listed; do not synthesize |
| 2023-01 | 21-end | No release listed; do not synthesize |
| 2024-02 | 11-20 | No release listed; final vintage unavailable for affected target |
| 2025-01 | 21-end | No release listed; do not synthesize |
| 2025-10 | 1-10 | No release listed; early/final target vintage unavailable |
| 2026-02 | 11-20 | No release listed; final vintage unavailable |

These absences coincide with major holiday periods, but the pipeline records
only the observable fact that no corresponding NBS release is listed. It does
not impute a fictitious source window. The early training matrix therefore has
55 rows and the final matrix 53 rows.

The current NBS index does not enumerate older history exhaustively. Older
official pages may exist, but this deployment does not claim complete coverage
before September 2021.

# China PPI Nowcast

Vintage-safe, survey-aligned nowcasting of the National Bureau of Statistics of
China (NBS) headline producer price index month-on-month change.

> [!IMPORTANT]
> This repository is a **reconstructed implementation**. The earlier
> `china_ppi_nowcast_v0_4_20260909.zip` could not be recovered. The frozen August
> 2026 forecasts are preserved exactly as historical records, but the executable
> estimators here are new candidates and are not claimed to reproduce the lost
> fitted objects.

## Current operational status

| Component | Status |
|---|---|
| Frozen August 2026 forecast registry | Preserved |
| NBS release discovery and immutable snapshots | Implemented |
| Survey-date-aligned feature construction | Implemented and tested |
| Six reconstructed model families | Implemented; training data/artifacts required |
| Append-only forecast and actual registries | Implemented and tested |
| Scheduled GitHub Actions workflow | Enabled daily at 02:35 UTC; push/manual reruns supported |
| Recovered original fitted model artifacts | Unavailable |
| Production forecast generation | Blocked until models are trained and validated |

Nothing in this repository installs software or creates a scheduler on a user's
device. Automation, when enabled, runs only in GitHub Actions and is visible in
the repository's Actions tab.

## Timing model

For target month `M`, the primary specification treats the NBS ten-day data as a
continuous price process:

- the first survey-date level combines `M-1`'s `21-end` carry-in and `M`'s
  `1-10` observation;
- the second survey-date level uses `M`'s `11-20` observation;
- `M`'s `21-end` observation is carry-in for `M+1`, not part of the final
  pre-release vintage for `M`;
- all source rows must have both `published_at <= as_of` and
  `retrieved_at <= as_of`.

The exact first-date interpolation weight is a configurable modeling choice,
not a recovered fact. The default is equal weighting on the log-price scale and
is recorded in every feature manifest.

## Install and test

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
ppi-nowcast status
```

## Commands

```bash
ppi-nowcast ingest --index-pages 4
ppi-nowcast build-features --target-month 2026-09 --as-of 2026-09-24T23:59:59+08:00
ppi-nowcast train --training-file data/processed/training_matrix.csv
ppi-nowcast forecast --target-month 2026-09 --as-of 2026-09-24T23:59:59+08:00
ppi-nowcast run
```

See `RECOVERY.md` for the evidence boundary, `docs/MODEL_CONTRACT.md` for the
training contract, and `OPERATIONS.md` for automation and failure behavior.

## Data provenance

The source index is the NBS [data-release listing](https://www.stats.gov.cn/sj/zxfb/index.html).
Raw HTML is stored by SHA-256 content hash with retrieval metadata. A changed
page becomes a new immutable snapshot rather than silently replacing the old
one.

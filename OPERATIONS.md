# Operations

## Safety state

The workflow runs daily at 02:35 UTC, on relevant repository pushes, and by
manual request. It runs only in GitHub Actions; nothing runs on a user's device.

## Intended scheduled operation

The daily job tests the code, snapshots recent NBS releases, parses prices and
official PPI results, attempts inference only with a validated model bundle,
and commits new registries/reports back to `main`.

## Idempotency and failure behavior

- Raw pages are keyed globally by SHA-256 content hash, so unchanged pages are
  not copied again on later runs.
- Parsed rows retain source hash and retrieval timestamp.
- Forecast logical keys cannot be overwritten.
- Repeated runs with an unchanged feature hash do not append duplicate forecasts.
- Source/schema failures preserve the raw snapshot and fail visibly.
- Missing windows produce `not_ready`, not silently imputed releases.
- Missing models produce `blocked_missing_validated_models` and no forecast.

## Manual run and kill switch

Use **Actions → China PPI prospective nowcast → Run workflow**. Leave the
backfill input blank for a normal run; supplying `backfill_start_month` performs
a resumable full-index crawl and retrains both vintage bundles only after a
zero-failure source pass. To stop all
automation, disable that workflow from the Actions tab or remove its `schedule`
entry if one is added later.

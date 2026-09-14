# Operations

## Safety state

The workflow runs on relevant repository pushes and can be started manually. It
has no `schedule` trigger until a clean GitHub Actions run is reviewed. Nothing
runs on a user's device.

## Intended scheduled operation

After verification, a daily 02:35 UTC schedule may be enabled explicitly. The
job tests the code, snapshots recent NBS releases, parses prices and official
PPI results, attempts inference only with a validated model bundle, and commits
new registries/reports back to `main`.

## Idempotency and failure behavior

- Raw pages are keyed globally by SHA-256 content hash, so unchanged pages are
  not copied again on later runs.
- Parsed rows retain source hash and retrieval timestamp.
- Forecast logical keys cannot be overwritten.
- Source/schema failures preserve the raw snapshot and fail visibly.
- Missing windows produce `not_ready`, not silently imputed releases.
- Missing models produce `blocked_missing_validated_models` and no forecast.

## Manual run and kill switch

Use **Actions → China PPI prospective nowcast → Run workflow**. To stop all
automation, disable that workflow from the Actions tab or remove its `schedule`
entry if one is added later.

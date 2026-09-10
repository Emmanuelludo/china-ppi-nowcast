# Operation and deployment status

Run `python scripts/v2_update.py` to reproduce results from the cached official evidence.
Run `python scripts/v2_update.py --refresh` to fetch new circulation and sector releases,
preserve source snapshots, fit models, and archive this run's forecasts and hashes.

The included GitHub workflow runs daily at 02:17 UTC once installed on a repository's
default branch with Actions enabled. It uploads results as run artifacts; it does not
silently push model-generated code or replace prior forecasts. Scheduling is daily polling,
not an instantaneous event subscription. GitHub may delay scheduled jobs.

**Deployment is not active in this delivery.** The connected GitHub interface provides
existing-repository operations but no repository creation capability. No GitHub repository
or live schedule has been created or verified. The workflow is executable configuration,
not evidence that a hosted service exists.

For permanent retention beyond GitHub artifact expiry, download the archived runs or add
an explicitly authorized durable data store. Raw input snapshots and SHA-256 hashes remain
in the project. The model's own dated-source provenance caveat still applies.

[GitHub schedule documentation](https://docs.github.com/actions/using-workflows/events-that-trigger-workflows)

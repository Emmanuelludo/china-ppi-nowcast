# Adaptive champion–challenger monitoring

The system monitors 28 calibrated product-model specifications independently: model family × timing × product panel. It retains all useful model families. The direct circulation-price tracker is not scored as a PPI forecast. Legacy survey benchmarks remain archived comparisons outside this automatic product-model lifecycle.

## Monitoring and diagnosis

Four newly released prospective monthly outcomes form the default deviation window. Historical backtests cannot satisfy this requirement. Within each timing specification, monitoring selects the last frozen pre-release forecast per month and matches it to the first observed official PPI result.

A trial is triggered when recent MAE exceeds both 1.5 times the incumbent's historical reference MAE and that reference plus 0.15 percentage points, or absolute mean bias exceeds 0.25 pp. After 12 new outcomes without a trial, a periodic refresh also starts. Missing outcomes never become zero errors. A completed trial requires four fresh outcomes before another error-triggered cycle.

Each registration freezes its rules and evidence: forecast IDs, residual sequence, source hashes, training age, product coverage, extrapolation beyond training ranges, sparse histories and available signed SHAP or linear attributions. These support a diagnosis of model failure; they cannot establish a causal economic explanation from four residuals. Source schema/unit/duplicate/coverage failures stop the pipeline rather than triggering a statistical repair.

## Refitting

A challenger fits using source snapshots published and retrieved by its creation cutoff and official targets known at that time. Current/future target-month outcomes are excluded. Historical feature reconstruction is explicitly pseudo-real-time because historical pages and revisions were retrieved later.

Three common chronological validation blocks compare all history, the most recent 60 eligible months and the most recent 120 eligible months. Each block fits preprocessing, feature eligibility and the estimator using only targets released before that block's forecast cutoff. Window length and regularization are selected jointly. Ridge also selects minimum observed product history and retains its observed-value scaling. Boosters retain their native missing-value handling and existing conservative architecture.

The latest 24 eligible expanding outer origins independently rerun this selection and record pseudo-real-time validation forecasts. These are not the prospective promotion sample. Artifacts retain feature order, selected parameters/window, package versions, code hash, commit, raw source hashes, training range and actual-release cutoff. At most two challengers are fitted per daily run; additional requests remain in the journal queue.

## Prospective comparison

Both the frozen incumbent and frozen challenger predict the next target month on the same raw snapshots, cutoff and feature vector. Each model applies its own saved feature contract. Tree SHAP or ridge linear decompositions are saved for both sides when supported and reconciled to their predictions. Retired/new product identities stay distinguishable. Matching never combines different timing variants or product panels. Refitting either contestant during a trial is prohibited by artifact-hash checks.

Six future matched monthly outcomes are required by default. Missing releases can extend the calendar duration. Daily reruns reuse an existing input/model pair. Corrections create separately frozen input vintages. The final pre-release pair per month is scored against the first observed official result; its evaluation is then immutable.

Promotion requires all of:

- At least 5% relative and 0.02 pp absolute MAE improvement.
- Challenger RMSE no more than 5% worse.
- Absolute bias no more than 0.05 pp worse.
- Strictly smaller absolute errors in at least half the paired months.

A paired circular block bootstrap is reported descriptively. Six observations do not demonstrate statistical or permanent superiority. Failure to meet any rule retains the incumbent, while preserving the challenger and its forecasts. Neither outcome removes an entire model family.

## Promotion and repetition

A successful challenger replaces only its own family/timing/panel artifact in a new composite active bundle. Other fitted artifacts retain their exact hashes. If that specification has already issued a forecast for the current month, promotion becomes effective next month; earlier forecasts are never replaced in place. The daily product inference step then uses the new active pointer.

The journal records requests, fitted challengers, decisions and promotions with chained hashes and sequence numbers. Replaying it rebuilds state. Models, source matrices, paired features, forecasts and outcome evaluations remain available for audit. Later source/official revisions do not silently alter prior trial decisions. The process repeats without a fixed end date. Explicit retraining or a new expanded-history bundle is recorded as an adoption, resets the fresh-outcome window, and cancels incompatible unfinished trials. A completed promotion interrupted before journaling is recovered from the active artifact identity. Requests and completed artifacts are checkpointed even when fitting fails; private unfinished transaction directories are excluded from Git.

## Controls and outputs

- [Configuration](../config/adaptive.json): monitoring/comparison lengths and thresholds.
- [Monitoring dashboard](../reports/adaptive.md): status and diagnostic evidence.
- `data/adaptive/events/`: authoritative append-only lifecycle journal.
- `data/adaptive/forecasts/`: matched forecasts and their shared frozen inputs.
- `data/adaptive/evaluations/`: frozen paired errors against official releases.
- `models/adaptive/`: challenger objects, metadata, training matrices and validation.
- `config/product_pipeline.json`: active composite champion bundle after promotion.

Defaults are operational choices, not estimates of an optimal adaptation policy. Continually searching and selecting models can overfit even prospective sequences; retain individual errors, rejected challengers and uncertainty rather than claiming a permanent winner.

# Recovery and evidence ledger

## Recovered evidence

- `HANDOFF.md`, six model-family names, twelve frozen August 2026 forecasts,
  the published `+0.40%` August result, and the survey-aligned timing rules.

## Not recovered

- `china_ppi_nowcast_v0_4_20260909.zip`.
- Original code, data, feature matrices, preprocessing, fitted estimators,
  hyperparameters, auxiliary inputs, or exact gradient-boosting library.
- Exact intraday timestamps for the August forecasts.

Cross-session retrieval was disabled and the internal conversation URI was
blocked by the execution browser. The repository held only a placeholder README
and the handoff.

## Reconstruction policy

1. Frozen forecasts are immutable historical imports and are never regenerated.
2. New estimators use version `reconstructed-v1` and provenance `reconstructed`.
3. The new boosting candidate is `HistGradientBoostingRegressor`; this is not a
   claim about the lost estimator.
4. No auxiliary economic series is invented. A hybrid may use only reviewed
   columns prefixed `econ__`.
5. Production inference is blocked unless a bundle manifest says
   `validated: true`.
6. Snapshots retrieved after a historical cutoff cannot be called ex-ante data.
   They may be used for explicitly pseudo-real-time training with publication
   cutoffs and a `revision_vintage_correct: false` manifest.

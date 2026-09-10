# Shared agent contract

All workstreams must conform to `config/master_schema.yaml` and `db/schema.sql`.
Agents may propose schema extensions but must not redefine existing fields or IDs.

## Data hand-off

Each table must include:

- `schema_version`
- provenance (`source_url`, and release/vintage identifier where applicable)
- reference dates and `available_at`
- deterministic IDs using the master rules
- explicit missingness/status rather than silent row deletion
- original values alongside parsed/standardized values

No agent may infer continuity from fuzzy name similarity alone. Proposed product links go
to `product_lineage` with evidence, method, and confidence. They do not mutate raw data.

## Required return structure

1. Findings
2. Data produced (exact paths and table names)
3. Data-quality issues
4. Methodological decisions
5. Confidence (high / medium / low, with reason)
6. Open questions

## Conflict protocol

- Preserve both conflicting source observations.
- Record the disagreement in `source_conflicts` or a workstream issue log.
- Do not choose a value based on convenience or recency alone.
- The lead agent adjudicates identity, classification, splice, and source-precedence
  conflicts in a dated decision record.

## Real-time integrity

Backtests filter every input on `available_at <= forecast_cutoff`. A revised observation
may be used only in a vintage that could have seen that revision. Annual/quarterly weights
must use the latest weight release available at the cutoff, not the ultimately revised
historical value.


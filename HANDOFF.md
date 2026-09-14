# China PPI Nowcast — Project Handoff

**Handoff date:** 2026-09-14  
**Repository:** <https://github.com/Emmanuelludo/china-ppi-nowcast>  
**Repository status at handoff:** public repository exists, but the full project upload, executable pipeline, scheduled workflow, and deployment have **not** been verified. The repository contained only its initialization commit and placeholder README when this handoff was created.

## How to use this document

This file is the authoritative conversational handoff for a new ChatGPT project. The new project should use the GitHub repository and this document as its working state instead of importing or reconstructing the long China Watch chat history.

The prior working archive was named `china_ppi_nowcast_v0_4_20260909.zip`. It was attached in an earlier conversation but is not currently present in the repository. It must be reattached or otherwise recovered before claiming that the model code, fitted artifacts, data, or pipeline have been deployed.

## User and working style

The user is a biostatistician/clinical data scientist and is comfortable with technical model discussion, missing-data mechanisms, validation design, leakage, robustness testing, model comparison, and production monitoring. Do not oversimplify the statistical reasoning.

The goal is not a one-off forecast. The user wants a durable, continuously updated China PPI nowcasting system that:

- collects newly released source data directly;
- preserves release vintages and prevents look-ahead leakage;
- loads saved models and produces a new nowcast as data arrive;
- retains multiple competing models rather than collapsing immediately to one model;
- records every forecast vintage before the official PPI release;
- evaluates forecast accuracy and robustness after at least six months of genuinely prospective operation;
- remains reproducible from the repository rather than depending on chat history.

## Forecast target

The principal target is the official National Bureau of Statistics of China (NBS) **headline producer price index month-on-month change** for month `M`.

Year-on-year PPI and component/sector outputs may be useful secondary targets, but they must not replace or become confused with the headline MoM nowcast.

## Authoritative timing methodology

This section supersedes the earlier practice of mechanically averaging all three NBS ten-day observations within the same calendar month.

The industrial-producer price survey underlying PPI is conducted around the **5th and 20th of each month**. The NBS “Market Prices of Important Means of Production in Circulation” series (流通领域重要生产资料市场价格) should therefore be treated as a continuous high-frequency price process aligned to those survey dates, not as three observations that reset at calendar month-end.

For target month `M`:

1. Approximate the price level around the first PPI survey date (about the 5th) using the prior month’s `21–end` observation as carry-in information together with month `M`’s `1–10` observation.
2. Approximate the price level around the second survey date (about the 20th) using month `M`’s `11–20` observation.
3. Construct the monthly signal from the two survey-aligned price levels, with product/category mappings and estimated historical relationships to official PPI.
4. Treat month `M`’s `21–end` observation primarily as carry into month `M+1`; it is released after the approximately 20th survey observation and must not be silently inserted into a supposedly earlier forecast vintage.

The legacy calendar-month comparison—average of all three observations in month `M` versus average of all three in `M-1`—may be retained as a benchmark or sensitivity feature. It is **not** the primary survey-aligned specification.

## Vintage and leakage rules

Every model output must be tied to an explicit `as_of` timestamp and the releases actually available at that time.

- Never use the subsequently published official PPI value when recreating an ex-ante forecast.
- Never use a ten-day price release that was not public at the stated forecast cutoff.
- Preserve raw source files or immutable snapshots, retrieval timestamps, transformed datasets, feature matrices, fitted model version, code commit, and resulting forecast.
- Label backtests as pseudo-real-time unless vintage-correct source data were genuinely used.
- Keep final pre-release forecasts separate from early-month forecasts.
- The published August 2026 PPI result may be used for evaluation only after the ex-ante predictions have been frozen.

## Core high-frequency source

The central input is the NBS ten-day release covering roughly 50 important means-of-production products. The pipeline should ingest product price levels and reported changes while preserving Chinese product names, units, release windows, source URLs, publication times, and revisions/corrections.

Do not use the count of products rising/falling as the main quantitative signal, and do not simply average the reported percentage changes. Work from comparable product price levels, appropriate transformations, mappings, and time alignment.

Additional economic and market inputs used by individual models must be documented in the recovered archive/code. Do not invent an auxiliary-data specification if it cannot be verified from the archive.

## Models to retain

The previous work compared six model families:

1. Category-factor regression
2. Gradient boosting
3. Economic + ML hybrid
4. Product-level ridge
5. Sector-first aggregation
6. Random forest

Retain these as competing forecast models during the prospective evaluation period. Do not select a permanent winner from one month.

The exact gradient-boosting implementation (for example CatBoost, XGBoost, LightGBM, histogram gradient boosting, or another estimator), its hyperparameters, saved fitted object, preprocessing, and feature contract must be verified from `china_ppi_nowcast_v0_4_20260909.zip`. The conversation history raised this question but the surviving handoff evidence does not establish the answer; do not guess.

Missing/changing product coverage must be handled explicitly. At minimum, compare:

- native missing-value handling where supported;
- imputation performed within each training fold/vintage;
- missingness indicators;
- stable common-product panels versus dynamic panels;
- product-entry/product-exit sensitivity;
- performance with delayed or failed source releases.

## Frozen August 2026 forecast vintages

The following forecasts were saved in the previous work. Preserve them as historical records; do not overwrite them with refitted values.

| Model | Early vintage (2026-08-14) | Final pre-PPI estimate | Error vs. published +0.40% MoM |
|---|---:|---:|---:|
| Category-factor regression | +0.187% | +0.279% | −0.121 pp |
| Gradient boosting | +0.397% | +0.453% | +0.053 pp |
| Economic + ML hybrid | +0.311% | +0.370% | −0.030 pp |
| Product-level ridge | +0.412% | +0.410% | +0.010 pp |
| Sector-first aggregation | +0.188% | +0.227% | −0.173 pp |
| Random forest | +0.438% | +0.509% | +0.109 pp |

The final survey-aligned estimates were described as using August `1–10` and `11–20` information, available by approximately August 24, together with prior-month carry-in information. The official August headline PPI was subsequently reported as **+0.40% MoM** and is shown above only for forecast evaluation.

Do not substitute the earlier qualitative/manual ex-ante call or a calendar-month three-window average for these frozen model outputs without a clearly labeled comparison.

## Evaluation plan

Run the system prospectively for at least six official monthly releases before making strong model-ranking claims. Store both early and final vintages.

Evaluate at least:

- error, absolute error, squared error, bias, and directional accuracy;
- performance by forecast vintage and information set;
- stability of model ranking;
- sensitivity to product-panel changes and missing inputs;
- revision sensitivity and source-release delays;
- residual behavior and large-error case review;
- calibration/dispersion of any ensemble or prediction interval;
- simple baselines, including no-change, prior-month persistence, historical mean, and the legacy calendar-month aggregation.

With only six observations, emphasize the individual error sequence and uncertainty rather than treating small differences in RMSE as decisive. Continue accumulating prospective observations.

## Required production pipeline

A complete deployment should eventually include:

1. **Ingestion:** fetch new NBS ten-day releases and official PPI releases; store immutable raw snapshots and metadata.
2. **Validation:** check schema, units, product-name mappings, duplicates, missing products, implausible jumps, and publication windows.
3. **Feature construction:** create survey-aligned features plus separately labeled benchmark features.
4. **Inference:** load versioned fitted models and preprocessing objects; produce all model forecasts from one frozen feature vintage.
5. **Forecast registry:** append forecasts rather than overwrite them, including `target_month`, `as_of`, model/version, data cutoff, commit SHA, estimate, and status.
6. **Reporting:** generate a readable nowcast summary showing information available, changes from the previous vintage, model dispersion, missing inputs, and warnings.
7. **Official-result update:** after release, append the actual value and evaluation metrics without retroactively altering forecasts.
8. **Automation:** scheduled workflow with logs, failure alerts, idempotency, retries, and manual rerun support.
9. **Tests:** unit tests for date alignment and transformations; integration tests using stored fixtures; leakage tests for each vintage.

## Recommended repository structure

Use the recovered archive’s structure if it is coherent. Otherwise migrate carefully toward:

```text
.
├── HANDOFF.md
├── README.md
├── pyproject.toml
├── config/
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── models/
├── reports/
├── src/china_ppi_nowcast/
│   ├── ingest/
│   ├── validation/
│   ├── features/
│   ├── modeling/
│   ├── forecast/
│   └── evaluation/
├── tests/
└── .github/workflows/
```

Large or frequently changing data/model artifacts should use an appropriate versioned storage strategy rather than silently exceeding ordinary Git limits. Never commit secrets.

## Current deployment status

As verified on 2026-09-14:

- GitHub repository: **exists**
- Repository visibility: **public**
- Default branch: `main`
- Latest observed commit: `fa69b5f0cd70c7b496035dfeea1f4a61fc397841` — “Initialize China PPI nowcast repository”
- Full source archive uploaded: **not verified / apparently no**
- Saved model artifacts uploaded: **not verified**
- Data pipeline runnable: **not verified**
- Automated scheduled workflow: **not present or not verified**
- Hosted application/API/dashboard: **not deployed**
- Prospective monitoring active: **no evidence**

Creating a GitHub repository is not equivalent to deploying a runnable nowcast. Do not tell the user that the project is deployed until a clean run and the intended schedule/runtime have been verified.

## Immediate next actions for the new project

1. Ask the user to attach `china_ppi_nowcast_v0_4_20260909.zip` to the new project/chat.
2. Inspect the archive without modifying it; inventory code, data, fitted artifacts, reports, configuration, and secrets/placeholders.
3. Reconcile the archive against this handoff, especially the survey-aligned timing rules and frozen August forecasts.
4. Run tests and reproduce the saved August predictions from the appropriate vintage inputs.
5. Identify the exact boosting estimator and all preprocessing/missing-data behavior.
6. Upload the validated project to the existing repository using small, reviewable commits.
7. Add and test the scheduled workflow.
8. Perform one dry run and one clean-from-checkout run.
9. Document how to trigger a manual nowcast and where outputs are stored.
10. Only then mark deployment as complete.

## Bootstrap prompt for a new ChatGPT project

Copy the following into the first chat of the new project:

> Continue the China PPI Nowcast using <https://github.com/Emmanuelludo/china-ppi-nowcast> as the authoritative repository. Read `HANDOFF.md` completely before acting. Do not import or reconstruct the old China Watch conversations. The existing repository is not yet a verified deployment. Ask me to attach `china_ppi_nowcast_v0_4_20260909.zip`, inspect it, reconcile it with the survey-aligned methodology and frozen August forecast vintages in `HANDOFF.md`, then complete and verify the repository upload, automated pipeline, and deployment. Preserve ex-ante vintages and do not use future information.

## Non-negotiable cautions

- Do not claim the repository is deployed merely because it exists.
- Do not change the frozen August predictions.
- Do not leak the published August result into a reconstructed pre-release forecast.
- Do not revert to same-calendar-month three-window averaging as the primary methodology.
- Do not guess the gradient-boosting library or recovered archive contents.
- Do not overwrite forecast history; append new vintages.
- Do not rely on conversational memory when repository evidence is available.

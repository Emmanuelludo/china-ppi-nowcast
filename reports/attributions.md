# What drives the forecasts?

Target month: **2026-09**.

[Back to latest forecasts](README.md) · [Product definitions](../docs/PRODUCTS.md)

SHAP values are model attributions in percentage points, not causal economic contributions. Baseline plus all product attributions equals the model forecast. Correlated products can share attribution differently across models.

## CatBoost — 20th-to-20th

Baseline: **+0.0253 pp** · Forecast: **+0.729% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Methanol (premium grade) | Monthly price change | +0.3858 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.1943 |
| Sulfuric acid (98%) | Monthly price change | -0.0727 |
| Polypropylene (raffia grade) | Monthly price change | +0.0599 |
| Diesel (0#China VI) | Monthly price change | +0.0458 |
| Polybutadiene rubber (BR9000) | Monthly price change | +0.0383 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0331 |
| Shanxi premium blended coal (5500 kcal/kg) | Monthly price change | +0.0316 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | +0.4269 |
| Petroleum and natural gas | +0.2543 |
| Agricultural inputs | -0.0357 |
| Non-metallic mineral products | +0.0192 |
| Non-ferrous metals | +0.0140 |
| Agricultural products | +0.0114 |
| Ferrous metals | +0.0109 |
| Coal and coke | +0.0025 |
| Building materials | +0.0000 |
| Forest products | -0.0000 |

[Full attribution record](../data/product/vintages/2026-09/ccff0fc38493f430f79a/shap.json)

## HistGradientBoosting — 20th-to-20th

Baseline: **+0.0301 pp** · Forecast: **+0.691% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Liquefied petroleum gas (LPG) | Monthly price change | +0.2133 |
| Methanol (premium grade) | Monthly price change | +0.1787 |
| Shanxi blended coal (5000 kcal/kg) | Monthly price change | +0.0875 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0761 |
| Polybutadiene rubber (BR9000) | Monthly price change | +0.0730 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0505 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | -0.0471 |
| Sulfuric acid (98%) | Monthly price change | -0.0451 |

| Sector | Attribution (pp) |
|---|---:|
| Petroleum and natural gas | +0.2731 |
| Chemicals | +0.2665 |
| Coal and coke | +0.1908 |
| Agricultural inputs | -0.0714 |
| Non-metallic mineral products | +0.0251 |
| Agricultural products | -0.0178 |
| Ferrous metals | -0.0125 |
| Non-ferrous metals | +0.0037 |
| Forest products | +0.0021 |
| Building materials | +0.0012 |

[Full attribution record](../data/product/vintages/2026-09/1b741548cb43517a9491/shap.json)

## LightGBM — 20th-to-20th

Baseline: **+0.0306 pp** · Forecast: **+0.644% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Liquefied petroleum gas (LPG) | Monthly price change | +0.1843 |
| Methanol (premium grade) | Monthly price change | +0.0942 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0846 |
| Sulfuric acid (98%) | Monthly price change | -0.0686 |
| Standard blended coal (4500 kcal/kg) | Monthly price change | +0.0564 |
| Polybutadiene rubber (BR9000) | Monthly price change | +0.0557 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0381 |
| Medium steel plate (20mm,Q235) | Monthly price change | +0.0378 |

| Sector | Attribution (pp) |
|---|---:|
| Petroleum and natural gas | +0.2640 |
| Coal and coke | +0.1789 |
| Chemicals | +0.1345 |
| Ferrous metals | +0.0418 |
| Non-metallic mineral products | +0.0286 |
| Agricultural products | -0.0251 |
| Non-ferrous metals | -0.0131 |
| Building materials | +0.0044 |
| Agricultural inputs | -0.0033 |
| Forest products | +0.0032 |

[Full attribution record](../data/product/vintages/2026-09/5dce6d6fc6047b7a904e/shap.json)

## Random forest — 20th-to-20th

Baseline: **+0.0382 pp** · Forecast: **+0.614% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Liquefied petroleum gas (LPG) | Monthly price change | +0.1862 |
| Methanol (premium grade) | Monthly price change | +0.1816 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0552 |
| Seamless steel pipe (219*6,20#) | Monthly price change | -0.0355 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0341 |
| Liquefied natural gas (LNG) | Monthly price change | +0.0230 |
| Polypropylene (raffia grade) | Monthly price change | +0.0225 |
| Shanxi blended coal (5000 kcal/kg) | Monthly price change | +0.0220 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | +0.2716 |
| Petroleum and natural gas | +0.2282 |
| Coal and coke | +0.0721 |
| Ferrous metals | -0.0251 |
| Non-ferrous metals | +0.0163 |
| Building materials | +0.0130 |
| Agricultural products | -0.0058 |
| Non-metallic mineral products | +0.0039 |
| Forest products | +0.0025 |
| Agricultural inputs | -0.0006 |

[Full attribution record](../data/product/vintages/2026-09/77d06b0288dc1f11f916/shap.json)

## XGBoost — 20th-to-20th

Baseline: **+0.0241 pp** · Forecast: **+0.682% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Liquefied petroleum gas (LPG) | Monthly price change | +0.2468 |
| Methanol (premium grade) | Monthly price change | +0.1371 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0810 |
| Sulfuric acid (98%) | Monthly price change | -0.0762 |
| Shanxi blended coal (5000 kcal/kg) | Monthly price change | +0.0687 |
| Polybutadiene rubber (BR9000) | Monthly price change | +0.0572 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0463 |
| Standard blended coal (4500 kcal/kg) | Monthly price change | +0.0363 |

| Sector | Attribution (pp) |
|---|---:|
| Petroleum and natural gas | +0.3148 |
| Coal and coke | +0.2048 |
| Chemicals | +0.1475 |
| Agricultural inputs | -0.0614 |
| Ferrous metals | +0.0469 |
| Non-metallic mineral products | +0.0338 |
| Agricultural products | -0.0294 |
| Non-ferrous metals | -0.0056 |
| Building materials | +0.0040 |
| Forest products | +0.0025 |

[Full attribution record](../data/product/vintages/2026-09/ddaf91689c83ede47305/shap.json)

## CatBoost — Two-survey period

Baseline: **+0.0143 pp** · Forecast: **+0.639% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Methanol (premium grade) | Monthly price change | +0.2884 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.1148 |
| Seamless steel pipe (219*6,20#) | Monthly price change | +0.1005 |
| Gasoline (95#China VI) | Monthly price change | +0.0641 |
| Diesel (0#China VI) | Monthly price change | +0.0454 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0346 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | -0.0326 |
| Hot-rolled steel sheet (3mm,Q235) | Monthly price change | -0.0314 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | +0.3266 |
| Petroleum and natural gas | +0.2357 |
| Ferrous metals | +0.0653 |
| Agricultural inputs | -0.0411 |
| Agricultural products | +0.0229 |
| Non-ferrous metals | +0.0181 |
| Forest products | -0.0083 |
| Coal and coke | +0.0039 |
| Non-metallic mineral products | +0.0008 |
| Building materials | +0.0006 |

[Full attribution record](../data/product/vintages/2026-09/fc36f17d4a26819c2d5b/shap.json)

## HistGradientBoosting — Two-survey period

Baseline: **+0.0153 pp** · Forecast: **+0.744% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Methanol (premium grade) | Monthly price change | +0.1960 |
| Seamless steel pipe (219*6,20#) | Monthly price change | +0.1344 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.1295 |
| Gasoline (95#China VI) | Monthly price change | +0.0731 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | -0.0723 |
| PVC (SG5) | Monthly price change | +0.0722 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0495 |
| Diesel (0#China VI) | Monthly price change | +0.0490 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | +0.3122 |
| Petroleum and natural gas | +0.2632 |
| Ferrous metals | +0.1359 |
| Coal and coke | +0.1007 |
| Agricultural inputs | -0.0963 |
| Building materials | +0.0140 |
| Agricultural products | -0.0128 |
| Forest products | +0.0049 |
| Non-metallic mineral products | +0.0047 |
| Non-ferrous metals | +0.0022 |

[Full attribution record](../data/product/vintages/2026-09/091560634debff233b1e/shap.json)

## LightGBM — Two-survey period

Baseline: **+0.0159 pp** · Forecast: **+0.671% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Liquefied petroleum gas (LPG) | Monthly price change | +0.1395 |
| Methanol (premium grade) | Monthly price change | +0.1317 |
| Seamless steel pipe (219*6,20#) | Monthly price change | +0.1127 |
| Diesel (0#China VI) | Monthly price change | +0.0960 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0548 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | -0.0501 |
| Sulfuric acid (98%) | Monthly price change | -0.0464 |
| Steel angle (5#) | Monthly price change | +0.0419 |

| Sector | Attribution (pp) |
|---|---:|
| Petroleum and natural gas | +0.2592 |
| Chemicals | +0.1810 |
| Ferrous metals | +0.1450 |
| Coal and coke | +0.1228 |
| Agricultural inputs | -0.0854 |
| Building materials | +0.0155 |
| Non-ferrous metals | +0.0129 |
| Non-metallic mineral products | +0.0108 |
| Agricultural products | -0.0036 |
| Forest products | -0.0033 |

[Full attribution record](../data/product/vintages/2026-09/91b46789622f7017559e/shap.json)

## XGBoost — Two-survey period

Baseline: **+0.0155 pp** · Forecast: **+0.696% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Liquefied petroleum gas (LPG) | Monthly price change | +0.1607 |
| Methanol (premium grade) | Monthly price change | +0.1537 |
| Seamless steel pipe (219*6,20#) | Monthly price change | +0.1250 |
| Diesel (0#China VI) | Monthly price change | +0.0790 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | -0.0572 |
| Shanxi blended coal (5000 kcal/kg) | Monthly price change | +0.0561 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0528 |
| Standard blended coal (4500 kcal/kg) | Monthly price change | +0.0392 |

| Sector | Attribution (pp) |
|---|---:|
| Petroleum and natural gas | +0.2651 |
| Chemicals | +0.1724 |
| Coal and coke | +0.1598 |
| Ferrous metals | +0.1276 |
| Agricultural inputs | -0.0818 |
| Non-ferrous metals | +0.0253 |
| Non-metallic mineral products | +0.0196 |
| Agricultural products | -0.0123 |
| Building materials | +0.0062 |
| Forest products | -0.0012 |

[Full attribution record](../data/product/vintages/2026-09/1fb25aa65e5abfff84c2/shap.json)

## CatBoost — Early month

Baseline: **+0.0294 pp** · Forecast: **+0.471% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Methanol (premium grade) | Monthly price change | +0.1774 |
| Diesel (0#China VI) | Monthly price change | +0.0783 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0649 |
| Gasoline (95#China VI) | Monthly price change | +0.0561 |
| Seamless steel pipe (219*6,20#) | Monthly price change | +0.0519 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | -0.0491 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.0370 |
| Medium steel plate (20mm,Q235) | Monthly price change | +0.0329 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | +0.2270 |
| Petroleum and natural gas | +0.1756 |
| Agricultural inputs | -0.0662 |
| Ferrous metals | +0.0562 |
| Agricultural products | +0.0203 |
| Non-ferrous metals | +0.0188 |
| Building materials | +0.0081 |
| Non-metallic mineral products | +0.0029 |
| Coal and coke | -0.0017 |
| Forest products | +0.0003 |

[Full attribution record](../data/product/vintages/2026-09/808e4be1a40c2bdf0738/shap.json)

## HistGradientBoosting — Early month

Baseline: **+0.0303 pp** · Forecast: **+0.596% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Methanol (premium grade) | Monthly price change | +0.1719 |
| PVC (SG5) | Monthly price change | +0.1269 |
| Gasoline (95#China VI) | Monthly price change | +0.0703 |
| Diesel (0#China VI) | Monthly price change | +0.0573 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | -0.0558 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0428 |
| Steel angle (5#) | Monthly price change | +0.0418 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.0352 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | +0.3451 |
| Petroleum and natural gas | +0.1862 |
| Agricultural inputs | -0.0906 |
| Coal and coke | +0.0418 |
| Ferrous metals | +0.0314 |
| Non-metallic mineral products | +0.0173 |
| Agricultural products | +0.0158 |
| Building materials | +0.0109 |
| Non-ferrous metals | +0.0085 |
| Forest products | -0.0007 |

[Full attribution record](../data/product/vintages/2026-09/41230c826b092b164bec/shap.json)

## LightGBM — Early month

Baseline: **+0.0292 pp** · Forecast: **+0.561% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Methanol (premium grade) | Monthly price change | +0.1573 |
| PVC (SG5) | Monthly price change | +0.0786 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0723 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | -0.0694 |
| Diesel (0#China VI) | Monthly price change | +0.0536 |
| Seamless steel pipe (219*6,20#) | Monthly price change | +0.0512 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.0506 |
| Compound fertilizer (potassium-sulfate-based,NPK content 45%) | Monthly price change | -0.0354 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | +0.2964 |
| Petroleum and natural gas | +0.1537 |
| Agricultural inputs | -0.1103 |
| Coal and coke | +0.0686 |
| Ferrous metals | +0.0649 |
| Agricultural products | +0.0226 |
| Non-metallic mineral products | +0.0191 |
| Non-ferrous metals | +0.0156 |
| Building materials | +0.0049 |
| Forest products | -0.0035 |

[Full attribution record](../data/product/vintages/2026-09/5b61b89b411c3cc18e06/shap.json)

## XGBoost — Early month

Baseline: **+0.0245 pp** · Forecast: **+0.618% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Methanol (premium grade) | Monthly price change | +0.1488 |
| PVC (SG5) | Monthly price change | +0.0838 |
| Gasoline (95#China VI) | Monthly price change | +0.0741 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | -0.0617 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0551 |
| Diesel (0#China VI) | Monthly price change | +0.0490 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.0405 |
| Seamless steel pipe (219*6,20#) | Monthly price change | +0.0391 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | +0.3024 |
| Petroleum and natural gas | +0.1874 |
| Agricultural inputs | -0.0864 |
| Coal and coke | +0.0705 |
| Ferrous metals | +0.0525 |
| Non-metallic mineral products | +0.0288 |
| Agricultural products | +0.0270 |
| Building materials | +0.0126 |
| Forest products | -0.0095 |
| Non-ferrous metals | +0.0080 |

[Full attribution record](../data/product/vintages/2026-09/14cc9b9142b8ada464b9/shap.json)

## CatBoost — Early + carry-in

Baseline: **+0.0265 pp** · Forecast: **+0.605% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Methanol (premium grade) | Monthly price change | +0.1942 |
| Gasoline (95#China VI) | Monthly price change | +0.1509 |
| Seamless steel pipe (219*6,20#) | Monthly price change | +0.0601 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0584 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.0470 |
| Diesel (0#China VI) | Monthly price change | +0.0370 |
| Liquefied petroleum gas (LPG) | Carry-in change | +0.0295 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | -0.0239 |

| Sector | Attribution (pp) |
|---|---:|
| Petroleum and natural gas | +0.2819 |
| Chemicals | +0.2509 |
| Agricultural inputs | -0.0610 |
| Ferrous metals | +0.0512 |
| Agricultural products | +0.0192 |
| Non-ferrous metals | +0.0159 |
| Non-metallic mineral products | +0.0094 |
| Coal and coke | +0.0089 |
| Building materials | +0.0031 |
| Forest products | -0.0008 |

[Full attribution record](../data/product/vintages/2026-09/e6e82443032bf0742038/shap.json)

## HistGradientBoosting — Early + carry-in

Baseline: **+0.0280 pp** · Forecast: **+0.677% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Methanol (premium grade) | Monthly price change | +0.1673 |
| Gasoline (95#China VI) | Monthly price change | +0.1651 |
| Steel angle (5#) | Monthly price change | +0.0652 |
| Seamless steel pipe (219*6,20#) | Monthly price change | +0.0590 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0545 |
| Standard blended coal (4500 kcal/kg) | Carry-in change | +0.0529 |
| Diesel (0#China VI) | Monthly price change | +0.0518 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Carry-in change | -0.0365 |

| Sector | Attribution (pp) |
|---|---:|
| Petroleum and natural gas | +0.2623 |
| Chemicals | +0.2268 |
| Coal and coke | +0.0910 |
| Agricultural inputs | -0.0893 |
| Ferrous metals | +0.0886 |
| Agricultural products | +0.0360 |
| Non-metallic mineral products | +0.0128 |
| Forest products | +0.0128 |
| Building materials | +0.0098 |
| Non-ferrous metals | -0.0021 |

[Full attribution record](../data/product/vintages/2026-09/347b30f8b049b0155d47/shap.json)

## LightGBM — Early + carry-in

Baseline: **+0.0276 pp** · Forecast: **+0.669% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Methanol (premium grade) | Monthly price change | +0.1673 |
| Gasoline (95#China VI) | Monthly price change | +0.1092 |
| Diesel (0#China VI) | Monthly price change | +0.0833 |
| Seamless steel pipe (219*6,20#) | Monthly price change | +0.0618 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0609 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Carry-in change | -0.0426 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0405 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | -0.0326 |

| Sector | Attribution (pp) |
|---|---:|
| Petroleum and natural gas | +0.2748 |
| Chemicals | +0.2566 |
| Agricultural inputs | -0.1088 |
| Coal and coke | +0.1069 |
| Ferrous metals | +0.0428 |
| Agricultural products | +0.0376 |
| Non-metallic mineral products | +0.0181 |
| Non-ferrous metals | +0.0087 |
| Building materials | +0.0037 |
| Forest products | +0.0011 |

[Full attribution record](../data/product/vintages/2026-09/7c6b93d11a3b359c24bc/shap.json)

## XGBoost — Early + carry-in

Baseline: **+0.0232 pp** · Forecast: **+0.675% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Methanol (premium grade) | Monthly price change | +0.1545 |
| Gasoline (95#China VI) | Monthly price change | +0.1263 |
| Diesel (0#China VI) | Monthly price change | +0.0705 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0625 |
| Seamless steel pipe (219*6,20#) | Monthly price change | +0.0582 |
| PVC (SG5) | Monthly price change | +0.0405 |
| Steel angle (5#) | Monthly price change | +0.0403 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0330 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | +0.2577 |
| Petroleum and natural gas | +0.2481 |
| Coal and coke | +0.0968 |
| Agricultural inputs | -0.0897 |
| Ferrous metals | +0.0851 |
| Agricultural products | +0.0304 |
| Non-ferrous metals | +0.0182 |
| Non-metallic mineral products | +0.0130 |
| Forest products | -0.0116 |
| Building materials | +0.0040 |

[Full attribution record](../data/product/vintages/2026-09/33b0d55448cd077204dc/shap.json)

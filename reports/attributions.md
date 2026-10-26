# What drives the forecasts?

Target month: **2026-10**.

[Back to latest forecasts](README.md) · [Product definitions](../docs/PRODUCTS.md)

SHAP values are model attributions in percentage points, not causal economic contributions. Baseline plus all product attributions equals the model forecast. Correlated products can share attribution differently across models.

## CatBoost — 20th-to-20th

Baseline: **+0.0253 pp** · Forecast: **+0.096% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.0894 |
| Polypropylene (raffia grade) | Monthly price change | +0.0599 |
| Sulfuric acid (98%) | Monthly price change | -0.0538 |
| Methanol (premium grade) | Monthly price change | -0.0425 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0339 |
| Diesel (0#China VI) | Monthly price change | +0.0259 |
| Urea (small prills [source spelling]) | Monthly price change | -0.0230 |
| Shanxi premium blended coal (5500 kcal/kg) | Monthly price change | +0.0181 |

| Sector | Attribution (pp) |
|---|---:|
| Agricultural inputs | +0.0666 |
| Petroleum and natural gas | +0.0516 |
| Ferrous metals | -0.0374 |
| Coal and coke | -0.0226 |
| Chemicals | -0.0221 |
| Non-metallic mineral products | +0.0178 |
| Agricultural products | +0.0069 |
| Non-ferrous metals | +0.0061 |
| Forest products | +0.0037 |
| Building materials | -0.0003 |

[Full attribution record](../data/product/vintages/2026-10/d56516ae59a3b7d80906/shap.json)

## HistGradientBoosting — 20th-to-20th

Baseline: **+0.0301 pp** · Forecast: **+0.112% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Shanxi blended coal (5000 kcal/kg) | Monthly price change | +0.0811 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.0738 |
| Sulfuric acid (98%) | Monthly price change | -0.0722 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0671 |
| Medium steel plate (20mm,Q235) | Monthly price change | -0.0579 |
| Methanol (premium grade) | Monthly price change | -0.0574 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0459 |
| Seamless steel pipe (219*6,20#) | Monthly price change | -0.0405 |

| Sector | Attribution (pp) |
|---|---:|
| Coal and coke | +0.1599 |
| Ferrous metals | -0.0945 |
| Chemicals | -0.0836 |
| Agricultural inputs | +0.0493 |
| Non-metallic mineral products | +0.0375 |
| Petroleum and natural gas | +0.0345 |
| Non-ferrous metals | -0.0259 |
| Forest products | +0.0025 |
| Building materials | +0.0012 |
| Agricultural products | +0.0005 |

[Full attribution record](../data/product/vintages/2026-10/589a4481983bf01518c3/shap.json)

## LightGBM — 20th-to-20th

Baseline: **+0.0306 pp** · Forecast: **+0.232% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.1194 |
| Sulfuric acid (98%) | Monthly price change | -0.0722 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0661 |
| Standard blended coal (4500 kcal/kg) | Monthly price change | +0.0534 |
| Methanol (premium grade) | Monthly price change | -0.0500 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0468 |
| Medium steel plate (20mm,Q235) | Monthly price change | -0.0351 |
| Seamless steel pipe (219*6,20#) | Monthly price change | -0.0322 |

| Sector | Attribution (pp) |
|---|---:|
| Coal and coke | +0.1521 |
| Petroleum and natural gas | +0.0944 |
| Ferrous metals | -0.0839 |
| Agricultural inputs | +0.0830 |
| Chemicals | -0.0695 |
| Non-metallic mineral products | +0.0318 |
| Non-ferrous metals | -0.0214 |
| Agricultural products | +0.0124 |
| Building materials | +0.0032 |
| Forest products | -0.0004 |

[Full attribution record](../data/product/vintages/2026-10/1e037ef6ff4bd8bd98ea/shap.json)

## Random forest — 20th-to-20th

Baseline: **+0.0382 pp** · Forecast: **+0.137% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Seamless steel pipe (219*6,20#) | Monthly price change | -0.0593 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0485 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.0449 |
| Methanol (premium grade) | Monthly price change | -0.0409 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.0305 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0275 |
| Coking coal (primary coking coal) | Monthly price change | -0.0244 |
| Polypropylene (raffia grade) | Monthly price change | +0.0227 |

| Sector | Attribution (pp) |
|---|---:|
| Ferrous metals | -0.0793 |
| Petroleum and natural gas | +0.0569 |
| Chemicals | +0.0440 |
| Agricultural inputs | +0.0399 |
| Coal and coke | +0.0219 |
| Building materials | +0.0133 |
| Non-ferrous metals | -0.0090 |
| Non-metallic mineral products | +0.0070 |
| Agricultural products | +0.0027 |
| Forest products | +0.0011 |

[Full attribution record](../data/product/vintages/2026-10/933b4a712fb415544e84/shap.json)

## XGBoost — 20th-to-20th

Baseline: **+0.0241 pp** · Forecast: **+0.279% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.0872 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0700 |
| Shanxi blended coal (5000 kcal/kg) | Monthly price change | +0.0687 |
| Sulfuric acid (98%) | Monthly price change | -0.0681 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0469 |
| Methanol (premium grade) | Monthly price change | -0.0438 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.0418 |
| Diesel (0#China VI) | Monthly price change | +0.0388 |

| Sector | Attribution (pp) |
|---|---:|
| Coal and coke | +0.1778 |
| Petroleum and natural gas | +0.1125 |
| Chemicals | -0.0625 |
| Ferrous metals | -0.0585 |
| Agricultural inputs | +0.0431 |
| Non-metallic mineral products | +0.0387 |
| Agricultural products | +0.0191 |
| Non-ferrous metals | -0.0174 |
| Building materials | +0.0040 |
| Forest products | -0.0022 |

[Full attribution record](../data/product/vintages/2026-10/69fc3a728bdbf3ff142c/shap.json)

## CatBoost — Two-survey period

Baseline: **+0.0143 pp** · Forecast: **+0.206% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.1596 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.0903 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0401 |
| Hot-rolled steel sheet (3mm,Q235) | Monthly price change | -0.0336 |
| Steel angle (5#) | Monthly price change | -0.0315 |
| Diesel (0#China VI) | Monthly price change | +0.0278 |
| Metallurgical coke (grade 2) | Monthly price change | -0.0259 |
| Methanol (premium grade) | Monthly price change | +0.0238 |

| Sector | Attribution (pp) |
|---|---:|
| Agricultural inputs | +0.1513 |
| Petroleum and natural gas | +0.1221 |
| Ferrous metals | -0.0936 |
| Coal and coke | -0.0331 |
| Chemicals | +0.0175 |
| Agricultural products | +0.0126 |
| Non-metallic mineral products | +0.0099 |
| Non-ferrous metals | +0.0069 |
| Forest products | -0.0023 |
| Building materials | +0.0006 |

[Full attribution record](../data/product/vintages/2026-10/a4475f1b2acc0975baf7/shap.json)

## HistGradientBoosting — Two-survey period

Baseline: **+0.0153 pp** · Forecast: **+0.595% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.2668 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.1699 |
| PVC (SG5) | Monthly price change | +0.0742 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0588 |
| Diesel (0#China VI) | Monthly price change | +0.0554 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0505 |
| Seamless steel pipe (219*6,20#) | Monthly price change | -0.0400 |
| Shanxi blended coal (5000 kcal/kg) | Monthly price change | +0.0398 |

| Sector | Attribution (pp) |
|---|---:|
| Agricultural inputs | +0.2361 |
| Petroleum and natural gas | +0.2296 |
| Chemicals | +0.1102 |
| Ferrous metals | -0.0949 |
| Coal and coke | +0.0869 |
| Building materials | +0.0142 |
| Non-ferrous metals | -0.0134 |
| Non-metallic mineral products | +0.0095 |
| Forest products | +0.0068 |
| Agricultural products | -0.0050 |

[Full attribution record](../data/product/vintages/2026-10/303b796fb28944c96a58/shap.json)

## LightGBM — Two-survey period

Baseline: **+0.0159 pp** · Forecast: **+0.472% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.1869 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.1486 |
| Diesel (0#China VI) | Monthly price change | +0.1055 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0535 |
| Sulfuric acid (98%) | Monthly price change | -0.0465 |
| Shanxi blended coal (5000 kcal/kg) | Monthly price change | +0.0390 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0355 |
| PVC (SG5) | Monthly price change | +0.0333 |

| Sector | Attribution (pp) |
|---|---:|
| Petroleum and natural gas | +0.2576 |
| Agricultural inputs | +0.1550 |
| Coal and coke | +0.1004 |
| Ferrous metals | -0.0929 |
| Non-metallic mineral products | +0.0189 |
| Building materials | +0.0118 |
| Chemicals | +0.0103 |
| Agricultural products | -0.0027 |
| Forest products | -0.0022 |
| Non-ferrous metals | -0.0002 |

[Full attribution record](../data/product/vintages/2026-10/a9e6d8993a53df134a89/shap.json)

## XGBoost — Two-survey period

Baseline: **+0.0155 pp** · Forecast: **+0.454% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.1935 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.1671 |
| Diesel (0#China VI) | Monthly price change | +0.0785 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0547 |
| Shanxi blended coal (5000 kcal/kg) | Monthly price change | +0.0526 |
| Seamless steel pipe (219*6,20#) | Monthly price change | -0.0502 |
| Sulfuric acid (98%) | Monthly price change | -0.0420 |
| Standard blended coal (4500 kcal/kg) | Monthly price change | +0.0392 |

| Sector | Attribution (pp) |
|---|---:|
| Petroleum and natural gas | +0.2502 |
| Agricultural inputs | +0.1696 |
| Coal and coke | +0.1277 |
| Ferrous metals | -0.1120 |
| Non-metallic mineral products | +0.0237 |
| Chemicals | -0.0138 |
| Building materials | +0.0094 |
| Agricultural products | -0.0091 |
| Non-ferrous metals | -0.0053 |
| Forest products | -0.0015 |

[Full attribution record](../data/product/vintages/2026-10/90d2195c564a57f3dbaa/shap.json)

## CatBoost — Early month

Baseline: **+0.0294 pp** · Forecast: **+0.357% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Methanol (premium grade) | Monthly price change | +0.1492 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.1184 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0640 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.0384 |
| Hot-rolled steel sheet (3mm,Q235) | Monthly price change | -0.0359 |
| Gasoline (95#China VI) | Monthly price change | +0.0325 |
| Diesel (0#China VI) | Monthly price change | +0.0300 |
| Metallurgical coke (grade 2) | Monthly price change | -0.0280 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | +0.1770 |
| Petroleum and natural gas | +0.1051 |
| Agricultural inputs | +0.1018 |
| Ferrous metals | -0.0680 |
| Non-metallic mineral products | +0.0325 |
| Non-ferrous metals | -0.0208 |
| Agricultural products | -0.0107 |
| Building materials | +0.0090 |
| Forest products | +0.0016 |
| Coal and coke | -0.0001 |

[Full attribution record](../data/product/vintages/2026-10/3ace6368d89fe2478bb6/shap.json)

## HistGradientBoosting — Early month

Baseline: **+0.0303 pp** · Forecast: **+0.544% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.1667 |
| Methanol (premium grade) | Monthly price change | +0.1619 |
| PVC (SG5) | Monthly price change | +0.1333 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0742 |
| Diesel (0#China VI) | Monthly price change | +0.0708 |
| Compound fertilizer (potassium-sulfate-based,NPK content 45%) | Monthly price change | -0.0354 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.0352 |
| Seamless steel pipe (219*6,20#) | Monthly price change | -0.0348 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | +0.3406 |
| Petroleum and natural gas | +0.1266 |
| Agricultural inputs | +0.1218 |
| Ferrous metals | -0.1116 |
| Coal and coke | +0.0453 |
| Agricultural products | -0.0324 |
| Non-metallic mineral products | +0.0272 |
| Non-ferrous metals | -0.0145 |
| Building materials | +0.0110 |
| Forest products | -0.0007 |

[Full attribution record](../data/product/vintages/2026-10/02ad46bf25065161c95b/shap.json)

## LightGBM — Early month

Baseline: **+0.0292 pp** · Forecast: **+0.602% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Methanol (premium grade) | Monthly price change | +0.1739 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.1546 |
| PVC (SG5) | Monthly price change | +0.0856 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0842 |
| Diesel (0#China VI) | Monthly price change | +0.0657 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.0586 |
| Ordinary Portland cement (P.O42.5bulk) | Monthly price change | +0.0454 |
| Cotton (lint,white cotton, grade 3) | Monthly price change | -0.0426 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | +0.3065 |
| Petroleum and natural gas | +0.1823 |
| Agricultural inputs | +0.1149 |
| Ferrous metals | -0.0689 |
| Coal and coke | +0.0460 |
| Non-metallic mineral products | +0.0454 |
| Agricultural products | -0.0427 |
| Non-ferrous metals | -0.0151 |
| Building materials | +0.0072 |
| Forest products | -0.0029 |

[Full attribution record](../data/product/vintages/2026-10/509489ebc66d3352402a/shap.json)

## XGBoost — Early month

Baseline: **+0.0245 pp** · Forecast: **+0.576% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.1520 |
| Methanol (premium grade) | Monthly price change | +0.1450 |
| PVC (SG5) | Monthly price change | +0.0977 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0791 |
| Diesel (0#China VI) | Monthly price change | +0.0682 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.0584 |
| Ordinary Portland cement (P.O42.5bulk) | Monthly price change | +0.0385 |
| Seamless steel pipe (219*6,20#) | Monthly price change | -0.0318 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | +0.3071 |
| Petroleum and natural gas | +0.1458 |
| Agricultural inputs | +0.1259 |
| Ferrous metals | -0.1109 |
| Coal and coke | +0.0609 |
| Non-metallic mineral products | +0.0385 |
| Building materials | +0.0164 |
| Non-ferrous metals | -0.0148 |
| Agricultural products | -0.0137 |
| Forest products | -0.0032 |

[Full attribution record](../data/product/vintages/2026-10/6ccdb07857b885ef6a27/shap.json)

## CatBoost — Early + carry-in

Baseline: **+0.0265 pp** · Forecast: **+0.389% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Gasoline (95#China VI) | Monthly price change | +0.1230 |
| Methanol (premium grade) | Monthly price change | +0.1033 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0596 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.0511 |
| Liquefied petroleum gas (LPG) | Monthly price change | +0.0470 |
| Seamless steel pipe (219*6,20#) | Monthly price change | +0.0458 |
| Steel angle (5#) | Monthly price change | -0.0375 |
| Liquefied petroleum gas (LPG) | Carry-in change | +0.0371 |

| Sector | Attribution (pp) |
|---|---:|
| Petroleum and natural gas | +0.2476 |
| Chemicals | +0.1190 |
| Agricultural inputs | +0.0416 |
| Ferrous metals | -0.0409 |
| Non-metallic mineral products | +0.0166 |
| Non-ferrous metals | -0.0128 |
| Agricultural products | -0.0118 |
| Building materials | +0.0027 |
| Coal and coke | +0.0010 |
| Forest products | -0.0008 |

[Full attribution record](../data/product/vintages/2026-10/b22e053eae81dfb85619/shap.json)

## HistGradientBoosting — Early + carry-in

Baseline: **+0.0280 pp** · Forecast: **+0.461% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Methanol (premium grade) | Monthly price change | +0.1314 |
| Gasoline (95#China VI) | Monthly price change | +0.0991 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0760 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.0623 |
| Diesel (0#China VI) | Monthly price change | +0.0607 |
| Standard blended coal (4500 kcal/kg) | Carry-in change | +0.0529 |
| Liquefied petroleum gas (LPG) | Carry-in change | +0.0471 |
| Steel angle (5#) | Monthly price change | -0.0450 |

| Sector | Attribution (pp) |
|---|---:|
| Petroleum and natural gas | +0.2284 |
| Chemicals | +0.1981 |
| Ferrous metals | -0.1263 |
| Coal and coke | +0.0886 |
| Agricultural inputs | +0.0254 |
| Agricultural products | -0.0250 |
| Forest products | +0.0237 |
| Non-metallic mineral products | +0.0149 |
| Building materials | +0.0096 |
| Non-ferrous metals | -0.0042 |

[Full attribution record](../data/product/vintages/2026-10/12428d3986095b4a4b24/shap.json)

## LightGBM — Early + carry-in

Baseline: **+0.0276 pp** · Forecast: **+0.593% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Methanol (premium grade) | Monthly price change | +0.1645 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.1069 |
| Gasoline (95#China VI) | Monthly price change | +0.1063 |
| Diesel (0#China VI) | Monthly price change | +0.0890 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0673 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0510 |
| Steel angle (5#) | Monthly price change | -0.0398 |
| Cotton (lint,white cotton, grade 3) | Monthly price change | -0.0388 |

| Sector | Attribution (pp) |
|---|---:|
| Petroleum and natural gas | +0.2738 |
| Chemicals | +0.2485 |
| Ferrous metals | -0.0945 |
| Coal and coke | +0.0902 |
| Agricultural inputs | +0.0578 |
| Agricultural products | -0.0341 |
| Non-metallic mineral products | +0.0220 |
| Building materials | +0.0067 |
| Non-ferrous metals | -0.0057 |
| Forest products | +0.0011 |

[Full attribution record](../data/product/vintages/2026-10/6c0fb853d082b7a67019/shap.json)

## XGBoost — Early + carry-in

Baseline: **+0.0232 pp** · Forecast: **+0.442% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Methanol (premium grade) | Monthly price change | +0.1681 |
| Benzene (petroleum-derived,industrial grade) | Monthly price change | +0.0775 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | +0.0746 |
| Diesel (0#China VI) | Monthly price change | +0.0699 |
| Steel angle (5#) | Monthly price change | -0.0456 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0428 |
| PVC (SG5) | Monthly price change | +0.0353 |
| Liquefied petroleum gas (LPG) | Carry-in change | +0.0339 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | +0.2540 |
| Petroleum and natural gas | +0.1543 |
| Ferrous metals | -0.0911 |
| Coal and coke | +0.0802 |
| Agricultural inputs | +0.0351 |
| Non-metallic mineral products | +0.0176 |
| Agricultural products | -0.0172 |
| Non-ferrous metals | -0.0110 |
| Forest products | -0.0052 |
| Building materials | +0.0027 |

[Full attribution record](../data/product/vintages/2026-10/532138aa11714d959c33/shap.json)

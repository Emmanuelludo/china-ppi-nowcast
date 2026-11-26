# What drives the forecasts?

Target month: **2026-11**.

[Back to latest forecasts](README.md) · [Product definitions](../docs/PRODUCTS.md)

SHAP values are model attributions in percentage points, not causal economic contributions. Baseline plus all product attributions equals the model forecast. Correlated products can share attribution differently across models.

## CatBoost — 20th-to-20th

Baseline: **+0.0253 pp** · Forecast: **-0.396% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Benzene (petroleum-derived,industrial grade) | Monthly price change | -0.0861 |
| Sulfuric acid (98%) | Monthly price change | -0.0828 |
| Liquefied petroleum gas (LPG) | Monthly price change | -0.0532 |
| Methanol (premium grade) | Monthly price change | -0.0409 |
| Urea (small prills [source spelling]) | Monthly price change | -0.0224 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | -0.0165 |
| Medium steel plate (20mm,Q235) | Monthly price change | -0.0146 |
| Electrolytic copper (1#) | Monthly price change | -0.0128 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | -0.2435 |
| Coal and coke | -0.0448 |
| Petroleum and natural gas | -0.0398 |
| Ferrous metals | -0.0339 |
| Agricultural inputs | -0.0325 |
| Non-ferrous metals | -0.0219 |
| Agricultural products | -0.0110 |
| Non-metallic mineral products | +0.0098 |
| Forest products | -0.0036 |
| Building materials | -0.0003 |

[Full attribution record](../data/product/vintages/2026-11/4cbd9bab0a2e0a64762b/shap.json)

## HistGradientBoosting — 20th-to-20th

Baseline: **+0.0301 pp** · Forecast: **-0.155% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Benzene (petroleum-derived,industrial grade) | Monthly price change | -0.1130 |
| Shanxi blended coal (5000 kcal/kg) | Monthly price change | +0.0968 |
| Sulfuric acid (98%) | Monthly price change | -0.0855 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0755 |
| Methanol (premium grade) | Monthly price change | -0.0646 |
| Ordinary Portland cement (P.O42.5bulk) | Monthly price change | +0.0556 |
| Seamless steel pipe (219*6,20#) | Monthly price change | -0.0402 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | -0.0373 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | -0.2725 |
| Coal and coke | +0.1959 |
| Agricultural inputs | -0.0615 |
| Non-metallic mineral products | +0.0556 |
| Ferrous metals | -0.0492 |
| Agricultural products | -0.0272 |
| Forest products | -0.0252 |
| Non-ferrous metals | -0.0216 |
| Petroleum and natural gas | +0.0196 |
| Building materials | +0.0009 |

[Full attribution record](../data/product/vintages/2026-11/53fe2617ef9d8a92010b/shap.json)

## LightGBM — 20th-to-20th

Baseline: **+0.0306 pp** · Forecast: **-0.191% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Benzene (petroleum-derived,industrial grade) | Monthly price change | -0.1044 |
| Sulfuric acid (98%) | Monthly price change | -0.0878 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0718 |
| Standard blended coal (4500 kcal/kg) | Monthly price change | +0.0552 |
| Methanol (premium grade) | Monthly price change | -0.0546 |
| Liquefied petroleum gas (LPG) | Monthly price change | -0.0527 |
| Ordinary Portland cement (P.O42.5bulk) | Monthly price change | +0.0432 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | -0.0371 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | -0.2503 |
| Coal and coke | +0.1644 |
| Agricultural inputs | -0.0737 |
| Ferrous metals | -0.0498 |
| Non-metallic mineral products | +0.0432 |
| Non-ferrous metals | -0.0304 |
| Forest products | -0.0126 |
| Agricultural products | -0.0115 |
| Petroleum and natural gas | -0.0036 |
| Building materials | +0.0024 |

[Full attribution record](../data/product/vintages/2026-11/95d4c7307a16d1cef962/shap.json)

## Random forest — 20th-to-20th

Baseline: **+0.0382 pp** · Forecast: **-0.227% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Benzene (petroleum-derived,industrial grade) | Monthly price change | -0.1014 |
| Liquefied petroleum gas (LPG) | Monthly price change | -0.0781 |
| Seamless steel pipe (219*6,20#) | Monthly price change | -0.0657 |
| Methanol (premium grade) | Monthly price change | -0.0397 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0288 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | -0.0272 |
| Sulfuric acid (98%) | Monthly price change | -0.0205 |
| Ordinary Portland cement (P.O42.5bulk) | Monthly price change | +0.0137 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | -0.1527 |
| Ferrous metals | -0.0660 |
| Petroleum and natural gas | -0.0521 |
| Coal and coke | +0.0463 |
| Agricultural inputs | -0.0325 |
| Non-ferrous metals | -0.0161 |
| Non-metallic mineral products | +0.0137 |
| Agricultural products | -0.0100 |
| Building materials | +0.0071 |
| Forest products | -0.0026 |

[Full attribution record](../data/product/vintages/2026-11/ac2bee06bbe2f2363a25/shap.json)

## XGBoost — 20th-to-20th

Baseline: **+0.0241 pp** · Forecast: **-0.260% MoM**

| Product | Feature | Attribution (pp) |
|---|---|---:|
| Benzene (petroleum-derived,industrial grade) | Monthly price change | -0.1088 |
| Sulfuric acid (98%) | Monthly price change | -0.0963 |
| Shanxi blended coal (5000 kcal/kg) | Monthly price change | +0.0667 |
| Datong blended coal (5800 kcal/kg) | Monthly price change | +0.0660 |
| Liquefied petroleum gas (LPG) | Monthly price change | -0.0660 |
| Methanol (premium grade) | Monthly price change | -0.0462 |
| Ordinary Portland cement (P.O42.5bulk) | Monthly price change | +0.0399 |
| Glyphosate herbicide (glyphosate,95%technical grade) | Monthly price change | -0.0364 |

| Sector | Attribution (pp) |
|---|---:|
| Chemicals | -0.2718 |
| Coal and coke | +0.1790 |
| Agricultural inputs | -0.0801 |
| Ferrous metals | -0.0454 |
| Non-metallic mineral products | +0.0399 |
| Agricultural products | -0.0373 |
| Petroleum and natural gas | -0.0364 |
| Non-ferrous metals | -0.0198 |
| Forest products | -0.0148 |
| Building materials | +0.0021 |

[Full attribution record](../data/product/vintages/2026-11/f8723cc108395abf077c/shap.json)

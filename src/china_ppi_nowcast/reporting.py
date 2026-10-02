"""English presentation of immutable forecasts. No feature or model transformations."""
import argparse
import csv
import json
from pathlib import Path
from .model_policy import is_active

LABELS = json.loads(Path(__file__).with_name('product_labels.json').read_text(encoding='utf-8'))
MODELS = {'ridge':'Product ridge','histgb':'HistGradientBoosting','xgboost':'XGBoost',
          'catboost':'CatBoost','lightgbm':'LightGBM','category_factor':'Category-factor regression',
          'sector_first':'Sector-first regression','random_forest':'Random forest',
          'economic_ml_hybrid':'Economic / ML hybrid (NBS prices)', 'direct_tracker':'Direct price tracker',
          'no_change':'No-change baseline','historical_mean':'Historical-mean baseline',
          'last_available_actual':'Last-released PPI baseline',
          'category_factor_regression':'Category-factor regression','gradient_boosting':'HistGradientBoosting',
          'product_level_ridge':'Product ridge','sector_first_aggregation':'Sector-first regression',
          'twentieth_to_twentieth_direct':'Direct trimmed price tracker',
          'twentieth_to_twentieth_ridge':'20th-to-20th ridge'}
TIMINGS = {'twentieth':'20th-to-20th','final':'Two-survey period','early':'Early month','early_carry':'Early + carry-in'}
PANELS = {'union':'All historical products','stable':'Stable products'}
ORDER = ['xgboost','catboost','lightgbm','histgb','ridge','random_forest','sector_first','economic_ml_hybrid']


def model_name(key):
    return MODELS.get(key,key.replace('_',' ').capitalize())


def product_name(pid):
    return LABELS['products'].get(pid,{}).get('english',f'Product {pid} (English label pending review)')


def group_name(key):
    return LABELS['groups'].get(key,'Other / unmapped group')


def write(root,path,lines):
    target=root/path;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text('\n'.join(lines)+'\n',encoding='utf-8')


def matrix_table(rows,panel='union'):
    lookup={(r['model'],r['variant']):r for r in rows if r['panel']==panel}
    lines=['| Model | 20th-to-20th | Two-survey period | Early month | Early + carry-in |',
           '|---|---:|---:|---:|---:|']
    for model in ORDER:
        if not any(k[0]==model for k in lookup):continue
        values=[]
        for timing in TIMINGS:
            row=lookup.get((model,timing))
            values.append(f"{row['prediction_mom']:+.3f}%" if row else '—')
        lines.append('| '+model_name(model)+' | '+' | '.join(values)+' |')
    return lines


def write_product_reports(root,manifest,catalog,month,as_of,outputs,pending):
    root=Path(root)
    outputs=[r for r in outputs if is_active(r["model"])]
    sources={}
    for r in outputs:
        feature=root/'data/product/vintages'/month/r['forecast_id'][:20]/'features.json'
        if feature.exists(): sources.update(json.loads(feature.read_text())['sources'])
    windows=sorted(k for k in sources if k.startswith(month+':'))
    intro=['# China PPI nowcast', '',f'**Target: {month} · Headline PPI month-on-month change**',
           '',f'Report refreshed: {as_of}. Forecast timestamps remain fixed when inputs are unchanged.',
           '',f"Current-month price windows incorporated: **{', '.join(k.split(':')[1] for k in windows) or 'None yet'}**.",
           '', '[Model explanations](../docs/METHODOLOGY.md) · [English product glossary](../docs/PRODUCTS.md) · [Attributions](attributions.md) · [Performance](product_candidates.md)',
           '', '## Product-price models', '',
           'All values are predicted official PPI MoM percentages. A dash means that model/timing combination has no saved output.', '']
    lines=intro+matrix_table(outputs)
    lines+=['','## Stable-product sensitivity','','These models use only series with complete coverage in their training sample.','']+matrix_table(outputs,'stable')
    lines+=['','## Direct market-price tracker','',
            'This is an uncalibrated circulation-market price index, **not an official PPI forecast**. It is excluded from forecast summaries.','']
    for r in outputs:
        if r['model']=='direct_tracker':lines.append(f"- {TIMINGS[r['variant']]}: **{r['prediction_mom']:+.3f}%**.")
    if pending:
        lines+=['','## Awaiting data','']
        for r in pending:lines.append(f"- {TIMINGS.get(r['variant'],r['variant'])}: {r['reason'].replace('QA: unavailable source release','awaiting price release')}.")
    lines+=['','## How to read the timings','',
        '- **20th-to-20th:** current versus previous month’s 11–20 period prices.',
        '- **Two-survey period:** average of 1–10 and 11–20 prices versus the same previous-month periods.',
        '- **Early month:** current versus previous 1–10 prices.',
        '- **Early + carry-in:** early-month features plus the change from the previous 21–end period.',
        '', 'Active models are retained for comparison. Category-factor models are retired; historical records remain archived. No permanent winner or weighted ensemble has been selected.',
        '',f"Training-source coverage: {manifest['source_start']} to {manifest['source_end']}. This is the fitted model's training snapshot, not the latest live-data cutoff.",
        '', '## Source releases used','', '| Price window | Publication time | Official source |','|---|---|---|']
    for key,items in sorted(sources.items()):
        for item in items:lines.append(f"| {key.replace(':',' / ')} | {item['published_at']} | [NBS release]({item['source_url']}) |")
    lines+=['','## Forecast archive','','[Immutable forecasts and input rows](../data/product/vintages/) · [Saved model objects](../models/)']
    write(root,'reports/product_latest.md',lines)
    attribution=['# What drives the forecasts?', '',f'Target month: **{month}**.', '',
        '[Back to latest forecasts](README.md) · [Product definitions](../docs/PRODUCTS.md)', '',
        'SHAP values are model attributions in percentage points, not causal economic contributions. Baseline plus all product attributions equals the model forecast. Correlated products can share attribution differently across models.']
    for r in sorted(outputs,key=lambda r:(list(TIMINGS).index(r['variant']),r['model'])):
        if r['panel']!='union':continue
        path=root/'data/product/vintages'/month/r['forecast_id'][:20]/'shap.json'
        if not path.exists():continue
        a=json.loads(path.read_text())
        attribution+=['',f"## {model_name(r['model'])} — {TIMINGS[r['variant']]}",'',
            f"Baseline: **{a['baseline']:+.4f} pp** · Forecast: **{a['prediction']:+.3f}% MoM**",'',
            '| Product | Feature | Attribution (pp) |','|---|---|---:|']
        for feature,value in sorted(a['product'].items(),key=lambda kv:abs(kv[1]),reverse=True)[:8]:
            kind,pid=feature.split('__',1)
            attribution.append(f"| {product_name(pid)} | {'Carry-in change' if kind=='carry' else 'Monthly price change'} | {value:+.4f} |")
        attribution+=['','| Sector | Attribution (pp) |','|---|---:|']
        for group,value in sorted(a['grouped'].items(),key=lambda kv:abs(kv[1]),reverse=True):
            attribution.append(f'| {group_name(group)} | {value:+.4f} |')
        attribution+=['',f"[Full attribution record](../data/product/vintages/{month}/{r['forecast_id'][:20]}/shap.json)"]
    write(root,'reports/attributions.md',attribution)
    overview=intro+matrix_table(outputs)+['','## Survey-aligned benchmarks','',
        'These use the carry-weighted survey-date feature specification. Their estimates are separate from the product-price models above.','',
        '| Model | Timing | PPI MoM | Frozen at |','|---|---|---:|---|']
    registry=root/'data/registry/forecasts.csv'
    if registry.exists():
        rows=list(csv.DictReader(registry.open()))
        active=Path(json.loads((root/'config/pipeline.json').read_text())['model_bundle']).name
        selected={}
        for r in sorted(rows,key=lambda r:r['as_of']):
            if r['target_month']==month and r['model_version'].startswith(active) and r['model_key']!='twentieth_to_twentieth_direct' and is_active(r['model_key']):
                selected[r['model_key']]=r
        for r in selected.values():overview.append(f"| {model_name(r['model_key'])} | {r['vintage'].capitalize()} | {float(r['estimate_mom_pct']):+.3f}% | {r['as_of']} |")
    overview+=['','## Explore the results','',
        '| Report | Contents |','|---|---|',
        '| [All product forecasts](product_latest.md) | Main models, stable-panel sensitivity, direct tracker and exact source releases |',
        '| [Forecast explanations](attributions.md) | English product and sector SHAP tables |',
        '| [Historical model comparison](product_candidates.md) | Rolling out-of-sample MAE, RMSE and bias |',
        '| [Performance over time](product_performance.md) | Prospective results and 6/12/24-month historical summaries |',
        '| [Survey-aligned benchmarks](latest_nowcast.md) | Benchmark estimates and model dispersion |',
        '| [Pipeline status](latest.md) | Data and model readiness |',
        '| [August 2026 forecast archive](august_2026_frozen.md) | Frozen historical forecast record |',
        '', 'No weighted ensemble has been adopted. Differences between models are not a calibrated confidence interval.',
        '', 'Advanced diagnostics: [source coverage audit](history_search.json), [benchmark validation](backfill_evaluation.md), [in-sample backcast](historical_backcast_2025_2026.md). The backcast is not forecast-accuracy evidence.']
    write(root,'reports/README.md',overview)
    write_product_glossary(root,catalog)
    from .dashboard import write_dashboard
    write_dashboard(root,manifest,month,as_of)


def write_product_glossary(root,catalog):
    lines=['# Product glossary','', '[Project home](../README.md) · [Latest forecasts](../reports/README.md)', '',
           'English display names retain the product specification and unit. Chinese names are included only here and in source/audit data for exact NBS matching.', '',
           'Historical specification changes and source footnote variants keep their original identifiers. Display translations do not merge series or change model inputs. First/last dates describe the fitted catalog, not current trading activity.', '',
           '| Product (English) | Sector | Unit | First / last observation in fitted catalog | NBS source name | Product ID |',
           '|---|---|---|---|---|---|']
    for pid,p in sorted(catalog['products'].items(),key=lambda kv:product_name(kv[0])):
        lines.append(f"| {product_name(pid)} | {group_name(p['group'])} | {p['unit']} | {p['first_available']} / {p['last_available']} | {p['canonical_name']} | `{pid}` |")
    write(root,'docs/PRODUCTS.md',lines)


def write_candidate_report(root,manifest):
    lines=['# Historical model comparison','', '[Latest forecasts](README.md) · [Evaluation methodology](../docs/METHODOLOGY.md)', '',
        'Expanding-window, nested chronological validation. These results are **pseudo-real-time**: release dates are respected, but historical pages were retrieved later.', '',
        'MAE, RMSE and bias are in percentage points. Compare models within the same timing and panel; the eligible forecast months differ across timing specifications. The direct tracker is an uncalibrated price index.', '',
        '| Timing | Product panel | Model | Forecast months | MAE | RMSE | Bias |','|---|---|---|---:|---:|---:|---:|']
    for r in manifest['models']:
        if not is_active(r['name']):continue
        m=r['metrics'];lines.append(f"| {TIMINGS[r['variant']]} | {PANELS[r['panel']]} | {model_name(r['name'])} | {m['n']} | {m['mae']:.3f} | {m['rmse']:.3f} | {m['bias']:.3f} |")
    lines+=['',f"Model version: `{manifest['version']}`. Training-source coverage: {manifest['source_start']} to {manifest['source_end']}.", '',
            'Stable product panels and preprocessing are selected within each training fold. At least six genuinely prospective monthly releases are needed before making strong model-ranking claims.']
    write(root,'reports/product_candidates.md',lines)


def refresh_saved_reports(root):
    root=Path(root);bundle=root/json.loads((root/'config/product_pipeline.json').read_text())['bundle']
    manifest=json.loads((bundle/'manifest.json').read_text());catalog=json.loads((bundle/'catalog.json').read_text())
    rows=[json.loads(p.read_text()) for p in (root/'data/product/vintages').glob('*/*/forecast.json')]
    rows=[r for r in rows if r['model_version']==manifest['version']]
    if not rows:raise ValueError('No forecasts for the active model version')
    month=max(r['target_month'] for r in rows);selected={}
    for r in sorted(rows,key=lambda r:r['as_of']):
        if r['target_month']==month:selected[(r['variant'],r['panel'],r['model'])]=r
    outputs=list(selected.values());as_of=max(r['as_of'] for r in outputs)
    pending=[dict(variant=v,reason='awaiting required source releases') for v in TIMINGS if not any(r['variant']==v for r in outputs)]
    write_product_reports(root,manifest,catalog,month,as_of,outputs,pending)
    write_candidate_report(root,manifest)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',default='.')
    refresh_saved_reports(Path(parser.parse_args().root).resolve())

"""Derived forecast diagnostics; stored inputs, models and estimates are immutable."""
import csv
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from statistics import median
from .model_policy import is_active

BOOSTERS=('xgboost','catboost','lightgbm','histgb')

def stamp(s):return datetime.fromisoformat(s)

def read_csv(path):
 with Path(path).open() as handle:return list(csv.DictReader(handle))

def latest_saved(root,manifest,as_of):
 selected={}
 for p in sorted((Path(root)/'data/product/vintages').glob('*/*/forecast.json')):
  r=json.loads(p.read_text())
  if r['model_version']!=manifest['version'] or not is_active(r['model']) or stamp(r['as_of'])>stamp(as_of):continue
  key=(r['target_month'],r['variant'],r['panel'],r['model'])
  if key not in selected or stamp(r['as_of'])>stamp(selected[key]['as_of']):selected[key]=r
 if not selected:return []
 month=max(r['target_month'] for r in selected.values())
 return [r for r in selected.values() if r['target_month']==month]

def diagnostics(root,bundle,manifest,as_of):
 root=Path(root);bundle=Path(bundle);saved=latest_saved(root,manifest,as_of);models={(c['variant'],c['panel'],c['name']):c for c in manifest['models']};matrices={};records=[]
 oos=read_csv(bundle/'rolling_predictions.csv')
 for r in saved:
  c=models[(r['variant'],r['panel'],r['model'])];directory=root/'data/product/vintages'/r['target_month']/r['forecast_id'][:20]
  meta=json.loads((directory/'features.json').read_text());cutoff=stamp(r['as_of'])
  assert c['training_end']<r['target_month'],'Training overlaps forecast month'
  assert stamp(manifest['training_actual_cutoff'])<=cutoff,'Later targets used in training'
  assert meta['feature_hash']==r['feature_hash'],'Frozen feature hash mismatch'
  for sources in meta['sources'].values():
   for source in sources:
    assert stamp(source['published_at'])<=cutoff and stamp(source['retrieved_at'])<=cutoff,'Unavailable source in frozen forecast'
  artifact=bundle/c['artifact']
  assert hashlib.sha256(artifact.read_bytes()).hexdigest()==c['artifact_sha256'],'Saved model hash mismatch'
  if r['variant'] not in matrices:matrices[r['variant']]=read_csv(bundle/r['variant']/'matrix.csv')
  matrix=matrices[r['variant']];learned=c['learned_features'];present=[k for k in learned if meta['values'].get(k) is not None];outside=[];short=[];counts={}
  for k in present:
   values=[float(row[k]) for row in matrix if row.get(k) and math.isfinite(float(row[k]))]
   if len(values)<12:short.append(k);counts[k]=len(values)
   if meta['values'][k]<min(values) or meta['values'][k]>max(values):outside.append(k)
  matched=[x for x in oos if x['variant']==r['variant'] and x['panel']==r['panel'] and x['model']==r['model']]
  if matched:
   last=max(x['target_month'] for x in matched);y,m=map(int,last.split('-'));threshold=12*y+m-12
   recent=[x for x in matched if 12*int(x['target_month'][:4])+int(x['target_month'][5:])>threshold]
  else:recent=[]
  recent_mae=sum(abs(float(x['prediction'])-float(x['actual'])) for x in recent)/len(recent) if recent else None
  records.append(dict(model=r['model'],variant=r['variant'],panel=r['panel'],prediction=r['prediction_mom'],
   forecast_month=r['target_month'],frozen_at=r['as_of'],used_products=len(present),learned_features=len(learned),
   outside_training_range=len(outside),short_history_features=len(short),outside_features=outside,short_features=short,short_history_counts=counts,
   historical_mae=c['metrics']['mae'],recent_12_calendar_month_mae=recent_mae,recent_forecast_months=len(recent),
   historical_forecast_months=c['metrics']['n'],checks='artifact hash, feature identity, source cutoff and training cutoff passed'))
 summaries=[]
 for variant in ('twentieth','final','early','early_carry'):
  values=[r['prediction'] for r in records if r['variant']==variant and r['panel']=='union' and r['model'] in BOOSTERS]
  if values:summaries.append(dict(variant=variant,n=len(values),median=median(values),minimum=min(values),maximum=max(values)))
 ridge={r['panel']:r for r in records if r['model']=='ridge' and r['variant']=='twentieth'}
 gap=abs(ridge['union']['prediction']-ridge['stable']['prediction']) if {'union','stable'}<=ridge.keys() else None
 return dict(forecast_month=saved[0]['target_month'] if saved else None,checked_as_of=as_of,models=records,
  booster_summaries=summaries,ridge_panel_gap_pp=gap,prospective_rankings_established=False)

def write_quality_report(root,bundle,manifest,as_of):
 from .reporting import model_name,TIMINGS,PANELS,product_name
 root=Path(root);d=diagnostics(root,bundle,manifest,as_of)
 lines=['# Forecast sense check','',f"Latest saved target: **{d['forecast_month'] or 'none'}**. Checked: {as_of[:10]}.",'',
  'Checks use frozen inputs and model artifacts. No forecasts or fitted models are changed. Current-month forecasts remain pending until their required price windows are available.','',
  '## Comparable forecasts','', '| Model | Timing | Panel | PPI MoM | Used product features | Outside training range | Features with <12 training months | Historical MAE | Recent MAE (N) |',
  '|---|---|---|---:|---:|---:|---:|---:|---:|']
 for r in sorted(d['models'],key=lambda r:(r['variant'],r['panel'],r['model'])):
  if r['model']=='direct_tracker':continue
  recent='—' if r['recent_12_calendar_month_mae'] is None else f"{r['recent_12_calendar_month_mae']:.3f} ({r['recent_forecast_months']})"
  lines.append(f"| {model_name(r['model'])} | {TIMINGS[r['variant']]} | {PANELS[r['panel']]} | {r['prediction']:+.3f}% | {r['used_products']} | {r['outside_training_range']} | {r['short_history_features']} | {r['historical_mae']:.3f} | {recent} |")
 lines+=['','MAE is in percentage points. Recent means the last 12 calendar months in the stored rolling validation; missing-window months are excluded, so N can be less than 12. All accuracy statistics are pseudo-real-time, not prospective evidence.','',
  '## Interpretation','']
 for s in d['booster_summaries']:
  lines.append(f"- {TIMINGS[s['variant']]}: {s['n']} product boosters span **{s['minimum']:+.3f}% to {s['maximum']:+.3f}%**; median **{s['median']:+.3f}%**. This is descriptive agreement, not an ensemble or confidence interval.")
 if d['ridge_panel_gap_pp'] is not None:
  lines.append(f"- Ridge 20th-to-20th panel sensitivity: **{d['ridge_panel_gap_pp']:.3f} pp** between all-product and stable-product versions. Treat the all-product estimate as sensitivity evidence; a sign reversal warrants investigation.")
 lines+=['- Several product changes can lie outside the fitted training range. Linear models extrapolate; trees often saturate. Both require monitoring.',
  '- Short-history product series and missingness indicators can encode basket/regime changes. Tight agreement among correlated boosters does not establish independent confirmation.',
  '- Sector-first and hybrid models remain useful comparisons: judge their full and recent validation alongside the pure product models.',
  '- The direct circulation-price index has no PPI weights or calibration and is excluded from all PPI summaries.',
  '- Do not combine early forecasts with later forecasts into one mean. They represent different information sets.',
  '- At least six prospective outcomes are still required before strong model-ranking claims.','',
  '## Sparse series and extrapolation','']
 for r in d['models']:
  if r['model']!='ridge' or r['variant']!='twentieth' or r['panel']!='union':continue
  for k in r['outside_features']:
   lines.append(f"- {product_name(k.split('__',1)[1])}: live change outside this feature’s fitted historical range.")
 (root/'reports/forecast_quality.md').write_text('\n'.join(lines)+'\n')
 (root/'reports/forecast_quality.json').write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
 return d

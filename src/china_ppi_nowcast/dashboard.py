"""English dashboard derived only from frozen forecasts; no model fitting."""
import argparse
import json
from datetime import datetime
from html import escape
from pathlib import Path
from .model_policy import is_active
from .reporting import model_name, product_name, group_name, TIMINGS

CORE = ('xgboost','catboost','lightgbm','histgb','ridge')
EXTRA = ('random_forest','sector_first','economic_ml_hybrid')
EXPLANATIONS = {
 'xgboost':'Shallow boosted trees learn nonlinear relationships between individual product-price changes and headline PPI.',
 'catboost':'Regularized boosted trees provide an independent nonlinear estimate and handle structural missing prices.',
 'lightgbm':'A strongly constrained tree booster tests an alternative way of learning product-price interactions.',
 'histgb':'Histogram-based gradient boosting provides a simpler tree-booster benchmark with native missing-value handling.',
 'ridge':'Regularized linear regression uses observed-value scaling, fold-local product eligibility and chronological tuning. Sparse missing inputs map to the observed training mean.',
 'random_forest':'Averages many decision trees to test a different nonlinear modelling assumption.',
 'sector_first':'Groups product changes into sector signals before fitting a regularized regression.',
 'economic_ml_hybrid':'Combines linear and boosting estimates built from NBS price signals.',
 'direct_tracker':'Tracks circulation-market price movements without calibration to headline PPI. This is a price index, not a PPI forecast.'}
TIMING_HELP = {
 'twentieth':'Current month 11–20 average prices compared with the previous month’s 11–20 averages. These are period averages, not point prices observed exactly on the 20th.',
 'final':'Average of current 1–10 and 11–20 prices compared with the same two periods in the previous month.',
 'early':'Current 1–10 prices compared with previous month 1–10 prices. No 11–20 prices enter this specification.',
 'early_carry':'Early-month changes plus previous 21–end to current 1–10 carry-in changes.'}

def month_name(value):
 return datetime.strptime(value,'%Y-%m').strftime('%B %Y')

def build_data(root,manifest,requested_month,as_of):
 rows=[]
 for p in (root/'data/product/vintages').glob('*/*/forecast.json'):
  r=json.loads(p.read_text())
  if r['model_version']!=manifest['version'] or not is_active(r['model']):continue
  if datetime.fromisoformat(r['as_of'])>datetime.fromisoformat(as_of):continue
  rows.append(r)
 chosen={}
 for r in sorted(rows,key=lambda r:r['as_of']):chosen[(r['target_month'],r['variant'],r['panel'],r['model'])]=r
 result=[]
 metrics={(r['variant'],r['panel'],r['name']):r['metrics'] for r in manifest['models']}
 for r in chosen.values():
  directory=root/'data/product/vintages'/r['target_month']/r['forecast_id'][:20]
  attr=[];groups=[]
  p=directory/'shap.json'
  if p.exists():
   a=json.loads(p.read_text())
   attr=[dict(label=product_name(k.split('__',1)[1]),value=v) for k,v in sorted(a['product'].items(),key=lambda kv:abs(kv[1]),reverse=True)[:6]]
   groups=[dict(label=group_name(k),value=v) for k,v in sorted(a['grouped'].items(),key=lambda kv:abs(kv[1]),reverse=True)]
  result.append(dict(month=r['target_month'],month_label=month_name(r['target_month']),timing=r['variant'],panel=r['panel'],
   model=r['model'],label=model_name(r['model']),prediction=r['prediction_mom'],frozen_at=r['as_of'],
   explanation=EXPLANATIONS[r['model']],products=attr,groups=groups,metrics=metrics[(r['variant'],r['panel'],r['model'])]))
 months=sorted(set(r['month'] for r in result),reverse=True)
 return dict(requested_month=requested_month,requested_label=month_name(requested_month),refreshed=as_of,
  latest_month=months[0] if months else None,months=[dict(value=m,label=month_name(m)) for m in months],
  current_available=any(r['month']==requested_month for r in result),timings=TIMINGS,timing_help=TIMING_HELP,forecasts=result)

def svg_chart(rows,title):
 width=960; height=100+len(rows)*60;left=230;right=800
 values=[r['prediction'] for r in rows];lo=min([0]+values)-.1;hi=max([0]+values)+.15
 def x(v):return left+(v-lo)/(hi-lo)*(right-left)
 zero=x(0)
 out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">',
 '<rect width="100%" height="100%" rx="16" fill="#f5f7fb"/>',f'<text x="28" y="35" font-family="sans-serif" font-size="20" fill="#162b46">{escape(title)}</text>',
 f'<line x1="{zero}" x2="{zero}" y1="55" y2="{height-35}" stroke="#8796a9"/>']
 for i,r in enumerate(rows):
  y=70+i*60;v=r['prediction'];a=min(x(v),zero);w=abs(x(v)-zero)
  out += [f'<text x="28" y="{y+20}" font-family="sans-serif" font-size="17" fill="#162b46">{escape(r["label"])}</text>',
   f'<rect x="{a:.2f}" y="{y}" width="{w:.2f}" height="29" rx="4" fill="{"#176b87" if v>=0 else "#a84450"}"/>',
   f'<text x="825" y="{y+20}" font-family="sans-serif" font-size="17" fill="#162b46">{v:+.3f}%</text>']
 out.append('</svg>');return '\n'.join(out)

def write_dashboard(root,manifest,requested_month,as_of):
 root=Path(root);data=build_data(root,manifest,requested_month,as_of)
 from .quality import write_quality_report
 bundle=root/json.loads((root/"config/product_pipeline.json").read_text())["bundle"]
 quality=write_quality_report(root,bundle,manifest,as_of)
 data["quality"]=quality
 latest=data['latest_month'];selected=[r for r in data['forecasts'] if r['month']==latest and r['timing']=='twentieth' and r['panel']=='union' and r['model'] in CORE]
 selected.sort(key=lambda r:CORE.index(r['model']))
 if not selected:
  selected=[r for r in data['forecasts'] if r['month']==latest and r['panel']=='union' and r['model'] in CORE]
  if selected:
   timing=selected[-1]['timing'];selected=[r for r in selected if r['timing']==timing]
 else:timing='twentieth'
 title=f"{month_name(latest)} · {TIMINGS[timing]} · PPI MoM" if selected else 'Awaiting price data'
 (root/'reports/forecast_comparison.svg').write_text(svg_chart(selected,title))
 lines=['# China PPI dashboard','', '[Project home](../README.md) · [Model details](../docs/METHODOLOGY.md) · [English product glossary](../docs/PRODUCTS.md)', '',
  f"## Current update: {data['requested_label']}",'',
  'Current-month forecasts are available below.' if data['current_available'] else '⏳ **Awaiting the current month’s price releases. No current-month projection has been generated.**', '',
  f"Report refreshed: {as_of.split('T')[0]}. Saved forecast timestamps are preserved.",'']
 if selected:
  values=sorted(r['prediction'] for r in selected);n=len(values);median=(values[(n-1)//2]+values[n//2])/2
  lines += [f"## Latest available forecasts: {month_name(latest)}",'',
   f"**{TIMINGS[timing]} · {n} product-price estimators · Median {median:+.3f}% MoM**",'',
   f"{sum(v>0 for v in values)} of {n} displayed models project an increase; {sum(v<0 for v in values)} project a decline. The estimates span **{min(values):+.3f}% to {max(values):+.3f}%**. The median describes this model group; it is not a selected ensemble or a confidence interval.",'',
   '![Forecast comparison](forecast_comparison.svg)','',
   '**How to read this:** +0.7% means prices are projected to be 0.7% higher than the previous month. These forecasts concern headline PPI month-on-month change, not year-on-year inflation.','',
   f'**Price dates:** {TIMING_HELP[timing]}','']
 if quality['ridge_panel_gap_pp'] is not None:
  lines += ['## Robustness check','',f"Ridge changes by **{quality['ridge_panel_gap_pp']:.3f} percentage points** between the all-product and stable-product 20th-to-20th panels. This measures sensitivity to product coverage; read it alongside rolling forecast errors. Several live product changes exceed their fitted historical ranges.",'', '[Read the forecast sense check, recent errors and all retained model estimates](forecast_quality.md)', '', 'Booster agreement is narrower than historical forecast errors; it is not a prediction interval. Sector-first and hybrid comparisons remain visible in the quality report.','']
 lines += ['## What each model does','', '| Active product model | Mechanism |','|---|---|']
 for m in CORE:lines.append(f'| {model_name(m)} | {EXPLANATIONS[m]} |')
 lines += ['','## Other retained comparisons','',
  'Random forest, sector-first regression and the economic / ML hybrid remain available in the detailed view. Stable-product panels test basket sensitivity. The direct market-price tracker is shown separately as an uncalibrated price index. Category-factor models are retired.','',
  '## Explore','',
  '- **[Interactive dashboard file](dashboard.html)** — download the file and open it in a browser; choose month, timing, product panel and retained comparison models. It works without a login or external scripts.',
  '- [All current model estimates and release availability](product_latest.md)',
  '- [Product and sector attributions in English](attributions.md)',
  '- [Ridge revision: specifications, validation and August comparison](ridge_revision.md)',
  '- [Historical accuracy](product_candidates.md) · [Prospective performance](product_performance.md)',
  '- [Source and pipeline status](latest.md)',
  '- [Frozen August forecast archive](august_2026_frozen.md)','',
  'Historical accuracy is pseudo-real-time. Keep accumulating prospective outcomes before ranking models. Product attributions explain the model output, not causal economic contributions.']
 (root/'reports/README.md').write_text('\n'.join(lines)+'\n')
 template=Path(__file__).with_name('dashboard_template.html').read_text()
 payload=json.dumps(data,ensure_ascii=True,allow_nan=False).replace('<','\\u003c')
 (root/'reports/dashboard.html').write_text(template.replace('__DASHBOARD_DATA__',payload))
 return data

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--target-month');p.add_argument('--as-of');args=p.parse_args()
 root=Path(args.root);bundle=root/json.loads((root/'config/product_pipeline.json').read_text())['bundle']
 manifest=json.loads((bundle/'manifest.json').read_text())
 now=datetime.now().astimezone()
 write_dashboard(root,manifest,args.target_month or now.strftime('%Y-%m'),args.as_of or now.isoformat())

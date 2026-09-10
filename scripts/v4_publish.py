"""Survey-state report, paired backtests and strictly past-error hybrid weights."""
from pathlib import Path
import json,base64,hashlib
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from v4_compare import targets
R=Path(__file__).resolve().parents[1];D=R/'data/v4';O=R/'reports/v4'
def tbl(x):return x.to_html(index=False,border=0,float_format=lambda x:f'{x:.3f}')
def img(fig,name):
 path=O/(name+'.png');fig.savefig(path,dpi=150,bbox_inches='tight');plt.close(fig)
 return '<img alt="'+name+'" src="data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()+'">'
def operational(f,t):
 f=f.copy();f['price_asof']=f.cutoff;f['state_source_vintage']=f.vintage
 for i,r in f[f.vintage.eq('final')&f.model.ne('calendar_product_ridge')].iterrows():
  prior=f[(f.target_month==r.target_month)&(f.model==r.model)&f.vintage.isin(['early','mid'])].sort_values('cutoff')
  if prior.empty:continue
  prev=prior.iloc[-1];newlabels=t[(t.available_at>pd.Timestamp(prev.cutoff))&(t.available_at<=pd.Timestamp(r.cutoff))]
  if not newlabels.empty:continue
  for col in ['forecast','timing','parameter','n_train','n_features','lower80','upper80','interval_n']:
   f.loc[i,col]=prev[col]
  f.loc[i,'price_asof']=prev.cutoff;f.loc[i,'state_source_vintage']=prev.vintage
 return f

def score(g,truth):
 e=g.forecast-g.actual;out=dict(n=len(g),correlation=g.forecast.corr(g.actual),rmse=np.sqrt(np.mean(e**2)),mae=np.mean(abs(e)),directional_accuracy=np.mean(np.sign(g.forecast)==np.sign(g.actual)),bias=e.mean(),max_miss=abs(e).max())
 turns=[];hits=0;actualturns=0;predturns=0
 for _,r in g.iterrows():
  prev=str(pd.Period(r.target_month,'M')-1)
  if prev not in truth.index:continue
  old=truth.loc[prev]
  if old.value==0 or old.available_at>=pd.Timestamp(r.cutoff):continue
  a=old.value*r.actual<0;p=old.value*r.forecast<0;turns.append(a==p);hits+=int(a and p);actualturns+=int(a);predturns+=int(p)
 out.update(turning_point_accuracy=np.mean(turns) if turns else np.nan,turning_point_n=len(turns),actual_turns=actualturns,turn_precision=hits/predturns if predturns else np.nan,turn_recall=hits/actualturns if actualturns else np.nan)
 big=g[g.actual.abs()>=.5];out['large_move_n']=len(big);out['large_move_rmse']=np.sqrt(np.mean((big.forecast-big.actual)**2)) if len(big) else np.nan
 return out

def main():
 O.mkdir(exist_ok=True,parents=True);t=targets();t['month']=t.month.astype(str);truth=t[t.target_id=='headline_ppi_mom'].set_index('month')
 raw=pd.read_csv(D/'comparison_forecasts.csv');f=operational(raw,t)
 sector=pd.read_csv(D/'sectorfirst_survey_state.csv').rename(columns={'month':'target_month','scheme':'timing'})
 sector['actual_available_at']=sector.target_month.map(truth.available_at)
 f=pd.concat([f,sector],ignore_index=True,sort=False)
 # Hybrid combines actual forecast streams. Weighting only uses released prior errors.
 hybrid=[]
 for vintage in f.vintage.unique():
  a=f[(f.vintage==vintage)&(f.model=='sectorfirst_survey_state')].set_index('target_month')
  b=f[(f.vintage==vintage)&(f.model=='aligned_boosting')].set_index('target_month')
  for month in sorted(a.index.intersection(b.index)):
   cutoff=pd.Timestamp(a.loc[month,'cutoff']);history=[m for m in a.index.intersection(b.index) if m<month and m in truth.index and truth.loc[m,'available_at']<cutoff]
   weight=.5
   if len(history)>=12:
    ea=np.mean((a.loc[history,'forecast']-truth.loc[history,'value'])**2);eb=np.mean((b.loc[history,'forecast']-truth.loc[history,'value'])**2);weight=(eb+.01)/(ea+eb+.02)
   hybrid.append(dict(target_month=month,vintage=vintage,cutoff=cutoff.isoformat(),model='economic_ML_hybrid',forecast=weight*a.loc[month,'forecast']+(1-weight)*b.loc[month,'forecast'],actual=truth.loc[month,'value'] if month in truth.index else np.nan,actual_available_at=truth.loc[month,'available_at'] if month in truth.index else None,sector_weight=weight,weight_calibration_n=len(history),price_asof=a.loc[month,'price_asof']))
 h=pd.DataFrame(hybrid);h.to_csv(D/'hybrid_forecasts.csv',index=False);f=pd.concat([f,h],ignore_index=True,sort=False);f.to_csv(D/'operational_forecasts.csv',index=False)
 valid=f[f.actual.notna()&(f.target_month<'2026-08')]
 rows=[]
 for (v,m),g in valid.groupby(['vintage','model']):rows.append(dict(vintage=v,model=m,**score(g,truth)))
 scores=pd.DataFrame(rows);scores.to_csv(O/'leaderboard.csv',index=False)
 final=valid[valid.vintage=='final'];sets=[set(g.target_month) for _,g in final.groupby('model')];common=set.intersection(*sets)
 paired=[]
 for m,g in final.groupby('model'):paired.append(dict(model=m,**score(g[g.target_month.isin(common)],truth)))
 paired=pd.DataFrame(paired).sort_values('rmse');paired.to_csv(O/'paired_final_scores.csv',index=False)
 # Original final refits retained to distinguish recalibration from new-price information.
 raw.to_csv(O/'separately_calibrated_final_challengers.csv',index=False)
 august=f[f.target_month=='2026-08'].copy();august['error']=august.forecast-.4;august.to_csv(O/'august_vintages.csv',index=False)
 year=f[(f.target_month>='2026-01')&(f.target_month<='2026-08')&(f.vintage=='final')]
 selected=['calendar_product_ridge','aligned_product_ridge','aligned_boosting','sectorfirst_survey_state','economic_ML_hybrid']
 year=year[year.model.isin(selected)].pivot(index='target_month',columns='model',values='forecast');year['Official_PPI']=truth.value.reindex(year.index);year.to_csv(O/'2026_cases.csv')
 regimes=[]
 for (v,m),g in valid.groupby(['vintage','model']):
  for label,z in [('before_2026',g[g.target_month<'2026-01']),('2026',g[g.target_month>='2026-01']),('without_April2026',g[g.target_month!='2026-04'])]:
   if len(z)>2:regimes.append(dict(vintage=v,model=m,regime=label,**score(z,truth)))
 pd.DataFrame(regimes).to_csv(O/'regime_sensitivity.csv',index=False)
 # Information state diagnostic, not weighted official PPI contributions.
 p=pd.read_csv(D/'product_features.csv');am=p[(p.month=='2026-08')&(p.vintage=='mid')&(p.scheme=='carry_25')].groupby('category_id').change.mean().rename('August_survey_proxy')
 sep=p[(p.month=='2026-09')&(p.vintage=='carry')&(p.scheme=='carry_25')].groupby('category_id').change.mean().rename('September_carry_proxy')
 signals=pd.concat([am,sep],axis=1);signals.to_csv(O/'august_september_state.csv')
 figs=[];fig,ax=plt.subplots(figsize=(12,4.8));actual=final.drop_duplicates('target_month').sort_values('target_month');ax.plot(pd.to_datetime(actual.target_month),actual.actual,'k-',lw=2,label='Official PPI')
 for m in ['calendar_product_ridge','aligned_product_ridge','sectorfirst_survey_state']:
  g=final[final.model==m].sort_values('target_month');ax.plot(pd.to_datetime(g.target_month),g.forecast,label=m)
 ax.legend(fontsize=9);ax.set_ylabel('MoM percent');ax.set_title('Operational final forecasts: calendar control, survey timing and sector-first');ax.grid(alpha=.15);figs.append(img(fig,'survey_forecast_history'))
 fig,ax=plt.subplots(figsize=(11,4.6));signals.plot.bar(ax=ax);ax.axhline(0,color='black',lw=.5);ax.set_ylabel('Price-proxy change percent');ax.set_title('Late August enters September: illustrative carry weight 25%');figs.append(img(fig,'august_september_signals'))
 live=pd.read_csv(D/'live_headline_forecasts.csv');ls=pd.read_csv(D/'live_sectorfirst_forecast.csv');live.to_csv(O/'september_headline_challengers.csv',index=False)
 b='<h1>China PPI: continuous survey-date nowcasting</h1>'
 b+='<p><strong>New baseline:</strong> exact-specification prices feed proxies for the 5th and 20th, sectors are forecast first, and historical effective sector weights aggregate their forecasts. Current days 21–end are excluded from the direct monthly proxy and become next-month carry-in. Calendar means remain economic-description and benchmark series.</p>'
 b+='<p><strong>What the results establish:</strong> timing correction improves the controlled product-regression comparison and produces an August mid-vintage aligned-ridge estimate of about +0.410%, using only price information available August 24. The sector-first baseline is lower, about +0.227%. Neither result is the user’s separately reported manual +0.4% forecast, and neither was actually issued before the outcome in this redevelopment exercise.</p>'
 b+='<h2>Official sampling versus estimated interpolation</h2><p><a href="https://www.stats.gov.cn/zs/tjws/tjzb/202301/t20230101_1903637.html">NBS confirms 5th/20th sampling</a>. Circulation survey observations are interval prices from a different transaction population, not point observations of factory-gate prices. The mapping remains an estimated proxy. Nearest, midpoint interpolation, learned carry weights and one-sided 20th-day extrapolation were compared without using current late-month prices.</p>'
 b+='<p>The 5th proxy uses carry weights 0, 25, 50 or 75% on the prior late-month level and the remainder on current early prices. The basic 20th proxy uses current mid prices; additional candidates project the early-to-mid movement forward toward the 20th. Timing and shrinkage/leaf parameters are chosen using chronological training folds. Early and carry forecasts persist the latest eligible level for not-yet-observed survey dates, explicitly flagged as estimated.</p>'
 b+='<h2>August vintages: late prices do not change August’s direct state</h2>'+tbl(august[august.model.isin(selected)][['vintage','model','forecast','error','price_asof','cutoff']].sort_values(['model','cutoff']))
 b+='<p>Operational final estimates retain the latest early/mid prediction when no target release has added information. The separate recalibrated-final challenger outputs are preserved in CSV, because changing historical calibration samples must not be described as information from late-August prices. The manual +0.4% call is user-reported and is not relabeled a model vintage.</p>'
 b+='<h2>Historical comparison on matching final-vintage months</h2><p>The table below uses the same '+str(len(common))+' months for every model, through July 2026; August remains a separate known-outcome diagnostic. Missing/cancelled releases and the minimum 36-month training rule explain differences from broader model-specific samples. These are retrospective redevelopment backtests, not a pristine holdout.</p>'+tbl(paired)+figs[0]
 b+='<h2>All vintage scores and sample sizes</h2><details><summary>Expand the complete leaderboard</summary>'+tbl(scores.sort_values(['vintage','rmse']))+'</details><p>Turning-point accuracy means correctly identifying a nonzero MoM sign crossing relative to the previous monthly PPI only when that previous value was already released. Precision/recall and event counts are included. Large moves are |PPI MoM| ≥0.5%. This is not a claim of early detection of every cyclical peak/trough.</p>'
 b+='<h2>2026 tests: April, May–June and August</h2>'+tbl(year.reset_index())+'<p>The May–June test is not automatically solved by timing alignment: residual sign errors remain in June for several models. April remains a substantial sector-first underprediction. The results do not establish that every apparent 2026 divergence disappears after alignment. Amplitude, pass-through, weights and omitted sectors still matter.</p>'
 b+='<h2>September carry-in</h2>'+figs[1]+tbl(signals.reset_index())+'<p>These category numbers illustrate the price state, not official sector weights or a headline forecast. September’s 5th/20th observations are not yet available in the retained price panel.</p>'
 b+='<h2>September estimates updated after the August PPI release</h2><p>Prices through September 4; target information through September 9. These updated estimates are separate from the September 4 frozen carry vintage.</p>'+tbl(ls)+tbl(live[['model','forecast','lower80','upper80','timing','n_train','price_asof','target_asof']])
 b+='<p>The interval columns use historical carry errors and are approximate for this post-PPI update; the short calibration history does not establish nominal coverage. The baseline/challenger spread is material and no ex-post winner is silently selected.</p>'
 b+='<h2>Sector mapping and changing composition</h2><p>Thirty industry forecasts feed nonnegative effective weights, constrained to sum to one and shrunk toward revenue weights released before the forecast cutoff. The source-revenue coverage is about 84.5% before normalization; these are reconstructed predictive weights, not official PPI weights. Products without current observations do not enter the sector forecast. New specifications can use an explicitly counted pooled sector coefficient prior; their price levels are never spliced to retired specifications. Unmapped downstream industries use labeled AR proxies.</p>'
 b+='<p>The seven January 2026 additions/removals and separate glass specifications are retained. A removed product stops contributing as soon as a newer permitted basket omits it. Reclassification is observation-dated. Weight fits roll over up to48 historical observations and annual revenue priors update only on publication; a separately identified 2026-rebase effect is not claimed from this short sample.</p>'
 b+='<h2>Limits and source separation</h2><p>Historical NBS pages retrieved now are not immutable first-release archives. Detailed consensus figures and the manual forecast retain user-supplied provenance unless independently verified. State-space/Kalman interpolation, external PMI/electronics inputs and comprehensive revision-vintage robustness remain outstanding. PPI prediction does not identify a domestic-demand boom or establish the property/non-property causal interpretation. Hosted GitHub execution remains undeployed.</p>'
 b+='<h2>Reproduce</h2><pre>python scripts/v4_timing.py\nOPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/v4_compare.py\npython scripts/v4_sector.py\npython scripts/v4_live.py\npython scripts/v4_live_sector.py\npython scripts/v4_publish.py</pre><p>The package includes source checks, per-product continuous proxies, all forecast rows, estimated industry weights/contributions, live fitted headline challengers and tests proving late-month exclusion and next-month carry effects.</p>'
 (O/'China_PPI_Survey_Aligned.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Survey-aligned China PPI</title><style>body{max-width:1240px;margin:38px auto;padding:0 24px;font:16px/1.6 system-ui;color:#173743}h1{font-size:34px}h2{margin-top:38px}table{display:block;overflow:auto;border-collapse:collapse;font-size:12px}td,th{padding:7px 9px;border-bottom:1px solid #dce5e8;text-align:right}th{background:#edf4f5}img{width:100%}pre{padding:16px;background:#edf4f5;overflow:auto}summary{cursor:pointer;font-weight:600}</style>'+b+'</html>')
 (O/'validation.json').write_text(json.dumps(dict(historical_primary_months=sorted(common),forecast_rows=len(f),inputs={str(x.relative_to(R)):hashlib.sha256(x.read_bytes()).hexdigest() for x in [D/'product_features.csv',D/'comparison_forecasts.csv',D/'sectorfirst_forecasts.csv']}),indent=2))
 print(paired[['model','n','correlation','rmse']].to_string(index=False))
if __name__=='__main__':main()

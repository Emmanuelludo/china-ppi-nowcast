"""Transparent redevelopment report: distinguishes August diagnostic from history."""
from pathlib import Path
import base64,json,hashlib
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];O=R/'reports/v3'
def table(x):return x.to_html(index=False,border=0,float_format=lambda x:f'{x:.3f}')
def figure(fig,name):
 p=O/(name+'.png');fig.savefig(p,dpi=150,bbox_inches='tight');plt.close(fig)
 return '<img src="data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()+'" alt="'+name+'">'
def main():
 O.mkdir(exist_ok=True,parents=True)
 f=pd.read_csv(R/'data/v3/forecasts.csv');s=pd.read_csv(R/'data/v3/leaderboard.csv')
 old=pd.read_csv(R/'data/v2/models/leaderboard.csv');old=old[(old.target_id=='headline_ppi_mom')&(old.window=='expanding')].copy();old.model='v2_'+old.model
 cols=['vintage','model','n','correlation','rmse','mae','bias','directional_accuracy']
 combined=pd.concat([s[cols],old[cols]],ignore_index=True);combined.to_csv(O/'all_model_scores.csv',index=False)
 final=combined[combined.vintage=='final'].sort_values('rmse')
 aug=f[(f.target_month=='2026-08')&(f.vintage=='final')][['model','forecast']].copy();aug['actual']=.4;aug['error']=aug.forecast-.4
 aug.to_csv(O/'august_comparison.csv',index=False)
 valid=f.dropna(subset=['actual']);assert not valid.duplicated(['target_id','target_month','vintage','model']).any()
 assert (pd.to_datetime(valid.cutoff,utc=True)<pd.to_datetime(valid.actual_available_at,utc=True)).all()
 # No retrospective promotion. Plot named structural and tree comparisons.
 fig,ax=plt.subplots(figsize=(12,4.8));actual=valid.drop_duplicates('target_month').sort_values('target_month')
 ax.plot(pd.to_datetime(actual.target_month),actual.actual,'k-',lw=2,label='Official PPI')
 for m in ['category_distributed_positive','family_average_ar','family_forest']:
  g=valid[(valid.vintage=='final')&(valid.model==m)].sort_values('target_month');ax.plot(pd.to_datetime(g.target_month),g.forecast,label=m)
 ax.axhline(0,color='#888',lw=.5);ax.set_ylabel('MoM percent');ax.legend(fontsize=9);ax.set_title('Forecast histories: delayed pass-through and tree models');ax.grid(alpha=.15)
 hist=figure(fig,'revised_forecast_history')
 fig,ax=plt.subplots(figsize=(10,5));ax.barh(aug.model,aug.forecast,color='#287d8e');ax.axvline(.4,color='black',ls='--',label='August official +0.4%');ax.set_xlabel('August reconstructed forecast, MoM percent');ax.legend();augfig=figure(fig,'august_models')
 raw=pd.read_csv(R/'data/v2/products/product_vintage_features.csv');a=raw[(raw.month=='2026-08')&(raw.vintage=='final')]
 signal=a.groupby('category_id')[['mom_average','mom_end','mom_sampling_5th_20th']].mean().reset_index();signal.to_csv(O/'august_category_signals.csv',index=False)
 dated=pd.read_csv(R/'data/v3/ten_day_category_indices.csv',index_col=0);dated.index=pd.to_datetime(dated.index)
 fig,ax=plt.subplots(figsize=(12,4.5))
 for col in ['CAT_coal','CAT_petroleum_gas','CAT_chemicals','CAT_nonferrous_metals']:
  x=dated.loc['2026-06':,col];ax.plot(x.index,100*x/x.iloc[0],label=col.replace('CAT_',''))
 ax.legend();ax.set_title('Ten-day reported-change chain indices, rebased at first June observation');ax.set_ylabel('Index');ax.grid(alpha=.15);idxfig=figure(fig,'ten_day_indices')
 b='<h1>China PPI: revising the assumptions and testing trees</h1>'
 b+='<p><strong>Finding:</strong> August inputs were positive. The old category bridge subtracted about 0.302 percentage points through lagged July PPI. A direct audit found no August price/sign parsing error. The feature and lag architecture—not a lack of price information—was a material problem.</p>'
 b+='<p><strong>Evaluation status:</strong> 22 early-vintage and 23 mid/final historical months, September 2024–July 2026, following 36 training months. August was already known during redevelopment and is shown separately. Chronological folds prevent within-run label leakage, but these results are not a pristine holdout after repeated model development.</p>'
 b+='<p><strong>New result:</strong> the positive distributed-lag category model reaches 0.917 historical MoM correlation (23 months), compared with 0.732 for v2 product ridge. Its RMSE is 0.290 pp, however, versus 0.261 pp for v2 category bridge. Its August estimate is +0.089%, while the random forest gives +0.372% but performs substantially worse historically. Meeting a correlation threshold does not eliminate magnitude errors or establish live performance.</p>'
 b+='<h2>What changed</h2><ul><li>One monthly return per product/family instead of hundreds of overlapping transformations; monthly average, endpoint and day-weighted alternatives tested separately.</li><li>Contemporaneous price effects separated from target autoregression. Positive-coefficient bridges test economically plausible pass-through without forcing the headline forecast itself to be positive.</li><li>Current and lagged category price changes model delayed pass-through explicitly.</li><li>Random forests and histogram gradient boosting consume missing values directly. Stable family features allow new specifications to contribute; exact-specification trees provide a separate comparison. Missing values are not zero price changes.</li><li>The proposed 5th/20th proxy is excluded from v3. It is an imperfect subset of window averages and suppresses August late acceleration.</li></ul>'
 b+='<h2>August price signals</h2>'+table(signal)+'<p>Monthly-average breadth: 24/50 products rose; latest ten-day breadth: 34/50. Strong energy/metals signals do not imply every product increased or prove stronger domestic demand.</p>'+idxfig
 b+='<h2>Why the old bridge suppressed August</h2><p>The category bridge had approximately +0.352 pp from current prices, −0.302 pp from lagged PPI, and −0.028 pp intercept: +0.022% in total. Simply deleting a lag is not universally correct: it must be distinguished from the delayed pass-through of input prices themselves.</p>'
 b+='<h2>Historical model comparison</h2><p>All final-vintage models share the same 23 target months. RMSE/MAE are percentage points. The full table includes unsuccessful candidates and v2 controls.</p>'+table(final)+hist
 stress=valid[(valid.vintage=='final')&(valid.model=='category_distributed_positive')]
 regimes=[]
 for label,g in [('full',stress),('pre_2026',stress[stress.target_month<'2026-01']),('2026_Jan_Jul',stress[stress.target_month>='2026-01']),('excluding_April_2026_sensitivity',stress[stress.target_month!='2026-04'])]:
  regimes.append(dict(sample=label,n=len(g),correlation=g.forecast.corr(g.actual),rmse=np.sqrt(np.mean((g.forecast-g.actual)**2))))
 regime=pd.DataFrame(regimes);regime.to_csv(O/'regime_sensitivity.csv',index=False)
 b+='<h2>Does the 0.917 correlation hold across regimes?</h2><p>The April 2026 spike is influential: excluding it as a sensitivity check reduces correlation to 0.866. The full sample remains the primary comparison. The pre-2026 and 2026 subsamples are very small, so the 0.90 threshold is not established as stable across regimes.</p>'+table(regime)
 b+='<h2>August known-outcome diagnostic</h2><p>Each estimate uses the September 4 information cutoff and excludes August PPI from training. Model specifications were nevertheless developed after the outcome was known. A close August fit alone is not grounds for model selection. <a href="https://www.stats.gov.cn/sj/zxfb/202609/t20260909_1965262.html">NBS published +0.4% MoM</a>.</p>'+table(aug)+augfig
 b+='<h2>Early, mid and final comparisons</h2>'+table(s[cols].sort_values(['model','vintage']))
 b+='<h2>Changing product composition</h2><p>Exact product IDs and historical observations remain intact. Family features average valid own-specification returns; they never divide the new specification price by the old specification price. Native-missing trees learn how to route absent predictors, but cannot learn a new product’s coefficient without history. Stable family/category inputs provide its initial contribution. Observation-level dated category mappings are exported; industry output/revenue composition remains a separate economic-weighting problem.</p>'
 b+='<h2>Published ten-day indices and research</h2><p><a href="https://pdf.dfcfw.com/pdf/H3_AP202503021643653709_1.pdf">Guosen Securities’ March 2025 report</a> constructs ten-day category indices from this NBS survey and combines category changes for PPI tracking. That establishes that this approach exists; it does not establish a 0.90 out-of-sample MoM correlation. <a href="https://www.zhiyanbao.cn/index/partFile/1/eastmoney/2022-03/1_39291.pdf">Huaan Securities’ March 2022 machine-learning report</a> uses monthly average product prices transformed into YoY features and excludes short product histories. High correlations from that design cannot be compared directly with our MoM and discontinued-product requirements. <a href="https://scikit-learn.org/stable/modules/ensemble.html#histogram-based-gradient-boosting">Scikit-learn documents native missing-value routing</a> for histogram boosting.</p>'
 b+='<h2>Limitations and acceptance</h2><p>No model is silently promoted by its August error or best full-period score. The original 0.90 MoM target remains an empirical acceptance criterion, not a promised result. Trees cannot reliably extrapolate beyond historical target ranges; 59 training months provide limited examples of commodity shocks. Published-change chain indices are approximate after missing comparator periods and are separate from actual observed-level changes. Historical pages are current retrieved snapshots, not certified immutable first releases. Scheduled GitHub execution is still not deployed.</p>'
 b+='<h2>Reproduce</h2><pre>OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/v3_experiments.py\npython scripts/v3_publish.py\nPYTHONPATH=src python -m pytest -q</pre><p>CSV outputs include every forecast, cutoff, selected penalty/leaf size and sample count. August linear contributions and zero-return sensitivities are supplied separately; tree sensitivities are not additive or causal contributions.</p>'
 (O/'China_PPI_Model_Revision.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>China PPI model revision</title><style>body{max-width:1160px;margin:36px auto;padding:0 24px;font:16px/1.6 system-ui;color:#173440}h1{font-size:32px}h2{margin-top:38px}table{display:block;overflow:auto;border-collapse:collapse;font-size:13px}td,th{padding:7px 9px;border-bottom:1px solid #dde6e9;text-align:right}th{background:#edf4f5}img{width:100%}pre{background:#edf4f5;padding:16px;overflow:auto}</style>'+b+'</html>')
 (O/'validation.json').write_text(json.dumps(dict(historical_forecasts=len(valid),models=s.model.nunique(),duplicate_check='passed',release_cutoff_check='passed',august_excluded_from_training=True,inputs={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [R/'data/v3/forecasts.csv',R/'data/v3/leaderboard.csv']}),indent=2))
 print(final[['model','correlation','rmse']].to_string(index=False))
if __name__=='__main__':main()

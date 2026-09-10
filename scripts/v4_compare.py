"""Survey-aligned headline challengers; nested time-only timing/model selection.
Calendar means are comparison controls, never mixed into survey features.
"""
from pathlib import Path
import json,warnings,argparse
import numpy as np,pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor,HistGradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit
R=Path(__file__).resolve().parents[1];O=R/'data/v4'
warnings.filterwarnings('ignore',category=RuntimeWarning)
TIMINGS=['carry_0','carry_25','carry_50','carry_75']
MODELS={
 'calendar_product_ridge':('product','ridge',['calendar']),
 'nearest_product_ridge':('product','ridge',['nearest']),
 'day_interpolated_ridge':('product','ridge',['continuous_days']),
 'aligned_product_ridge':('product','ridge',TIMINGS),
 'equal_return_benchmark':('equal','ridge',TIMINGS),
 'breadth_benchmark':('breadth','ridge',TIMINGS),
 'aligned_sector_factor':('category','positive',TIMINGS),
 'aligned_random_forest':('product','forest',TIMINGS),
 'aligned_boosting':('product','boost',TIMINGS),
 'point_extrapolated_ridge':('product','ridge',['linear_points']),
 'learned_points_ridge':('product','ridge',TIMINGS+['linear_points','endpoint_25','endpoint_50']),
 'learned_points_boosting':('product','boost',TIMINGS+['linear_points','endpoint_25','endpoint_50']),
}
def targets():
 t=pd.concat([pd.read_csv(R/'data/v2/targets/sector_targets_long.csv'),pd.read_csv(R/'data/v2/post_release/august2026_targets.csv')],ignore_index=True)
 t['month']=pd.PeriodIndex(t.month,freq='M');t['available_at']=pd.to_datetime(t.available_at,utc=True)
 return t.sort_values('available_at').drop_duplicates(['month','target_id'])
class Estimator:
 def __init__(self,kind,param):self.kind=kind;self.param=param
 def fit(self,X,y):
  self.cols=X.columns[(X.notna().sum()>=12)&(X.std()>1e-10)]
  if not len(self.cols):raise ValueError('No eligible predictors')
  a=X[self.cols]
  if self.kind in ['forest','boost']:
   self.est=RandomForestRegressor(n_estimators=70,max_features=.7,min_samples_leaf=int(self.param),random_state=137,n_jobs=1) if self.kind=='forest' else HistGradientBoostingRegressor(max_iter=80,max_leaf_nodes=3,min_samples_leaf=int(self.param),l2_regularization=2,early_stopping=False,random_state=137)
   self.est.fit(a,y)
  else:
   # Explicit masked design: absent prices contribute no price term; separate
   # observation indicators distinguish absence from a measured zero change.
   self.scaler=StandardScaler().fit(self.design(a))
   self.est=Ridge(alpha=self.param,positive=self.kind=='positive').fit(self.scaler.transform(self.design(a)),y)
  return self
 @staticmethod
 def design(a):return np.concatenate([a.fillna(0).to_numpy(),a.notna().to_numpy(dtype=float)],axis=1)
 def predict(self,X):
  a=X[self.cols]
  return self.est.predict(a if self.kind in ['forest','boost'] else self.scaler.transform(self.design(a)))
def matrix(p,level,calendar):
 if level=='category':x=p.pivot_table(index='month',columns='category_id',values='change',aggfunc='mean')
 else:
  x=p.pivot_table(index='month',columns='exact_product_id',values='change',aggfunc='mean')
  if level=='equal':x=x.mean(axis=1).to_frame('mean_return')
  elif level=='breadth':x=(((x>0).sum(axis=1)-(x<0).sum(axis=1))/x.notna().sum(axis=1)).to_frame('diffusion')
 return x.reindex(calendar)
def select(matrices,y,months,kind):
 params=[3,6] if kind in ['forest','boost'] else [1.,10.,100.]
 best=None
 for timing,X in matrices.items():
  a=X.loc[months]
  for param in params:
   errors=[]
   for tr,va in TimeSeriesSplit(n_splits=3,test_size=3,gap=1).split(a):
    try:model=Estimator(kind,param).fit(a.iloc[tr],y.reindex(months).iloc[tr]);errors.extend((model.predict(a.iloc[va])-y.reindex(months).iloc[va].to_numpy())**2)
    except ValueError:continue
   loss=np.mean(errors) if errors else np.inf
   if best is None or loss<best[0]:best=(loss,timing,param)
 if best is None or not np.isfinite(best[0]):raise ValueError('No valid inner folds')
 _,timing,param=best
 return Estimator(kind,param).fit(matrices[timing].loc[months],y.loc[months]),timing,param,best[0]
def run(selected=None,resume=False):
 p=pd.read_csv(O/'product_features.csv');p['month']=pd.PeriodIndex(p.month,freq='M')
 cut=pd.read_csv(O/'cutoffs.csv');cut['month']=pd.PeriodIndex(cut.month,freq='M');cut['cutoff']=pd.to_datetime(cut.cutoff,utc=True)
 t=targets();t=t[t.target_id=='headline_ppi_mom'].set_index('month')
 months=pd.period_range(p.month.min(),p.month.max(),freq='M');y=t.value.reindex(months)
 rows=pd.read_csv(O/'comparison_forecasts.csv').to_dict('records') if resume else []
 done={(r['vintage'],r['model'],r['target_month']) for r in rows}
 for vintage in ['carry','early','mid','final']:
  c=cut[cut.vintage==vintage].set_index('month').cutoff
  cache={}
  for name,(level,kind,schemes) in MODELS.items():
   if selected and name not in selected:continue
   for scheme in schemes:
    key=(level,scheme)
    if key not in cache:cache[key]=matrix(p[(p.vintage==vintage)&(p.scheme==scheme)],level,months)
   inputs={s:cache[level,s] for s in schemes}
   for month,cutoff in c.items():
    if (vintage,name,str(month)) in done:continue
    if month in t.index and cutoff>=t.loc[month,'available_at']:continue
    train=months[(months<month)&y.notna()];train=train[t.available_at.reindex(train)<cutoff]
    if len(train)<36:continue
    model,timing,param,cv=select(inputs,y,train,kind)
    pred=float(model.predict(inputs[timing].loc[[month]])[0]);actual=y.get(month,np.nan)
    past=[r['actual']-r['forecast'] for r in rows if r['vintage']==vintage and r['model']==name and pd.notna(r['actual']) and pd.Timestamp(r['actual_available_at'])<cutoff]
    lo,hi=pred+np.quantile(past,[.1,.9]) if len(past)>=12 else (np.nan,np.nan)
    rows.append(dict(target_month=str(month),vintage=vintage,model=name,forecast=pred,actual=actual,cutoff=cutoff.isoformat(),actual_available_at=t.loc[month,'available_at'].isoformat() if month in t.index else None,timing=timing,parameter=param,inner_mse=cv,n_train=len(train),n_features=len(model.cols),lower80=lo,upper80=hi,interval_n=len(past),evaluation='known_August_diagnostic' if str(month)=='2026-08' else 'carry_nowcast' if pd.isna(actual) else 'historical_redevelopment'))
   print(vintage,name,'complete',flush=True);pd.DataFrame(rows).to_csv(O/'comparison_forecasts.csv',index=False)
 (O/'comparison_design.json').write_text(json.dumps(dict(models=MODELS,min_train=36,validation='3 chronological folds, 3 months each, one-month gap; timing and penalty selected inside each fold sequence',missingness='Linear masked price terms plus explicit observed indicators; trees consume NaNs; new/untrained predictors excluded; no raw level filling',status='Retrospective redevelopment; no untouched holdout claim'),indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--models',nargs='+');a.add_argument('--resume',action='store_true');args=a.parse_args();run(args.models,args.resume)

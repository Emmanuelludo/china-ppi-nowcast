"""Controlled v3 feature/model ablations. August is a known-outcome diagnostic.
Outer forecasts use prior released labels only; nested tuning is chronological.
"""
from pathlib import Path
import argparse,json,warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor,HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from v3_features import build
R=Path(__file__).resolve().parents[1]
warnings.filterwarnings('ignore',category=RuntimeWarning)

class Model:
 def __init__(self,kind,parameter):self.kind=kind;self.parameter=parameter
 def fit(self,X,y):
  self.cols=X.columns[(X.notna().sum()>=12)&(X.std()>1e-10)]
  if not len(self.cols):raise ValueError('No eligible predictors')
  a=X[self.cols]
  if self.kind in ['forest','boost']:
   self.est=RandomForestRegressor(n_estimators=100,min_samples_leaf=self.parameter,max_features=.7,random_state=137,n_jobs=1) if self.kind=='forest' else HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=3,min_samples_leaf=self.parameter,learning_rate=.05,l2_regularization=2,early_stopping=False,random_state=137)
   self.est.fit(a,y)
  else:
   self.median=a.median();self.scaler=StandardScaler().fit(a.fillna(self.median))
   self.est=Ridge(alpha=self.parameter,positive=self.kind=='positive').fit(self.scaler.transform(a.fillna(self.median)),y)
  return self
 def predict(self,X):
  a=X[self.cols]
  if self.kind not in ['forest','boost']:a=self.scaler.transform(a.fillna(self.median))
  return self.est.predict(a)

def tuned(X,y,kind):
 grid=[3,6] if kind in ['forest','boost'] else [1.,10.,100.]
 errors=[]
 for param in grid:
  e=[]
  for tr,va in TimeSeriesSplit(n_splits=3,test_size=3,gap=1).split(X):
   m=Model(kind,param).fit(X.iloc[tr],y.iloc[tr]);e.extend((m.predict(X.iloc[va])-y.iloc[va].to_numpy())**2)
  errors.append(np.mean(e))
 param=grid[int(np.argmin(errors))];return Model(kind,param).fit(X,y),param

# Fixed before examining v3 results. No tuning to August.
SPECS={
 'family_average':('mom_average_product_family_id','ridge',False),
 'family_average_ar':('mom_average_product_family_id','ridge',True),
 'family_end':('mom_end_product_family_id','ridge',False),
 'family_days':('mom_day_weighted_product_family_id','ridge',False),
 'category_positive':('mom_average_category_id','positive',False),
 'chain_category_positive':('chain_category','positive',False),
 'family_positive':('mom_average_product_family_id','positive',False),
 'family_forest':('mom_average_product_family_id','forest',False),
 'family_boost':('mom_average_product_family_id','boost',False),
 'exact_boost':('mom_average_exact_product_id','boost',False),
 'category_distributed_positive':('distributed_category','positive',False),
 'category_distributed_ridge':('distributed_category','ridge',False),
 'category_distributed_boost':('distributed_category','boost',False),
}

def run(targets=None,vintages=None,models=None,resume=False):
 matrices=build();t=pd.read_csv(R/'data/v2/targets/sector_targets_long.csv')
 t['month']=pd.PeriodIndex(t.month,freq='M');t['available_at']=pd.to_datetime(t.available_at,utc=True)
 rows=[];audit=[];signals=[]
 if resume:
  for path,destination in [('forecasts.csv',rows),('august_linear_attribution.csv',audit),('august_zero_return_sensitivity.csv',signals)]:
   destination.extend(pd.read_csv(R/'data/v3'/path).to_dict('records'))
 done={(r['target_id'],r['vintage'],r['model'],r['target_month']) for r in rows}
 selected=targets or ['headline_ppi_mom']
 for target in selected:
  tt=t[t.target_id==target].sort_values('available_at').drop_duplicates('month').set_index('month')
  for vintage,(blocks,cutoffs) in matrices.items():
   if vintages and vintage not in vintages:continue
   for name,(block,kind,ar) in SPECS.items():
    if models and name not in models:continue
    if block=='distributed_category':
     cats=blocks['mom_average_category_id'];blocks[block]=pd.concat([cats,cats.shift(1).add_prefix('lag1::')],axis=1)
    X=blocks[block].copy();y=tt.value.reindex(X.index)
    if ar:
     X['ppi_lag1']=y.shift(1)
     for month in X.index:
      prev=month-1
      if prev not in tt.index or month not in cutoffs or pd.isna(cutoffs.get(month)) or tt.loc[prev,'available_at']>=cutoffs[month]:X.loc[month,'ppi_lag1']=np.nan
    for month in X.index:
     if (target,vintage,name,str(month)) in done:continue
     cutoff=cutoffs.get(month)
     if pd.isna(cutoff):continue
     if month in tt.index and cutoff>=tt.loc[month,'available_at']:continue
     tr=X.index[(X.index<month)&y.notna()]
     tr=tr[tt.available_at.reindex(tr)<cutoff]
     if len(tr)<36:continue
     model,param=tuned(X.loc[tr],y.loc[tr],kind)
     pred=float(model.predict(X.loc[[month]])[0]);actual=y.get(month,np.nan)
     rows.append(dict(target_id=target,target_month=str(month),vintage=vintage,model=name,forecast=pred,actual=actual,cutoff=cutoff.isoformat(),actual_available_at=tt.loc[month,'available_at'].isoformat() if month in tt.index else None,n_train=len(tr),n_features=len(model.cols),parameter=param))
     if str(month)=='2026-08':
      if kind not in ['boost','forest']:
       beta=model.est.coef_/model.scaler.scale_;values=X.loc[month,model.cols].fillna(model.median)
       intercept=float(model.est.intercept_-model.scaler.mean_@beta)
       for feature,b,v in zip(model.cols,beta,values):audit.append(dict(target_id=target,vintage=vintage,model=name,feature=feature,coefficient=b,value=v,contribution=b*v))
       audit.append(dict(target_id=target,vintage=vintage,model=name,feature='intercept',coefficient=np.nan,value=1.,contribution=intercept))
      # Conditional historical sensitivities, not causal attribution. Same fit.
      for feature in model.cols:
       if feature=='ppi_lag1':continue
       z=X.loc[[month]].copy();z[feature]=0.
       signals.append(dict(target_id=target,vintage=vintage,model=name,feature=feature,prediction_minus_zero_return=float(pred-model.predict(z)[0])))
    print(target,vintage,name,'complete',flush=True)
    pd.DataFrame(rows).to_csv(R/'data/v3/forecasts.csv',index=False)
    pd.DataFrame(audit).to_csv(R/'data/v3/august_linear_attribution.csv',index=False)
    pd.DataFrame(signals).to_csv(R/'data/v3/august_zero_return_sensitivity.csv',index=False)
 f=pd.DataFrame(rows);valid=f.dropna(subset=['actual']);metrics=[]
 for keys,g in valid.groupby(['target_id','vintage','model']):
  e=g.forecast-g.actual
  metrics.append(dict(zip(['target_id','vintage','model'],keys))|dict(n=len(g),correlation=g.forecast.corr(g.actual),rmse=np.sqrt(np.mean(e**2)),mae=np.mean(abs(e)),bias=e.mean(),directional_accuracy=np.mean(np.sign(g.forecast)==np.sign(g.actual))))
 pd.DataFrame(metrics).to_csv(R/'data/v3/leaderboard.csv',index=False)
 (R/'data/v3/design.json').write_text(json.dumps(dict(specifications=SPECS,min_train=36,inner_folds=3,validation_months=3,gap=1,seed=137,warning='V3 developed after August outcome and prior test results were known. All historical metrics are retrospective redevelopment evidence; no pristine held-out model-selection claim.'),indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--targets',nargs='+');p.add_argument('--vintages',nargs='+');p.add_argument('--models',nargs='+');p.add_argument('--resume',action='store_true');a=p.parse_args();run(a.targets,a.vintages,a.models,a.resume)

"""Persist the exact final-vintage fitted estimators and their forecast inputs."""
from pathlib import Path
import json
import numpy as np,pandas as pd,joblib
from v3_features import build
from v3_experiments import Model,SPECS
R=Path(__file__).resolve().parents[1]
def main():
 blocks,cutoffs=build()['final'];cats=blocks['mom_average_category_id'];blocks['distributed_category']=pd.concat([cats,cats.shift(1).add_prefix('lag1::')],axis=1)
 t=pd.read_csv(R/'data/v2/targets/sector_targets_long.csv');t=t[t.target_id=='headline_ppi_mom'].sort_values('available_at').drop_duplicates('month');t['month']=pd.PeriodIndex(t.month,freq='M');t=t.set_index('month');t['available_at']=pd.to_datetime(t.available_at,utc=True)
 f=pd.read_csv(R/'data/v3/forecasts.csv');current=f[(f.vintage=='final')&f.actual.isna()]
 out=R/'data/v3/fitted';out.mkdir(exist_ok=True)
 for _,row in current.iterrows():
  block,kind,ar=SPECS[row.model];X=blocks[block].copy();y=t.value.reindex(X.index);month=pd.Period(row.target_month,'M');cutoff=pd.Timestamp(row.cutoff)
  if ar:
   X['ppi_lag1']=y.shift(1)
   for m in X.index:
    prior=m-1
    if prior not in t.index or pd.isna(cutoffs.get(m)) or t.loc[prior,'available_at']>=cutoffs[m]:X.loc[m,'ppi_lag1']=np.nan
  tr=X.index[(X.index<month)&y.notna()];tr=tr[t.available_at.reindex(tr)<cutoff]
  param=int(row.parameter) if kind in ['forest','boost'] else float(row.parameter)
  model=Model(kind,param).fit(X.loc[tr],y.loc[tr]);pred=float(model.predict(X.loc[[month]])[0]);assert np.isclose(pred,row.forecast,atol=1e-9)
  bundle=dict(model=row.model,estimator=model.est,columns=list(model.cols),scaler=getattr(model,'scaler',None),median=getattr(model,'median',None),cutoff=row.cutoff,target_month=str(month),forecast=pred)
  joblib.dump(bundle,out/(row.model+'.joblib'),compress=3)
  X.loc[[month],model.cols].to_csv(out/(row.model+'_inputs.csv'),index_label='month')
  (out/(row.model+'_metadata.json')).write_text(json.dumps({k:v for k,v in bundle.items() if k not in ['estimator','scaler','median']},indent=2))
 print('Saved and prediction-verified',len(current),'final-vintage fitted estimators')
if __name__=='__main__':main()

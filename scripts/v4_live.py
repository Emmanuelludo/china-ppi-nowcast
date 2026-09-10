"""Update the next-month carry state after the latest released PPI information."""
from pathlib import Path
import pandas as pd,numpy as np,json,joblib
from v4_compare import targets,matrix,select,MODELS
R=Path(__file__).resolve().parents[1];O=R/'data/v4'
def run():
 p=pd.read_csv(O/'product_features.csv');p['month']=pd.PeriodIndex(p.month,freq='M');p['cutoff']=pd.to_datetime(p.cutoff,utc=True)
 month=p[p.vintage=='carry'].month.max();price_asof=p[(p.month==month)&(p.vintage=='carry')].cutoff.max()
 t=targets();t=t[t.target_id=='headline_ppi_mom'].set_index('month');latest=t.available_at.max();cutoff=max(price_asof,latest)+pd.Timedelta(nanoseconds=1)
 calendar=pd.period_range(p.month.min(),p.month.max(),freq='M');y=t.value.reindex(calendar)
 train=calendar[(calendar<month)&y.notna()];train=train[t.available_at.reindex(train)<cutoff]
 history=pd.read_csv(O/'comparison_forecasts.csv');rows=[];folder=O/'fitted';folder.mkdir(exist_ok=True)
 for name in ['aligned_product_ridge','aligned_boosting','learned_points_ridge','aligned_sector_factor']:
  level,kind,schemes=MODELS[name]
  inputs={s:matrix(p[(p.vintage=='carry')&(p.scheme==s)],level,calendar) for s in schemes}
  model,scheme,param,cv=select(inputs,y,train,kind);X=inputs[scheme].loc[[month]];pred=float(model.predict(X)[0])
  h=history[(history.vintage=='carry')&(history.model==name)&history.actual.notna()];h=h[pd.to_datetime(h.actual_available_at,utc=True)<cutoff]
  lo,hi=pred+np.quantile(h.actual-h.forecast,[.1,.9]) if len(h)>=12 else (np.nan,np.nan)
  rows.append(dict(target_month=str(month),model=name,forecast=pred,lower80=lo,upper80=hi,price_asof=price_asof.isoformat(),target_asof=latest.isoformat(),cutoff=cutoff.isoformat(),timing=scheme,parameter=param,n_train=len(train),interval_n=len(h),interval_note='historical carry residuals; approximate for post-PPI update'))
  joblib.dump(dict(estimator=model.est,scaler=getattr(model,'scaler',None),columns=list(model.cols),kind=kind,masked_linear_design='concat(price.where(observed,0),observed)' if kind not in ['boost','forest'] else None,forecast=pred,cutoff=cutoff.isoformat(),target_month=str(month),scheme=scheme),folder/(name+'.joblib'),compress=3)
  X[model.cols].to_csv(folder/(name+'_inputs.csv'),index_label='month')
 pd.DataFrame(rows).to_csv(O/'live_headline_forecasts.csv',index=False);print(pd.DataFrame(rows).to_string(index=False))
if __name__=='__main__':run()

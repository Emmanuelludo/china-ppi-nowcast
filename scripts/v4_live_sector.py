"""Update September carry state for newly released August labels; preserve history."""
import numpy as np
import pandas as pd
from v4_sector import ROOT, OUT, MAP, SCHEMES, choose_scheme, product_prediction, ar_forecast, effective_weights

def run():
    p=pd.read_csv(OUT/'product_features.csv');p['cutoff']=pd.to_datetime(p.cutoff,utc=True)
    t=pd.concat([pd.read_csv(ROOT/'data/v2/targets/sector_targets_long.csv'),pd.read_csv(ROOT/'data/v2/post_release/august2026_targets.csv')],ignore_index=True)
    t=t[t.transformation.eq('mom')].copy();t['available_at']=pd.to_datetime(t.available_at,utc=True);t=t.sort_values('available_at').drop_duplicates(['month','target_id'])
    target_asof=t.available_at.max();cutoff=target_asof+pd.Timedelta(1,'ns')
    vals=t.pivot(index='month',columns='target_id',values='value');avail=t.pivot(index='month',columns='target_id',values='available_at')
    pp=p[p.vintage.eq('carry')&p.cutoff.lt(cutoff)];month=pp.month.max();price_asof=pp.loc[pp.month.eq(month),'cutoff'].max()
    panels={s:q.pivot(index='month',columns='exact_product_id',values='change') for s,q in pp[pp.scheme.isin(SCHEMES)].groupby('scheme')}
    mapping=pp.drop_duplicates('exact_product_id').set_index('exact_product_id').ppi_industry_id
    eligible=vals.index[(vals.index<month)&(avail.headline_ppi_mom<cutoff)&vals.headline_ppi_mom.notna()];train=eligible.intersection(panels['carry_25'].index)
    if len(train)<36:raise RuntimeError('Not enough dated training months')
    scheme,scores=choose_scheme(panels,train,vals.means_ppi_mom);X=panels[scheme];now=X.loc[month]
    names=t[t.component_type.eq('industry')].drop_duplicates('target_id').set_index('target_id').target_name_zh.to_dict()
    common=dict(month=month,vintage='carry_after_target_release',cutoff=cutoff,data_price_asof=price_asof,target_asof=target_asof,scheme=scheme)
    rows=[];preds={}
    for target,name in names.items():
        ids=[c for c in X if mapping.get(c) in MAP.get(name,[])]
        y=vals[target].reindex(train).where(avail[target].reindex(train)<cutoff)
        if y.notna().sum()<36:continue
        forecast,n,new=product_prediction(X.reindex(train)[ids],y,now) if ids else (np.nan,0,0)
        method='product_positive_pass_through'
        if not np.isfinite(forecast):forecast=ar_forecast(y,month);method='AR1_unmapped_or_unavailable'
        preds[target]=forecast
        rows.append(dict(common,target_id=target,industry=name,forecast=forecast,n_train=int(y.notna().sum()),n_active_products=n,n_new_prior_products=new,method=method,train_last_month=y.dropna().index.max(),training_max_release=avail[target].reindex(train)[y.notna()].max()))
    wt=train[-48:];A=vals.reindex(wt)[list(preds)].where(avail.reindex(wt)[list(preds)]<cutoff);good=A.columns[A.notna().all()];A=A[good]
    w=pd.read_csv(ROOT/'data/v2/weights/industry_revenue_weights.csv');w['available_at']=pd.to_datetime(w.available_at,utc=True);dated=w[w.available_at<cutoff];latest=dated[dated.available_at.eq(dated.available_at.max())].set_index('industry_name')
    prior=np.array([latest.economic_weight.get(names[g],0) for g in good],float) if len(latest) else np.ones(len(good))
    if prior.sum()==0:prior=np.ones(len(good))
    coverage=prior.sum() if len(latest) else np.nan
    ww,intercept=effective_weights(A,vals.loc[wt,'headline_ppi_mom'],prior)
    forecast=intercept+sum(ww[i]*preds[g] for i,g in enumerate(good))
    pd.DataFrame([dict(common,model='sectorfirst_effective_weights',forecast=forecast,intercept=intercept,n_train=len(train),weight_train_n=len(wt),n_sectors=len(good),revenue_coverage=coverage)]).to_csv(OUT/'live_sectorfirst_forecast.csv',index=False)
    pd.DataFrame([dict(common,target_id=g,industry=names[g],effective_weight=ww[i],revenue_prior=prior[i]/prior.sum(),sector_forecast=preds[g],contribution=ww[i]*preds[g],weight_source_available_at=latest.available_at.max(),weight_type='estimated_nonnegative_not_official') for i,g in enumerate(good)]).to_csv(OUT/'live_sector_weights.csv',index=False)
    pd.DataFrame(rows).to_csv(OUT/'live_sector_forecasts.csv',index=False)
    stages={'mining_ppi_mom':['PPI_B06','PPI_C25','PPI_C32'],'raw_material_ppi_mom':['PPI_B06','PPI_C25','PPI_C26','PPI_C31','PPI_C32'],'means_ppi_mom':list(mapping.dropna().unique()),'processing_ppi_mom':['PPI_C17','PPI_C22','PPI_C26','PPI_C28','PPI_C29','PPI_C30','PPI_C31','PPI_C32'],'purchasing_ppi_mom':list(mapping.dropna().unique()),'consumer_goods_ppi_mom':[]}
    stage_rows=[]
    for target,codes in stages.items():
        y=vals[target].reindex(train).where(avail[target].reindex(train)<cutoff);ids=[c for c in X if mapping.get(c) in codes]
        pred,n,new=product_prediction(X.reindex(train)[ids],y,now) if ids else (np.nan,0,0)
        method='independent_stage_product_pass_through'
        if not np.isfinite(pred):pred=ar_forecast(y,month);method='AR1_missing_contemporaneous_consumer_prices'
        stage_rows.append(dict(common,target_id=target,forecast=pred,n_train=int(y.notna().sum()),n_active_products=n,n_new_prior_products=new,method=method,training_max_release=avail[target].reindex(train)[y.notna()].max()))
    pd.DataFrame(stage_rows).to_csv(OUT/'live_stage_forecasts.csv',index=False)
    print(pd.read_csv(OUT/'live_sectorfirst_forecast.csv').to_string(index=False));print(pd.DataFrame(stage_rows)[['target_id','forecast','method']].to_string(index=False))
if __name__=='__main__':run()

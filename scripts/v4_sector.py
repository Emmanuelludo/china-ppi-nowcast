"""Survey aligned, composition-aware sector-first challenge. Effective weights, not official."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data/v4'
MAP={'煤炭开采和洗选业':['PPI_B06'],'石油和天然气开采业':['PPI_C25','PPI_D45'],'黑色金属矿采选业':['PPI_C31'],'有色金属矿采选业':['PPI_C32'],'农副食品加工业':['PPI_C13'],'食品制造业':['PPI_C13'],'纺织业':['PPI_C17'],'造纸和纸制品业':['PPI_C22'],'石油、煤炭及其他燃料加工业':['PPI_C25'],'化学原料和化学制品制造业':['PPI_C26'],'化学纤维制造业':['PPI_C28'],'橡胶和塑料制品业':['PPI_C29'],'非金属矿物制品业':['PPI_C30'],'黑色金属冶炼和压延加工业':['PPI_C31'],'有色金属冶炼和压延加工业':['PPI_C32'],'燃气生产和供应业':['PPI_D45'],'木材加工和木、竹、藤、棕、草制品业':['PPI_C20']}
SCHEMES=['carry_0','carry_25','carry_50','carry_75','linear_points','endpoint_25','endpoint_50']
def positive_line(x,y):
    x=np.asarray(x,float);y=np.asarray(y,float);mx=x.mean();my=y.mean();b=max(0.,np.dot(x-mx,y-my)/(np.dot(x-mx,x-mx)+1.));return my-b*mx,b

def product_prediction(X,y,now):
    """Per-specification positive pass-through; missing live specifications excluded."""
    estimates=[];pool=[]
    for col in X:
        ok=X[col].notna()&y.notna()
        if ok.sum()<12:continue
        xx=X.loc[ok,col].to_numpy();yy=y[ok].to_numpy();a,b=positive_line(xx,yy);pool.append((a,b))
        if pd.isna(now.get(col,np.nan)):continue
        errors=[]
        for stop in range(max(8,len(xx)-9),len(xx),3):
            aa,bb=positive_line(xx[:stop-1],yy[:stop-1]);errors.extend((yy[stop:stop+3]-aa-bb*xx[stop:stop+3])**2)
        estimates.append((a+b*now[col],1/(np.mean(errors)+.05),False))
    # New valid specification gets a labeled sector pass-through prior, not a filled price.
    if pool:
        aa,bb=np.median(pool,axis=0)
        for col in X:
            if X[col].notna().sum()<12 and pd.notna(now.get(col,np.nan)):
                estimates.append((aa+bb*now[col],1/(np.var(y.dropna())+.05),True))
    if not estimates:return np.nan,0,0
    p,w,new=map(np.asarray,zip(*estimates));return float(np.average(p,weights=w)),len(p),int(new.sum())

def ar_forecast(y,target_month):
    observed=y.dropna()
    if len(observed)<3:return float(observed.mean())
    # Fit only adjacent calendar months; do not compress missing periods.
    calendar=pd.period_range(observed.index.min(),observed.index.max(),freq='M').astype(str)
    z=observed.reindex(calendar);lag=z.shift(1);ok=z.notna()&lag.notna()
    if ok.sum()<2:return float(observed.mean())
    a,b=positive_line(lag[ok],z[ok]);prediction=float(observed.iloc[-1])
    steps=pd.Period(target_month,freq='M').ordinal-pd.Period(observed.index[-1],freq='M').ordinal
    for _ in range(max(0,steps)):prediction=a+b*prediction
    return float(prediction)

def choose_scheme(panels,train,means):
    scores={}
    for scheme,X in panels.items():
        z=X.reindex(train).mean(axis=1);y=means.reindex(train);err=[]
        for stop in [len(train)-9,len(train)-6,len(train)-3]:
            ok=z.iloc[:stop-1].notna()&y.iloc[:stop-1].notna()
            a,b=positive_line(z.iloc[:stop-1][ok],y.iloc[:stop-1][ok]);truth=y.iloc[stop:stop+3];pred=a+b*z.iloc[stop:stop+3];err.extend((truth-pred).dropna()**2)
        scores[scheme]=np.mean(err) if err else np.inf
    return min(scores,key=scores.get),scores

def effective_weights(A,y,prior):
    # Penalization fixes weak identification across the correlated industry series.
    A=np.asarray(A,float);y=np.asarray(y,float);prior=np.asarray(prior,float);prior=prior/prior.sum()
    def f(q):return np.mean((y-q[-1]-A@q[:-1])**2)+.5*np.sum((q[:-1]-prior)**2)+.1*q[-1]**2
    res=minimize(f,np.r_[prior,0.],method='SLSQP',bounds=[(0,1)]*len(prior)+[(-.5,.5)],constraints={'type':'eq','fun':lambda q:q[:-1].sum()-1},options={'maxiter':300,'ftol':1e-10})
    if not res.success:raise RuntimeError(res.message)
    return res.x[:-1],res.x[-1]

def operational_state(heads,targets):
    """Preserve the last survey-window forecast absent newly published labels."""
    frame=pd.DataFrame(heads).copy();frame['price_asof']=frame.cutoff;frame['state_source_vintage']=frame.vintage
    frame['freeze_reason']='original_vintage'
    for idx,row in frame[frame.vintage.eq('final')].iterrows():
        candidates=frame[(frame.month==row.month)&frame.vintage.isin(['early','mid'])&(frame.cutoff<row.cutoff)]
        if candidates.empty:continue
        source=candidates.sort_values('cutoff').iloc[-1]
        news=targets[(targets.month<row.month)&(targets.available_at>source.cutoff)&(targets.available_at<=row.cutoff)]
        if not news.empty:continue
        for col in ['forecast','scheme','intercept','n_train','weight_train_n','n_sectors','revenue_coverage']:
            frame.loc[idx,col]=source[col]
        frame.loc[idx,'price_asof']=source.cutoff;frame.loc[idx,'state_source_vintage']=source.vintage
        frame.loc[idx,'freeze_reason']='no_new_target_labels_and_no_new_current_month_survey_price'
    frame['model']='sectorfirst_survey_state'
    return frame

def run():
    p=pd.read_csv(OUT/'product_features.csv');p['cutoff']=pd.to_datetime(p.cutoff,utc=True)
    t=pd.concat([pd.read_csv(ROOT/'data/v2/targets/sector_targets_long.csv'),pd.read_csv(ROOT/'data/v2/post_release/august2026_targets.csv')],ignore_index=True)
    t=t[t.transformation.eq('mom')].copy();t['available_at']=pd.to_datetime(t.available_at,utc=True);t=t.sort_values('available_at').drop_duplicates(['month','target_id'])
    vals=t.pivot(index='month',columns='target_id',values='value');avail=t.pivot(index='month',columns='target_id',values='available_at')
    names=t[t.component_type.eq('industry')].drop_duplicates('target_id').set_index('target_id').target_name_zh.to_dict()
    w=pd.read_csv(ROOT/'data/v2/weights/industry_revenue_weights.csv');w['available_at']=pd.to_datetime(w.available_at,utc=True)
    rows=[];weights=[];heads=[]
    for vintage in ['carry','early','mid','final']:
        pp=p[p.vintage.eq(vintage)];panels={s:q.pivot(index='month',columns='exact_product_id',values='change') for s,q in pp[pp.scheme.isin(SCHEMES)].groupby('scheme')}
        mapping=pp.drop_duplicates('exact_product_id').set_index('exact_product_id').ppi_industry_id
        for month,cutoff in pp.groupby('month').cutoff.max().items():
            eligible=vals.index[(vals.index<month)&(avail.headline_ppi_mom<cutoff)&vals.headline_ppi_mom.notna()];train=eligible.intersection(panels['carry_25'].index)
            if len(train)<36:continue
            if month in avail.index and pd.notna(avail.loc[month,'headline_ppi_mom']) and cutoff>=avail.loc[month,'headline_ppi_mom']:continue
            scheme,sc=choose_scheme(panels,train,vals.means_ppi_mom);X=panels[scheme];now=X.loc[month];preds={}
            for target,name in names.items():
                ids=[c for c in X if mapping.get(c) in MAP.get(name,[])]
                y=vals[target].reindex(train).where(avail[target].reindex(train)<cutoff)
                if y.notna().sum()<36:continue
                forecast,n,new=product_prediction(X.reindex(train)[ids],y,now) if ids else (np.nan,0,0)
                method='product_positive_pass_through'
                if not np.isfinite(forecast):forecast=ar_forecast(y,month);method='AR1_unmapped_or_unavailable'
                preds[target]=forecast
                rows.append(dict(month=month,vintage=vintage,cutoff=cutoff,target_id=target,industry=name,scheme=scheme,forecast=forecast,actual=vals[target].get(month,np.nan),n_train=int(y.notna().sum()),n_active_products=n,n_new_prior_products=new,method=method,train_last_month=y.dropna().index.max(),training_max_release=avail[target].reindex(train)[y.notna()].max()))
            # Only historically available industry releases may enter weight estimation.
            wt=train[-48:];A=vals.reindex(wt)[list(preds)].where(avail.reindex(wt)[list(preds)]<cutoff);good=A.columns[A.notna().all()];A=A[good]
            if len(good)<10:continue
            dated=w[w.available_at<cutoff];latest=dated[dated.available_at.eq(dated.available_at.max())].set_index('industry_name')
            prior=np.array([latest.economic_weight.get(names[g],0) for g in good],float) if len(latest) else np.ones(len(good))
            if prior.sum()==0:prior=np.ones(len(good))
            revenue_coverage=prior.sum() if len(latest) else np.nan
            ww,intercept=effective_weights(A,vals.loc[wt,'headline_ppi_mom'],prior)
            prediction=intercept+sum(ww[i]*preds[g] for i,g in enumerate(good))
            heads.append(dict(month=month,vintage=vintage,cutoff=cutoff,model='sectorfirst_effective_weights',scheme=scheme,forecast=prediction,actual=vals.headline_ppi_mom.get(month,np.nan),intercept=intercept,n_train=len(train),weight_train_n=len(wt),n_sectors=len(good),revenue_coverage=revenue_coverage))
            for i,g in enumerate(good):weights.append(dict(month=month,vintage=vintage,cutoff=cutoff,target_id=g,industry=names[g],effective_weight=ww[i],revenue_prior=prior[i]/prior.sum(),sector_forecast=preds[g],contribution=ww[i]*preds[g],weight_source_available_at=latest.available_at.max() if len(latest) else pd.NaT,weight_type='estimated_nonnegative_not_official'))
        print(vintage,len(heads),flush=True)
    pd.DataFrame(rows).to_csv(OUT/'sector_forecasts.csv',index=False);pd.DataFrame(heads).to_csv(OUT/'sectorfirst_forecasts.csv',index=False);pd.DataFrame(weights).to_csv(OUT/'sector_weights.csv',index=False)
    results=[]
    for vintage,g in pd.DataFrame(heads).dropna(subset=['actual']).groupby('vintage'):
        e=g.forecast-g.actual;results.append(dict(vintage=vintage,n=len(g),correlation=g.forecast.corr(g.actual),rmse=np.sqrt(np.mean(e**2)),mae=np.mean(abs(e)),directional_accuracy=np.mean(np.sign(g.forecast)==np.sign(g.actual))))
    operational_state(heads,t).to_csv(OUT/'sectorfirst_survey_state.csv',index=False)
    pd.DataFrame(results).to_csv(OUT/'sectorfirst_metrics.csv',index=False);print(pd.DataFrame(results).to_string(index=False))
if __name__=='__main__':run()

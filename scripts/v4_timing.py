"""Release-gated, continuous exact-specification price proxies for survey dates.

The 10-day prices are interval averages, not point quotes. Alignment is an
empirical approximation. Missing scheduled releases produce no invented release
vintage. Within a released vintage, stale prices may persist for at most 35 days;
these and forecasts of the second observation are explicitly flagged estimated.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from v3_features import observation_categories
R=Path(__file__).resolve().parents[1]
SCHEMES={'nearest':0.,'continuous_equal':.5,'continuous_days':None,'carry_0':0.,'carry_25':.25,'carry_50':.5,'carry_75':.75,'calendar':0.,'linear_points':None,'endpoint_25':.25,'endpoint_50':.25}
META=['product_family_id','category_id','ppi_industry_id']

def prepare(raw):
    raw=observation_categories(raw)
    raw['start']=pd.to_datetime(raw.reference_period_start)
    raw['end']=pd.to_datetime(raw.reference_period_end)
    raw['month']=raw.start.dt.to_period('M')
    raw['slot']=np.minimum((raw.start.dt.day-1)//10+1,3)
    raw['available_at']=pd.to_datetime(raw.available_at,utc=True)
    raw['raw_price']=pd.to_numeric(raw.raw_price,errors='coerce')
    return raw.sort_values('available_at').drop_duplicates(['month','slot','exact_product_id'],keep='first')

def release_cutoffs(raw):
    releases=raw.groupby(['month','slot']).available_at.max()
    out={v:{} for v in ['carry','early','mid','final']}
    for (m,s),date in releases.items():
        out[{1:'early',2:'mid',3:'final'}[s]][m]=date
        if s==3:out['carry'][m+1]=date
    return {v:pd.Series(d,name='cutoff').sort_index() for v,d in out.items()}

def proxy(records,month,scheme,vintage):
    """Records already gated by forecast publication cutoff; return level/flags."""
    def get(m,s):
        desired=m.start_time+pd.Timedelta(days={1:9,2:19,3:m.days_in_month-1}[s])
        permitted=[r for r in records if r['end']<=desired]
        if not permitted:return np.nan,True,None
        r=permitted[-1]
        if (desired-r['end']).days>35:return np.nan,True,None
        exact=(r['month']==m and r['slot']==s)
        return r['raw_price'],not exact,r
    if scheme=='calendar':
        slots={'carry':[],'early':[1],'mid':[1,2],'final':[1,2,3]}[vintage]
        if not slots:
            x,e,_=get(month-1,3);return x,True,0
        vals=[get(month,s) for s in slots]
        if any(not np.isfinite(x[0]) for x in vals):return np.nan,True,len(slots)
        return float(np.mean([x[0] for x in vals])),any(x[1] for x in vals),len(slots)
    if vintage=='carry':
        p,e,_=get(month-1,3)
        return p,True,0
    early,e1,r1=get(month,1)
    mid,e2,r2=get(month,2)
    if vintage=='early':mid=early;e2=True
    weight=SCHEMES[scheme]
    if weight is None:
        prev,ep,rp=get(month-1,3)
        # Early interval midpoint is normally 5.5. Linear interpolation uses
        # the preceding late interval midpoint, never a future current late quote.
        if r1 is not None and rp is not None and r1['month']==month and r1['slot']==1:
            left=rp['start']+(rp['end']-rp['start'])/2
            right=r1['start']+(r1['end']-r1['start'])/2
            day5=month.start_time+pd.Timedelta(days=4)
            weight=float(np.clip((right-day5)/(right-left),0,1)) if right>left else 0.
        else:weight=0.
    if weight>0:
        prev,ep,_=get(month-1,3)
        fifth=weight*prev+(1-weight)*early;e1=e1 or ep
    else:fifth=early
    twentieth=mid
    if vintage!='early':
        if scheme in ['endpoint_25','endpoint_50']:
            twentieth=mid+({'endpoint_25':.25,'endpoint_50':.5}[scheme])*(mid-early)
        elif scheme=='linear_points' and r1 is not None and r2 is not None:
            x1=r1['start']+(r1['end']-r1['start'])/2
            x2=r2['start']+(r2['end']-r2['start'])/2
            if x2>x1:
                fraction=float(np.clip((month.start_time+pd.Timedelta(days=19)-x2)/(x2-x1),0,.5))
                twentieth=mid+fraction*(mid-early)
    level=(fifth+twentieth)/2
    if level<=0:return np.nan,True,0
    return level,e1 or e2,1 if vintage=='early' else 2

def build(raw=None,write=True):
    raw=prepare(pd.read_csv(R/'data/v2/products/mapped_raw_observations.csv') if raw is None else raw.copy())
    cuts=release_cutoffs(raw)
    groups={pid:g.sort_values('end').to_dict('records') for pid,g in raw.groupby('exact_product_id')}
    result={v:{} for v in cuts};all_frames=[]
    for vintage,cutoffs in cuts.items():
        rows={s:[] for s in SCHEMES}
        for month,cutoff in cutoffs.items():
            released=raw[raw.available_at<=cutoff]
            aligned=released[released.end<=month.start_time+pd.Timedelta(days=19)]
            active={}
            for kind,available in [('calendar',released),('aligned',aligned)]:
                active[kind]=set(available.loc[available.end==available.end.max(),'exact_product_id']) if len(available) else set()
            for pid,records in groups.items():
                known=[r for r in records if r['available_at']<=cutoff]
                if not known:continue
                # Mapping belongs to the latest permitted observation, not the
                # latest basket. Current late metadata cannot enter aligned M.
                allowed=[r for r in known if r['end']<=month.start_time+pd.Timedelta(days=19)]
                if not allowed:continue
                for scheme in SCHEMES:
                    use=known if scheme=='calendar' else allowed
                    level,estimated,n=proxy(use,month,scheme,vintage)
                    previous,prev_estimated,_=proxy(use,month-1,scheme,'final')
                    change=100*(level/previous-1) if np.isfinite(level) and np.isfinite(previous) and previous>0 else np.nan
                    is_active=pid in active['calendar' if scheme=='calendar' else 'aligned']
                    if not is_active:change=np.nan
                    meta=use[-1]
                    row={'month':month,'exact_product_id':pid,**{c:meta[c] for c in META},'change':change,'active':is_active,'observed':bool(np.isfinite(change) and not estimated and not prev_estimated),'estimated':bool(estimated or prev_estimated),'price_proxy':level,'previous_price_proxy':previous,'proxy_observations':n,'cutoff':cutoff}
                    rows[scheme].append(row)
        for scheme,rr in rows.items():
            frame=pd.DataFrame(rr)
            result[vintage][scheme]=(frame,cutoffs)
            all_frames.append(frame.assign(vintage=vintage,scheme=scheme))
    if write:
        out=R/'data/v4';out.mkdir(parents=True,exist_ok=True)
        pd.concat(all_frames,ignore_index=True).to_csv(out/'product_features.csv',index=False)
        pd.concat([s.rename_axis('month').reset_index().assign(vintage=v) for v,s in cuts.items()],ignore_index=True).to_csv(out/'cutoffs.csv',index=False)
    return result

if __name__=='__main__':
    result=build()
    print({v:{s:len(x[0]) for s,x in schemes.items()} for v,schemes in result.items()})

"""Canonical absolute prices and strict, publication-aware monthly product features."""
import hashlib
import json
import re
import unicodedata
import numpy as np
import pandas as pd

VERSION = 'product-log-v3'
VARIANTS = ('twentieth', 'final', 'early', 'early_carry')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False, default=str).encode()).hexdigest()


def normalize(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(text)))


def identity(name, unit):
    return 'p_' + digest(normalize(name) + '|' + normalize(unit))[:16]


def canonicalize(observations):
    x = observations.copy()
    x['product_id'] = [identity(n,u) for n,u in zip(x.product_name_cn,x.unit_cn)]
    x['product_name'] = x.product_name_cn.map(normalize)
    x['product_specification'] = x.product_name.str.extract(r'\((.*)\)',expand=False).fillna('')
    x['unit'] = x.unit_cn.map(normalize).map({'吨':'CNY/tonne','千克':'CNY/kg','张':'CNY/sheet'})
    if x.unit.isna().any(): raise ValueError('QA: unreviewed unit')
    x['absolute_price'] = pd.to_numeric(x.price_cny,errors='raise')
    if not (np.isfinite(x.absolute_price) & x.absolute_price.gt(0)).all():
        raise ValueError('QA: invalid absolute price')
    x['observation_period'] = x.release_month + ':' + x.window
    bounds={'1-10':(1,10),'11-20':(11,20),'21-end':(21,None)}
    start,end=[],[]
    for month,window in zip(x.release_month,x.window):
        if window not in bounds: raise ValueError('QA: invalid observation window')
        p=pd.Period(month,freq='M'); a,b=bounds[window]
        start.append(p.start_time+pd.Timedelta(days=a-1))
        end.append(p.start_time+pd.Timedelta(days=(b or p.days_in_month)-1))
    x['period_start'],x['period_end']=start,end
    x['period_midpoint']=x.period_start+(x.period_end-x.period_start)/2
    x['calendar_month']=x.release_month
    x['reported_pct_change']=x.change_pct
    x['retrieval_date']=x.retrieved_at
    for c in ('published_at','retrieved_at'): x[c]=pd.to_datetime(x[c],utc=True,errors='raise')
    for _,g in x.groupby(['content_sha256','observation_period']):
        if len(g)!=50 or g.product_id.duplicated().any():
            raise ValueError('QA: expected 50 unique series per release; review parser/basket')
    return x


def catalog_from(x):
    products={}
    for pid,g in x.groupby('product_id'):
        r=g.sort_values('period_start').iloc[-1]
        products[pid]=dict(product_id=pid,canonical_name=r.product_name,specification=r.product_specification,
            unit=r.unit,continuity_group=r.product_name.split('(')[0],replacement_product=None,
            first_available=str(g.period_start.min().date()),last_available=str(g.period_end.max().date()),
            group=re.sub(r'^[一二三四五六七八九十]+、','',r.category_cn))
    epochs=[];previous=set()
    latest=x.sort_values(['period_start','retrieved_at']).drop_duplicates(['observation_period','product_id'],keep='last')
    for period,g in latest.groupby('observation_period',sort=False):
        present=set(g.product_id)
        if present==previous: continue
        if epochs: epochs[-1]['effective_to']=str((g.period_start.min()-pd.Timedelta(days=1)).date())
        epochs.append(dict(basket_version='basket_'+digest(sorted(present))[:12],
            effective_from=str(g.period_start.min().date()),effective_to=None,active_products=sorted(present),
            products_added=sorted(present-previous),products_removed=sorted(previous-present),
            source_url=g.iloc[0].source_url,NBS_note=None,
            evidence='observed membership; onset bounded by available releases'))
        previous=present
    for pid,record in products.items():
        membership=[b for b in epochs if pid in b['active_products']]
        record['basket_version_start']=membership[0]['basket_version']
        record['basket_version_end']=membership[-1]['basket_version']
    return dict(products=products,baskets=epochs,first_observation=str(x.period_start.min().date()),
                last_observation=str(x.period_end.max().date()),history_complete_from_2014=False)


def basket_at(catalog,date):
    date=str(pd.Timestamp(date).date())
    matches=[b for b in catalog['baskets'] if b['effective_from']<=date and
             (b['effective_to'] is None or date<=b['effective_to'])]
    if len(matches)!=1: raise ValueError('QA: no reviewed basket for '+date)
    return matches[0]


def active_products(catalog,month):
    return basket_at(catalog,month+'-01')['active_products']


def available(x,cutoff,realtime=True):
    cutoff=pd.Timestamp(cutoff)
    if cutoff.tzinfo is None: raise ValueError('as_of needs a timezone')
    selected=x[x.published_at.le(cutoff)]
    if realtime: selected=selected[selected.retrieved_at.le(cutoff)]
    snap=selected[['observation_period','content_sha256','published_at','retrieved_at']].drop_duplicates()
    snap=snap.sort_values(['published_at','retrieved_at']).drop_duplicates('observation_period',keep='last')
    return selected.merge(snap[['observation_period','content_sha256']],on=['observation_period','content_sha256'])


def feature_row(x,catalog,month,variant,cutoff,realtime=True):
    if variant not in VARIANTS: raise ValueError('unknown timing specification')
    x=available(x,cutoff,realtime); ids=sorted(catalog['products']); sources={}; baskets=set()
    prior=str(pd.Period(month,freq='M')-1)
    def price(m,w):
        g=x[x.release_month.eq(m)&x.window.eq(w)]
        if g.empty: raise ValueError(f'QA: unavailable source release {m}:{w}')
        expected=basket_at(catalog,g.period_start.iloc[0])
        if set(g.product_id)!=set(expected['active_products']) or g.product_id.duplicated().any():
            raise ValueError(f'QA: unexpected missing product or unit/spec change {m}:{w}')
        sources[m+':'+w]=g[['source_url','content_sha256','published_at','retrieved_at']].drop_duplicates().astype(str).to_dict('records')
        baskets.add(expected['basket_version'])
        return g.set_index('product_id').absolute_price.reindex(ids)
    if variant=='twentieth': current,previous=price(month,'11-20'),price(prior,'11-20')
    elif variant=='final':
        current=(price(month,'1-10')+price(month,'11-20'))/2
        previous=(price(prior,'1-10')+price(prior,'11-20'))/2
    else: current,previous=price(month,'1-10'),price(prior,'1-10')
    changes=100*np.log(current/previous); changes.index='price__'+changes.index
    if variant=='early_carry':
        carry=100*np.log(current/price(prior,'21-end'));carry.index='carry__'+carry.index
        changes=pd.concat([changes,carry])
    if changes.filter(like='price__').notna().sum()==0: raise ValueError('QA: no comparable products')
    meta=dict(feature_version=VERSION,variant=variant,target_month=month,
        sources=sources,basket_versions=sorted(baskets),
        availability_basis='publication_and_retrieval' if realtime else 'publication',
        realtime_status='prospective' if realtime else 'pseudo_real_time',
        values={k:None if pd.isna(v) else float(v) for k,v in changes.items()},
        structural_missing=[k for k,v in changes.items() if pd.isna(v)],
        transformation='100*log(current_level/previous_level)')
    meta['feature_hash']=digest(meta);meta['as_of']=str(pd.Timestamp(cutoff))
    return changes,meta


def training_matrix(x,catalog,actuals,variant):
    actuals=actuals.copy();actuals['published_at']=pd.to_datetime(actuals.published_at,utc=True)
    actuals=actuals.sort_values('published_at').drop_duplicates('target_month',keep='last')
    rows=[];excluded=[]
    for r in actuals.sort_values('target_month').itertuples():
        window='1-10' if variant.startswith('early') else '11-20'
        times=x.loc[x.release_month.eq(r.target_month)&x.window.eq(window),'published_at']
        if times.empty: excluded.append(dict(month=r.target_month,reason='missing '+window));continue
        cutoff=times.min()
        if r.published_at<=cutoff: excluded.append(dict(month=r.target_month,reason='actual already public'));continue
        try: values,meta=feature_row(x,catalog,r.target_month,variant,cutoff,False)
        except ValueError as e: excluded.append(dict(month=r.target_month,reason=str(e)));continue
        row=values.to_dict();row.update(target_month=r.target_month,target_mom_pct=float(r.actual_mom_pct),
            feature_cutoff=cutoff.isoformat(),actual_published_at=r.published_at.isoformat(),feature_hash=meta['feature_hash'])
        rows.append(row)
    return pd.DataFrame(rows),excluded

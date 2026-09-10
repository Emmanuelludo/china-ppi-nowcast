import sys
from pathlib import Path
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from v4_timing import build

def raw():
    rows=[]
    for m in pd.period_range('2026-05','2026-08',freq='M'):
        for slot,start,end in [(1,1,10),(2,11,20),(3,21,m.days_in_month)]:
            d=m.start_time+pd.Timedelta(days=end-1)
            rows.append(dict(exact_product_id='A',product_family_id='F',category_id='C',ppi_industry_id='I',reference_period_start=str(m.start_time+pd.Timedelta(days=start-1)),reference_period_end=str(d),available_at=str((d+pd.Timedelta(days=3)).tz_localize('UTC')),raw_price=100+(m.month-5)*3+slot))
    return pd.DataFrame(rows)

def value(result,vintage,scheme,month,pid='A'):
    f=result[vintage][scheme][0]
    return f[(f.month==pd.Period(month,'M'))&(f.exact_product_id==pid)].iloc[0]

def test_late_current_excluded_and_next_carry_affected():
    r=raw();old=build(r,False)
    r.loc[r.reference_period_start.str.startswith('2026-08-21'),'raw_price']=300
    new=build(r,False)
    for scheme in ['nearest','continuous_equal','continuous_days','carry_25','carry_75','linear_points','endpoint_25','endpoint_50']:
        assert value(old,'final',scheme,'2026-08').change==value(new,'final',scheme,'2026-08').change
        assert value(old,'mid',scheme,'2026-08').change==value(new,'final',scheme,'2026-08').change
        assert value(old,'carry',scheme,'2026-09').change!=value(new,'carry',scheme,'2026-09').change

def test_new_spec_never_level_spliced():
    r=raw();r.loc[r.reference_period_start.str.startswith('2026-08'),'exact_product_id']='B'
    f=value(build(r,False),'mid','nearest','2026-08','B')
    assert np.isnan(f.change)
    assert not f.observed

def test_future_publication_never_enters_early():
    r=raw();old=build(r,False)
    r.loc[r.reference_period_start.str.startswith('2026-08-11'),'raw_price']=9000
    new=build(r,False)
    assert value(old,'early','continuous_equal','2026-08').change==value(new,'early','continuous_equal','2026-08').change
    assert value(new,'early','continuous_equal','2026-08').estimated

def test_prior_late_carry_in_and_actual_price_amplitude():
    r=raw();old=build(r,False)
    r.loc[r.reference_period_start.str.startswith('2026-07-21'),'raw_price']=150
    new=build(r,False)
    assert value(old,'mid','continuous_equal','2026-08').change!=value(new,'mid','continuous_equal','2026-08').change
    assert value(old,'mid','nearest','2026-08').change==value(new,'mid','nearest','2026-08').change

def test_expired_product_not_carried_indefinitely():
    r=raw();old=r[r.reference_period_start.str.startswith('2026-05')].copy()
    newer=r[~r.reference_period_start.str.startswith('2026-05')].copy();newer['exact_product_id']='B'
    f=value(build(pd.concat([old,newer]),False),'final','nearest','2026-08','A')
    assert np.isnan(f.change)

def test_removed_product_exits_on_new_basket_not_stale_price_imputation():
    r=raw();r.loc[r.reference_period_start.str.startswith('2026-08-11') | r.reference_period_start.str.startswith('2026-08-21'),'exact_product_id']='B'
    result=build(r,False)
    old=value(result,'early','nearest','2026-08','A')
    removed=value(result,'mid','nearest','2026-08','A')
    assert old.active and np.isfinite(old.change)
    assert not removed.active and np.isnan(removed.change)
    assert value(result,'final','nearest','2026-08','A').active==removed.active
    assert value(result,'mid','nearest','2026-07','A').active


def test_linear_points_reconstruct_linear_daily_process():
    from v4_timing import prepare,proxy
    r=raw();origin=pd.Timestamp('2026-08-01')
    for i,row in r.iterrows():
        a=pd.Timestamp(row.reference_period_start);b=pd.Timestamp(row.reference_period_end)
        r.loc[i,'raw_price']=100+((a-origin).days+(b-origin).days)/2
    records=prepare(r).sort_values('end').to_dict('records')
    level,_,_=proxy(records,pd.Period('2026-08'),'linear_points','final')
    assert np.isclose(level,(104+119)/2)

import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
s=importlib.util.spec_from_file_location('v4_sector',Path(__file__).resolve().parents[1]/'scripts/v4_sector.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_absent_specification_excluded_without_imputation():
    X=pd.DataFrame({'old':np.arange(20.),'current':np.arange(20.)});y=pd.Series(np.arange(20.)*.3)
    pred,n,new=m.product_prediction(X,y,pd.Series({'old':np.nan,'current':2.}))
    assert n==1 and new==0 and np.isfinite(pred)
    all_missing=m.product_prediction(X,y,pd.Series({'old':np.nan,'current':np.nan}))
    assert np.isnan(all_missing[0]) and all_missing[1]==0

def test_new_specification_uses_labeled_sector_prior():
    X=pd.DataFrame({'old':np.arange(20.),'new':[np.nan]*20});y=pd.Series(np.arange(20.)*.3)
    pred,n,new=m.product_prediction(X,y,pd.Series({'old':np.nan,'new':2.}))
    assert np.isfinite(pred) and n==1 and new==1

def test_effective_weights_nonnegative_normalized():
    rng=np.random.default_rng(9);X=rng.normal(size=(40,3));y=X@np.array([.6,.3,.1])
    w,a=m.effective_weights(X,y,[.4,.4,.2]);assert (w>=0).all();assert abs(w.sum()-1)<1e-8

def test_delivered_training_and_weights_precede_cutoff():
    root=Path(__file__).resolve().parents[1];p=root/'data/v4/sector_forecasts.csv'
    if not p.exists():return
    t=pd.read_csv(p);assert (pd.to_datetime(t.training_max_release,utc=True)<pd.to_datetime(t.cutoff,utc=True)).all()
    assert (t.train_last_month<t.month).all()
    w=pd.read_csv(root/'data/v4/sector_weights.csv');known=w.weight_source_available_at.notna()
    assert (pd.to_datetime(w.loc[known,'weight_source_available_at'],utc=True)<pd.to_datetime(w.loc[known,'cutoff'],utc=True)).all()
    assert np.allclose(w.groupby(['month','vintage']).effective_weight.sum(),1)

def test_ar_forecast_iterates_two_calendar_steps():
    y=pd.Series([.1,.4,.7,1.],index=['2025-01','2025-02','2025-03','2025-04'])
    a,b=m.positive_line(y.iloc[:-1],y.iloc[1:])
    assert np.isclose(m.ar_forecast(y,'2025-06'),a+b*(a+b*1.))
    assert not np.isclose(m.ar_forecast(y,'2025-06'),a+b*1.)

def test_ar_does_not_fit_across_missing_calendar_month():
    y=pd.Series([.1,.4,999.,.7,1.],index=['2025-01','2025-02','2025-04','2025-06','2025-07'])
    a,b=m.positive_line([.1,.7],[.4,1.])
    assert np.isclose(m.ar_forecast(y,'2025-08'),a+b)

def test_operational_final_does_not_move_without_new_survey_information():
    common=dict(month='2026-08',scheme='carry_25',intercept=0.,n_train=40,weight_train_n=40,n_sectors=30,revenue_coverage=.84)
    a=dict(common,vintage='mid',cutoff=pd.Timestamp('2026-08-24',tz='UTC'),forecast=.2)
    b=dict(common,vintage='final',cutoff=pd.Timestamp('2026-09-04',tz='UTC'),forecast=.9)
    targets=pd.DataFrame({'month':['2026-07'],'available_at':[pd.Timestamp('2026-08-09',tz='UTC')]})
    z=m.operational_state([a,b],targets)
    assert z.iloc[1].forecast==.2 and z.iloc[1].price_asof==a['cutoff']

def test_live_update_preserves_separate_price_and_label_cutoffs():
    root=Path(__file__).resolve().parents[1];f=root/'data/v4/live_sectorfirst_forecast.csv'
    if not f.exists():return
    h=pd.read_csv(f);s=pd.read_csv(root/'data/v4/live_sector_forecasts.csv')
    assert (pd.to_datetime(h.data_price_asof,utc=True)<pd.to_datetime(h.target_asof,utc=True)).all()
    assert (pd.to_datetime(s.training_max_release,utc=True)<pd.to_datetime(s.cutoff,utc=True)).all()
    assert (s.train_last_month<s.month).all()
    w=pd.read_csv(root/'data/v4/live_sector_weights.csv')
    assert np.isclose(w.contribution.sum()+h.intercept.iloc[0],h.forecast.iloc[0])

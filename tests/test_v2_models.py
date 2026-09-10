import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

s=importlib.util.spec_from_file_location('v2',Path(__file__).parents[1]/'scripts/v2_fit_models.py')
v2=importlib.util.module_from_spec(s);s.loader.exec_module(v2)

def test_training_only_missingness_and_exact_attribution():
    X=pd.DataFrame({'old':np.arange(30.),'new':[np.nan]*25+list(range(5)),'other':np.sin(np.arange(30))})
    model=v2.PanelRegressor().fit(X,pd.Series(np.arange(30.)*.1))
    assert 'new' not in model.columns
    test=pd.DataFrame({'old':[np.nan],'new':[999999],'other':[2.]})
    assert np.isclose(sum(model.contributions(test).values()),model.predict(test)[0])
    assert model.median['old']==14.5

def test_pca_attribution_exact():
    X=pd.DataFrame(np.random.default_rng(1).normal(size=(40,8)))
    m=v2.PanelRegressor('pca').fit(X,X[0]*2-X[3])
    assert np.isclose(sum(m.contributions(X.iloc[[0]]).values()),m.predict(X.iloc[[0]])[0])

def test_lag_uses_calendar_not_previous_row():
    p=pd.DataFrame({'month':['2025-01','2025-03'],'vintage':['early']*2,'exact_product_id':['a']*2,'available_at':['2025-01-15','2025-03-15'],'mom_average':[1.,3.]})
    X,_=v2.build_matrix(p,'early')
    assert np.isnan(X.loc[pd.Period('2025-03'),'lag1::mom_average::a'])

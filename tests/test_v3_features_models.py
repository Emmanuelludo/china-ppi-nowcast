"""Behavioral guards for missing baskets and v3 model restrictions."""
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

SCRIPTS = Path(__file__).parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import v3_features
import v3_experiments


@pytest.mark.parametrize('kind', ['forest', 'boost'])
def test_native_missing_predictors_are_not_imputed(kind):
    rng = np.random.default_rng(42)
    x = rng.normal(size=60)
    y = pd.Series(2*x + rng.normal(scale=.1, size=60))
    X = pd.DataFrame({'price_return': x, 'other_return': rng.normal(size=60)})
    X.loc[::3, 'price_return'] = np.nan
    X.loc[1::4, 'other_return'] = np.nan
    model = v3_experiments.Model(kind, 3).fit(X, y)
    probe = pd.DataFrame({'price_return': [np.nan, 1., np.nan],
                          'other_return': [.5, np.nan, np.nan]})
    assert np.isfinite(model.predict(probe)).all()
    # Native estimator receives the same NaNs; there is no fitted median path.
    np.testing.assert_allclose(model.predict(probe), model.est.predict(probe[model.cols]))
    assert not hasattr(model, 'median')


@pytest.mark.parametrize('kind', ['ridge', 'positive', 'forest', 'boost'])
def test_future_only_column_cannot_change_historical_fit_or_forecast(kind):
    X = pd.DataFrame({'existing': np.linspace(-2, 2, 40),
                      'not_yet_introduced': [np.nan]*40})
    model = v3_experiments.Model(kind, 3).fit(X, pd.Series(X.existing*2))
    assert list(model.cols) == ['existing']
    probes = pd.DataFrame({'existing': [1., 1., 1.],
                           'not_yet_introduced': [-1e9, np.nan, 1e9]})
    predicted = model.predict(probes)
    np.testing.assert_allclose(predicted, np.repeat(predicted[0], 3))


def test_positive_ridge_has_nonnegative_partial_price_effects():
    rng = np.random.default_rng(91)
    X = pd.DataFrame(rng.normal(size=(60, 3)), columns=['coal', 'steel', 'copper'])
    # A deliberately negative true relation tests that the constraint binds.
    y = pd.Series(3*X.coal - 5*X.steel + .4*X.copper)
    model = v3_experiments.Model('positive', 1.).fit(X, y)
    base = pd.DataFrame([[0., 0., 0.]], columns=X.columns)
    baseline = model.predict(base)[0]
    for column in X.columns:
        increased = base.copy()
        increased[column] += 1.
        assert model.predict(increased)[0] >= baseline - 1e-12
    assert model.predict(base.assign(coal=1.))[0] > baseline


def test_family_accepts_new_spec_return_without_splicing_price_levels(tmp_path, monkeypatch):
    source = tmp_path / 'data/v2/products'
    source.mkdir(parents=True)
    (tmp_path / 'data/v3').mkdir(parents=True)
    observations = []
    features = []
    # The replacement jumps 100-fold in price units/specification; its first
    # comparable monthly return is intentionally unavailable, never 9,900%.
    for month, exact, price, change in [
        ('2025-01', 'old', 10., 1.), ('2025-02', 'old', 10.2, 2.),
        ('2025-03', 'new', 1020., np.nan), ('2025-04', 'new', 1050.6, 3.),
    ]:
        available = month + '-15T01:30:00Z'
        observations.append(dict(reference_period_start=month+'-01', available_at=available,
                                 exact_product_id=exact, category_id='metal',
                                 raw_pct_change=0., raw_price=price))
        for vintage in ['early', 'mid', 'final']:
            features.append(dict(month=month, vintage=vintage, available_at=available,
                                 exact_product_id=exact, product_family_id='same_family',
                                 category_id='metal', mom_average=change, mom_end=change,
                                 mom_day_weighted=change, published_chain=change,
                                 price_average=price))
    pd.DataFrame(observations).to_csv(source/'mapped_raw_observations.csv', index=False)
    pd.DataFrame(features).to_csv(source/'product_vintage_features.csv', index=False)
    monkeypatch.setattr(v3_features, 'R', tmp_path)
    blocks, _ = v3_features.build()['final']
    family = blocks['mom_average_product_family_id']['same_family']
    assert family.loc[pd.Period('2025-02')] == 2.
    assert np.isnan(family.loc[pd.Period('2025-03')])
    assert family.loc[pd.Period('2025-04')] == 3.
    exact = blocks['mom_average_exact_product_id']
    assert np.isnan(exact.loc[pd.Period('2025-04'), 'old'])
    assert exact.loc[pd.Period('2025-04'), 'new'] == 3.


def test_reclassification_is_applied_only_after_its_release(tmp_path, monkeypatch):
    source = tmp_path / 'data/v2/products'
    source.mkdir(parents=True)
    (tmp_path / 'data/v3').mkdir(parents=True)
    raw = pd.DataFrame([
        dict(reference_period_start='2025-01-01', available_at='2025-01-14T01:30:00Z',
             exact_product_id='same_spec', category_id='CAT_ferrous_metals',
             raw_category_name='一、黑色金属', raw_price=100., raw_pct_change=1.),
        dict(reference_period_start='2025-01-11', available_at='2025-01-24T01:30:00Z',
             exact_product_id='same_spec', category_id='CAT_ferrous_metals',
             raw_category_name='五、煤炭', raw_price=101., raw_pct_change=1.),
    ])
    raw.to_csv(source/'mapped_raw_observations.csv', index=False)
    features = pd.DataFrame([dict(month='2025-01', vintage=vintage,
        available_at='2025-01-14T01:30:00Z' if vintage=='early' else '2025-01-24T01:30:00Z',
        exact_product_id='same_spec', product_family_id='same_family',
        category_id='CAT_ferrous_metals', mom_average=1., mom_end=1.,
        mom_day_weighted=1., published_chain=1.) for vintage in ['early','mid','final']])
    features.to_csv(source/'product_vintage_features.csv', index=False)
    monkeypatch.setattr(v3_features, 'R', tmp_path)
    matrices = v3_features.build()
    assert list(matrices['early'][0]['mom_average_category_id']) == ['CAT_ferrous_metals']
    assert list(matrices['mid'][0]['mom_average_category_id']) == ['CAT_coal']
    assert list(matrices['final'][0]['mom_average_category_id']) == ['CAT_coal']


def test_unknown_source_category_requires_review():
    raw = pd.DataFrame({'category_id':['CAT_coal'], 'raw_category_name':['十、新分类']})
    with pytest.raises(ValueError, match='Unreviewed source category'):
        v3_features.observation_categories(raw)


def test_comparator_gap_and_discrepancy_are_independent():
    raw = pd.DataFrame({'exact_product_id':['a']*3,
        'date':pd.to_datetime(['2025-01-01','2025-01-21','2025-02-01']),
        'month':pd.PeriodIndex(['2025-01','2025-01','2025-02'],freq='M'),
        'slot':[1,3,1], 'available_at':['2025-01-14','2025-02-04','2025-02-14'],
        'raw_price':[100.,110.,121.], 'raw_pct_change':[0.,2.,10.]})
    audit = v3_features.comparator_audit(raw)
    assert audit.gap_since_previous_observation.tolist() == [False,True,False]
    assert audit.comparator_discrepancy_gt_015pp.tolist() == [False,True,False]
    assert audit.comparator_available.tolist() == [False,True,True]

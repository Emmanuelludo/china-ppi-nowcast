import unittest
import numpy as np
import pandas as pd
from china_ppi_nowcast.product.data import canonicalize,catalog_from,feature_row,identity,active_products
from china_ppi_nowcast.product.models import ProductEstimator,ALL_MODELS


def fixture():
    rows=[]
    for month,base in [('2025-12',100.),('2026-01',110.),('2026-02',121.)]:
        for window,bump,pub in [('1-10',0.,14),('11-20',10.,24),('21-end',30.,28)]:
            for i in range(50):
                name=f'商品{i}(规格A)'
                if i==49 and month!='2025-12':name='新产品(规格B)'
                rows.append(dict(release_month=month,window=window,product_name_cn=name,unit_cn='吨',
                    price_cny=base+bump+i,change_pct=0.,category_cn='一、黑色金属',
                    published_at=f'{month}-{pub:02d}T09:30:00+08:00',retrieved_at=f'{month}-{pub:02d}T02:00:00Z',
                    source_url=f'https://example.test/{month}/{window}',content_sha256=month+window))
    return pd.DataFrame(rows)


class ProductTests(unittest.TestCase):
    def setUp(self):
        self.x=canonicalize(fixture());self.c=catalog_from(self.x)

    def test_identity_format_not_specification(self):
        self.assertEqual(identity(' 铜 （1＃） ','吨'),identity('铜(1#)','吨'))
        self.assertNotEqual(identity('铜(1#)','吨'),identity('铜(2#)','吨'))
        self.assertNotEqual(identity('铜(1#)','吨'),identity('铜(1#)','千克'))

    def test_twentieth_uses_only_second_windows(self):
        x,m=feature_row(self.x,self.c,'2026-01','twentieth','2026-01-25T00:00:00Z')
        key='price__'+identity('商品0(规格A)','吨')
        self.assertAlmostEqual(x[key],100*np.log(120/110))
        self.assertEqual(set(m['sources']),{'2025-12:11-20','2026-01:11-20'})

    def test_final_uses_arithmetic_level_means(self):
        x,m=feature_row(self.x,self.c,'2026-01','final','2026-01-25T00:00:00Z')
        key='price__'+identity('商品0(规格A)','吨')
        self.assertAlmostEqual(x[key],100*np.log(115/105))
        self.assertFalse(any('21-end' in k for k in m['sources']))

    def test_early_never_sees_second_window(self):
        x,m=feature_row(self.x,self.c,'2026-01','early','2026-01-15T00:00:00Z')
        self.assertEqual(set(m['sources']),{'2025-12:1-10','2026-01:1-10'})
        with self.assertRaisesRegex(ValueError,'unavailable source release'):
            feature_row(self.x,self.c,'2026-01','twentieth','2026-01-15T00:00:00Z')

    def test_structural_missing_and_basket_transition(self):
        x,m=feature_row(self.x,self.c,'2026-01','twentieth','2026-01-25T00:00:00Z')
        self.assertTrue(pd.isna(x['price__'+identity('新产品(规格B)','吨')]))
        self.assertEqual(len(active_products(self.c,'2026-01')),50)
        self.assertNotEqual(active_products(self.c,'2025-12'),active_products(self.c,'2026-01'))
        xx,_=feature_row(self.x,self.c,'2026-02','twentieth','2026-02-25T00:00:00Z')
        self.assertTrue(np.isfinite(xx['price__'+identity('新产品(规格B)','吨')]))

    def test_pipeline_missing_is_not_structural(self):
        with self.assertRaisesRegex(ValueError,'50 unique'):
            canonicalize(fixture().iloc[1:])
        corrupt=self.x[~(self.x.release_month.eq('2026-01')&self.x.window.eq('11-20')&self.x.product_name.eq('商品0(规格A)'))]
        with self.assertRaisesRegex(ValueError,'unexpected missing'):
            feature_row(corrupt,self.c,'2026-01','twentieth','2026-01-25T00:00:00Z')

    def test_retrieval_cutoff(self):
        late=self.x.copy();late['retrieved_at']=pd.Timestamp('2026-03-01',tz='UTC')
        with self.assertRaisesRegex(ValueError,'unavailable source release'):
            feature_row(late,self.c,'2026-01','twentieth','2026-01-25T00:00:00Z')
        _,m=feature_row(late,self.c,'2026-01','twentieth','2026-01-25T00:00:00Z',False)
        self.assertEqual(m['realtime_status'],'pseudo_real_time')

    def test_fold_local_preprocessing_and_order(self):
        X=pd.DataFrame({'a':[1.,2.,3.,4.,5.,6.],'future':[np.nan]*6,'partial':[np.nan,2.,3.,4.,5.,6.]})
        y=pd.Series([.1,.2,.3,.4,.5,.6])
        m=ProductEstimator('ridge').fit(X,y)
        self.assertNotIn('future',m.columns_)
        np.testing.assert_allclose(m.predict(X),m.predict(X[['partial','future','a']]))
        stable=ProductEstimator('ridge',stable=True).fit(X,y)
        self.assertEqual(stable.columns_,['a'])

    def test_retains_all_families(self):
        self.assertEqual(set(ALL_MODELS),{'ridge','histgb','xgboost','catboost','lightgbm',
            'category_factor','sector_first','random_forest','economic_ml_hybrid','direct_tracker'})


if __name__=='__main__':unittest.main()

import unittest
import numpy as np
import pandas as pd
from china_ppi_nowcast.product.ridge_revision import ObservedScaleRidge


class RidgeRevisionTests(unittest.TestCase):
    def test_observed_scaling_does_not_compress_sparse_variance(self):
        x=pd.DataFrame({'old':np.arange(100.),'new':[np.nan]*95+[1.,2.,3.,4.,5.]})
        fitted=ObservedScaleRidge().fit(x,np.arange(100.)/100)
        self.assertAlmostEqual(fitted.means_['new'],3.)
        self.assertAlmostEqual(fitted.scales_['new'],np.sqrt(2.))
        self.assertEqual(fitted.transform(x).loc[0,'new'],0.)
        self.assertEqual(len(fitted.estimator_.coef_),2)

    def test_training_history_eligibility_and_column_order(self):
        x=pd.DataFrame({'old':np.arange(30.),'new':[np.nan]*25+list(range(5)), 'empty':[np.nan]*30})
        fitted=ObservedScaleRidge(min_observations=12).fit(x,np.arange(30.)/100)
        self.assertEqual(fitted.columns_,['old'])
        self.assertTrue(np.allclose(fitted.predict(x),fitted.predict(x[['empty','new','old']])))
        stable=ObservedScaleRidge(stable=True).fit(x,np.arange(30.)/100)
        self.assertEqual(stable.columns_,['old'])

    def test_constant_series_scale_floor_and_exact_decomposition(self):
        x=pd.DataFrame({'constant':[1.]*30,'price':np.arange(30.)})
        fitted=ObservedScaleRidge().fit(x,np.arange(30.)/100)
        self.assertEqual(fitted.scales_['constant'],1.)
        z=fitted.transform(x.iloc[[-1]])
        expected=fitted.estimator_.intercept_+z.to_numpy()[0]@fitted.estimator_.coef_
        self.assertAlmostEqual(fitted.predict(x.iloc[[-1]])[0],expected)

    def test_saved_revision_august_models_reproduce_without_august_training(self):
        import json
        import hashlib
        import joblib
        from pathlib import Path
        root=Path(__file__).parents[1]
        bundle=root/json.loads((root/'config/product_pipeline.json').read_text())['bundle']
        manifest=json.loads((bundle/'manifest.json').read_text())
        if 'ridge_revision' not in manifest:
            self.skipTest('Revision not activated yet; checked again from clean deployment')
        validation=json.loads((bundle/'ridge_validation.json').read_text())
        self.assertEqual(len(validation['august']),5)
        for row in validation['august']:
            self.assertEqual(row['training_end'],'2026-07')
            matrix=pd.read_csv(bundle/row['variant']/'matrix.csv')
            train=matrix[matrix.target_month.le('2026-07')]
            august=matrix[matrix.target_month.eq('2026-08')]
            model=joblib.load(bundle/row['variant']/f"{row['panel']}_ridge_august_oos.joblib")
            self.assertAlmostEqual(model.predict(august)[0],row['prediction'],places=12)
            pd.testing.assert_series_equal(model.means_,train[model.columns_].mean())
        parent=root/'models'/manifest['ridge_revision']['parent_bundle']
        promoted={r['key'] for r in manifest.get('adaptive_promotions',[])}
        for c in manifest['models']:
            identity='/'.join((c['variant'],c['panel'],c['name']))
            if c['name']!='ridge' and identity not in promoted:
                self.assertEqual(hashlib.sha256((bundle/c['artifact']).read_bytes()).hexdigest(),
                                 hashlib.sha256((parent/c['artifact']).read_bytes()).hexdigest())

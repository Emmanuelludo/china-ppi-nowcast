import unittest
import numpy as np
import pandas as pd
import test_features
from china_ppi_nowcast.features import build_feature_vintage
from china_ppi_nowcast.modeling.models import DirectTrimmedIndex, model_specs_for_vintage


class TwentiethTests(unittest.TestCase):
    def test_only_second_windows_determine_changes(self):
        rows = test_features.FeatureTests().base_rows()
        first = build_feature_vintage(pd.DataFrame(rows), '2026-08', '2026-09-05T00:00:00+08:00')
        self.assertAlmostEqual(first.frame['twentieth_product__测试产品'].iloc[0], 21.0)
        for row in rows:
            if row['window'] != '11-20':
                row['price_cny'] *= 17
        second = build_feature_vintage(pd.DataFrame(rows), '2026-08', '2026-09-05T00:00:00+08:00')
        self.assertEqual(first.frame['twentieth_product__测试产品'].iloc[0], second.frame['twentieth_product__测试产品'].iloc[0])

    def test_early_cutoff_has_no_twentieth_signal(self):
        built = build_feature_vintage(pd.DataFrame(test_features.FeatureTests().base_rows()), '2026-08', '2026-08-14T23:00:00+08:00')
        self.assertTrue(pd.isna(built.frame['twentieth_product__测试产品'].iloc[0]))
        self.assertEqual(len(model_specs_for_vintage('early')), 6)
        self.assertEqual(len(model_specs_for_vintage('final')), 8)

    def test_direct_index_has_no_target_fitted_weights(self):
        x = pd.DataFrame([[*range(9), 1000, np.nan]])
        estimator = DirectTrimmedIndex().fit(x, pd.Series([999]))
        self.assertAlmostEqual(estimator.predict(x)[0], 4.5)
        self.assertTrue(np.isnan(estimator.predict(x * np.nan)[0]))

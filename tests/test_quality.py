import json
import unittest
from pathlib import Path
from unittest.mock import patch
from china_ppi_nowcast.quality import diagnostics,latest_saved

class QualityTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(__file__).parents[1]
        self.bundle=self.root/json.loads((self.root/'config/product_pipeline.json').read_text())['bundle']
        self.manifest=json.loads((self.bundle/'manifest.json').read_text())
        self.cutoff='2026-10-06T20:10:00Z'
    def test_regression_detects_ridge_sensitivity_and_sparse_extrapolation(self):
        q=diagnostics(self.root,self.bundle,self.manifest,self.cutoff)
        self.assertEqual(q['forecast_month'],'2026-09')
        self.assertEqual(len(q['models']),29)
        self.assertAlmostEqual(q['ridge_panel_gap_pp'],1.156297365837328,places=6)
        union=next(r for r in q['models'] if (r['variant'],r['panel'],r['model'])==('twentieth','union','ridge'))
        stable=next(r for r in q['models'] if (r['variant'],r['panel'],r['model'])==('twentieth','stable','ridge'))
        self.assertEqual(union['outside_training_range'],9)
        self.assertEqual(stable['used_products'],25)
        self.assertEqual(union['recent_forecast_months'],10)
        self.assertGreater(union['recent_12_calendar_month_mae'],union['historical_mae'])
    def test_future_target_cutoff_is_rejected(self):
        corrupt=dict(self.manifest,training_actual_cutoff='2026-10-07T00:00:00Z')
        with self.assertRaisesRegex(AssertionError,'Later targets'):
            diagnostics(self.root,self.bundle,corrupt,self.cutoff)
    def test_no_saved_forecasts_before_cutoff(self):
        self.assertEqual(latest_saved(self.root,self.manifest,'2014-01-01T00:00:00Z'),[])

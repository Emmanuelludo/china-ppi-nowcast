import json
import re
import unittest
from pathlib import Path
from china_ppi_nowcast.dashboard import build_data, CORE

class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(__file__).parents[1]
        bundle=self.root/'models/product-v3-6ebe4ddbf8e9c7bc'
        self.manifest=json.loads((bundle/'manifest.json').read_text())
    def test_pending_month_keeps_latest_available_and_retired_models_hidden(self):
        d=build_data(self.root,self.manifest,'2026-10','2026-10-02T10:00:00Z')
        self.assertFalse(d['current_available'])
        self.assertEqual(d['latest_month'],'2026-09')
        self.assertNotIn('category_factor',{r['model'] for r in d['forecasts']})
        self.assertFalse(re.search('[\u4e00-\u9fff]',json.dumps(d,ensure_ascii=False)))
        rows=[r for r in d['forecasts'] if r['month']=='2026-09' and r['timing']=='twentieth' and r['panel']=='union' and r['model'] in CORE]
        self.assertEqual(len(rows),5)
        self.assertEqual(next(r['prediction'] for r in rows if r['model']=='ridge'),-.3423944949137124)
    def test_no_future_forecasts_enter_earlier_cutoff(self):
        d=build_data(self.root,self.manifest,'2014-01','2014-01-01T00:00:00Z')
        self.assertEqual(d['forecasts'],[])
        self.assertIsNone(d['latest_month'])
        self.assertEqual(d['actuals'],[])
    def test_live_payload_preserves_latest_ridge_and_exact_information_set(self):
        manifest=json.loads((self.root/'models/product-ridge-v2-3200ca1610c2d8e9/manifest.json').read_text())
        d=build_data(self.root,manifest,'2026-10','2026-10-07T15:00:00Z')
        r=next(r for r in d['forecasts'] if r['model']=='ridge' and r['timing']=='twentieth' and r['panel']=='union')
        frozen=json.loads((self.root/'data/product/vintages'/r['month']/r['forecast_id'][:20]/'forecast.json').read_text())
        self.assertEqual(r['prediction'],frozen['prediction_mom'])
        self.assertEqual(r['data_cutoff'],frozen['data_cutoff'])
        self.assertEqual(set(r['sources']),{'2026-09:11-20','2026-08:11-20'})
        self.assertEqual(r['training_end'],'2026-08')
        self.assertEqual(r['training_rows'],139)
        self.assertEqual(d['schema_version'],1)
        self.assertFalse(d['current_available'])
        self.assertEqual(d['actuals'][-1]['month'],'2026-08')
        self.assertEqual(d['actuals'][-1]['value'],.4)

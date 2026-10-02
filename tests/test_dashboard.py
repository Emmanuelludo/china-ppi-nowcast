import json
import re
import unittest
from pathlib import Path
from china_ppi_nowcast.dashboard import build_data, CORE

class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(__file__).parents[1]
        bundle=self.root/json.loads((self.root/'config/product_pipeline.json').read_text())['bundle']
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

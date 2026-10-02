import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from china_ppi_nowcast.modeling.refresh import main
from china_ppi_nowcast.features.survey_alignment import AwaitingSourceRelease

class RefreshPendingTests(unittest.TestCase):
    def invoke(self,error):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in ['reports','config','models/reconstructed-v3']:
                (root/name).mkdir(parents=True)
            (root/'reports/history_search.json').write_text(json.dumps({'failed':0,'parser_version':'headline_v2'}))
            (root/'config/pipeline.json').write_text(json.dumps({'first_survey_carry_weight':.5}))
            (root/'models/reconstructed-v3/manifest.json').write_text(json.dumps({'validated':True}))
            with patch('sys.argv',['refresh','--root',tmp,'--target-month','2026-10']), \
                 patch('china_ppi_nowcast.modeling.refresh.create_forecast',side_effect=error), \
                 patch('china_ppi_nowcast.modeling.refresh.repository_status',return_value={}), \
                 patch('china_ppi_nowcast.modeling.refresh.write_status_report') as status:
                main()
                return status.call_args.args[2]
    def test_missing_first_release_is_pending(self):
        result=self.invoke(AwaitingSourceRelease('awaiting first release'))
        self.assertEqual(result['forecast_status'],'pending')
        self.assertEqual(result['forecasts_added'],0)
    def test_other_validation_failures_still_fail(self):
        with self.assertRaisesRegex(ValueError,'leakage'):
            self.invoke(ValueError('leakage'))

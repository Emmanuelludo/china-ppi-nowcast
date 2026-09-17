import json
from pathlib import Path
import tempfile
import unittest
import pandas as pd
from china_ppi_nowcast.product.evaluation import evaluate


class ProductEvaluationTests(unittest.TestCase):
    def test_actual_scoring_waits_for_release_and_never_changes_forecast(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);bundle=root/'models/test';bundle.mkdir(parents=True)
            (root/'reports').mkdir();(root/'data/registry').mkdir(parents=True)
            fp=root/'data/product/vintages/2026-08/test/forecast.json';fp.parent.mkdir(parents=True)
            forecast=dict(forecast_id='frozen',model_version='test',target_month='2026-08',as_of='2026-08-24T02:00:00Z',
                variant='twentieth',model='ridge',panel='union',prediction_mom=.35)
            fp.write_text(json.dumps(forecast));frozen=fp.read_bytes()
            pd.DataFrame([dict(target_month='2026-08',actual_mom_pct=.4,published_at='2026-09-09T01:30:00Z',
                source_url='https://example.test/nbs',content_sha256='actual')]).to_csv(root/'data/registry/actuals.csv',index=False)
            pd.DataFrame([dict(variant='twentieth',panel='union',model='ridge',target_month='2026-07',
                actual=.1,prediction=.2,error=.1,absolute_error=.1,squared_error=.01)]).to_csv(bundle/'rolling_predictions.csv',index=False)
            before=evaluate(root,bundle,'2026-09-08T00:00:00Z')
            self.assertEqual(before['evaluated_forecast_actual_pairs'],0)
            after=evaluate(root,bundle,'2026-09-10T00:00:00Z')
            self.assertEqual(after['evaluated_forecast_actual_pairs'],1)
            records=list((root/'data/product/evaluations').glob('*.json'))
            self.assertEqual(len(records),1)
            record=json.loads(records[0].read_text())
            self.assertAlmostEqual(record['error'],-.05)
            evaluate(root,bundle,'2026-09-11T00:00:00Z')
            self.assertEqual(fp.read_bytes(),frozen)
            self.assertEqual(len(list((root/'data/product/evaluations').glob('*.json'))),1)


if __name__=='__main__':unittest.main()

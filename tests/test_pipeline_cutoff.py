import unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
from china_ppi_nowcast import pipeline


class PipelineCutoffTests(unittest.TestCase):
    def test_new_release_retrieved_during_run_is_available_at_default_cutoff(self):
        start=datetime(2026,9,24,1,30,tzinfo=timezone.utc)
        finished=datetime(2026,9,24,1,35,tzinfo=timezone.utc)
        config=dict(request_timeout_seconds=10,request_retries=1,nbs_index_url='https://example.test',
                    index_pages=1,download_workers=1,model_bundle='models/test',first_survey_carry_weight=.5)
        with patch.object(pipeline,'datetime') as clock, patch.object(pipeline,'load_config',return_value=config), \
             patch.object(pipeline,'ingest_nbs',return_value={}),patch.object(pipeline,'create_forecast',return_value={}) as forecast, \
             patch.object(pipeline,'write_registry_evaluation',return_value={}), \
             patch.object(pipeline,'repository_status',return_value={}),patch.object(pipeline,'write_status_report'):
            clock.now.side_effect=[start,finished]
            pipeline.run_pipeline(Path('.'),target_month='2026-09')
            self.assertEqual(forecast.call_args.args[2],finished.isoformat())
            cutoff='2026-09-14T02:00:00+00:00'
            clock.now.side_effect=[finished]
            pipeline.run_pipeline(Path('.'),target_month='2026-09',as_of=cutoff)
            self.assertEqual(forecast.call_args.args[2],cutoff)

    def test_failed_retrieval_blocks_new_forecast(self):
        config=dict(request_timeout_seconds=10,request_retries=1,nbs_index_url='https://example.test',
                    index_pages=1,download_workers=1,model_bundle='models/test',first_survey_carry_weight=.5)
        with patch.object(pipeline,'load_config',return_value=config), \
             patch.object(pipeline,'ingest_nbs',return_value={'failed':1}), \
             patch.object(pipeline,'create_forecast') as forecast, \
             patch.object(pipeline,'repository_status',return_value={}),patch.object(pipeline,'write_status_report'):
            with self.assertRaisesRegex(RuntimeError,'NBS ingestion failed'):
                pipeline.run_pipeline(Path('.'),target_month='2026-09')
            forecast.assert_not_called()


if __name__=='__main__':unittest.main()

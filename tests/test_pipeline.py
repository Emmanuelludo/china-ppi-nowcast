from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from china_ppi_nowcast.features.survey_alignment import FeatureVintage
from china_ppi_nowcast.forecast.service import _persist_vintage
from china_ppi_nowcast.pipeline import write_status_report


class PipelineTests(unittest.TestCase):
    def test_feature_vintage_artifacts_are_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "vintage"
            first = FeatureVintage(
                frame=pd.DataFrame([{"as_of": "2026-09-14T19:40:00+08:00", "value": 1.0}]),
                product_changes=pd.DataFrame([{"product": "钢材", "value": 1.0}]),
                manifest={"target_month": "2026-09", "vintage": "early", "feature_hash": "abc", "as_of": "first"},
            )
            replay = FeatureVintage(
                frame=pd.DataFrame([{"as_of": "2026-09-14T20:10:00+08:00", "value": 1.0}]),
                product_changes=first.product_changes,
                manifest={**first.manifest, "as_of": "replay"},
            )
            _persist_vintage(directory, first)
            before = {path.name: path.read_bytes() for path in directory.iterdir()}
            _persist_vintage(directory, replay)
            after = {path.name: path.read_bytes() for path in directory.iterdir()}
            self.assertEqual(before, after)

    def test_ephemeral_run_cutoff_does_not_change_committed_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status = {"observations": 600, "forecasts": 12}
            first = {"target_month": "2026-09", "as_of": "2026-09-14T10:00:00+08:00"}
            second = {"target_month": "2026-09", "as_of": "2026-09-14T11:00:00+08:00"}
            write_status_report(root, status, first)
            before = (root / "reports" / "latest.md").read_bytes()
            write_status_report(root, status, second)
            after = (root / "reports" / "latest.md").read_bytes()
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from china_ppi_nowcast.registry import append_forecasts


class RegistryTests(unittest.TestCase):
    def example(self, estimate: float = 0.2) -> dict[str, object]:
        return {
            "target_month": "2026-09", "as_of": "2026-09-24T10:00:00+08:00",
            "vintage": "final", "model_key": "ridge", "model_label": "Ridge",
            "model_version": "test", "model_provenance": "test", "estimate_mom_pct": estimate,
            "feature_hash": "abc", "status": "frozen_pre_release"
        }

    def test_idempotent_and_conflict_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "forecasts.csv"
            self.assertEqual(append_forecasts(path, [self.example()]), 1)
            self.assertEqual(append_forecasts(path, [self.example()]), 0)
            later_same_data = self.example()
            later_same_data["as_of"] = "2026-09-25T10:00:00+08:00"
            self.assertEqual(append_forecasts(path, [later_same_data]), 0)
            self.assertEqual(append_forecasts(path, [self.example(0.2 + 1e-14)]), 0)
            self.assertEqual(len(pd.read_csv(path)), 1)
            with self.assertRaises(ValueError):
                append_forecasts(path, [self.example(0.3)])


if __name__ == "__main__":
    unittest.main()

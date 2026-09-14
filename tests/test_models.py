from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from china_ppi_nowcast.modeling import MODEL_SPECS, load_bundle, predict_bundle, train_bundle


class ModelTests(unittest.TestCase):
    def test_committed_reconstructed_bundles_load(self) -> None:
        root = Path(__file__).parents[1] / "models" / "reconstructed-v1"
        for vintage in ("early", "final"):
            manifest, models = load_bundle(root / vintage, require_validated=True)
            self.assertTrue(manifest["validated"])
            self.assertEqual(set(models), {spec.key for spec in MODEL_SPECS})

    def test_all_six_reconstructed_models_train_and_predict(self) -> None:
        rng = np.random.default_rng(20260914)
        n = 30
        signal = rng.normal(0, 0.5, n)
        frame = pd.DataFrame({
            "target_month": pd.period_range("2024-01", periods=n, freq="M").astype(str),
            "target_mom_pct": 0.7 * signal + rng.normal(0, 0.08, n),
            "global__mean": signal,
            "category__一、测试__mean": signal + rng.normal(0, 0.05, n),
            "category__一、测试__missing": np.zeros(n),
            "product__测试产品": signal + rng.normal(0, 0.1, n),
            "missing__测试产品": np.zeros(n),
            "econ__reviewed_test": rng.normal(0, 1, n),
        })
        frame.loc[3, "product__测试产品"] = np.nan
        frame.loc[3, "missing__测试产品"] = 1
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            manifest = train_bundle(frame, output)
            self.assertFalse(manifest["validated"])
            self.assertEqual(len(manifest["models"]), len(MODEL_SPECS))
            self.assertIn("missing_panel_stress", manifest["models"][0]["metrics"])
            feature_row = frame.drop(columns=["target_mom_pct"]).tail(1)
            predictions = predict_bundle(output, feature_row, require_validated=False)
            self.assertEqual(len(predictions), 6)
            self.assertTrue(all(np.isfinite(item["estimate_mom_pct"]) for item in predictions))

    def test_operational_validation_requires_chronology_metadata(self) -> None:
        rng = np.random.default_rng(7)
        n = 40
        signal = rng.normal(0, 0.4, n)
        frame = pd.DataFrame({
            "target_month": pd.period_range("2022-01", periods=n, freq="M").astype(str),
            "target_mom_pct": signal,
            "global__mean": signal + rng.normal(0, 0.1, n),
            "category__测试__mean": signal,
            "product__测试": signal,
            "missing__测试": np.zeros(n),
        })
        metadata = {"actual_after_cutoff": True, "realtime_status": "pseudo_real_time"}
        with tempfile.TemporaryDirectory() as tmp:
            manifest = train_bundle(
                frame, Path(tmp), validate=True, vintage="early", training_metadata=metadata
            )
            self.assertTrue(manifest["validated"])


if __name__ == "__main__":
    unittest.main()

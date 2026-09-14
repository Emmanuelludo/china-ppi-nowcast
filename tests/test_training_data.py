from __future__ import annotations

import unittest

import pandas as pd

from china_ppi_nowcast.modeling import build_training_matrix


def observation(month: str, window: str, price: float, published: str) -> dict[str, object]:
    return {
        "release_id": f"{month}-{window}", "release_month": month, "window": window,
        "category_cn": "一、测试", "product_name_cn": "产品", "unit_cn": "吨",
        "price_cny": price, "change_cny": 0, "change_pct": 0,
        "published_at": published, "retrieved_at": "2026-09-14T00:00:00Z",
        "source_url": f"https://example/{month}/{window}", "content_sha256": f"{month}-{window}",
    }


class TrainingDataTests(unittest.TestCase):
    def test_historical_matrix_is_labeled_and_target_is_released_later(self) -> None:
        observations = pd.DataFrame([
            observation("2025-12", "21-end", 100, "2026-01-04T09:00:00+08:00"),
            observation("2026-01", "1-10", 100, "2026-01-14T09:00:00+08:00"),
            observation("2026-01", "11-20", 100, "2026-01-24T09:00:00+08:00"),
            observation("2026-01", "21-end", 105, "2026-02-04T09:00:00+08:00"),
            observation("2026-02", "1-10", 105, "2026-02-14T09:00:00+08:00"),
            observation("2026-02", "11-20", 110, "2026-02-24T09:00:00+08:00"),
        ])
        actuals = pd.DataFrame([{
            "target_month": "2026-02", "actual_mom_pct": 0.3,
            "published_at": "2026-03-10T09:30:00+08:00",
        }])
        matrix, manifest = build_training_matrix(observations, actuals, "final")
        self.assertEqual(len(matrix), 1)
        self.assertTrue(manifest["actual_after_cutoff"])
        self.assertEqual(manifest["realtime_status"], "pseudo_real_time")


if __name__ == "__main__":
    unittest.main()

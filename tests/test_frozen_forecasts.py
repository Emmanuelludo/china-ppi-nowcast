from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


class FrozenForecastTests(unittest.TestCase):
    def test_august_values_are_exact(self) -> None:
        path = Path(__file__).parents[1] / "data" / "registry" / "forecasts.csv"
        frame = pd.read_csv(path)
        august = frame[frame.target_month == "2026-08"]
        self.assertEqual(len(august), 12)
        early = august[august.vintage == "early"].set_index("model_key").estimate_mom_pct.to_dict()
        final = august[august.vintage == "final"].set_index("model_key").estimate_mom_pct.to_dict()
        self.assertEqual(early, {
            "category_factor_regression": 0.187, "gradient_boosting": 0.397,
            "economic_ml_hybrid": 0.311, "product_level_ridge": 0.412,
            "sector_first_aggregation": 0.188, "random_forest": 0.438,
        })
        self.assertEqual(final, {
            "category_factor_regression": 0.279, "gradient_boosting": 0.453,
            "economic_ml_hybrid": 0.370, "product_level_ridge": 0.410,
            "sector_first_aggregation": 0.227, "random_forest": 0.509,
        })


if __name__ == "__main__":
    unittest.main()

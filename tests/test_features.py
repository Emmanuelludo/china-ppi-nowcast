from __future__ import annotations

import math
import unittest

import pandas as pd

from china_ppi_nowcast.features import build_feature_vintage, select_available_observations


def row(month: str, window: str, price: float, published: str, retrieved: str, url: str | None = None, digest: str | None = None) -> dict[str, object]:
    return {
        "release_id": f"{month}:{window}",
        "release_month": month,
        "window": window,
        "category_cn": "一、测试类别",
        "product_name_cn": "测试产品",
        "unit_cn": "吨",
        "price_cny": price,
        "change_cny": 0,
        "change_pct": 0,
        "published_at": published,
        "retrieved_at": retrieved,
        "source_url": url or f"https://example/{month}/{window}",
        "content_sha256": digest or f"{month}-{window}-{price}",
    }


class FeatureTests(unittest.TestCase):
    def base_rows(self) -> list[dict[str, object]]:
        return [
            row("2026-06", "21-end", 100, "2026-07-04T09:30:00+08:00", "2026-07-04T02:00:00Z"),
            row("2026-07", "1-10", 100, "2026-07-14T09:30:00+08:00", "2026-07-14T02:00:00Z"),
            row("2026-07", "11-20", 100, "2026-07-24T09:30:00+08:00", "2026-07-24T02:00:00Z"),
            row("2026-07", "21-end", 110, "2026-08-04T09:30:00+08:00", "2026-08-04T02:00:00Z"),
            row("2026-08", "1-10", 110, "2026-08-14T09:30:00+08:00", "2026-08-14T02:00:00Z"),
            row("2026-08", "11-20", 121, "2026-08-24T09:30:00+08:00", "2026-08-24T02:00:00Z"),
            row("2026-08", "21-end", 10000, "2026-09-04T09:30:00+08:00", "2026-09-04T02:00:00Z"),
        ]

    def test_final_alignment_excludes_target_third_window(self) -> None:
        vintage = build_feature_vintage(
            pd.DataFrame(self.base_rows()), "2026-08", "2026-09-05T00:00:00+08:00", carry_weight=0.5
        )
        expected = 100 * (math.sqrt(110 * 121) / 100 - 1)
        actual = float(vintage.product_changes.iloc[0]["survey_aligned_change_pct"])
        self.assertEqual(vintage.manifest["vintage"], "final")
        self.assertFalse(vintage.manifest["current_21_end_used"])
        self.assertNotIn(
            ("2026-08", "21-end"),
            {(item["release_month"], item["window"]) for item in vintage.manifest["sources"]},
        )
        self.assertAlmostEqual(actual, expected, places=8)

    def test_early_vintage_uses_first_survey_only(self) -> None:
        rows = self.base_rows()[:5]
        vintage = build_feature_vintage(pd.DataFrame(rows), "2026-08", "2026-08-14T23:00:00+08:00")
        self.assertEqual(vintage.manifest["vintage"], "early")
        self.assertAlmostEqual(float(vintage.product_changes.iloc[0]["survey_aligned_change_pct"]), 10.0)

    def test_retrieval_after_cutoff_is_leakage_and_excluded(self) -> None:
        rows = self.base_rows()
        rows.append(
            row(
                "2026-08", "1-10", 999, "2026-08-14T09:30:00+08:00", "2026-09-01T02:00:00Z",
                url="https://example/2026-08/1-10", digest="late-correction"
            )
        )
        selected = select_available_observations(pd.DataFrame(rows), "2026-08-24T23:00:00+08:00")
        value = selected.loc[(selected.release_month == "2026-08") & (selected.window == "1-10"), "price_cny"].iloc[0]
        self.assertEqual(float(value), 110.0)


if __name__ == "__main__":
    unittest.main()

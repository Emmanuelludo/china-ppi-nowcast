from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path

from china_ppi_nowcast.ingest.nbs import parse_ppi_page, parse_ten_day_page


FIXTURES = Path(__file__).parent / "fixtures"


class IngestTests(unittest.TestCase):
    def test_parse_ten_day_page_preserves_chinese_fields(self) -> None:
        content = (FIXTURES / "nbs_ten_day_sample.html").read_bytes()
        frame = parse_ten_day_page(content, "https://www.stats.gov.cn/example.html", datetime(2026, 4, 24, 2, tzinfo=timezone.utc))
        self.assertEqual(len(frame), 3)
        self.assertEqual(frame.iloc[0]["release_month"], "2026-04")
        self.assertEqual(frame.iloc[0]["window"], "11-20")
        self.assertEqual(frame.iloc[0]["category_cn"], "一、黑色金属")
        self.assertAlmostEqual(float(frame.iloc[2]["price_cny"]), 101647.5)

    def test_parse_ppi_headline_mom(self) -> None:
        content = (FIXTURES / "nbs_ppi_sample.html").read_bytes()
        row = parse_ppi_page(content, "https://www.stats.gov.cn/ppi.html", datetime(2026, 4, 10, 2, tzinfo=timezone.utc))
        self.assertEqual(row["target_month"], "2026-03")
        self.assertAlmostEqual(float(row["actual_mom_pct"]), 0.4)


if __name__ == "__main__":
    unittest.main()

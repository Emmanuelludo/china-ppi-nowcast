from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path

from china_ppi_nowcast.ingest.nbs import parse_ppi_page, parse_ten_day_page
from china_ppi_nowcast.time import Window, parse_release_title


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

    def test_parse_legacy_numeric_window_title(self) -> None:
        parsed = parse_release_title("流通领域重要生产资料市场价格变动情况（2014年1月1-10日）")
        self.assertEqual(parsed, ("2014-01", Window.FIRST))

    def test_parse_ppi_headline_modifiers(self) -> None:
        for phrase, expected in [("环比均下降0.2%", -0.2), ("环比继续上涨0.1%", 0.1), ("环比分别下降0.2%、0.3%", -0.2), ("环比持平", 0.0)]:
            page = f"""<html><head><meta charset="utf-8"><title>2025年1月份工业生产者出厂价格</title></head>
            <body><p>2025/02/09 09:30</p><p>2025年1月份，全国工业生产者出厂价格{phrase}。</p></body></html>""".encode()
            row = parse_ppi_page(page, "https://example/ppi", datetime(2025, 2, 9, tzinfo=timezone.utc))
            self.assertAlmostEqual(float(row["actual_mom_pct"]), expected)


if __name__ == "__main__":
    unittest.main()

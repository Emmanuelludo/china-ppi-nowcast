from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path

from china_ppi_nowcast.ingest.nbs import parse_ten_day_page
from china_ppi_nowcast.validation import validate_release


class ValidationTests(unittest.TestCase):
    def test_fixture_validates_with_expected_small_panel_warning(self) -> None:
        content = (Path(__file__).parent / "fixtures" / "nbs_ten_day_sample.html").read_bytes()
        frame = parse_ten_day_page(content, "https://example/release", datetime.now(timezone.utc))
        warnings = validate_release(frame, minimum_products=40)
        self.assertEqual(len(warnings), 1)

    def test_nonpositive_price_fails(self) -> None:
        content = (Path(__file__).parent / "fixtures" / "nbs_ten_day_sample.html").read_bytes()
        frame = parse_ten_day_page(content, "https://example/release", datetime.now(timezone.utc))
        frame.loc[0, "price_cny"] = 0
        with self.assertRaises(ValueError):
            validate_release(frame)


if __name__ == "__main__":
    unittest.main()

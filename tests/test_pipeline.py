from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from china_ppi_nowcast.pipeline import write_status_report


class PipelineTests(unittest.TestCase):
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

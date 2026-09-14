from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from china_ppi_nowcast.storage import atomic_write_csv, read_csv_or_empty


class StorageTests(unittest.TestCase):
    def test_compressed_csv_round_trip_preserves_unicode(self) -> None:
        source = pd.DataFrame([{"product": "钢材", "price": 1.25}])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "observations.csv.gz"
            atomic_write_csv(path, source)
            loaded = read_csv_or_empty(path, source.columns)
        self.assertEqual(loaded.to_dict(orient="records"), [{"product": "钢材", "price": "1.25"}])


if __name__ == "__main__":
    unittest.main()

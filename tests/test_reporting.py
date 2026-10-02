import json
import unittest
from pathlib import Path
from china_ppi_nowcast.reporting import LABELS, matrix_table, product_name
from china_ppi_nowcast.model_policy import is_active

class ReportingTests(unittest.TestCase):
    def test_english_labels_cover_saved_catalog(self):
        root=Path(__file__).parents[1]
        bundle=root/json.loads((root/'config/product_pipeline.json').read_text())['bundle']
        catalog=json.loads((bundle/'catalog.json').read_text())
        self.assertTrue(set(catalog['products']) <= set(LABELS['products']))
        for pid in catalog['products']:
            self.assertFalse(any('\u4e00' <= c <= '\u9fff' for c in product_name(pid)))
    def test_retired_category_is_excluded_from_current_comparison(self):
        rows=[dict(model=m,variant='twentieth',panel='union',prediction_mom=.625)
              for m in ['ridge','category_factor']]
        text='\n'.join(matrix_table(rows))
        self.assertIn('+0.625%',text)
        self.assertNotIn('Category',text)
        self.assertFalse(is_active('category_factor_regression'))
        self.assertTrue(is_active('sector_first'))

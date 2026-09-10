import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('sector_targets',Path(__file__).parents[1]/'scripts/v2_collect_sector_targets.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

def fixture(date='2026/02/11 09:30'):
    return f'''<html><meta name="ArticleTitle" content="2026年1月份工业生产者出厂价格同比下降"><meta name="PubDate" content="{date}"><table><tr><td></td><td>环比</td><td>同比</td></tr><tr><td>一、工业生产者出厂价格</td><td>0.4</td><td>-1.4</td></tr><tr><td>生产资料</td><td>0.5</td><td>-1.3</td></tr><tr><td>三、主要行业出厂价格</td><td></td><td></td></tr><tr><td>煤炭开采和洗选业</td><td>-3.2</td><td>-9.8</td></tr></table></html>'''.encode()

def test_targets_preserve_units_date_and_rows():
    rows=module.parse(fixture(),'https://www.stats.gov.cn/test')
    assert len(rows)==6
    assert rows[0]['target_id']=='headline_ppi_mom'
    assert rows[0]['value']==0.4
    assert rows[0]['available_at']=='2026-02-11T09:30:00+08:00'
    assert rows[-1]['component_type']=='industry'

def test_date_only_conservative():
    rows=module.parse(fixture('2026/02/11'),'https://www.stats.gov.cn/test')
    assert rows[0]['available_at'].endswith('23:59:59+08:00')

def test_migrated_page_rejected():
    with pytest.raises(ValueError): module.parse(fixture('2029/02/11'),'https://www.stats.gov.cn/test')

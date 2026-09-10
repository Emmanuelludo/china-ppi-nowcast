import importlib.util,json
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('archive',Path(__file__).parents[1]/'scripts/v4_archive.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_append_and_integrity(tmp_path):
    p=tmp_path/'data/v4/fitted/model.joblib';p.parent.mkdir(parents=True);p.write_bytes(b'fixture1')
    first=m.archive(tmp_path)
    assert m.archive(tmp_path)==first
    stamp=json.loads((first/'manifest.json').read_text())['recorded_at']
    assert stamp.endswith('+00:00')
    p.write_bytes(b'fixture2');second=m.archive(tmp_path)
    assert second!=first
    assert (first/'data/v4/fitted/model.joblib').read_bytes()==b'fixture1'
    (second/'data/v4/fitted/model.joblib').write_bytes(b'tampered')
    with pytest.raises(ValueError,match='integrity'):m.archive(tmp_path)
def test_missing_models(tmp_path):
    with pytest.raises(ValueError,match='No fitted'):m.archive(tmp_path)

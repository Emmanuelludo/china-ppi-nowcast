"""Read saved model contracts and prove repeat inference preserves frozen vintages."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import joblib
import numpy as np
import pandas as pd
from china_ppi_nowcast.product.service import run
from china_ppi_nowcast.time import CHINA_TZ

root=Path.cwd()
bundle=root/json.loads((root/'config/product_pipeline.json').read_text())['bundle']
manifest=json.loads((bundle/'manifest.json').read_text())
assert len(manifest['models'])==30
checked=0
for candidate in manifest['models']:
    artifact=bundle/candidate['artifact']
    if candidate.get('artifact_sha256'):
        assert hashlib.sha256(artifact.read_bytes()).hexdigest()==candidate['artifact_sha256']
    fitted=joblib.load(artifact)
    matrix=pd.read_csv(bundle/candidate['variant']/'matrix.csv')
    X=matrix.tail(1).reindex(columns=candidate['feature_order'])
    prediction=fitted.predict(X)
    assert np.isfinite(prediction).all()
    attribution=fitted.attribution(X)
    if attribution is not None:
        baseline,values,_=attribution
        assert np.allclose(baseline+values.sum(axis=1),prediction,rtol=2e-5,atol=2e-5)
    checked+=1

def snapshots():
    files=list((root/'data/product/vintages').rglob('*.json'))+[root/'data/registry/forecasts.csv']
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

registry=pd.read_csv(root/'data/registry/forecasts.csv').set_index('forecast_id')
expected={'early':dict(cfr=.187,gb=.397,hybrid=.311,ridge=.412,sector=.188,rf=.438),
          'final':dict(cfr=.279,gb=.453,hybrid=.370,ridge=.410,sector=.227,rf=.509)}
for vintage,models in expected.items():
    for model,value in models.items():
        row=registry.loc[f'frozen-202608-{vintage}-{model}']
        assert float(row.estimate_mom_pct)==value, 'Frozen August forecast changed'
before=snapshots()
now=datetime.now(CHINA_TZ)
result=run(root,bundle,now.strftime('%Y-%m'),now.isoformat())
after_first=snapshots()
assert all(after_first.get(k)==v for k,v in before.items()),'Existing forecast changed'
run(root,bundle,now.strftime('%Y-%m'),now.isoformat())
assert snapshots()==after_first,'Repeat inference not idempotent'
print(json.dumps(dict(models_verified=checked,source_start=manifest['source_start'],
    immutable_files_checked=len(before),repeat_inference='passed',result=result),indent=2))

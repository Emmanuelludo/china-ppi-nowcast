"""Read-only clean-checkout verification of the adaptive deployment contracts."""
from pathlib import Path
import hashlib,json
import joblib
import numpy as np
import pandas as pd
from china_ppi_nowcast.adaptive.engine import read_events,replay

root=Path.cwd();events=read_events(root)
assert events,'Adaptive monitoring not initialized'
state=replay(events)
assert state==json.loads((root/'data/adaptive/state.json').read_text()),'Adaptive cache does not match authoritative journal'
refs=list(state['champions'].values())
for c in state['cycles'].values():
 if c.get('challenger'):refs.append(c['challenger'])
for ref in refs:
 path=root/ref['bundle']/ref['candidate']['artifact']
 assert hashlib.sha256(path.read_bytes()).hexdigest()==ref['model_id'],'Adaptive model artifact changed'
pairs=0
for path in (root/'data/adaptive/forecasts').glob('*/*/pair.json'):
 r=json.loads(path.read_text());cycle=state['cycles'][r['cycle_id']];meta=json.loads((path.parent/'features.json').read_text())
 assert r['feature_hash']==meta['feature_hash'],'Trial feature identity differs'
 assert pd.Timestamp(r['as_of'])>=pd.Timestamp(cycle['requested_at'])
 for sources in meta['sources'].values():
  for source in sources:
   assert pd.Timestamp(source['published_at'])<=pd.Timestamp(r['as_of'])
   assert pd.Timestamp(source['retrieved_at'])<=pd.Timestamp(r['as_of'])
 X=pd.DataFrame([meta['values']],dtype=float)
 for role in ['champion','challenger']:
  ref=cycle[role];candidate=ref['candidate']
  assert candidate['training_end']<r['target_month'],'Trial target leakage'
  model=joblib.load(root/ref['bundle']/candidate['artifact'])
  assert np.isclose(model.predict(X.reindex(columns=candidate['feature_order']))[0],r[role+'_prediction'],rtol=0,atol=1e-10)
 for attr_path in path.parent.glob('*_attributions.json'):
  a=json.loads(attr_path.read_text());assert np.isclose(a['baseline']+sum(a['product'].values()),a['prediction'],rtol=2e-5,atol=2e-5)
 pairs+=1
for cycle in state['cycles'].values():
 for month,h in cycle.get('decision',{}).get('evaluation_hashes',{}).items():
  from china_ppi_nowcast.product.data import digest
  r=json.loads((root/'data/adaptive/evaluations'/cycle['cycle_id']/(month+'.json')).read_text())
  assert digest(r)==h,'Promotion evaluation evidence changed'
for path in (root/'data/adaptive/evaluations').glob('*/*.json'):
 r=json.loads(path.read_text());assert pd.Timestamp(r['as_of'])<pd.Timestamp(r['actual_published_at']),'Post-release trial forecast'
print(json.dumps(dict(adaptive_monitored_models=len(state['champions']),journal_events=len(events),
    journal_integrity='passed',derived_state='passed',fitted_artifacts='passed',matched_forecasts_reproduced=pairs),indent=2))

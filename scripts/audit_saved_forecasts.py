"""Reproduce the latest actual forecast rows, not only training-row smoke tests."""
from pathlib import Path
from datetime import datetime,timezone
import json
import gzip
import hashlib
import joblib
import numpy as np
import pandas as pd
from china_ppi_nowcast.quality import latest_saved,diagnostics
from china_ppi_nowcast.ingest.nbs import parse_ten_day_page
from china_ppi_nowcast.product.data import canonicalize,feature_row,digest

root=Path.cwd();bundle=root/json.loads((root/'config/product_pipeline.json').read_text())['bundle']
manifest=json.loads((bundle/'manifest.json').read_text());as_of=datetime.now(timezone.utc).isoformat()
rows=latest_saved(root,manifest,as_of);candidates={(c['variant'],c['panel'],c['name']):c for c in manifest['models']}
observations=pd.read_csv(root/'data/processed/nbs_ten_day_observations.csv.gz')
x=canonicalize(observations)
verified_sources=set()
for r in rows:
 candidate=candidates[(r['variant'],r['panel'],r['model'])]
 directory=root/'data/product/vintages'/r['target_month']/r['forecast_id'][:20]
 frozen=json.loads((directory/'features.json').read_text())
 for sources in frozen['sources'].values():
  for source in sources:
   sha=source['content_sha256']
   if sha in verified_sources:continue
   raw=gzip.decompress((root/'data/raw/nbs/objects'/f'{sha}.html.gz').read_bytes())
   assert hashlib.sha256(raw).hexdigest()==sha,'Raw source hash mismatch'
   fresh=parse_ten_day_page(raw,source['source_url'],datetime.fromisoformat(source['retrieved_at']))
   stored=observations[observations.content_sha256.eq(sha)].set_index(['product_name_cn','unit_cn'])
   fresh=fresh.set_index(['product_name_cn','unit_cn']).reindex(stored.index)
   assert len(stored)==50 and len(fresh)==50,'Source product panel mismatch'
   assert np.allclose(fresh.price_cny,stored.price_cny,rtol=0,atol=1e-9),'Raw source absolute prices differ'
   verified_sources.add(sha)
 values,rebuilt=feature_row(x,json.loads((bundle/'catalog.json').read_text()),r['target_month'],r['variant'],r['as_of'],True)
 assert digest({k:v for k,v in frozen.items() if k not in ('feature_hash','as_of')})==frozen['feature_hash'],'Frozen feature content hash differs'
 for key in frozen:
  if key not in ('values','feature_hash','as_of'):assert rebuilt[key]==frozen[key],'Frozen source/feature metadata differs: '+key
 assert set(rebuilt['values'])==set(frozen['values']),'Feature order/identity differs'
 for key,value in frozen['values'].items():
  fresh=rebuilt['values'][key]
  assert (fresh is None) if value is None else (fresh is not None and np.isclose(fresh,value,rtol=0,atol=1e-12)), 'Frozen feature values differ'
 # Logarithms may differ in their final binary bit across NumPy/platform builds.
 # Metadata and missingness remain exact; numeric reconstruction uses 1e-12 pp tolerance.
 fitted=joblib.load(bundle/candidate['artifact']);X=pd.DataFrame([frozen['values']],dtype=float).reindex(columns=candidate['feature_order'])
 prediction=float(fitted.predict(X)[0]);assert np.isclose(prediction,r['prediction_mom'],rtol=0,atol=1e-10),'Saved forecast reproduction differs'
 p=directory/'shap.json'
 if p.exists():
  a=json.loads(p.read_text());assert np.isclose(a['baseline']+sum(a['product'].values()),prediction,rtol=2e-5,atol=2e-5),'Saved SHAP does not reconcile'
quality=diagnostics(root,bundle,manifest,as_of)
print(json.dumps(dict(latest_forecast_month=quality['forecast_month'],live_saved_forecasts_reproduced=len(rows),
 raw_source_snapshots_reparsed=len(verified_sources),frozen_feature_content_hash='passed',source_feature_reconstruction='passed (1e-12 pp tolerance)',fitted_prediction_reproduction='passed',frozen_shap_reconciliation='passed',
 ridge_panel_gap_pp=quality['ridge_panel_gap_pp']),indent=2))

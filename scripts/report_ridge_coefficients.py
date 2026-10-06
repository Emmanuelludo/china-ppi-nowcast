"""Readable fitted ridge coefficients and latest-vintage linear decomposition."""
from pathlib import Path
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime,timezone
from china_ppi_nowcast.quality import latest_saved
from china_ppi_nowcast.reporting import product_name

root=Path.cwd();bundle=root/json.loads((root/'config/product_pipeline.json').read_text())['bundle']
manifest=json.loads((bundle/'manifest.json').read_text())
if 'ridge_revision' not in manifest:raise SystemExit('No revised ridge bundle active')
candidates={(c['variant'],c['panel'],c['name']):c for c in manifest['models']}
records=[]
for r in latest_saved(root,manifest,datetime.now(timezone.utc).isoformat()):
 if r['model']!='ridge':continue
 forecast_bundle=bundle if r['model_version']==manifest['version'] else root/'models'/r['model_version']
 actual_manifest=manifest if forecast_bundle==bundle else json.loads((forecast_bundle/'manifest.json').read_text())
 c=next(c for c in actual_manifest['models'] if (c['variant'],c['panel'],c['name'])==(r['variant'],r['panel'],r['model']))
 model=joblib.load(forecast_bundle/c['artifact'])
 if not hasattr(model,'scales_'):continue
 directory=root/'data/product/vintages'/r['target_month']/r['forecast_id'][:20]
 frozen=json.loads((directory/'features.json').read_text())
 x=pd.DataFrame([frozen['values']],dtype=float);z=model.transform(x)
 contribution=z.to_numpy()[0]*model.estimator_.coef_
 assert np.isclose(model.estimator_.intercept_+contribution.sum(),r['prediction_mom'],rtol=0,atol=1e-12)
 for i,k in enumerate(model.columns_):
  records.append(dict(model_version=r['model_version'],forecast_month=r['target_month'],as_of=r['as_of'],timing=r['variant'],panel=r['panel'],
   product=product_name(k.split('__',1)[1]),feature=k,observed_training_months=int(model.counts_[k]),
   observed_training_mean=float(model.means_[k]),observed_training_sd_with_floor=float(model.scales_[k]),
   live_log_change=x[k].iloc[0],standardized_value=float(z[k].iloc[0]),
   standardized_coefficient=float(model.estimator_.coef_[i]),raw_coefficient=float(model.estimator_.coef_[i]/model.scales_[k]),
   contribution_pp=float(contribution[i]),intercept_pp=float(model.estimator_.intercept_),prediction_mom=r['prediction_mom'],
   alpha=model.alpha,minimum_history=model.min_observations,missingness_indicators=False))
pd.DataFrame(records).to_csv(root/'reports/ridge_coefficients.csv',index=False)
print(f'Ridge coefficients and exact forecast decomposition saved: {len(records)} feature rows')

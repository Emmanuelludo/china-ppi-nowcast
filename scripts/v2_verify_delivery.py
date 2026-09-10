"""Validate delivered forecast timestamps, identities and additive attribution."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1]
def main():
 f=pd.read_csv(R/'data/v2/models/rolling_forecasts.csv')
 c=pd.read_csv(R/'data/v2/models/current_nowcasts.csv')
 a=pd.read_csv(R/'data/v2/models/current_attributions.csv')
 key=['target_month','vintage','target_id','window','model']
 assert not f.duplicated(key).any(), 'Duplicate forecast identities'
 assert (pd.to_datetime(f.forecast_vintage,utc=True)<pd.to_datetime(f.actual_available_at,utc=True)).all(),'Post-release forecast'
 assert (f.n_train>=36).all()
 assert f[['actual','forecast']].notna().all().all()
 assert (f.loc[f.interval_calibration_n<12,['lower_80','upper_80']].isna()).all().all()
 sums=a.groupby(key).contribution.sum().rename('sum').reset_index()
 check=c.merge(sums,on=key,validate='one_to_one')
 assert np.allclose(check.forecast,check['sum'],atol=1e-8),'Contributions do not reconcile'
 p=pd.read_csv(R/'data/v2/products/mapped_raw_observations.csv')
 assert p.exact_product_id.notna().all()
 assert not p.category_id.eq('UNRESOLVED').any()
 result=dict(status='passed',historical_forecasts=len(f),targets=f.target_id.nunique(),attribution_forecasts_checked=len(check),raw_observations=len(p),unique_exact_specs=p.exact_product_id.nunique())
 (R/'reports/v2/delivery_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()

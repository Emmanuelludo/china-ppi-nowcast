"""As-of industry-revenue-weighted aggregation of separately forecast sector PPI.
An incomplete-coverage economic proxy, never official headline PPI weights.
"""
from pathlib import Path
import re
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def normalize(x):return re.sub(r'[\s、，,]','',x).replace('及','和')
def main():
    folder=ROOT/'data/v2/models'
    f=pd.concat([pd.read_csv(folder/'rolling_forecasts.csv'),pd.read_csv(folder/'current_nowcasts.csv')])
    f=f[(f.window=='expanding')&(f.model=='ridge')&(f.vintage=='final')&f.target_id.str.startswith('industry_')]
    t=pd.read_csv(ROOT/'data/v2/targets/sector_targets_long.csv').drop_duplicates('target_id').set_index('target_id')
    f['industry']=f.target_id.map(t.target_name_zh).map(normalize)
    w=pd.read_csv(ROOT/'data/v2/weights/industry_revenue_weights.csv');w['industry']=w.industry_name.map(normalize)
    w['available_at']=pd.to_datetime(w.available_at,utc=True)
    rows=[];detail=[]
    for month,g in f.groupby('target_month'):
        cutoff=pd.to_datetime(g.forecast_vintage,utc=True).min()
        eligible=w[w.available_at<cutoff]
        if eligible.empty:continue
        latest=eligible.available_at.max();weights=eligible[eligible.available_at==latest]
        joined=g.merge(weights[['industry','economic_weight','available_at','source_url']],on='industry',validate='one_to_one')
        if joined.empty:continue
        coverage=joined.economic_weight.sum();joined['normalized_weight']=joined.economic_weight/coverage
        joined['weighted_contribution']=joined.normalized_weight*joined.forecast
        detail.append(joined)
        rows.append(dict(target_month=month,forecast_vintage=cutoff.isoformat(),weight_available_at=latest.isoformat(),forecast=joined.weighted_contribution.sum(),actual=(joined.normalized_weight*joined.actual).sum() if joined.actual.notna().all() else None,covered_revenue_share=coverage,sectors=len(joined),measure='revenue_weighted_covered_sector_ppi_proxy_not_headline'))
    pd.DataFrame(rows).to_csv(folder/'economic_sector_proxy.csv',index=False)
    if detail:pd.concat(detail).to_csv(folder/'economic_sector_contributions.csv',index=False)
if __name__=='__main__':main()

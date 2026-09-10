"""One return per family/spec; published-change chain indices retain basket history.
No price level splices. Raw NaNs remain for native-missing tree models.
"""
from pathlib import Path
import re
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1]

CATEGORY_IDS = {
 '黑色金属':'CAT_ferrous_metals', '有色金属':'CAT_nonferrous_metals',
 '化工产品':'CAT_chemicals', '石油天然气':'CAT_petroleum_gas', '煤炭':'CAT_coal',
 '非金属矿产品':'CAT_nonmetallic', '非金属建材':'CAT_nonmetallic',
 '非金属矿物制品':'CAT_nonmetallic', '农产品':'CAT_agricultural',
 '农产品（主要用于加工）':'CAT_agricultural', '农业生产资料':'CAT_ag_inputs',
 '农资':'CAT_ag_inputs', '林产品':'CAT_forest', '林业':'CAT_forest',
}

def observation_categories(raw):
 """Source-dated classifications; unseen source labels require explicit review."""
 raw=raw.copy()
 raw['previous_static_category_id']=raw['category_id']
 if 'raw_category_name' in raw:
  names=raw.raw_category_name.fillna('').map(lambda s: re.sub(r'^[一二三四五六七八九十]+、','',str(s).strip()))
  mapped=names.map(CATEGORY_IDS)
  if mapped.isna().any():raise ValueError('Unreviewed source category: '+str(sorted(names[mapped.isna()].unique())))
  raw['category_id']=mapped
  raw['classification_method']='explicit_source_category'
 else:
  raw['classification_method']='supplied_observation_category_no_raw_label'
 raw['category_changed_from_static']=raw.category_id!=raw.previous_static_category_id
 return raw

def comparator_audit(raw):
 """Diagnostic only: preserve published changes and current chain-model values."""
 a=raw.sort_values(['exact_product_id','date','available_at']).copy()
 grouped=a.groupby('exact_product_id')
 a['previous_observed_date']=grouped.date.shift(1)
 a['previous_observed_price']=grouped.raw_price.shift(1)
 ordinal=a.month.astype('int64')*3+a.slot
 a['survey_slots_since_previous']=ordinal-ordinal.groupby(a.exact_product_id).shift(1)
 a['gap_since_previous_observation']=a.survey_slots_since_previous.gt(1)
 a['calculated_level_return']=100*(a.raw_price/a.previous_observed_price-1)
 a['published_minus_level_return']=a.raw_pct_change-a.calculated_level_return
 a['comparator_discrepancy_gt_015pp']=a.published_minus_level_return.abs().gt(.15)
 a['comparator_available']=a.previous_observed_price.notna() & a.raw_pct_change.notna()
 return a

def build():
 p=pd.read_csv(R/'data/v2/products/product_vintage_features.csv')
 raw=pd.read_csv(R/'data/v2/products/mapped_raw_observations.csv')
 raw=observation_categories(raw)
 raw['date']=pd.to_datetime(raw.reference_period_start)
 raw['month']=raw.date.dt.to_period('M')
 raw['slot']=np.select([raw.date.dt.day<=10,raw.date.dt.day<=20],[1,2],default=3)
 raw=raw.sort_values('available_at').drop_duplicates(['month','slot','exact_product_id'])
 mapping_cols=[c for c in ['observation_id','exact_product_id','date','month','slot','available_at','raw_category_name','category_id','previous_static_category_id','category_changed_from_static','classification_method','source_url'] if c in raw]
 raw[mapping_cols].to_csv(R/'data/v3/dated_observation_categories.csv',index=False)
 comparator_audit(raw).to_csv(R/'data/v3/published_level_comparator_audit.csv',index=False)
 # Chain published like-for-like changes, never average incomparable raw prices.
 idx=raw.groupby(['date','category_id']).raw_pct_change.mean().unstack().sort_index()
 chain=(1+idx/100).cumprod()*100
 chain.to_csv(R/'data/v3/ten_day_category_indices.csv')
 idx.to_csv(R/'data/v3/ten_day_category_changes.csv')
 monthly_full=chain.groupby(chain.index.to_period('M')).mean()
 matrices={}
 for vintage,limit in [('early',1),('mid',2),('final',3)]:
  a=p[p.vintage==vintage].copy();a['month']=pd.PeriodIndex(a.month,freq='M')
  dated=raw[raw.slot<=limit].sort_values('available_at').drop_duplicates(['month','exact_product_id'],keep='last')
  dated=dated[['month','exact_product_id','category_id']].rename(columns={'category_id':'dated_category_id'})
  a=a.merge(dated,on=['month','exact_product_id'],how='left',validate='many_to_one')
  # Empty unbalanced-panel rows retain their metadata, never their old category
  # for any newly observed return. Current vintage uses only released slots.
  a['category_id']=a.dated_category_id.fillna(a.category_id)
  cut=pd.to_datetime(a.available_at,utc=True).groupby(a.month).max()
  calendar=pd.period_range(a.month.min(),a.month.max(),freq='M')
  blocks={}
  for method in ['mom_average','mom_end','mom_day_weighted','published_chain']:
   for level in ['exact_product_id','product_family_id','category_id']:
    x=a.pivot_table(index='month',columns=level,values=method,aggfunc='mean').reindex(calendar)
    x.columns=[str(c) for c in x.columns]
    blocks[method+'_'+level]=x
  # Stable category index returns constructed using reported comparable price changes.
  partial=chain[np.select([chain.index.day<=10,chain.index.day<=20],[1,2],default=3)<=limit]
  monthly=partial.groupby(partial.index.to_period('M')).mean()
  blocks['chain_category']=100*(monthly/monthly_full.shift(1)-1)
  f=blocks['mom_average_product_family_id']
  breadth=pd.DataFrame(index=calendar)
  breadth['mean']=f.mean(axis=1);breadth['median']=f.median(axis=1)
  breadth['diffusion']=((f>0).sum(axis=1)-(f<0).sum(axis=1))/f.notna().sum(axis=1)
  breadth['coverage']=f.notna().sum(axis=1)
  blocks['breadth']=breadth
  for name,x in blocks.items():
   x.to_csv(R/'data/v3'/f'{vintage}_{name}.csv',index_label='month')
  cut.to_csv(R/'data/v3'/f'{vintage}_cutoffs.csv',index_label='month')
  matrices[vintage]=(blocks,cut)
 return matrices
if __name__=='__main__':build()

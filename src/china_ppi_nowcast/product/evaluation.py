"""Derived dashboards and append-only actual/forecast matching; never refit past forecasts."""
import json
import numpy as np
import pandas as pd
from .data import digest
from .train import metrics,write_json


def evaluate(root,bundle,as_of):
    cutoff=pd.Timestamp(as_of)
    actuals=pd.read_csv(root/'data/registry/actuals.csv')
    actuals=actuals[pd.to_datetime(actuals.published_at,utc=True).le(cutoff)]
    forecasts=[];scores=[]
    for path in sorted((root/'data/product/vintages').glob('*/*/forecast.json')):
        forecast=json.loads(path.read_text());forecasts.append(forecast)
        for actual in actuals[actuals.target_month.eq(forecast['target_month'])].to_dict('records'):
            if pd.Timestamp(forecast['as_of'])>=pd.Timestamp(actual['published_at']):
                raise ValueError('attempt to score post-release forecast as prospective')
            e=forecast['prediction_mom']-float(actual['actual_mom_pct'])
            record=dict(forecast_id=forecast['forecast_id'],model_version=forecast['model_version'],
                target_month=forecast['target_month'],as_of=forecast['as_of'],variant=forecast['variant'],
                model=forecast['model'],panel=forecast['panel'],prediction=forecast['prediction_mom'],
                actual=float(actual['actual_mom_pct']),error=e,absolute_error=abs(e),squared_error=e**2,
                actual_published_at=actual['published_at'],actual_source=actual['source_url'],
                actual_sha=actual['content_sha256'],realtime_status='prospective')
            key=forecast['forecast_id']+'-'+digest(actual)[:16]
            write_json(root/'data/product/evaluations'/f'{key}.json',record);scores.append(record)
    lines=['# Product model performance','',
        'Prospective results and pseudo-real-time historical results are reported separately.',
        'Prospective monthly summaries select the last frozen pre-release vintage within each model/version/timing.',
        'Small differences are not grounds to remove models. At least six prospective releases are required before ranking claims.',
        '', '|Evidence|Timing|Panel|Model|Window|N|MAE|RMSE|Bias|Direction|',
        '|---|---|---|---|---|---:|---:|---:|---:|---:|']
    sources=[('pseudo_real_time',pd.read_csv(bundle/'rolling_predictions.csv'))]
    if scores:
        latest=pd.DataFrame(scores).sort_values(['actual_published_at','as_of']).drop_duplicates(
            ['model_version','variant','panel','model','target_month'],keep='last')
        sources.append(('prospective',latest))
    else: lines.append('\nNo prospective product-model outcomes have been released yet.\n')
    for evidence,frame in sources:
        grouping=['variant','panel','model']+(['model_version'] if evidence=='prospective' else [])
        for key,g in frame.groupby(grouping):
            variant,panel,model=key[:3]
            g=g.sort_values('target_month');latest_month=pd.Period(g.target_month.max(),freq='M')
            for n in [6,12,24,None]:
                selected=g if n is None else g[g.target_month>str(latest_month-n)]
                if selected.empty:continue
                m=metrics(selected.actual,selected.prediction)
                label=evidence if len(key)==3 else evidence+':'+key[3]
                lines.append(f"|{label}|{variant}|{panel}|{model}|{n or 'full'}|{m['n']}|{m['mae']:.3f}|{m['rmse']:.3f}|{m['bias']:.3f}|{m['directional_accuracy']:.2f}|")
    (root/'reports/product_performance.md').write_text('\n'.join(lines)+'\n')
    regimes=[]
    historical=sources[0][1].copy()
    historical['regime']=np.select([historical.actual.ge(.5),historical.actual.le(-.5)],
        ['large_positive_ge_0.5','large_negative_le_-0.5'],default='small_absolute_change_lt_0.5')
    for keys,g in historical.groupby(['variant','panel','model','regime']):
        regimes.append(dict(zip(['variant','panel','model','regime'],keys))|metrics(g.actual,g.prediction))
    pd.DataFrame(regimes).to_csv(root/'reports/product_regime_performance.csv',index=False)
    return dict(prospective_forecasts=len(forecasts),evaluated_forecast_actual_pairs=len(scores))

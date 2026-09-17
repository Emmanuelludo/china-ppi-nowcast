"""Monthly expanding validation; immutable fitted objects and attribution histories."""
import importlib.metadata
import hashlib
import sys
import itertools
import json
import subprocess
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from .data import canonicalize,catalog_from,training_matrix,digest,VERSION,VARIANTS
from .models import ALL_MODELS,PRODUCT_MODELS,TREE_MODELS,select_fit


def json_safe(value):
    if isinstance(value,dict): return {str(k):json_safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [json_safe(v) for v in value]
    if isinstance(value,(float,np.floating)) and not np.isfinite(value): return None
    if isinstance(value,np.generic): return value.item()
    if value is None or isinstance(value,(str,int,float,bool)): return value
    return str(value)


def write_json(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(json_safe(obj),ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if path.exists() and path.read_text()!=text: raise ValueError('immutable artifact collision: '+str(path))
    path.write_text(text)


def metrics(y,p):
    y,p=np.asarray(y),np.asarray(p);e=p-y
    return dict(n=len(e),mae=float(np.mean(abs(e))),rmse=float(np.sqrt(np.mean(e**2))),
        median_absolute_error=float(np.median(abs(e))),bias=float(np.mean(e)),
        maximum_absolute_error=float(max(abs(e))),directional_accuracy=float(np.mean(np.sign(y)==np.sign(p))))


def paired_comparisons(oof):
    result=[];rng=np.random.default_rng(20260916)
    for (variant,panel),g in oof.groupby(['variant','panel']):
        for a,b in itertools.combinations(sorted(g.model.unique()),2):
            x=g[g.model.eq(a)].set_index('target_month');y=g[g.model.eq(b)].set_index('target_month')
            matched=x[['absolute_error']].join(y[['absolute_error']],lsuffix='_a',rsuffix='_b',how='inner')
            d=(matched.absolute_error_a-matched.absolute_error_b).to_numpy()
            if len(d)<6: continue
            ix=np.concatenate([(rng.integers(0,len(d),(1000,1))+np.arange(3))%len(d)
                              for _ in range((len(d)+2)//3)],axis=1)[:,:len(d)]
            boot=d[ix].mean(axis=1)
            result.append(dict(variant=variant,panel=panel,model_a=a,model_b=b,n=len(d),
                mean_absolute_loss_difference=float(d.mean()),ci_low=float(np.quantile(boot,.025)),
                ci_high=float(np.quantile(boot,.975)),method='circular_block_bootstrap_length_3_1000_resamples'))
    return result


def train(root,variants=VARIANTS,min_train=24,stable=True):
    root=Path(root)
    x=canonicalize(pd.read_csv(root/'data/processed/nbs_ten_day_observations.csv.gz'))
    actuals=pd.read_csv(root/'data/registry/actuals.csv');catalog=catalog_from(x)
    code_hash=digest({p.name:p.read_text() for p in sorted(Path(__file__).parent.glob('*.py'))})
    source_hash=digest(sorted(x.content_sha256.unique()))
    packages={m:importlib.metadata.version(m) for m in ['numpy','pandas','scikit-learn','xgboost-cpu','catboost','lightgbm','shap','joblib']}
    version='product-v3-'+digest(dict(code=code_hash,sources=source_hash,variants=list(variants),min_train=min_train,
        stable=stable,packages=packages,actuals=actuals.fillna('').to_dict('records')))[:16]
    dest=root/'models'/version;dest.mkdir(parents=True,exist_ok=True)
    if (dest/'manifest.json').exists(): return json.loads((dest/'manifest.json').read_text())
    write_json(dest/'environment.json',dict(python=sys.version,packages={d.metadata['Name']:d.version for d in importlib.metadata.distributions() if d.metadata['Name']}))
    write_json(dest/'catalog.json',catalog)
    x['basket_version']=[next(b['basket_version'] for b in catalog['baskets'] if b['effective_from']<=str(d.date()) and (b['effective_to'] is None or str(d.date())<=b['effective_to'])) for d in x.period_start]
    x.to_csv(dest/'canonical_prices.csv.gz',index=False)
    all_oof=[];shap_rows=[];models=[]
    for variant in variants:
        matrix,excluded=training_matrix(x,catalog,actuals,variant)
        if len(matrix)<=min_train: raise ValueError('insufficient monthly history')
        directory=dest/variant;directory.mkdir(exist_ok=True)
        matrix.to_csv(directory/'matrix.csv',index=False);write_json(directory/'exclusions.json',excluded)
        columns=[c for c in matrix if c.startswith(('price__','carry__'))]
        groups={c:catalog['products'][c.split('__',1)[1]]['group'] for c in columns}
        X,y=matrix[columns],matrix.target_mom_pct
        names=ALL_MODELS if variant=='twentieth' else PRODUCT_MODELS
        panels=('union','stable') if stable and variant=='twentieth' else ('union',)
        origins=[]
        for i in range(min_train,len(matrix)):
            eligible=(pd.to_datetime(matrix.actual_published_at,utc=True)<pd.Timestamp(matrix.iloc[i].feature_cutoff)) & (matrix.target_month<matrix.iloc[i].target_month)
            indices=np.flatnonzero(eligible.to_numpy())
            if len(indices)>=min_train: origins.append((i,indices))
        for panel in panels:
            for name in names:
                if panel=='stable' and name not in PRODUCT_MODELS: continue
                print(f'Training {variant}/{panel}/{name}: {len(matrix)} months, {len(origins)} origins',flush=True)
                records=[]
                for i,indices in origins:
                    fitted,tuning=select_fit(X.iloc[indices],y.iloc[indices],name,panel=='stable',groups,matrix.iloc[indices])
                    xt=X.iloc[[i]];p=float(fitted.predict(xt)[0]);a=float(y.iloc[i]);e=p-a
                    if not np.isfinite(p): raise ValueError('nonfinite OOS prediction')
                    row=dict(variant=variant,panel=panel,model=name,target_month=matrix.iloc[i].target_month,
                        prediction=p,actual=a,error=e,absolute_error=abs(e),squared_error=e**2,
                        training_end=matrix.iloc[indices[-1]].target_month,feature_cutoff=matrix.iloc[i].feature_cutoff,
                        selected_strength=tuning['selected_strength'],realtime_status='pseudo_real_time')
                    records.append(row);all_oof.append(row)
                    if name in TREE_MODELS:
                        baseline,values,_=fitted.attribution(xt)
                        for c,v in values.iloc[0].items(): shap_rows.append(dict(variant=variant,panel=panel,model=name,
                            target_month=row['target_month'],feature=c,group=groups[c],shap=float(v),baseline=float(baseline[0]),prediction=p))
                fitted,tuning=select_fit(X,y,name,panel=='stable',groups,matrix)
                file=f'{variant}/{panel}_{name}.joblib';joblib.dump(fitted,dest/file,compress=3)
                models.append(dict(variant=variant,panel=panel,name=name,artifact=file,artifact_sha256=hashlib.sha256((dest/file).read_bytes()).hexdigest(),tuning=tuning,
                    hyperparameters=json_safe(fitted.estimator_.get_params(deep=False)) if name!='direct_tracker' else {},
                    feature_order=columns,learned_features=fitted.columns_,training_start=matrix.iloc[0].target_month,
                    training_end=matrix.iloc[-1].target_month,training_rows=len(matrix),
                    metrics=metrics([r['actual'] for r in records],[r['prediction'] for r in records])))
        for i,indices in origins:
            known=matrix.iloc[indices]
            for name,pred in {'no_change':0.,'historical_mean':known.target_mom_pct.mean(),
                             'last_available_actual':known.iloc[-1].target_mom_pct}.items():
                a=float(y.iloc[i]);e=float(pred)-a
                all_oof.append(dict(variant=variant,panel='union',model=name,target_month=matrix.iloc[i].target_month,
                    prediction=float(pred),actual=a,error=e,absolute_error=abs(e),squared_error=e**2,
                    training_end=known.iloc[-1].target_month,feature_cutoff=matrix.iloc[i].feature_cutoff,
                    selected_strength=None,realtime_status='pseudo_real_time'))
    oof=pd.DataFrame(all_oof);oof.to_csv(dest/'rolling_predictions.csv',index=False)
    pd.DataFrame(shap_rows).to_csv(dest/'historical_shap.csv.gz',index=False)
    write_json(dest/'paired_comparisons.json',paired_comparisons(oof))
    manifest=dict(version=version,feature_version=VERSION,code_hash=code_hash,source_hash=source_hash,
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),packages=packages,models=models,
        training_actual_cutoff=str(pd.to_datetime(actuals.published_at,utc=True).max()),
        source_start=catalog['first_observation'],source_end=catalog['last_observation'],
        validation='nested monthly expanding-window pseudo-real-time; later-retrieved revisions',
        missingness='Native tree NaN; fold-local median+indicators+scaling for ridge/factors; all-missing training columns excluded from fitting',
        external_covariates=[],proxy_backfill=False,history_complete_from_2014=False)
    write_json(dest/'manifest.json',manifest)
    report=['# Additional product models','',f'Bundle: `{version}`','',
        'Existing models and forecasts are preserved. No permanent winner or ensemble promotion.',
        f"Verified history: {catalog['first_observation']}–{catalog['last_observation']}; see the historical discovery audit for remaining gaps.",
        '20th-to-20th uses current versus previous 11–20 period prices, not exact day-20 factory-gate prices.',
        'All models share eligible monthly OOS origins within a timing specification. Results are pseudo-real-time.',
        '', '|Timing|Panel|Model|OOS n|MAE|RMSE|Bias|','|---|---|---|---:|---:|---:|---:|']
    for model in models:
        m=model['metrics'];report.append(f"|{model['variant']}|{model['panel']}|{model['name']}|{m['n']}|{m['mae']:.3f}|{m['rmse']:.3f}|{m['bias']:.3f}|")
    report.extend(['','Tree SHAP values are saved per product and origin, with numerical reconciliation. They are not causal contributions.',
        'Category/sector/hybrid models retain their own aggregation. The hybrid has no unverified external economic inputs.',
        'The direct tracker is an uncalibrated circulation-price index. Stable panels are selected within each training fold.'])
    (root/'reports/product_candidates.md').write_text('\n'.join(report)+'\n')
    return manifest

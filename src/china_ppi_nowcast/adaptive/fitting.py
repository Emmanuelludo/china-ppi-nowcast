"""Challenger fitting with nested chronological choice of history and penalty."""
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from ..product.data import canonicalize,available,catalog_from,training_matrix,VERSION
from ..product.models import ProductEstimator
from ..product.ridge_revision import ObservedScaleRidge,GRID_ALPHA,GRID_HISTORY
from ..product.train import metrics,write_json,json_safe


def estimator(name,strength,minimum,stable,groups):
    if name=='ridge':return ObservedScaleRidge(strength,minimum,stable)
    return ProductEstimator(name,strength,stable,groups)


def select(X,y,meta,name,stable,groups,config):
    # Common validation blocks for all history lengths; only their training changes.
    n=len(X);nval=min(24,max(6,n-config['minimum_training_months']))
    blocks=np.array_split(np.arange(n-nval,n),3)
    strengths=GRID_ALPHA if name=='ridge' else ((4,8,12) if name=='random_forest' else (5.,25.,100.))
    minima=GRID_HISTORY if name=='ridge' and not stable else (2,)
    scores=[]
    for window in config['training_windows']:
      for strength in strengths:
       for minimum in minima:
        losses=[]
        for va in blocks:
            if len(va)==0:continue
            cutoff=pd.Timestamp(meta.iloc[va[0]].feature_cutoff)
            ix=np.flatnonzero(((np.arange(n)<va[0]) & (pd.to_datetime(meta.actual_published_at,utc=True)<cutoff)).to_numpy())
            if window:ix=ix[-window:]
            if len(ix)<config['minimum_training_months'] or (name=='ridge' and not stable and X.iloc[ix].notna().sum().max()<minimum):
                losses=[];break
            model=estimator(name,strength,minimum,stable,groups).fit(X.iloc[ix],y.iloc[ix])
            losses.extend(abs(model.predict(X.iloc[va])-y.iloc[va].to_numpy()))
        if losses:scores.append(dict(window=window,strength=strength,min_observations=minimum,mae=float(np.mean(losses))))
    if not scores:raise ValueError('QA: insufficient released training targets for adaptive tuning')
    best=min(scores,key=lambda r:(r['mae'],-r['strength'],r['window'] is not None,-r['min_observations']))
    ix=np.arange(n) if best['window'] is None else np.arange(max(0,n-best['window']),n)
    model=estimator(name,best['strength'],best['min_observations'],stable,groups).fit(X.iloc[ix],y.iloc[ix])
    return model,dict(best,candidates=scores,inner_blocks=3),ix


def fit(root,cycle,as_of):
    root=Path(root);dest=root/'models/adaptive'/cycle['cycle_id']
    if (dest/'manifest.json').exists():return json.loads((dest/'manifest.json').read_text())
    temp=dest.with_name(dest.name+'.tmp')
    if temp.exists():shutil.rmtree(temp)  # Only an unfinished private transaction directory.
    temp.mkdir(parents=True)
    cutoff=pd.Timestamp(as_of);raw=pd.read_csv(root/'data/processed/nbs_ten_day_observations.csv.gz')
    x=available(canonicalize(raw),cutoff,True);catalog=catalog_from(x)
    actuals=pd.read_csv(root/'data/registry/actuals.csv')
    actuals=actuals[(pd.to_datetime(actuals.published_at,utc=True)<=cutoff)&(pd.to_datetime(actuals.retrieved_at,utc=True)<=cutoff)]
    matrix,exclusions=training_matrix(x,catalog,actuals,cycle['variant'])
    matrix=matrix[matrix.target_month.lt(cycle['start_month'])].reset_index(drop=True)
    columns=[c for c in matrix if c.startswith(('price__','carry__'))]
    X,y=matrix[columns],matrix.target_mom_pct
    groups={c:catalog['products'][c.split('__',1)[1]]['group'] for c in columns}
    config=cycle['config'];name=cycle['model'];stable=cycle['panel']=='stable'
    oof=[]
    for i in range(max(2*config['minimum_training_months'],len(matrix)-config['validation_months']),len(matrix)):
        ix=np.flatnonzero(((matrix.target_month<matrix.iloc[i].target_month)&(pd.to_datetime(matrix.actual_published_at,utc=True)<pd.Timestamp(matrix.iloc[i].feature_cutoff))).to_numpy())
        if len(ix)<2*config['minimum_training_months']:continue
        fitted,tuning,_=select(X.iloc[ix],y.iloc[ix],matrix.iloc[ix],name,stable,groups,config)
        p=float(fitted.predict(X.iloc[[i]])[0]);a=float(y.iloc[i]);e=p-a
        oof.append(dict(variant=cycle['variant'],panel=cycle['panel'],model=name,target_month=matrix.iloc[i].target_month,
            prediction=p,actual=a,error=e,absolute_error=abs(e),squared_error=e*e,training_end=matrix.iloc[ix[-1]].target_month,
            feature_cutoff=matrix.iloc[i].feature_cutoff,selected_strength=tuning['strength'],realtime_status='pseudo_real_time'))
    if not oof:raise ValueError('QA: no adaptive outer validation origins')
    fitted,tuning,ix=select(X,y,matrix,name,stable,groups,config)
    joblib.dump(fitted,temp/'model.joblib',compress=3)
    matrix.iloc[ix].to_csv(temp/'matrix.csv',index=False)
    pd.DataFrame(oof).to_csv(temp/'rolling_predictions.csv',index=False)
    write_json(temp/'catalog.json',catalog);write_json(temp/'exclusions.json',exclusions)
    candidate=dict(name=name,variant=cycle['variant'],panel=cycle['panel'],artifact='model.joblib',
        artifact_sha256=hashlib.sha256((temp/'model.joblib').read_bytes()).hexdigest(),
        feature_order=columns,learned_features=fitted.columns_,training_rows=len(ix),
        training_start=matrix.iloc[ix[0]].target_month,training_end=matrix.iloc[ix[-1]].target_month,
        hyperparameters=json_safe(fitted.get_params() if name=='ridge' else fitted.estimator_.get_params(deep=False)),
        tuning=tuning,metrics=metrics([r['actual'] for r in oof],[r['prediction'] for r in oof]),
        metrics_evidence='nested recent expanding-window pseudo-real-time; prospective trial determines promotion')
    manifest=dict(version='adaptive-'+cycle['cycle_id'],created_at=as_of,candidate=candidate,feature_version=VERSION,
        training_actual_cutoff=str(pd.to_datetime(actuals.published_at,utc=True).max()),
        source_hashes=sorted(x.content_sha256.unique()),source_start=catalog['first_observation'],source_end=catalog['last_observation'],
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        code_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        packages={k:importlib.metadata.version(k) for k in ['numpy','pandas','scikit-learn','joblib','xgboost-cpu','catboost','lightgbm','shap']},
        historical_evidence='pseudo-real-time; historical revisions available at refitting cutoff',prospective_start_month=cycle['start_month'])
    write_json(temp/'manifest.json',manifest);temp.rename(dest)
    return manifest

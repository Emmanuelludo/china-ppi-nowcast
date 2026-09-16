"""Frozen prospective candidates, exact features, and reconciled SHAP artifacts."""
import importlib.metadata
import json
import subprocess
import joblib
import numpy as np
import pandas as pd
from .data import canonicalize,feature_row,digest,VARIANTS
from .train import write_json


def run(root,bundle,month,as_of):
    manifest=json.loads((bundle/'manifest.json').read_text());catalog=json.loads((bundle/'catalog.json').read_text())
    for name,expected in manifest['packages'].items():
        if importlib.metadata.version(name)!=expected: raise ValueError('package version mismatch: '+name)
    cutoff=pd.Timestamp(as_of)
    if cutoff.tzinfo is None: raise ValueError('as_of needs timezone')
    actuals=pd.read_csv(root/'data/registry/actuals.csv')
    if (actuals.target_month.eq(month)&pd.to_datetime(actuals.published_at,utc=True).le(cutoff)).any():
        raise ValueError('target actual already public; prospective inference prohibited')
    if pd.Timestamp(manifest['training_actual_cutoff'])>cutoff: raise ValueError('model training used later target releases')
    x=canonicalize(pd.read_csv(root/'data/processed/nbs_ten_day_observations.csv.gz'))
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    outputs=[];pending=[]
    for variant in VARIANTS:
        try:features,meta=feature_row(x,catalog,month,variant,cutoff,True)
        except ValueError as e:
            if 'unavailable source release' not in str(e): raise
            pending.append(dict(variant=variant,reason=str(e)));continue
        for candidate in manifest['models']:
            if candidate['variant']!=variant:continue
            if candidate['training_end']>=month:raise ValueError('model target-month leakage')
            model=joblib.load(bundle/candidate['artifact'])
            X=pd.DataFrame([features]).reindex(columns=candidate['feature_order'])
            prediction=float(model.predict(X)[0])
            if not np.isfinite(prediction):raise ValueError('nonfinite forecast')
            key=digest(dict(month=month,feature=meta['feature_hash'],model=candidate['name'],
                            panel=candidate['panel'],version=manifest['version']))
            directory=root/'data/product/vintages'/month/key[:20]
            if (directory/'forecast.json').exists():
                saved=json.loads((directory/'forecast.json').read_text())
                if not np.isclose(saved['prediction_mom'],prediction,rtol=0,atol=1e-12):raise ValueError('forecast collision')
                outputs.append(saved);continue
            row=dict(forecast_id=key,target_month=month,as_of=as_of,variant=variant,model=candidate['name'],
                panel=candidate['panel'],model_version=manifest['version'],feature_version=manifest['feature_version'],
                feature_hash=meta['feature_hash'],basket_versions=meta['basket_versions'],prediction_mom=prediction,
                implied_yoy=None,implied_yoy_status='requires verified official index path',
                data_cutoff=max(s['published_at'] for sources in meta['sources'].values() for s in sources),
                hyperparameters=candidate['hyperparameters'],training_end=candidate['training_end'],
                git_commit=commit,status='frozen_pre_release_candidate',
                unseen_training_features=[c for c in X if c not in model.columns_ and X[c].notna().any()])
            attr=model.attribution(X)
            if attr is not None:
                baseline,values,_=attr;contributions=values.iloc[0].to_dict();grouped={}
                for c,v in contributions.items():
                    group=catalog['products'][c.split('__',1)[1]]['group'];grouped[group]=grouped.get(group,0)+float(v)
                write_json(directory/'shap.json',dict(baseline=float(baseline[0]),product=contributions,grouped=grouped,
                    prediction=prediction,method='tree_path_dependent',causal=False,tolerance=2e-5))
            write_json(directory/'features.json',meta);write_json(directory/'forecast.json',row);outputs.append(row)
    lines=['# Additional product PPI forecasts','',f'Target: {month}; as of {as_of}','',
        'Existing models remain active. These additional candidates do not replace them.',
        '20th-to-20th waits for the current 11–20 release; it is a period-price proxy.',
        '', '|Timing|Panel|Model|MoM (%)|','|---|---|---|---:|']
    for r in outputs:lines.append(f"|{r['variant']}|{r['panel']}|{r['model']}|{r['prediction_mom']:+.3f}|")
    for r in pending:lines.append(f"\nPending {r['variant']}: {r['reason']}")
    lines.extend(['','Direct tracker is uncalibrated. No ensemble weights or model winner have been promoted.',
        'Individual and grouped SHAP files are stored beside each tree forecast. They are model attributions, not causal contributions.',
        f"Verified historical source range: {manifest['source_start']}–{manifest['source_end']}. See the historical discovery audit for gaps."])
    for r in outputs:
        if r['panel']!='union':continue
        sp=root/'data/product/vintages'/month/r['forecast_id'][:20]/'shap.json'
        if not sp.exists():continue
        attr=json.loads(sp.read_text());lines.extend(['',f"## {r['variant']} / {r['model']} attribution",'',f"Baseline: {attr['baseline']:+.4f} pp; prediction: {attr['prediction']:+.4f}%.",'','|Product feature|SHAP (pp)|','|---|---:|'])
        for c,v in sorted(attr['product'].items(),key=lambda item:abs(item[1]),reverse=True)[:8]:
            label=catalog['products'][c.split('__',1)[1]]['canonical_name']
            lines.append(f'|{c.split("__",1)[0]}: {label}|{v:+.4f}|')
        lines.extend(['','|Group|SHAP (pp)|','|---|---:|'])
        for g,v in sorted(attr['grouped'].items(),key=lambda item:abs(item[1]),reverse=True):lines.append(f'|{g}|{v:+.4f}|')
    (root/'reports/product_latest.md').write_text('\n'.join(lines)+'\n')
    from .evaluation import evaluate
    evaluation=evaluate(root,bundle,as_of)
    return dict(forecasts=len(outputs),pending=pending,bundle=manifest['version'],evaluation=evaluation)

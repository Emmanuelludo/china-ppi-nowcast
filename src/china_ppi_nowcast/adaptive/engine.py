"""Append-only lifecycle, matched live trials and per-model active promotion."""
import copy
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from .policy import trigger,decide
from ..product.data import digest,canonicalize,available,catalog_from,feature_row
from ..product.train import write_json
from ..storage import atomic_write_text
from ..model_policy import is_active


def key(c):return '/'.join((c['variant'],c['panel'],c.get('name',c.get('model'))))

def read_events(root):
    events=[];previous=None
    for p in sorted((root/'data/adaptive/events').glob('*.json')):
        e=json.loads(p.read_text());identity=digest({k:v for k,v in e.items() if k!='event_id'})
        if e['event_id']!=identity or e['previous_event']!=previous or e['sequence']!=len(events)+1:
            raise ValueError('Adaptive journal hash/sequence integrity failure')
        events.append(e);previous=e['event_id']
    return events


def append(root,kind,payload,as_of):
    events=read_events(root)
    e=dict(sequence=len(events)+1,previous_event=events[-1]['event_id'] if events else None,
           type=kind,as_of=as_of,payload=payload)
    e['event_id']=digest(e)
    write_json(root/'data/adaptive/events'/f"{e['sequence']:06d}-{e['event_id'][:16]}.json",e)
    return e


def replay(events):
    s=dict(champions={},cycles={},completed={},activation=None)
    for e in events:
        p=e['payload'];kind=e['type']
        if kind=='initialized':s['champions']=p['champions'];s['activation']=e['as_of']
        elif kind=='trial_requested':s['cycles'][p['cycle_id']]=dict(p,status='requested',requested_at=e['as_of'])
        elif kind=='refit_failed':s['cycles'][p['cycle_id']]['last_fit_failure']=dict(p,as_of=e['as_of'])
        elif kind=='challenger_fitted':s['cycles'][p['cycle_id']].update(status='testing',challenger=p['challenger'])
        elif kind=='trial_decided':
            c=s['cycles'][p['cycle_id']];c.update(status='decided',decision=p)
            s['completed'][c['key']]=max(p['comparison']['months'])
        elif kind=='adopted':
            s['champions'][p['champion']['key']]=p['champion']
            s['completed'][p['champion']['key']]=p['baseline_month']
        elif kind=='trial_cancelled':s['cycles'][p['cycle_id']]['status']='cancelled'
        elif kind=='promoted':
            c=s['cycles'][p['cycle_id']];s['champions'][c['key']]=p['champion'];c['status']='promoted'
        else:raise ValueError('Unknown adaptive lifecycle event')
    return s


def known_actuals(root,as_of):
    a=pd.read_csv(root/'data/registry/actuals.csv');cutoff=pd.Timestamp(as_of)
    a['actual_mom_pct']=pd.to_numeric(a.actual_mom_pct,errors='raise')
    if not np.isfinite(a.actual_mom_pct).all():raise ValueError('QA: invalid official PPI outcome')
    a=a[(pd.to_datetime(a.published_at,utc=True)<=cutoff)&(pd.to_datetime(a.retrieved_at,utc=True)<=cutoff)]
    # Freeze the first observed official result; revisions remain separate sensitivity evidence.
    return a.sort_values(['published_at','retrieved_at']).drop_duplicates('target_month',keep='first').set_index('target_month').to_dict('index')


def forecast_scores(root,champion,actuals):
    manifests={};selected={}
    for path in sorted((root/'data/product/vintages').glob('*/*/forecast.json')):
        r=json.loads(path.read_text())
        if key(r)!=champion['key'] or r['target_month'] not in actuals:continue
        a=actuals[r['target_month']]
        if pd.Timestamp(r['as_of'])>=pd.Timestamp(a['published_at']):continue
        version=r['model_version']
        if version not in manifests:
            p=root/'models'/version/'manifest.json'
            manifests[version]=json.loads(p.read_text()) if p.exists() else None
        m=manifests[version]
        if not m:continue
        c=next((c for c in m['models'] if key(c)==champion['key']),None)
        if not c or c['artifact_sha256']!=champion['model_id']:continue
        if c['training_end']>=r['target_month'] or pd.Timestamp(m['training_actual_cutoff'])>pd.Timestamp(r['as_of']):continue
        previous=selected.get(r['target_month'])
        if previous is None or pd.Timestamp(r['as_of'])>pd.Timestamp(previous['as_of']):selected[r['target_month']]=r
    return [dict(target_month=m,prediction=r['prediction_mom'],actual=float(actuals[m]['actual_mom_pct']),
        forecast_id=r['forecast_id'],as_of=r['as_of'],actual_sha=actuals[m]['content_sha256'],
        model_version=r['model_version']) for m,r in sorted(selected.items())]


def diagnose(root,champion,scores):
    from ..reporting import product_name
    b=root/champion['bundle'];model=joblib.load(b/champion['candidate']['artifact'])
    rows=[]
    matrix=pd.read_csv(b/champion['candidate'].get('training_matrix',champion['candidate']['variant']+'/matrix.csv'))
    for r in scores:
        p=root/'data/product/vintages'/r['target_month']/r['forecast_id'][:20]
        meta=json.loads((p/'features.json').read_text());values=meta['values'];outside=[];short=[]
        for k in model.columns_:
            if values.get(k) is None:continue
            observed=matrix[k].dropna() if k in matrix else pd.Series(dtype=float)
            if len(observed)<12:short.append(k)
            if len(observed) and not observed.min()<=values[k]<=observed.max():outside.append(k)
        attributions=[]
        if (p/'shap.json').exists():
            a=json.loads((p/'shap.json').read_text());attributions=[dict(product=product_name(k.split('__',1)[1]),value=v)
                for k,v in sorted(a['product'].items(),key=lambda kv:abs(kv[1]),reverse=True)[:8]]
        elif champion['candidate']['name']=='ridge' and hasattr(model,'scales_'):
            X=pd.DataFrame([values],dtype=float);z=model.transform(X).iloc[0];c=z*model.estimator_.coef_
            attributions=[dict(product=product_name(k.split('__',1)[1]),value=float(v)) for k,v in c.abs().sort_values(ascending=False).head(8).items()]
            # Preserve signed values, not absolute importance.
            for a,k in zip(attributions,c.abs().sort_values(ascending=False).head(8).index):a['value']=float(c[k])
        rows.append(dict(month=r['target_month'],error_pp=r['prediction']-r['actual'],
            source_hashes=sorted({s['content_sha256'] for v in meta['sources'].values() for s in v}),
            outside_training_range=[product_name(k.split('__',1)[1]) for k in outside],
            short_histories=[product_name(k.split('__',1)[1]) for k in short],
            structural_missing_features=len(meta['structural_missing']),top_model_attributions=attributions))
    return dict(evidence=rows,training_end=champion['candidate']['training_end'],
        interpretation='Residual bias, input extrapolation, sparse coverage and model attributions are diagnostic clues, not proof of an economic cause. Source QA must pass before refitting.')


def matched_forecast(root,cycle,as_of,month):
    actuals=known_actuals(root,as_of)
    if month in actuals or month<cycle['start_month']:return None
    cutoff=pd.Timestamp(as_of)
    if cutoff<pd.Timestamp(cycle['requested_at']):raise ValueError('Trial cannot precede registration')
    incumbent=cycle['champion'];new=cycle['challenger'];b=root/new['bundle']
    m=json.loads((b/'manifest.json').read_text())
    if pd.Timestamp(m['training_actual_cutoff'])>cutoff:raise ValueError('Challenger target-release leakage')
    raw=canonicalize(pd.read_csv(root/'data/processed/nbs_ten_day_observations.csv.gz'))
    x=available(raw,cutoff,True);catalog=catalog_from(x)
    try:_,meta=feature_row(x,catalog,month,cycle['variant'],cutoff,True)
    except ValueError as e:
        if 'unavailable source release' in str(e):return None
        raise
    X=pd.DataFrame([meta['values']],dtype=float);predictions={};attributions={}
    for role,ref in [('champion',incumbent),('challenger',new)]:
        c=ref['candidate'];artifact=root/ref['bundle']/c['artifact']
        if c['training_end']>=month:raise ValueError('Trial trained on its forecast month')
        if hashlib.sha256(artifact.read_bytes()).hexdigest()!=ref['model_id']:raise ValueError('Trial model artifact changed')
        model=joblib.load(artifact);p=float(model.predict(X.reindex(columns=c['feature_order']))[0])
        if not np.isfinite(p):raise ValueError('Nonfinite adaptive forecast')
        predictions[role]=p
        attr=model.attribution(X.reindex(columns=c['feature_order']))
        if attr is not None:
            baseline,values,_=attr
            attributions[role]=dict(baseline=float(baseline[0]),product={k:float(v) for k,v in values.iloc[0].items()},prediction=p,causal=False)
        elif c['name']=='ridge' and hasattr(model,'scales_'):
            z=model.transform(X).iloc[0]
            attributions[role]=dict(baseline=float(model.estimator_.intercept_),product={k:float(v) for k,v in (z*model.estimator_.coef_).items()},prediction=p,causal=False,method='linear_decomposition')
    identity=digest(dict(cycle=cycle['cycle_id'],month=month,feature_hash=meta['feature_hash']))
    directory=root/'data/adaptive/forecasts'/cycle['cycle_id']/identity[:20]
    if (directory/'pair.json').exists():return json.loads((directory/'pair.json').read_text())
    record=dict(pair_id=identity,cycle_id=cycle['cycle_id'],key=cycle['key'],target_month=month,as_of=as_of,
        feature_hash=meta['feature_hash'],champion_model_id=incumbent['model_id'],challenger_model_id=new['model_id'],
        champion_prediction=predictions['champion'],challenger_prediction=predictions['challenger'],
        status='matched_pre_release_trial',information_set='identical raw source snapshots and feature vintage for both models')
    write_json(directory/'features.json',meta);write_json(directory/'pair.json',record)
    for role,a in attributions.items():
        if not np.isclose(a['baseline']+sum(a['product'].values()),a['prediction'],atol=2e-5,rtol=2e-5):raise ValueError('Trial attribution reconciliation failed')
        write_json(directory/(role+'_attributions.json'),a)
    return record


def score_trial(root,cycle,actuals):
    chosen={}
    for p in (root/'data/adaptive/forecasts'/cycle['cycle_id']).glob('*/pair.json'):
        r=json.loads(p.read_text());a=actuals.get(r['target_month'])
        if a is None or pd.Timestamp(r['as_of'])>=pd.Timestamp(a['published_at']):continue
        if r['target_month'] not in chosen or pd.Timestamp(r['as_of'])>pd.Timestamp(chosen[r['target_month']]['as_of']):chosen[r['target_month']]=r
    results=[]
    for month,r in sorted(chosen.items()):
        path=root/'data/adaptive/evaluations'/cycle['cycle_id']/f'{month}.json'
        if path.exists():results.append(json.loads(path.read_text()));continue
        directory=root/'data/adaptive/forecasts'/cycle['cycle_id']/r['pair_id'][:20]
        meta=json.loads((directory/'features.json').read_text())
        if digest({k:v for k,v in meta.items() if k not in ('feature_hash','as_of')})!=r['feature_hash']:
            raise ValueError('Matched trial feature content changed')
        X=pd.DataFrame([meta['values']],dtype=float)
        for role in ['champion','challenger']:
            ref=cycle[role];candidate=ref['candidate'];artifact=root/ref['bundle']/candidate['artifact']
            if hashlib.sha256(artifact.read_bytes()).hexdigest()!=ref['model_id']:raise ValueError('Trial contestant changed')
            p=float(joblib.load(artifact).predict(X.reindex(columns=candidate['feature_order']))[0])
            if not np.isclose(p,r[role+'_prediction'],rtol=0,atol=1e-10):raise ValueError('Matched prediction changed')
        a=actuals[month];row=dict(r,actual=float(a['actual_mom_pct']),actual_published_at=a['published_at'],actual_sha=a['content_sha256'])
        write_json(path,row);results.append(row)
    return results


def promote(root,cycle,as_of):
    """Composite active bundle: replace one family/specification, keep the rest."""
    pointer=root/'config/product_pipeline.json';base=root/json.loads(pointer.read_text())['bundle']
    old=json.loads((base/'manifest.json').read_text());ref=cycle['challenger'];source=root/ref['bundle']
    new=json.loads((source/'manifest.json').read_text());candidate=copy.deepcopy(new['candidate'])
    version='product-adaptive-'+digest(dict(parent=old['version'],cycle=cycle['cycle_id']))[:16]
    dest=root/'models'/version
    if not (dest/'manifest.json').exists():
        if dest.exists():raise ValueError('Incomplete promotion bundle; inspect before retry')
        final_dest=dest;dest=dest.with_name(dest.name+'.tmp')
        if dest.exists():shutil.rmtree(dest)
        shutil.copytree(base,dest);(dest/'manifest.json').unlink()
        directory=dest/'adaptive'/cycle['cycle_id'];shutil.copytree(source,directory)
        candidate['artifact']=str((directory/'model.joblib').relative_to(dest))
        candidate['training_matrix']=str((directory/'matrix.csv').relative_to(dest))
        manifest=copy.deepcopy(old);manifest['version']=version
        manifest['models']=[candidate if key(c)==cycle['key'] else c for c in old['models']]
        # All historical product IDs are retained in the latest canonical catalog.
        current=available(canonicalize(pd.read_csv(root/'data/processed/nbs_ten_day_observations.csv.gz')),pd.Timestamp(as_of),True)
        live_catalog=catalog_from(current)
        (dest/'catalog.json').unlink()
        write_json(dest/'catalog.json',live_catalog)
        manifest.update(source_start=new['source_start'],source_end=new['source_end'],
            training_actual_cutoff=max(old['training_actual_cutoff'],new['training_actual_cutoff'],key=pd.Timestamp))
        manifest.setdefault('adaptive_promotions',[]).append(dict(cycle_id=cycle['cycle_id'],as_of=as_of,key=cycle['key'],
            effective_month=cycle['decision']['effective_month'],prospective_comparison=cycle['decision']['comparison']))
        oof=pd.read_csv(base/'rolling_predictions.csv');keep=~((oof.variant==candidate['variant'])&(oof.panel==candidate['panel'])&(oof.model==candidate['name']))
        pd.concat([oof[keep],pd.read_csv(source/'rolling_predictions.csv')],ignore_index=True).to_csv(dest/'rolling_predictions.csv',index=False)
        write_json(dest/'manifest.json',manifest)
        dest.rename(final_dest);dest=final_dest
    else:manifest=json.loads((dest/'manifest.json').read_text());candidate=next(c for c in manifest['models'] if key(c)==cycle['key'])
    atomic_write_text(pointer,json.dumps(dict(bundle='models/'+version),indent=2)+'\n')
    return dict(key=cycle['key'],bundle='models/'+version,candidate=candidate,model_id=candidate['artifact_sha256'])


def run(root,as_of,month=None,fit_callback=None):
    from .fitting import fit
    root=Path(root).resolve();cutoff=pd.Timestamp(as_of)
    if cutoff.tzinfo is None:raise ValueError('Adaptive cutoff needs a timezone')
    month=month or cutoff.tz_convert('Asia/Shanghai').strftime('%Y-%m')
    config=json.loads((root/'config/adaptive.json').read_text())
    if not config['enabled']:return dict(enabled=False)
    if config['monitor_months']<2 or config['comparison_months']<2:raise ValueError('At least two outcomes required per window')
    events=read_events(root)
    if events and cutoff<pd.Timestamp(events[-1]['as_of']):raise ValueError('Adaptive lifecycle cannot run backwards in time')
    if not events:
        bundle=json.loads((root/'config/product_pipeline.json').read_text())['bundle'];m=json.loads((root/bundle/'manifest.json').read_text())
        champions={key(c):dict(key=key(c),bundle=bundle,candidate=c,model_id=c['artifact_sha256']) for c in m['models'] if is_active(c['name']) and c['name']!='direct_tracker'}
        append(root,'initialized',dict(champions=champions,config=config),as_of)
    state=replay(read_events(root));actuals=known_actuals(root,as_of);monitors={}
    # Explicit/manual retraining or expanded-history bundles cannot silently strand monitoring.
    active_bundle=json.loads((root/'config/product_pipeline.json').read_text())['bundle']
    active_manifest=json.loads((root/active_bundle/'manifest.json').read_text())
    for candidate in active_manifest['models']:
        k=key(candidate)
        if k not in state['champions'] or candidate['artifact_sha256']==state['champions'][k]['model_id']:continue
        ref=dict(key=k,bundle=active_bundle,candidate=candidate,model_id=candidate['artifact_sha256'])
        unfinished=[c for c in state['cycles'].values() if c['key']==k and (c['status'] in ('requested','testing') or (c['status']=='decided' and c['decision']['comparison']['promote']))]
        recovered=next((c for c in unfinished if c['status']=='decided' and c['decision']['comparison']['promote'] and c['challenger']['model_id']==ref['model_id']),None)
        if recovered:
            append(root,'promoted',dict(cycle_id=recovered['cycle_id'],champion=ref),as_of)
        else:
            for c in unfinished:
                append(root,'trial_cancelled',dict(cycle_id=c['cycle_id'],reason='active specification changed outside this trial'),as_of)
            append(root,'adopted',dict(champion=ref,baseline_month=max(actuals,default='0000-00'),reason='explicit retraining or expanded-history active bundle'),as_of)
    state=replay(read_events(root))
    for k,champion in state['champions'].items():
        rows=forecast_scores(root,champion,actuals)
        fresh=[r for r in rows if r['target_month']>state['completed'].get(k,'0000-00')]
        cfg=dict(config,_all_months=fresh)
        monitor=trigger(fresh,champion['candidate']['metrics']['mae'],cfg);monitors[k]=monitor
        active=[c for c in state['cycles'].values() if c['key']==k and (c['status'] in ('requested','testing') or (c['status']=='decided' and c['decision']['comparison']['promote']))]
        if monitor['triggered'] and not active:
            # One registration per fresh outcome set and champion identity.
            cycle_id=digest(dict(key=k,model_id=champion['model_id'],months=monitor['months']))[:24]
            diagnostic=diagnose(root,champion,fresh[-config['monitor_months']:])
            append(root,'trial_requested',dict(cycle_id=cycle_id,key=k,variant=champion['candidate']['variant'],
                panel=champion['candidate']['panel'],model=champion['candidate']['name'],champion=champion,
                start_month=max(month,str(pd.Period(max(monitor['months']),freq='M')+1)),
                monitor=monitor,diagnostic=diagnostic,config=config),as_of)
    state=replay(read_events(root));refits=0
    for cycle in sorted(state['cycles'].values(),key=lambda c:c['requested_at']):
        if cycle['status']!='requested' or refits>=config['max_refits_per_run']:continue
        try:
            m=(fit_callback or fit)(root,cycle,as_of)
        except Exception as exc:
            append(root,'refit_failed',dict(cycle_id=cycle['cycle_id'],error_type=type(exc).__name__,message=str(exc)),as_of)
            failed_state=replay(read_events(root))
            atomic_write_text(root/'data/adaptive/state.json',json.dumps(failed_state,indent=2,ensure_ascii=False)+'\n')
            write_report(root,failed_state,monitors,as_of)
            raise
        c=m['candidate']
        if c['training_end']>=cycle['start_month'] or pd.Timestamp(m['training_actual_cutoff'])>cutoff:raise ValueError('Challenger fitting used future outcomes')
        append(root,'challenger_fitted',dict(cycle_id=cycle['cycle_id'],challenger=dict(key=cycle['key'],bundle='models/adaptive/'+cycle['cycle_id'],candidate=c,model_id=c['artifact_sha256'])),as_of)
        refits+=1
    state=replay(read_events(root))
    for cycle in state['cycles'].values():
        if cycle['status']!='testing':continue
        matched_forecast(root,cycle,as_of,month)
        pairs=score_trial(root,cycle,actuals);decision=decide(pairs,cycle['config'])
        if not decision['complete']:continue
        # Never rewrite the current month's already-issued incumbent forecasts.
        has_current=any(json.loads(p.read_text())['target_month']==month and key(json.loads(p.read_text()))==cycle['key']
            for p in (root/'data/product/vintages'/month).glob('*/forecast.json'))
        effective=str(pd.Period(month,freq='M')+1) if has_current else month
        append(root,'trial_decided',dict(cycle_id=cycle['cycle_id'],comparison=decision,effective_month=effective,
            evaluation_hashes={r['target_month']:digest(r) for r in sorted(pairs,key=lambda r:r['target_month'])[:cycle['config']['comparison_months']]}),as_of)
    state=replay(read_events(root));promotions=0
    for cycle in state['cycles'].values():
        if cycle['status']=='decided' and cycle['decision']['comparison']['promote'] and cycle['decision']['effective_month']<=month:
            champion=promote(root,cycle,as_of)
            append(root,'promoted',dict(cycle_id=cycle['cycle_id'],champion=champion),as_of);promotions+=1
    state=replay(read_events(root));write_report(root,state,monitors,as_of)
    atomic_write_text(root/'data/adaptive/state.json',json.dumps(state,indent=2,ensure_ascii=False)+'\n')
    return dict(monitored_models=len(state['champions']),active_trials=sum(c['status']=='testing' for c in state['cycles'].values()),
        queued_refits=sum(c['status']=='requested' for c in state['cycles'].values()),refits=refits,promotions=promotions,
        journal_events=len(read_events(root)),report='reports/adaptive.md')


def write_report(root,state,monitors,as_of):
    from ..reporting import model_name,TIMINGS,PANELS
    lines=['# Adaptive model monitoring','',f'Updated: {as_of}. Monitoring started: {state["activation"]}.','',
        'Four newly released monthly outcomes form the default monitoring window. Triggered models receive independently fitted challengers. Each frozen champion/challenger pair uses identical source snapshots, and six future matched monthly outcomes determine a provisional promotion. No historical forecast is rewritten.', '',
        'Diagnostics describe residual bias, sparse histories, extrapolation and model attributions; they do not establish an economic cause. Source QA failures stop the pipeline. Historical tuning is pseudo-real-time; promotion evidence is prospective.', '',
        '| Model | Timing | Panel | Released outcomes | Status / trigger |','|---|---|---|---:|---|']
    for k,c in sorted(state['champions'].items()):
        m=monitors.get(k,{});candidate=c['candidate'];n=m.get('n',0)
        lines.append(f"| {model_name(candidate['name'])} | {TIMINGS[candidate['variant']]} | {PANELS[candidate['panel']]} | {n} | {m.get('reason','pending')} |")
    lines+=['','## Challenger trials','', '| Model / specification | State | Completed comparison months | Champion MAE | Challenger MAE | Decision |','|---|---|---:|---:|---:|---|']
    for c in state['cycles'].values():
        scores=list((root/'data/adaptive/evaluations'/c['cycle_id']).glob('*.json'))
        comparison=c.get('decision',{}).get('comparison',{})
        ma=comparison.get('champion',{}).get('mae');mb=comparison.get('challenger',{}).get('mae')
        decision=(('Promote challenger from '+c['decision']['effective_month']) if comparison.get('promote') else 'Keep incumbent') if comparison else 'Awaiting matched future outcomes'
        lines.append(f"| {c['key']} | {c['status']} | {len(scores)} / {c['config']['comparison_months']} | {ma if ma is not None else '—'} | {mb if mb is not None else '—'} | {decision} |")
    if not state['cycles']:lines.append('| No trials yet | Armed | 0 | — | — | Awaiting genuinely prospective outcomes |')
    lines+=['','## Latest matched trial forecasts','', '| Model / specification | Target month | Incumbent | Refit challenger | Frozen |','|---|---|---:|---:|---|']
    for c in state['cycles'].values():
        pairs=[json.loads(p.read_text()) for p in (root/'data/adaptive/forecasts'/c['cycle_id']).glob('*/pair.json')]
        if pairs:
            r=max(pairs,key=lambda r:(r['target_month'],pd.Timestamp(r['as_of'])))
            lines.append(f"| {c['key']} | {r['target_month']} | {r['champion_prediction']:+.3f}% | {r['challenger_prediction']:+.3f}% | {r['as_of']} |")
        else:lines.append(f"| {c['key']} | Pending required releases | — | — | — |")
    lines+=['','## Diagnostic evidence for registered trials','']
    for c in state['cycles'].values():
        lines += [f"### {c['key']} · {c['cycle_id']}",'',c['monitor']['reason']+'.','',
            f"Champion trained through {c['diagnostic']['training_end']}.",'',
            '| Outcome month | Error (pp) | Outside fitted ranges | Short histories | Leading model attributions |',
            '|---|---:|---|---|---|']
        for r in c['diagnostic']['evidence']:
            outside='; '.join(r['outside_training_range']) or 'None'
            short='; '.join(r['short_histories']) or 'None'
            drivers='; '.join(f"{a['product']}: {a['value']:+.3f} pp" for a in r['top_model_attributions'][:4]) or 'Not available'
            lines.append(f"| {r['month']} | {r['error_pp']:+.3f} | {outside} | {short} | {drivers} |")
        lines+=['',c['diagnostic']['interpretation'],'']
        if c.get('last_fit_failure'):
            f=c['last_fit_failure']
            lines += [f"Last recorded fitting failure: {f['error_type']}: {f['message']}. The request is retained for retry; a later successful fit remains in the journal.",'']
    lines+=['','A challenger must improve MAE by at least 5% and 0.02 pp, avoid more than 5% RMSE deterioration or 0.05 pp bias deterioration, and win at least half the paired months. These thresholds are operational defaults; six outcomes do not prove permanent superiority.', '',
        'After a trial, four fresh incumbent outcomes are needed for a new deviation-triggered cycle. A 12-outcome periodic refresh also prevents indefinite staleness. Training and comparison rules are frozen when each trial is registered.', '',
        '[Monitoring configuration](../config/adaptive.json) · [Append-only decision journal](../data/adaptive/events) · [Matched forecast archive](../data/adaptive/forecasts) · [Technical method](../docs/ADAPTIVE.md)']
    (root/'reports/adaptive.md').write_text('\n'.join(lines)+'\n')

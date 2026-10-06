"""Deterministic error monitoring and predeclared paired promotion rules."""
import numpy as np
from ..product.train import metrics


def trigger(rows, reference_mae, config):
    n=config['monitor_months']
    rows=sorted(rows,key=lambda r:r['target_month'])[-n:]
    if len(rows)<n:return dict(triggered=False,reason='awaiting released prospective outcomes',n=len(rows),required=n)
    m=metrics([r['actual'] for r in rows],[r['prediction'] for r in rows])
    limit=max(reference_mae*config['mae_ratio_trigger'],reference_mae+config['mae_increase_trigger_pp'])
    reasons=[]
    if m['mae']>limit:reasons.append('recent MAE exceeds the historical reference threshold')
    if abs(m['bias'])>config['absolute_bias_trigger_pp']:reasons.append('persistent signed forecast error')
    if len(rows)>=n and len(config.get('_all_months',rows))>=config['max_months_without_trial']:
        reasons.append('scheduled refresh after enough new outcomes')
    return dict(triggered=bool(reasons),reason='; '.join(reasons) or 'within monitoring thresholds',
                n=len(rows),required=n,metrics=m,reference_mae=reference_mae,mae_threshold=limit,
                months=[r['target_month'] for r in rows])


def decide(pairs,config):
    required=config['comparison_months']
    rows=sorted(pairs,key=lambda r:r['target_month'])[:required]
    if len(rows)<required:return dict(complete=False,n=len(rows),required=required)
    y=[r['actual'] for r in rows];old=[r['champion_prediction'] for r in rows];new=[r['challenger_prediction'] for r in rows]
    a,b=metrics(y,old),metrics(y,new)
    gain=a['mae']-b['mae'];wins=float(np.mean(np.abs(np.asarray(new)-y)<np.abs(np.asarray(old)-y)))
    rules=dict(mae_relative=gain>=a['mae']*config['minimum_relative_mae_gain'],
        mae_absolute=gain>=config['minimum_absolute_mae_gain_pp'],
        rmse=b['rmse']<=a['rmse']*config['maximum_rmse_ratio'],
        bias=abs(b['bias'])<=abs(a['bias'])+config['maximum_bias_deterioration_pp'],
        wins=wins>=config['minimum_win_fraction'])
    # Paired circular block bootstrap is descriptive with six observations.
    delta=np.abs(np.asarray(new)-y)-np.abs(np.asarray(old)-y)
    rng=np.random.default_rng(20261006);ix=np.concatenate([(rng.integers(0,len(rows),(2000,1))+np.arange(2))%len(rows)
        for _ in range((len(rows)+1)//2)],axis=1)[:,:len(rows)]
    ci=np.quantile(delta[ix].mean(axis=1),[.025,.975])
    return dict(complete=True,n=len(rows),required=required,promote=all(rules.values()),rules=rules,
        champion=a,challenger=b,mae_gain_pp=gain,win_fraction=wins,
        paired_absolute_loss_difference_ci=[float(v) for v in ci],
        uncertainty='descriptive block bootstrap; operational choice, not proof of permanent superiority',
        months=[r['target_month'] for r in rows])

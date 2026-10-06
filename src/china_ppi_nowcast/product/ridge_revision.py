"""Ridge v2: observed-value scaling, explicit sparse eligibility, nested time CV.

Existing bundles/vintages remain immutable. Only ridge artifacts are refitted;
other candidate artifacts and their rolling predictions are copied byte-for-byte.
"""
import argparse
import copy
import hashlib
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit

from .data import digest
from .train import metrics, write_json

GRID_ALPHA = (10., 25., 100., 400., 1600.)
GRID_HISTORY = (2, 12, 24)


class ObservedScaleRidge(RegressorMixin, BaseEstimator):
    """Missing inputs equal the training observed mean, with no regime dummies.

    Scale is estimated from genuinely observed values, not mean-filled rows.
    A fixed 1 log-percentage-point floor guards nearly constant/short series.
    With missing standardized values zero, rare products have less information
    relative to the same ridge penalty, rather than artificially unit variance.
    """
    def __init__(self, alpha=100., min_observations=2, stable=False, scale_floor=1.):
        self.alpha = alpha
        self.min_observations = min_observations
        self.stable = stable
        self.scale_floor = scale_floor

    def fit(self, X, y):
        counts = X.notna().sum()
        eligible = counts.eq(len(X)) if self.stable else counts.ge(self.min_observations)
        self.columns_ = list(counts[eligible].index)
        if not self.columns_:
            raise ValueError('No eligible ridge product histories')
        x = X[self.columns_]
        self.counts_ = counts[self.columns_]
        self.means_ = x.mean()
        self.scales_ = x.std(ddof=0).clip(lower=self.scale_floor)
        self.feature_names_in_ = np.asarray(X.columns)
        self.estimator_ = Ridge(alpha=self.alpha).fit(self.transform(X), y)
        return self

    def transform(self, X):
        x = X.reindex(columns=self.columns_)
        return ((x-self.means_)/self.scales_).fillna(0.)

    def predict(self, X):
        return self.estimator_.predict(self.transform(X))

    def attribution(self, X):
        return None


def select_ridge(X, y, metadata, stable=False):
    """Three inner expanding folds; target availability checked at each cutoff."""
    candidates = []
    history = (2,) if stable else GRID_HISTORY
    for minimum in history:
        for alpha in GRID_ALPHA:
            losses = []
            for tr, va in TimeSeriesSplit(n_splits=3).split(X):
                known = pd.to_datetime(metadata.iloc[tr].actual_published_at, utc=True) < pd.Timestamp(metadata.iloc[va[0]].feature_cutoff)
                tr = tr[known.to_numpy()]
                if len(tr)<4:
                    raise ValueError('Insufficient released targets in inner training fold')
                if not stable and X.iloc[tr].notna().sum().max()<minimum:
                    losses=[]
                    break
                fitted = ObservedScaleRidge(alpha, minimum, stable).fit(X.iloc[tr], y.iloc[tr])
                losses.extend(abs(fitted.predict(X.iloc[va])-y.iloc[va].to_numpy()))
            candidates.append(dict(alpha=alpha, min_observations=minimum, mae=float(np.mean(losses)) if losses else float('inf')))
    # Deterministic tie rule: strongest penalty and longer history at equal MAE.
    selected = min(candidates, key=lambda c:(c['mae'], -c['alpha'], -c['min_observations']))
    fitted = ObservedScaleRidge(selected['alpha'], selected['min_observations'], stable).fit(X, y)
    return fitted, dict(selected_strength=selected['alpha'], min_observations=selected['min_observations'],
                        selected_inner_mae=selected['mae'], inner_splits=3, candidates=candidates)


def refit(root, issue_forecast=True):
    root = Path(root).resolve()
    pointer = root/'config/product_pipeline.json'
    old_bundle = root/json.loads(pointer.read_text())['bundle']
    old = json.loads((old_bundle/'manifest.json').read_text())
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if old.get('ridge_revision', {}).get('code_hash') == code_hash:
        print('Ridge revision already fitted and activated.', flush=True)
        return old
    version = 'product-ridge-v2-'+digest(dict(parent=old['version'],code=code_hash))[:16]
    dest = root/'models'/version
    if dest.exists():
        raise ValueError('Unfinished/immutable ridge bundle already exists: '+str(dest))
    shutil.copytree(old_bundle, dest)
    (dest/'manifest.json').unlink()
    manifest = copy.deepcopy(old)
    manifest.update(version=version, git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip())
    manifest['ridge_revision'] = dict(code_hash=code_hash,parent_bundle=old['version'],
        scaling='observed-value population SD, floor 1 log percentage point; mean imputation maps missing to zero',
        missingness_indicators=False,alpha_grid=GRID_ALPHA,min_observations_grid=GRID_HISTORY,
        selection='three inner chronological folds inside each expanding outer origin; no target-month outcomes',
        scope='all five retained ridge timing/panel specifications; all non-ridge fits unchanged',
        limitation='designed after inspecting August/September instability; historical results remain exploratory')
    manifest['missingness'] = 'Native tree NaN unchanged; revised ridge uses observed-only mean/SD and no missingness indicators; sector/hybrid preprocessing unchanged'
    old_oof = pd.read_csv(old_bundle/'rolling_predictions.csv')
    new_records = []
    comparisons = []
    august = []
    for candidate in manifest['models']:
        if candidate['name'] != 'ridge':
            continue
        variant, panel = candidate['variant'], candidate['panel']
        matrix = pd.read_csv(dest/variant/'matrix.csv')
        X, y = matrix[candidate['feature_order']], matrix.target_mom_pct
        previous = old_oof[(old_oof.variant==variant)&(old_oof.panel==panel)&(old_oof.model=='ridge')]
        records = []
        august_model = None
        print(f'Ridge v2: {variant}/{panel}, {len(matrix)} months, {len(previous)} matched origins',flush=True)
        for old_row in previous.to_dict('records'):
            i = matrix.index[matrix.target_month.eq(old_row['target_month'])][0]
            eligible = (matrix.target_month < matrix.iloc[i].target_month) & (pd.to_datetime(matrix.actual_published_at,utc=True) < pd.Timestamp(matrix.iloc[i].feature_cutoff))
            ix = np.flatnonzero(eligible.to_numpy())
            fitted,tuning = select_ridge(X.iloc[ix],y.iloc[ix],matrix.iloc[ix],panel=='stable')
            prediction = float(fitted.predict(X.iloc[[i]])[0])
            a = float(y.iloc[i]);e=prediction-a
            row=dict(old_row,prediction=prediction,error=e,absolute_error=abs(e),squared_error=e**2,
                selected_strength=tuning['selected_strength'],selected_min_observations=tuning['min_observations'])
            assert row['training_end'] < row['target_month']
            records.append(row)
            if row['target_month']=='2026-08':
                august.append(dict(row,inner_tuning=tuning))
                august_model=fitted
                joblib.dump(fitted,dest/variant/f'{panel}_ridge_august_oos.joblib',compress=3)
        fitted,tuning=select_ridge(X,y,matrix,panel=='stable')
        artifact=dest/candidate['artifact'];joblib.dump(fitted,artifact,compress=3)
        candidate.update(artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
            tuning=tuning,hyperparameters=fitted.get_params(),learned_features=fitted.columns_,
            metrics=metrics([r['actual'] for r in records],[r['prediction'] for r in records]))
        new_records.extend(records)
        def summary(rows):
            return metrics([r['actual'] for r in rows],[r['prediction'] for r in rows])
        # Calendar threshold matches dashboard's last 12 calendar months.
        last=max(r['target_month'] for r in records);ym=pd.Period(last,freq='M');threshold=str(ym-12)
        comparisons.append(dict(variant=variant,panel=panel,old_full=summary(previous.to_dict('records')),
            revised_full=summary(records),old_recent=summary(previous[previous.target_month>threshold].to_dict('records')),
            revised_recent=summary([r for r in records if r['target_month']>threshold]),
            final_alpha=fitted.alpha,final_min_observations=fitted.min_observations,
            final_learned_features=len(fitted.columns_)))
    pd.concat([old_oof[old_oof.model!='ridge'],pd.DataFrame(new_records)],ignore_index=True).to_csv(dest/'rolling_predictions.csv',index=False)
    from .train import paired_comparisons
    (dest/'paired_comparisons.json').unlink()
    write_json(dest/'paired_comparisons.json',paired_comparisons(pd.read_csv(dest/'rolling_predictions.csv')))
    write_json(dest/'ridge_validation.json',dict(comparisons=comparisons,august=august))
    write_json(dest/'manifest.json',manifest)
    # Make the bundle reproducible, then infer September before changing the pointer.
    if issue_forecast:
        from .service import run
        from ..time import CHINA_TZ
        now=datetime.now(CHINA_TZ).isoformat()
        actuals=pd.read_csv(root/'data/registry/actuals.csv')
        if (actuals.target_month.eq('2026-09') & pd.to_datetime(actuals.published_at,utc=True).le(pd.Timestamp(now))).any():
            raise ValueError('September actual already public: cannot issue replacement prospective forecast')
        # Reporting reads the active pointer: set only after fits complete.
        pointer.write_text(json.dumps(dict(bundle='models/'+version),indent=2)+'\n')
        run(root,dest,'2026-09',now)
        from ..reporting import write_candidate_report
        write_candidate_report(root,manifest)
        from ..dashboard import write_dashboard
        write_dashboard(root,manifest,'2026-10',now)
    write_review(root,dest,manifest)
    print(json.dumps(dict(bundle=version,comparison=comparisons,august=[{k:v for k,v in r.items() if k!='inner_tuning'} for r in august]),indent=2),flush=True)
    return manifest


def write_review(root,bundle,manifest):
    from ..reporting import TIMINGS, PANELS
    review=json.loads((bundle/'ridge_validation.json').read_text())
    lines=['# Ridge specification revision','',
        'Ridge v2 scales price changes using genuinely observed training values, with a fixed minimum scale of one log percentage point. Missing values map to the observed training mean. Basket-era missingness indicators are removed.', '',
        'Each expanding outer training window selects alpha from 10, 25, 100, 400, 1600 and minimum observed history from 2, 12, 24 months using three chronological inner folds. Stable panels require complete training coverage. Preprocessing and eligibility are refitted within every fold. No prediction clipping is applied.', '',
        '**Caution:** this revision was designed after inspecting August/September instability. August outcomes were excluded from its fitting and tuning, but it is not an untouched validation experiment. Historical scores are exploratory pseudo-real-time evidence; prospective evaluation remains necessary.', '',
        'All non-ridge artifacts are unchanged. Earlier September forecasts and the original frozen August +0.410% ridge record remain immutable. New September estimates are issued at the actual rerun timestamp, not backdated.', '',
        '## Matched rolling validation','',
        '| Timing | Panel | N | Old MAE | Revised MAE | Old RMSE | Revised RMSE | Old recent MAE | Revised recent MAE | Final alpha | Minimum history | Learned products |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for c in review['comparisons']:
        a,b=c['old_full'],c['revised_full'];ra,rb=c['old_recent'],c['revised_recent']
        lines.append(f"| {TIMINGS[c['variant']]} | {PANELS[c['panel']]} | {b['n']} | {a['mae']:.3f} | {b['mae']:.3f} | {a['rmse']:.3f} | {b['rmse']:.3f} | {ra['mae']:.3f} | {rb['mae']:.3f} | {c['final_alpha']:g} | {c['final_min_observations']} | {c['final_learned_features']} |")
    lines+=['','Recent means the last 12 calendar months with eligible observations, not necessarily 12 forecasts. Errors are percentage points.','',
        '## August 2026 reconstructed forecasts','',
        '| Timing | Panel | Prediction | Actual | Error | Training through |','|---|---|---:|---:|---:|---|']
    for r in review['august']:
        lines.append(f"| {TIMINGS[r['variant']]} | {PANELS[r['panel']]} | {r['prediction']:+.3f}% | {r['actual']:+.3f}% | {r['error']:+.3f} | {r['training_end']} |")
    lines+=['','## September replacement vintages','', '| Timing | Panel | Prediction | Issued |','|---|---|---:|---|']
    for path in sorted((root/'data/product/vintages/2026-09').glob('*/forecast.json')):
        r=json.loads(path.read_text())
        if r['model_version']==manifest['version'] and r['model']=='ridge':
            lines.append(f"| {TIMINGS[r['variant']]} | {PANELS[r['panel']]} | {r['prediction_mom']:+.3f}% | {r['as_of']} |")
    (root/'reports/ridge_revision.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',default='.');parser.add_argument('--fit-only',action='store_true')
    args=parser.parse_args()
    # Fit through the importable module so joblib never records __main__.
    from .ridge_revision import refit as canonical_refit
    canonical_refit(args.root,not args.fit_only)

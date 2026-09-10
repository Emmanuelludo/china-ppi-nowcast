"""Publication-aware, nested chronological product-panel PPI evaluation.

No interpolated/backfilled product values. Missing predictors use training medians;
eligibility, scaling, dimensionality reduction and tuning are training-only.
"""
from pathlib import Path
import argparse, json, warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit

warnings.filterwarnings('ignore', category=RuntimeWarning)
ROOT = Path(__file__).resolve().parents[1]
INDUSTRY_CODES={'煤炭开采和洗选业':'PPI_B06','农副食品加工业':'PPI_C13','纺织业':'PPI_C17','造纸和纸制品业':'PPI_C22','石油、煤炭及其他燃料加工业':'PPI_C25','化学原料和化学制品制造业':'PPI_C26','化学纤维制造业':'PPI_C28','橡胶和塑料制品业':'PPI_C29','非金属矿物制品业':'PPI_C30','黑色金属冶炼和压延加工业':'PPI_C31','有色金属冶炼和压延加工业':'PPI_C32','燃气生产和供应业':'PPI_D45'}

class PanelRegressor:
    def __init__(self, kind='ridge', strength=10., components=3):
        self.kind, self.strength, self.components = kind, strength, components
    def fit(self, X, y):
        self.columns = X.columns[(X.notna().sum() >= min(12, len(X))) & (X.std() > 1e-10)]
        if not len(self.columns): raise ValueError('No eligible predictors')
        self.median = X[self.columns].median()
        self.scaler = StandardScaler().fit(X[self.columns].fillna(self.median))
        z = self.scaler.transform(X[self.columns].fillna(self.median))
        self.pca = None
        if self.kind == 'pca':
            self.pca = PCA(n_components=min(self.components, z.shape[0]-1, z.shape[1]), svd_solver='full').fit(z)
            z = self.pca.transform(z)
        self.model = (ElasticNet(alpha=self.strength, l1_ratio=.5, max_iter=3000, tol=1e-3) if self.kind == 'elastic_net' else Ridge(alpha=self.strength)).fit(z, y)
        if self.kind=='elastic_net' and self.model.n_iter_>=3000:raise ValueError('Elastic net did not converge')
        beta = self.model.coef_ if self.pca is None else self.pca.components_.T @ self.model.coef_
        self.beta = beta / self.scaler.scale_
        offset = 0 if self.pca is None else float(self.pca.mean_ @ beta)
        self.intercept = float(self.model.intercept_ - self.scaler.mean_ @ self.beta - offset)
        return self
    def predict(self, X):
        return self.intercept + X[self.columns].fillna(self.median).to_numpy() @ self.beta
    def contributions(self, X):
        v = X[self.columns].fillna(self.median).iloc[0]
        return {'intercept': self.intercept, **dict(zip(self.columns, v * self.beta))}

def tune(X, y, kind):
    grid = {'ridge':[.1, 10., 100., 1000.], 'elastic_net':[.01,.05,.2], 'pca':[1,3,5]}[kind]
    splits = TimeSeriesSplit(n_splits=3, test_size=3, gap=1)
    if kind=='ridge':
        # Reuse identical fold preprocessing across penalties. Dual ridge solves
        # are small (training months), even with hundreds of product features.
        errors=[[] for _ in grid]
        for tr,va in splits.split(X):
            a=X.iloc[tr]; b=X.iloc[va]
            cols=a.columns[(a.notna().sum()>=min(12,len(a)))&(a.std()>1e-10)]
            if not len(cols):continue
            med=a[cols].median();scaler=StandardScaler().fit(a[cols].fillna(med))
            z=scaler.transform(a[cols].fillna(med));v=scaler.transform(b[cols].fillna(med))
            yy=y.iloc[tr].to_numpy();center=yy.mean();kernel=z@z.T
            for k,alpha in enumerate(grid):
                pred=center+v@z.T@np.linalg.solve(kernel+alpha*np.eye(len(z)),yy-center)
                errors[k].extend((pred-y.iloc[va].to_numpy())**2)
        scores=[np.mean(e) if e else np.inf for e in errors]
        if not np.isfinite(scores).any():raise ValueError('No eligible inner validation folds')
        best=grid[int(np.argmin(scores))]
        return PanelRegressor('ridge',best).fit(X,y),best
    scores=[]
    for parameter in grid:
        errors=[]
        for tr, va in splits.split(X):
            try:
                model=PanelRegressor(kind, parameter if kind != 'pca' else 10., int(parameter) if kind == 'pca' else 3).fit(X.iloc[tr],y.iloc[tr])
                errors.extend((model.predict(X.iloc[va])-y.iloc[va].to_numpy())**2)
            except ValueError: pass
        scores.append(np.mean(errors) if errors else np.inf)
    p=grid[int(np.argmin(scores))]
    return PanelRegressor(kind, p if kind!='pca' else 10., int(p) if kind=='pca' else 3).fit(X,y), p

def build_matrix(panel, vintage):
    p=panel.loc[panel.vintage.eq(vintage)].copy()
    p['month']=pd.PeriodIndex(p.month, freq='M')
    dates=pd.to_datetime(p.available_at, utc=True)
    cutoff=dates.groupby(p.month).max()
    pieces=[]
    for transformation in ['mom_average','mom_end','mom_day_weighted','mom_sampling_5th_20th','slot_1_published_change','slot_2_published_change','slot_3_published_change','published_latest','published_chain','change_3m','momentum_3m']:
        if transformation not in p: continue
        a=p.pivot_table(index='month',columns='exact_product_id',values=transformation,aggfunc='last')
        a.columns=[f'{transformation}::{c}' for c in a.columns]
        pieces.append(a)
    if not pieces: raise ValueError('No recognized individual-product transformations')
    X=pd.concat(pieces,axis=1).sort_index()
    # Family/category return factors retain historical families when exact specs
    # disappear. These are auxiliary predictors, never asserted official weights.
    for group in ['product_family_id','category_id']:
        if group in p:
            f=p.groupby(['month',group]).mom_average.mean().unstack(group)
            f.columns=[f'{group}::{c}' for c in f.columns]
            X=pd.concat([X,f],axis=1)
    X['equal_weight_benchmark']=p.groupby('month').mom_average.mean()
    calendar=pd.period_range(X.index.min(),X.index.max(),freq='M')
    X=X.reindex(calendar)
    # Lag always means preceding calendar month, never previous nonmissing row.
    base=[c for c in X if c.startswith('mom_average::')]
    X=pd.concat([X,X[base].shift(1).add_prefix('lag1::')],axis=1)
    return X,cutoff

def metrics(g):
    e=g.forecast-g.actual
    return pd.Series(dict(n=len(g),rmse=np.sqrt(np.mean(e**2)),mae=np.mean(abs(e)),bias=e.mean(),correlation=g.forecast.corr(g.actual),directional_accuracy=np.mean(np.sign(g.forecast)==np.sign(g.actual)),max_absolute_error=abs(e).max()))

def run(args):
    out=ROOT/'data/v2/models';out.mkdir(parents=True,exist_ok=True)
    panel=pd.read_csv(args.panel); targets=pd.read_csv(args.targets)
    targets['month']=pd.PeriodIndex(targets.month,freq='M')
    targets['available_at']=pd.to_datetime(targets.available_at,utc=True)
    series='target_id' if 'target_id' in targets else 'series_id'
    if 'transformation' in targets: targets=targets[targets.transformation.astype(str).str.lower().isin(['mom','month_on_month','m/m']) | targets[series].str.endswith('_mom')]
    if args.headline_only:targets=targets[targets[series].eq('headline_ppi_mom')]
    rows=[];current=[];attrib=[];selection=[]
    if args.resume:
        for name,destination in [('rolling_forecasts.csv',rows),('current_nowcasts.csv',current),('current_attributions.csv',attrib)]:
            if (out/name).exists():
                try: destination.extend(pd.read_csv(out/name).to_dict('records'))
                except pd.errors.EmptyDataError: pass
    done={(r['target_month'],r['vintage'],r['target_id'],r['window'],r['model']) for r in rows+current}
    for vintage in ['early','mid','final']:
        X,cutoffs=build_matrix(panel,vintage)
        for target_id,t in targets.groupby(series):
            if vintage != 'final' and (target_id.startswith('industry_') or target_id.startswith('purchasing_') and target_id!='purchasing_ppi_mom'):
                continue
            t=t.sort_values('available_at').drop_duplicates('month',keep='first').set_index('month')
            y=t.value.reindex(X.index)
            full=X.copy()
            if target_id.startswith('industry_'):
                name=t.target_name_zh.iloc[0] if 'target_name_zh' in t else ''
                code=INDUSTRY_CODES.get(name)
                ids=set(panel.loc[panel.ppi_industry_id.eq(code),'exact_product_id']) if code else set()
                full=full[[c for c in full if c.split('::')[-1] in ids or c.startswith('category_id::') or c=='equal_weight_benchmark']]
            for lag in [1,2,3]:full[f'ppi_lag{lag}']=y.shift(lag)
            for month,cutoff in cutoffs.items():
                if month not in full.index or pd.isna(cutoff):continue
                # A nowcast is valid only before the target release.
                if month in t.index and cutoff >= t.loc[month,'available_at']:continue
                train_months=t.index[(t.index<month)&(t.available_at<cutoff)]
                train_months=full.index.intersection(train_months)
                train_months=train_months[y.reindex(train_months).notna()]
                if len(train_months)<args.min_train:continue
                test=full.loc[[month]].copy()
                for lag in [1,2,3]:
                    prior=month-lag
                    if prior not in t.index or t.loc[prior,'available_at']>=cutoff:test[f'ppi_lag{lag}']=np.nan
                actual=float(y.loc[month]) if pd.notna(y.loc[month]) else np.nan
                for window in ['expanding','rolling']:
                    if window=='rolling' and target_id!='headline_ppi_mom':continue
                    tr=train_months if window=='expanding' else train_months[-args.rolling_months:]
                    if len(tr)<args.min_train:continue
                    xx,yy=full.loc[tr].copy(),y.loc[tr]
                    # Historical lag values must have been released by that training row's cutoff.
                    for lag in [1,2,3]:
                        for tm in tr:
                            prior=tm-lag; historical_cutoff=cutoffs.get(tm)
                            if historical_cutoff is None or prior not in t.index or t.loc[prior,'available_at']>=historical_cutoff:xx.loc[tm,f'ppi_lag{lag}']=np.nan
                    kinds=['zero','ar','equal_bridge','category_bridge','ridge','elastic_net','pca'] if target_id=='headline_ppi_mom' else ['zero','ar','category_bridge','ridge']
                    if vintage!='final': kinds=[k for k in kinds if k not in ['elastic_net','pca']]
                    for kind in kinds:
                        if (str(month),vintage,target_id,window,kind) in done:continue
                        try:
                            if kind=='zero':pred=0.;model=None;parameter=None
                            elif kind=='ar':
                                cols=['ppi_lag1','ppi_lag2','ppi_lag3'];model=PanelRegressor('ridge',1.).fit(xx[cols],yy);pred=float(model.predict(test)[0]);parameter=1.
                            elif kind in ['equal_bridge','category_bridge']:
                                cols=(['equal_weight_benchmark'] if kind=='equal_bridge' else [c for c in xx if c.startswith('category_id::')])+['ppi_lag1']
                                model,parameter=tune(xx[cols],yy,'ridge');pred=float(model.predict(test)[0])
                            else:model,parameter=tune(xx,yy,kind);pred=float(model.predict(test)[0])
                        except ValueError:continue
                        previous=[r['actual']-r['forecast'] for r in rows if r['target_id']==target_id and r['vintage']==vintage and r['window']==window and r['model']==kind and pd.notna(r['actual']) and pd.Timestamp(r['actual_available_at'])<cutoff]
                        lower,upper=(pred+np.quantile(previous,[.1,.9])) if len(previous)>=12 else (np.nan,np.nan)
                        row=dict(target_month=str(month),forecast_vintage=cutoff.isoformat(),vintage=vintage,target_id=target_id,window=window,model=kind,forecast=pred,actual=actual,actual_available_at=t.loc[month,'available_at'].isoformat() if month in t.index else None,n_train=len(tr),n_features=len(model.columns) if model else 0,tuning_parameter=parameter,lower_80=lower,upper_80=upper,interval_calibration_n=len(previous),target_provenance='dated_original_page_snapshot_not_immutable_first_release')
                        if pd.notna(actual):rows.append(row)
                        else:
                            current.append(row)
                            if model:
                                for feature,value in model.contributions(test).items():attrib.append(dict(target_month=str(month),vintage=vintage,target_id=target_id,window=window,model=kind,feature=feature,contribution=value))
            print(vintage,target_id,'complete',flush=True)
            pd.DataFrame(rows).to_csv(out/'rolling_forecasts.csv',index=False)
            pd.DataFrame(current).to_csv(out/'current_nowcasts.csv',index=False)
            pd.DataFrame(attrib).to_csv(out/'current_attributions.csv',index=False)
    f=pd.DataFrame(rows); f.groupby(['target_id','vintage','window','model']).apply(metrics,include_groups=False).reset_index().to_csv(out/'leaderboard.csv',index=False)
    pd.DataFrame(current).to_csv(out/'current_nowcasts.csv',index=False)
    pd.DataFrame(attrib).to_csv(out/'current_attributions.csv',index=False)
    (out/'run_metadata.json').write_text(json.dumps(dict(min_train=args.min_train,rolling_months=args.rolling_months,inner_validation='3 expanding folds, three-month validation blocks, one-month gap',interval='80% past OOS actual-minus-forecast empirical quantiles; unavailable below 12',limitation='Original release pages can have unobserved revisions; not certified immutable real-time vintages'),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--panel',default=str(ROOT/'data/v2/products/product_vintage_features.csv'));p.add_argument('--targets',default=str(ROOT/'data/v2/targets/sector_targets_long.csv'));p.add_argument('--min-train',type=int,default=36);p.add_argument('--rolling-months',type=int,default=48);p.add_argument('--headline-only',action='store_true');p.add_argument('--resume',action='store_true');run(p.parse_args())

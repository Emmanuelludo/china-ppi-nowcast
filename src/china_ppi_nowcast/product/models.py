"""Fold-local preprocessing and nested chronological tuning for all retained families."""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingRegressor,RandomForestRegressor,VotingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

PRODUCT_MODELS=('ridge','histgb','xgboost','catboost','lightgbm')
ALL_MODELS=PRODUCT_MODELS+('category_factor','sector_first','random_forest','economic_ml_hybrid','direct_tracker')
TREE_MODELS=('histgb','xgboost','catboost','lightgbm','random_forest')
SEED=20260916


def ridge(alpha):
    return make_pipeline(SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True),
                         StandardScaler(),Ridge(alpha=alpha))


def factory(name,strength,n_columns):
    if name in ('ridge','sector_first'): return ridge(strength)
    if name=='category_factor':
        return make_pipeline(SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True),
            StandardScaler(),PCA(n_components=min(3,n_columns)),Ridge(alpha=strength))
    if name=='histgb':
        return HistGradientBoostingRegressor(max_iter=150,learning_rate=.04,max_leaf_nodes=4,
            min_samples_leaf=8,l2_regularization=strength,early_stopping=False,random_state=SEED)
    if name=='xgboost':
        from xgboost import XGBRegressor
        return XGBRegressor(n_estimators=150,max_depth=2,learning_rate=.04,min_child_weight=8,
            subsample=.8,colsample_bytree=.8,reg_alpha=.1,reg_lambda=strength,random_state=SEED,
            n_jobs=1,tree_method='hist',missing=np.nan)
    if name=='catboost':
        from catboost import CatBoostRegressor
        return CatBoostRegressor(iterations=150,depth=2,learning_rate=.04,l2_leaf_reg=strength,
            random_strength=1,loss_function='RMSE',nan_mode='Min',random_seed=SEED,
            verbose=False,allow_writing_files=False,thread_count=1)
    if name=='lightgbm':
        from lightgbm import LGBMRegressor
        return LGBMRegressor(n_estimators=150,learning_rate=.04,num_leaves=4,max_depth=2,
            min_child_samples=8,min_split_gain=.001,colsample_bytree=.8,subsample=.8,
            subsample_freq=1,reg_alpha=.1,reg_lambda=strength,verbosity=-1,random_state=SEED,
            n_jobs=1,deterministic=True,force_col_wise=True)
    if name=='random_forest':
        return RandomForestRegressor(n_estimators=100,max_depth=4,min_samples_leaf=int(strength),
                                     max_features=.8,n_jobs=1,random_state=SEED)
    if name=='economic_ml_hybrid':
        return VotingRegressor([('ridge',ridge(strength)),('histgb',factory('histgb',strength,n_columns))])
    raise ValueError(name)


class ProductEstimator(RegressorMixin,BaseEstimator):
    def __init__(self,name='histgb',strength=5.,stable=False,groups=None):
        self.name,self.strength,self.stable,self.groups=name,strength,stable,groups

    def transform(self,X):
        X=X.reindex(columns=self.columns_)
        if self.name in ('category_factor','sector_first','economic_ml_hybrid'):
            return pd.DataFrame({g:X[[c for c in X if self.groups[c]==g]].mean(axis=1)
                for g in sorted(set(self.groups[c] for c in self.columns_))},index=X.index)
        return X

    def fit(self,X,y):
        self.feature_names_in_=np.asarray(X.columns)
        coverage=X.notna().mean()
        self.columns_=list(coverage[coverage.eq(1) if self.stable else coverage.gt(0)].index)
        if not self.columns_: raise ValueError('no learnable product columns')
        x=self.transform(X)
        if self.name!='direct_tracker': self.estimator_=factory(self.name,self.strength,x.shape[1]).fit(x,y)
        return self

    def predict(self,X):
        x=self.transform(X)
        if self.name=='direct_tracker': return 100*np.expm1(x.mean(axis=1).to_numpy()/100)
        return np.asarray(self.estimator_.predict(x),dtype=float)

    def attribution(self,X):
        if self.name not in TREE_MODELS: return None
        x=self.transform(X)
        if self.name=='xgboost':
            import xgboost as xgb
            values=self.estimator_.get_booster().predict(xgb.DMatrix(x),pred_contribs=True)
            baseline,contrib=values[:,-1],values[:,:-1]
        elif self.name=='catboost':
            from catboost import Pool
            values=self.estimator_.get_feature_importance(Pool(x),type='ShapValues')
            baseline,contrib=values[:,-1],values[:,:-1]
        elif self.name=='lightgbm':
            values=self.estimator_.predict(x,pred_contrib=True)
            baseline,contrib=values[:,-1],values[:,:-1]
        else:
            import shap
            explainer=shap.TreeExplainer(self.estimator_,feature_perturbation='tree_path_dependent')
            contrib=np.asarray(explainer.shap_values(x,check_additivity=True))
            baseline=np.repeat(float(np.asarray(explainer.expected_value).ravel()[0]),len(x))
        prediction=self.predict(X)
        if not np.allclose(baseline+contrib.sum(axis=1),prediction,atol=2e-5,rtol=2e-5):
            raise ValueError('SHAP reconciliation failure')
        attribution=pd.DataFrame(contrib,columns=self.columns_,index=X.index)
        return baseline,attribution.reindex(columns=X.columns,fill_value=0),prediction


def select_fit(X,y,name,stable,groups,metadata=None):
    grid=[0.] if name=='direct_tracker' else ([4,8] if name=='random_forest' else [5.,25.])
    scores=[]
    for strength in grid:
        losses=[]
        for tr,va in TimeSeriesSplit(n_splits=2).split(X):
            if metadata is not None:
                known=pd.to_datetime(metadata.iloc[tr].actual_published_at,utc=True) < pd.Timestamp(metadata.iloc[va[0]].feature_cutoff)
                tr=tr[known.to_numpy()]
                if len(tr)<4: raise ValueError('insufficient released targets in inner training fold')
            fitted=ProductEstimator(name,strength,stable,groups).fit(X.iloc[tr],y.iloc[tr])
            losses.extend(abs(fitted.predict(X.iloc[va])-y.iloc[va].to_numpy()))
        scores.append((float(np.mean(losses)),strength))
    score,strength=min(scores)
    return ProductEstimator(name,strength,stable,groups).fit(X,y),dict(
        selected_strength=strength,inner_mae=score,candidates=grid,inner_splits=2,
        selection='nested_expanding_window_MAE')

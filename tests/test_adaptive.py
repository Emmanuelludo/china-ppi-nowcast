import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import joblib
import numpy as np
import pandas as pd
from china_ppi_nowcast.adaptive.policy import trigger,decide
from china_ppi_nowcast.adaptive.engine import run,read_events,replay,known_actuals,key
from china_ppi_nowcast.adaptive.fitting import select
from china_ppi_nowcast.product.data import canonicalize,catalog_from,available,feature_row
from china_ppi_nowcast.product.ridge_revision import ObservedScaleRidge

ROOT=Path(__file__).parents[1]
CONFIG=json.loads((ROOT/'config/adaptive.json').read_text())

class PolicyTests(unittest.TestCase):
    def test_four_outcomes_required_and_bias_triggers(self):
        r=[dict(target_month=f'2026-0{i+1}',actual=.5,prediction=0.) for i in range(4)]
        self.assertFalse(trigger(r[:3],.1,CONFIG)['triggered'])
        self.assertTrue(trigger(r,.1,CONFIG)['triggered'])
        self.assertFalse(trigger([dict(x,prediction=.5) for x in r],.1,CONFIG)['triggered'])
    def test_promotion_requires_six_common_months_and_material_gain(self):
        r=[dict(target_month=f'2026-0{i+1}',actual=.5,champion_prediction=0.,challenger_prediction=.4) for i in range(6)]
        self.assertFalse(decide(r[:5],CONFIG)['complete'])
        self.assertTrue(decide(r,CONFIG)['promote'])
        self.assertFalse(decide([dict(x,challenger_prediction=.001) for x in r],CONFIG)['promote'])
    def test_bad_challenger_is_retained_only_as_archive(self):
        r=[dict(target_month=f'2026-0{i+1}',actual=.5,champion_prediction=.4,challenger_prediction=1.) for i in range(6)]
        self.assertFalse(decide(r,CONFIG)['promote'])
    def test_nested_selector_respects_target_release_and_handles_missingness(self):
        n=72;months=pd.period_range('2019-01',periods=n,freq='M');rng=np.random.default_rng(9)
        X=pd.DataFrame(rng.normal(size=(n,4)),columns=['a','b','c','d']);X.loc[:50,'d']=np.nan
        y=pd.Series(.15*X.a-.1*X.b)
        meta=pd.DataFrame(dict(target_month=months.astype(str),actual_published_at=[(m+1).start_time.tz_localize('UTC')+pd.Timedelta(days=8) for m in months],
            feature_cutoff=[m.start_time.tz_localize('UTC')+pd.Timedelta(days=23) for m in months]))
        cfg=dict(CONFIG,minimum_training_months=12)
        fitted,tuning,ix=select(X,y,meta,'ridge',False,{},cfg)
        self.assertTrue(np.isfinite(fitted.predict(X.tail(1))).all())
        self.assertEqual(tuning['inner_blocks'],3)
        # If every target is released after the fitting cutoff, tuning cannot proceed.
        future=meta.copy();future.actual_published_at=pd.Timestamp('2100-01-01',tz='UTC')
        with self.assertRaisesRegex(ValueError,'insufficient released'):
            select(X,y,future,'ridge',False,{},cfg)
    def test_all_retained_calibrated_families_can_fit_the_adaptive_selector(self):
        if any(importlib.util.find_spec(k) is None for k in ['xgboost','catboost','lightgbm']):
            self.skipTest('External candidates verified in the pinned GitHub environment')
        rng=np.random.default_rng(42);n=60
        X=pd.DataFrame(rng.normal(size=(n,5)),columns=['a','b','c','d','e']);X.loc[:20,'e']=np.nan
        y=pd.Series(.1*X.a+.03*X.b);months=pd.period_range('2019-01',periods=n,freq='M')
        meta=pd.DataFrame(dict(actual_published_at=[(m+1).start_time.tz_localize('UTC')+pd.Timedelta(days=8) for m in months],
            feature_cutoff=[m.start_time.tz_localize('UTC')+pd.Timedelta(days=23) for m in months]))
        cfg=dict(CONFIG,minimum_training_months=12,training_windows=[None])
        for name in ['histgb','xgboost','catboost','lightgbm','random_forest','sector_first','economic_ml_hybrid']:
            with self.subTest(model=name):
                fitted,_,_=select(X,y,meta,name,False,{c:'sector' for c in X},cfg)
                self.assertTrue(np.isfinite(fitted.predict(X.tail(1))).all())


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT);self.root=Path(self.temp.name)
        for d in ['config','reports','data/registry','data/processed','models/base']:(self.root/d).mkdir(parents=True)
        (self.root/'config/adaptive.json').write_text(json.dumps(CONFIG))
        months=pd.period_range('2026-01','2027-08',freq='M');raw=[];actuals=[]
        for j,m in enumerate(months):
            actual=1. if m>=pd.Period('2027-04',freq='M') else .5
            pub=((m+1).start_time+pd.Timedelta(days=8,hours=1)).tz_localize('UTC').isoformat()
            actuals.append(dict(target_month=str(m),actual_mom_pct=actual,published_at=pub,retrieved_at=pub,source_url='fixture:official',content_sha256='actual-'+str(m)))
            for w,day in [('1-10',13),('11-20',23),('21-end',m.days_in_month+3)]:
                pub=(m.start_time+pd.Timedelta(days=day,hours=1)).tz_localize('UTC').isoformat()
                for i in range(50):
                    raw.append(dict(release_month=str(m),window=w,product_name_cn=f'Material {i:02d}',unit_cn='吨',
                        price_cny=100+i+j,change_pct=1.,category_cn='sector',published_at=pub,retrieved_at=pub,
                        source_url=f'fixture:{m}:{w}',content_sha256=f'snapshot-{m}-{w}'))
        self.raw=pd.DataFrame(raw);self.raw.to_csv(self.root/'data/processed/nbs_ten_day_observations.csv.gz',index=False)
        pd.DataFrame(actuals).to_csv(self.root/'data/registry/actuals.csv',index=False)
        x=canonicalize(self.raw);self.catalog=catalog_from(x);self.columns=['price__'+p for p in sorted(self.catalog['products'])[:2]]
        bundle=self.root/'models/base';(bundle/'twentieth').mkdir()
        matrix=self.matrix('2026-04');matrix.to_csv(bundle/'twentieth/matrix.csv',index=False)
        cs=[]
        for i,name in enumerate(['ridge','histgb']):
            column=self.columns[i];model=ObservedScaleRidge().fit(matrix[[column]],np.full(len(matrix),0. if i==0 else .5))
            path=bundle/f'{name}.joblib';joblib.dump(model,path)
            cs.append(dict(name=name,variant='twentieth',panel='union',artifact=path.name,
                artifact_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),feature_order=[column],learned_features=[column],
                training_start=matrix.iloc[0].target_month,training_end='2026-04',training_rows=len(matrix),metrics=dict(mae=.1,n=16),hyperparameters={}))
        (bundle/'catalog.json').write_text(json.dumps(self.catalog))
        (bundle/'rolling_predictions.csv').write_text('variant,panel,model,target_month,prediction,actual,error,absolute_error,squared_error\n'+'twentieth,union,ridge,2026-04,0,.5,-.5,.5,.25\n'+'twentieth,union,histgb,2026-04,.5,.5,0,0,0\n')
        self.base=dict(version='base',models=cs,packages={},training_actual_cutoff='2026-05-09T01:00:00Z',source_start='2026-01-01',source_end='2026-08-31')
        (bundle/'manifest.json').write_text(json.dumps(self.base));(self.root/'config/product_pipeline.json').write_text('{"bundle":"models/base"}')
        for m in ['2026-05','2026-06','2026-07','2026-08']:
            for c,p in zip(cs,[0.,.5]):self.register(m,c,'base',p)
        self.fits=0
    def tearDown(self):self.temp.cleanup()
    def matrix(self,end):
        return pd.DataFrame({c:np.arange(16.)/10 for c in self.columns}|dict(target_month=pd.period_range(end=end,periods=16,freq='M').astype(str)))
    def register(self,month,c,version,prediction):
        asof=pd.Timestamp(month+'-24T02:00:00Z').isoformat()
        _,meta=feature_row(canonicalize(self.raw),self.catalog,month,'twentieth',asof,True)
        fid=hashlib.sha256(f'{version}-{month}-{c["name"]}'.encode()).hexdigest()
        directory=self.root/'data/product/vintages'/month/fid[:20];directory.mkdir(parents=True)
        (directory/'features.json').write_text(json.dumps(meta))
        (directory/'forecast.json').write_text(json.dumps(dict(forecast_id=fid,target_month=month,as_of=asof,
            variant='twentieth',panel='union',model=c['name'],model_version=version,prediction_mom=prediction)))
    def fit(self,root,cycle,asof):
        self.fits+=1;dest=root/'models/adaptive'/cycle['cycle_id'];dest.mkdir(parents=True)
        actuals=known_actuals(root,asof);end=max(actuals);target=actuals[end]['actual_mom_pct'];matrix=self.matrix(end)
        c=copy.deepcopy(cycle['champion']['candidate']);model=ObservedScaleRidge().fit(matrix[c['feature_order']],np.full(len(matrix),target))
        joblib.dump(model,dest/'model.joblib');matrix.to_csv(dest/'matrix.csv',index=False)
        c.update(artifact='model.joblib',artifact_sha256=hashlib.sha256((dest/'model.joblib').read_bytes()).hexdigest(),training_end=end)
        x=available(canonicalize(self.raw),asof,True);(dest/'catalog.json').write_text(json.dumps(catalog_from(x)))
        (dest/'rolling_predictions.csv').write_text('variant,panel,model,target_month,prediction,actual,error,absolute_error,squared_error\ntwentieth,union,ridge,2026-04,.5,.5,0,0,0\n')
        m=dict(candidate=c,created_at=asof,training_actual_cutoff=actuals[end]['published_at'],source_start='2026-01-01',source_end=str(x.period_end.max().date()))
        (dest/'manifest.json').write_text(json.dumps(m));return m
    def test_full_lifecycle_promotes_after_six_future_months_and_repeats(self):
        first=run(self.root,'2026-10-06T20:00:00Z',fit_callback=self.fit)
        self.assertEqual(first['refits'],1);self.assertEqual(first['active_trials'],1)
        hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('forecast.json')}
        repeated=run(self.root,'2026-10-06T21:00:00Z',fit_callback=self.fit)
        self.assertEqual(self.fits,1);self.assertEqual(first['journal_events'],repeated['journal_events'])
        for month in pd.period_range('2026-10','2027-03',freq='M'):
            run(self.root,str(month)+'-24T02:00:00Z',fit_callback=self.fit)
        self.assertEqual(json.loads((self.root/'config/product_pipeline.json').read_text())['bundle'],'models/base')
        outcome=run(self.root,'2027-04-09T02:00:00Z',fit_callback=self.fit)
        self.assertEqual(outcome['promotions'],1)
        state=replay(read_events(self.root));cycle=next(iter(state['cycles'].values()))
        self.assertEqual(cycle['status'],'promoted');self.assertEqual(cycle['decision']['comparison']['n'],6)
        bundle=json.loads((self.root/'config/product_pipeline.json').read_text())['bundle'];m=json.loads((self.root/bundle/'manifest.json').read_text())
        # Other model families retain the exact incumbent artifact.
        untouched=next(c for c in m['models'] if c['name']=='histgb')
        self.assertEqual(untouched['artifact_sha256'],self.base['models'][1]['artifact_sha256'])
        for p,h in hashes.items():self.assertEqual(hashlib.sha256(Path(p).read_bytes()).hexdigest(),h)
        champion=next(c for c in m['models'] if c['name']=='ridge')
        for month in ['2027-04','2027-05','2027-06','2027-07']:self.register(month,champion,m['version'],.5)
        run(self.root,'2027-08-10T02:00:00Z',fit_callback=self.fit)
        self.assertEqual(self.fits,2)
        self.assertEqual(len(replay(read_events(self.root))['cycles']),2)
    def test_journal_tampering_and_backdated_lifecycle_fail(self):
        run(self.root,'2026-10-06T20:00:00Z',fit_callback=self.fit)
        with self.assertRaisesRegex(ValueError,'backwards'):
            run(self.root,'2026-10-05T20:00:00Z',fit_callback=self.fit)
        p=next((self.root/'data/adaptive/events').glob('*.json'));e=json.loads(p.read_text());e['as_of']='2000-01-01';p.write_text(json.dumps(e))
        with self.assertRaisesRegex(ValueError,'integrity'):read_events(self.root)
    def test_missing_release_stays_pending_and_actual_prevents_late_pairs(self):
        run(self.root,'2026-10-06T20:00:00Z',fit_callback=self.fit)
        self.assertEqual(len(list((self.root/'data/adaptive/forecasts').rglob('pair.json'))),0)
        run(self.root,'2026-11-10T02:00:00Z','2026-10',fit_callback=self.fit)
        self.assertEqual(len(list((self.root/'data/adaptive/forecasts').rglob('pair.json'))),0)

    def test_retrospective_fit_cannot_supply_prospective_monitoring_outcomes(self):
        path=self.root/'models/base/manifest.json'
        m=json.loads(path.read_text())
        m['models'][0]['training_end']='2026-08'
        path.write_text(json.dumps(m))
        result=run(self.root,'2026-10-06T20:00:00Z',fit_callback=self.fit)
        self.assertEqual(result['refits'],0)
        self.assertEqual(self.fits,0)

    def test_failed_refit_preserves_a_replayable_queue_and_retries(self):
        def fail(root,cycle,asof):raise ValueError('fixture fitting failure')
        with self.assertRaisesRegex(ValueError,'fixture fitting failure'):
            run(self.root,'2026-10-06T20:00:00Z',fit_callback=fail)
        state=replay(read_events(self.root))
        self.assertEqual(state,json.loads((self.root/'data/adaptive/state.json').read_text()))
        self.assertEqual(next(iter(state['cycles'].values()))['status'],'requested')
        result=run(self.root,'2026-10-07T20:00:00Z',fit_callback=self.fit)
        self.assertEqual(result['refits'],1)
        self.assertEqual(len(replay(read_events(self.root))['cycles']),1)

    def test_explicit_new_bundle_adoption_does_not_strand_an_old_trial(self):
        import shutil
        run(self.root,'2026-10-06T20:00:00Z',fit_callback=self.fit)
        manual=self.root/'models/manual';shutil.copytree(self.root/'models/base',manual)
        m=json.loads((manual/'manifest.json').read_text());m['version']='manual'
        matrix=self.matrix('2026-08');candidate=m['models'][0]
        model=ObservedScaleRidge().fit(matrix[candidate['feature_order']],np.full(len(matrix),.25))
        joblib.dump(model,manual/candidate['artifact'])
        candidate['artifact_sha256']=hashlib.sha256((manual/candidate['artifact']).read_bytes()).hexdigest()
        candidate['training_end']='2026-08';m['training_actual_cutoff']='2026-09-09T01:00:00Z'
        (manual/'manifest.json').write_text(json.dumps(m))
        (self.root/'config/product_pipeline.json').write_text('{"bundle":"models/manual"}')
        run(self.root,'2026-10-10T20:00:00Z',fit_callback=self.fit)
        state=replay(read_events(self.root))
        self.assertEqual(next(iter(state['cycles'].values()))['status'],'cancelled')
        self.assertEqual(state['champions']['twentieth/union/ridge']['bundle'],'models/manual')
        self.assertEqual(state['completed']['twentieth/union/ridge'],'2026-09')

class StoredSourceRefitTests(unittest.TestCase):
    def test_real_ridge_refit_saved_contract_and_idempotency(self):
        import shutil
        import importlib.metadata
        from unittest.mock import patch
        from china_ppi_nowcast.adaptive.fitting import fit
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root=Path(directory)
            for p in ['data/processed','data/registry','models']:(root/p).mkdir(parents=True)
            for p in ['data/processed/nbs_ten_day_observations.csv.gz','data/registry/actuals.csv']:
                shutil.copyfile(ROOT/p,root/p)
            cycle=dict(cycle_id='stored-source-ridge-test',variant='twentieth',panel='union',model='ridge',
                start_month='2026-09',config=dict(CONFIG,validation_months=2,training_windows=[None]))
            actual_version=importlib.metadata.version
            def versions(name):
                try:return actual_version(name)
                except importlib.metadata.PackageNotFoundError:return 'not-installed-in-ridge-only-test'
            with patch('china_ppi_nowcast.adaptive.fitting.subprocess.check_output',return_value='fixture-commit\n'),patch('china_ppi_nowcast.adaptive.fitting.importlib.metadata.version',side_effect=versions):
                manifest=fit(root,cycle,'2026-10-06T20:48:00Z')
                again=fit(root,cycle,'2026-10-06T20:49:00Z')
            self.assertEqual(manifest,again)
            self.assertEqual(manifest['candidate']['training_end'],'2026-08')
            self.assertLess(pd.Timestamp(manifest['training_actual_cutoff']),pd.Timestamp('2026-10-06T20:48:00Z'))
            dest=root/'models/adaptive'/cycle['cycle_id'];candidate=manifest['candidate']
            model=joblib.load(dest/candidate['artifact']);matrix=pd.read_csv(dest/'matrix.csv')
            self.assertTrue(np.isfinite(model.predict(matrix.tail(1).reindex(columns=candidate['feature_order']))).all())
            oof=pd.read_csv(dest/'rolling_predictions.csv')
            self.assertTrue((oof.training_end<oof.target_month).all())
            self.assertEqual(len(oof),2)

"""Reproduce v2 results or collect newly published official observations first.

Each successful run archives its forecasts and provenance. No run is described as
deployed merely because this command or a workflow file exists.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, os, shutil, subprocess, sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def run(script,*args):
    env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src');env['OPENBLAS_NUM_THREADS']='1';env['OMP_NUM_THREADS']='1'
    subprocess.run([sys.executable,str(ROOT/'scripts'/script),*map(str,args)],cwd=ROOT,env=env,check=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');a=p.parse_args()
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    archive=ROOT/'data/v2/runs'/stamp;archive.mkdir(parents=True)
    master=ROOT/'data/v2/master_raw_market_prices.csv'
    raw=master if master.exists() else ROOT/'data/interim/nbs_market_prices/raw_market_prices.csv'
    if a.refresh:
        stage=archive/'collection'
        run('collect_market_prices.py','--root',stage,'--page-count',4,'--workers',4)
        fresh=pd.read_csv(stage/'data/interim/nbs_market_prices/raw_market_prices.csv')
        old=pd.read_csv(raw)
        # Preserve older row vintages; product builder audits reference/spec duplicates.
        merged=pd.concat([old,fresh],ignore_index=True).drop_duplicates('observation_id',keep='first')
        raw=archive/'raw_union.csv';merged.to_csv(raw,index=False)
        run('v2_collect_sector_targets.py','--refresh')
        shutil.copy2(raw,master)
    targets=pd.read_csv(ROOT/'data/v2/targets/sector_targets_long.csv')
    canonical=targets[['month','target_id','value','available_at','source_sha256']].drop_duplicates().sort_values(['month','target_id','source_sha256']).to_csv(index=False)
    code_bytes=b''.join(p.read_bytes() for p in sorted((ROOT/'scripts').glob('v[234]_*.py')))
    fingerprint=hashlib.sha256(raw.read_bytes()+canonical.encode()+code_bytes).hexdigest()
    previous=ROOT/'data/v2/last_successful_input.json'
    if a.refresh and previous.exists() and json.loads(previous.read_text()).get('input_hash')==fingerprint:
        (archive/'manifest.json').write_text(json.dumps(dict(run_id=stamp,status='unchanged',input_hash=fingerprint),indent=2))
        print('No new source content: retained the last successful model run.');return
    run('v2_build_product_panel.py','--raw',raw)
    run('v2_fit_models.py')
    run('v2_sector_aggregation.py')
    run('v2_publish_results.py')
    run('v2_verify_delivery.py')
    run('v3_experiments.py')
    run('v3_freeze_models.py')
    run('v3_publish.py')
    shutil.copytree(ROOT/'data/v3',archive/'v3')
    run('v4_timing.py')
    run('v4_compare.py')
    run('v4_sector.py')
    run('v4_live.py')
    run('v4_live_sector.py')
    run('v4_publish.py')
    shutil.copytree(ROOT/'data/v4',archive/'v4')
    for name in ['rolling_forecasts.csv','leaderboard.csv','current_nowcasts.csv','current_attributions.csv','run_metadata.json']:
        source=ROOT/'data/v2/models'/name
        if source.exists():shutil.copy2(source,archive/name)
    record=dict(run_id=stamp,status='succeeded',refreshed=a.refresh,raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),report='reports/v2/China_PPI_Results.html')
    (archive/'manifest.json').write_text(json.dumps(record,indent=2))
    previous.write_text(json.dumps(dict(input_hash=fingerprint,run_id=stamp),indent=2))
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()

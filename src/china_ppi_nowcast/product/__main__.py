"""python -m china_ppi_nowcast.product train|ensure|run --root ."""
import argparse
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
from ..time import CHINA_TZ
from .train import train
from .service import run


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('train','ensure','run'))
    p.add_argument('--root',default='.');p.add_argument('--target-month');p.add_argument('--as-of')
    args=p.parse_args();root=Path(args.root).resolve();pointer=root/'config/product_pipeline.json'
    needs_training=not pointer.exists()
    if args.command=='ensure' and pointer.exists():
        configured=root/json.loads(pointer.read_text())['bundle']
        previous=json.loads((configured/'manifest.json').read_text())
        source_start=pd.read_csv(root/'data/processed/nbs_ten_day_observations.csv.gz',usecols=['release_month']).release_month.min()
        needs_training=source_start<previous['source_start'][:7]
    if args.command=='train' or (args.command=='ensure' and needs_training):
        manifest=train(root);pointer.write_text(json.dumps(dict(bundle='models/'+manifest['version']),indent=2)+'\n')
    if args.command!='train':
        now=datetime.now(CHINA_TZ);bundle=root/json.loads(pointer.read_text())['bundle']
        print(json.dumps(run(root,bundle,args.target_month or now.strftime('%Y-%m'),args.as_of or now.isoformat()),indent=2))


if __name__=='__main__':main()

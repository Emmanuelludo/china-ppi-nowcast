"""Versioned refresh of retained survey benchmarks after headline parser corrections."""
import argparse
import json
from datetime import datetime
from pathlib import Path
from .project import train_project_bundles
from ..forecast import create_forecast
from ..pipeline import load_config,repository_status,write_status_report
from ..storage import atomic_write_text
from ..time import CHINA_TZ


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--target-month');p.add_argument('--as-of')
    args=p.parse_args();root=Path(args.root).resolve();config=load_config(root)
    audit=json.loads((root/'reports/history_search.json').read_text())
    if audit.get('failed') or audit.get('parser_version')!='headline_v2':
        raise ValueError('corrected historical source pass required before benchmark refresh')
    bundle=root/'models/reconstructed-v3'
    if not (bundle/'manifest.json').exists():
        train_project_bundles(root,bundle,float(config['first_survey_carry_weight']))
    manifest=json.loads((bundle/'manifest.json').read_text())
    if not manifest.get('validated'):raise ValueError('refreshed benchmark bundle failed validation')
    config['model_bundle']='models/reconstructed-v3'
    atomic_write_text(root/'config/pipeline.json',json.dumps(config,indent=2)+'\n')
    now=datetime.now(CHINA_TZ)
    result=create_forecast(root,args.target_month or now.strftime('%Y-%m'),args.as_of or now.isoformat(),
        bundle,float(config['first_survey_carry_weight']))
    write_status_report(root,repository_status(root),result)
    print(json.dumps(result))


if __name__=='__main__':main()

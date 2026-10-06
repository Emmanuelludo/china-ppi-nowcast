import argparse,json
from datetime import datetime
from ..time import CHINA_TZ
from .engine import run
p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--as-of');p.add_argument('--target-month')
a=p.parse_args();print(json.dumps(run(a.root,a.as_of or datetime.now(CHINA_TZ).isoformat(),a.target_month),indent=2))

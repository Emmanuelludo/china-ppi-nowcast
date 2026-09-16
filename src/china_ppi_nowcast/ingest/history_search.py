"""Discover older official releases through NBS's public search frontend API.

The ordinary news index stops in 2021. The endpoint and parameter names are
published in www.stats.gov.cn/search/s and its public API JavaScript.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone,date,timedelta
import gzip
import hashlib
import json
import math
from pathlib import Path
import time
import urllib.parse
import urllib.request

from .nbs import NBSClient,ReleaseLink,PPI_TITLE_RE,_ingest_links
from ..time import parse_release_title
from ..storage import atomic_write_text

ENDPOINT='https://api.so-gov.cn/query/s'


def discover(root,kind,start='2014-01-01',end='2021-09-30',workers=4):
    directory=root/'data/raw/nbs/search';directory.mkdir(parents=True,exist_ok=True)
    cached={}
    for meta_path in sorted(directory.glob('*.metadata.json')):
        meta=json.loads(meta_path.read_text())
        cached[json.dumps(meta['params'],sort_keys=True)]=directory/(meta['content_sha256']+'.json.gz')
    query='流通领域重要生产资料' if kind=='ten_day' else '工业生产者'
    def page(number):
        params=dict(siteCode='bm36000002',qt=query,tab='',keyPlace=1,sort='dateDesc',
                    timeOption=2,startDateStr=start,endDateStr=end,page=number,pageSize=20)
        existing=cached.get(json.dumps(params,sort_keys=True))
        if existing is not None and existing.exists():return json.loads(gzip.decompress(existing.read_bytes()))
        payload=urllib.parse.urlencode(params).encode()
        request=urllib.request.Request(ENDPOINT,data=payload,headers={
            'Referer':'https://www.stats.gov.cn/','User-Agent':'china-ppi-nowcast/0.6'})
        for attempt in range(3):
            try:
                content=urllib.request.urlopen(request,timeout=30).read();break
            except Exception:
                if attempt==2:raise
                time.sleep(2**attempt)
        data=json.loads(content)
        if not data.get('ok'):raise ValueError('NBS search failed: '+str(data.get('msg')))
        sha=hashlib.sha256(content).hexdigest()
        path=directory/(sha+'.json.gz')
        if not path.exists():
            path.write_bytes(gzip.compress(content,mtime=0))
            atomic_write_text(directory/(sha+'.metadata.json'),json.dumps(dict(endpoint=ENDPOINT,params=params,
                content_sha256=sha,retrieved_at=datetime.now(timezone.utc).isoformat()),ensure_ascii=False,indent=2)+'\n')
        return data
    first=page(1);size=first.get('currentHits',0)
    if not size:raise ValueError('NBS search returned no historical hits')
    pages=math.ceil(first['totalHits']/size)
    # The public search UI caps pagination at 25; partition dates to avoid silently repeating its last page.
    if pages>25:
        first_day,last_day=date.fromisoformat(start),date.fromisoformat(end)
        if first_day>=last_day:raise ValueError('too many search results for one day')
        middle=first_day+(last_day-first_day)//2
        left,lreport=discover(root,kind,start,middle.isoformat(),workers)
        right,rreport=discover(root,kind,(middle+timedelta(days=1)).isoformat(),end,workers)
        unique={link.url:link for link in left+right}
        return list(unique.values()),dict(kind=kind,partitioned=True,parts=[lreport,rreport],official_release_links=len(unique))
    all_pages=[first]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        all_pages.extend(executor.map(page,range(2,pages+1)))
    links={}
    for data in all_pages:
        for result in data.get('resultDocs',[]):
            row=result['data'];url=row['url'];title=row['titleO']
            if urllib.parse.urlparse(url).hostname not in ('www.stats.gov.cn','stats.gov.cn'):continue
            valid=parse_release_title(title) if kind=='ten_day' else PPI_TITLE_RE.search(title)
            if valid:links[url]=ReleaseLink(title,url,kind)
    return list(links.values()),dict(kind=kind,pages=pages,total_hits=first['totalHits'],official_release_links=len(links))


def backfill(root,start='2014-01-01',end='2021-09-30'):
    links=[];discovery=[]
    for kind in ('ten_day','ppi'):
        found,report=discover(root,kind,start,end);links.extend(found);discovery.append(report)
        print(json.dumps(report),flush=True)
    result=_ingest_links(root,links,NBSClient(timeout=30,retries=3),6,skip_known_urls=True)
    import pandas as pd
    observations=pd.read_csv(root/'data/processed/nbs_ten_day_observations.csv.gz')
    actuals=pd.read_csv(root/'data/registry/actuals.csv')
    present=set(zip(observations.release_month,observations.window))
    months=pd.period_range(start[:7],observations.release_month.max(),freq='M')
    missing=[dict(month=str(m),window=w,reason='no retrieved official release; cancellation or discovery gap requires review')
             for m in months for w in ('1-10','11-20','21-end') if (str(m),w) not in present]
    result.update(discovery=discovery,requested_start=start,requested_end=end,
        source_start=observations.release_month.min(),source_end=observations.release_month.max(),
        price_releases=len(present),price_observations=len(observations),
        actual_months=actuals.target_month.nunique(),missing_price_windows=missing,
        missing_actual_months=[str(m) for m in months if str(m) not in set(actuals.target_month)])
    atomic_write_text(root/'reports/history_search.json',json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    if result['failed']:raise RuntimeError('historical release failures require review')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--start',default='2014-01-01');p.add_argument('--end',default='2021-09-30')
    a=p.parse_args();backfill(Path(a.root).resolve(),a.start,a.end)

"""Official dated PPI release tables; immutable snapshots, no invented target vintages."""
from __future__ import annotations
import argparse, hashlib, json, re, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
import pandas as pd
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/v2/targets'
BASE = 'https://www.stats.gov.cn/sj/zxfb/'
PATTERN = re.compile(r'(20\d{2})年(\d{1,2})月份?工业生产者出厂价格')
STAGES = {'工业生产者出厂价格':'headline_ppi', '生产资料':'means_ppi', '采掘':'mining_ppi', '原材料':'raw_material_ppi', '加工':'processing_ppi', '生活资料':'consumer_goods_ppi', '食品':'food_consumer_ppi','衣着':'clothing_consumer_ppi','一般日用品':'daily_consumer_ppi','耐用消费品':'durable_consumer_ppi','工业生产者购进价格':'purchasing_ppi'}

def fetch(url):
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=45) as r: return r.read()
        except Exception:
            if attempt == 2: raise

def discover(pages=67):
    def listing(i):
        url = BASE if i == 0 else urljoin(BASE, f'index_{i}.html')
        doc=html.fromstring(fetch(url)); result=[]
        for a in doc.xpath('//a[@href]'):
            title=re.sub(r'\s+','',a.text_content())
            if PATTERN.search(title): result.append((urljoin(url,a.get('href')),title))
        return result
    with ThreadPoolExecutor(max_workers=16) as pool:
        return dict(item for group in pool.map(listing,range(pages)) for item in group)

def parse(payload, url, title=''):
    doc=html.fromstring(payload.decode('utf-8'))
    title=(doc.xpath('//meta[@name="ArticleTitle"]/@content') or [title])[0]
    match=PATTERN.search(re.sub(r'\s+','',title))
    if not match: raise ValueError('Not a dated monthly PPI release')
    month=f'{int(match[1]):04d}-{int(match[2]):02d}'
    publication=(doc.xpath('//meta[@name="PubDate"]/@content') or [None])[0]
    if not publication:
        visible = doc.text_content()
        dated = re.search(r'(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\s+(\d{1,2}:\d{2})', visible)
        if dated: publication = dated[1].replace('/','-') + ' ' + dated[2]
    if not publication: raise ValueError('Missing official publication metadata')
    ts=pd.Timestamp(str(publication))
    if ts.year > int(match[1])+1: raise ValueError('Migrated page date is not original publication date')
    date_only=not bool(re.search(r'\d{1,2}:\d{2}',publication))
    if date_only: ts=ts+pd.Timedelta(hours=23,minutes=59,seconds=59)
    published=ts.tz_localize('Asia/Shanghai').isoformat()
    sha=hashlib.sha256(payload).hexdigest(); rows=[]
    for table in doc.xpath('//table'):
        if '环比' not in table.text_content() or '同比' not in table.text_content(): continue
        section='stage'
        for tr in table.xpath('.//tr'):
            cells=[re.sub(r'\s+','',c.text_content()) for c in tr.xpath('./td|./th')]
            if not cells: continue
            name=re.sub(r'^[一二三四五六七八九十]+[、.]','',cells[0])
            if '主要行业' in name: section='industry'; continue
            if '工业生产者购进价格' == name: section='purchasing'
            if len(cells)<3: continue
            try: values=[float(c.replace('−','-').replace('－','-').replace('％','').replace('%','')) for c in cells[1:3]]
            except ValueError: continue
            sid=STAGES.get(name) or ('industry_' if section=='industry' else 'purchasing_')+hashlib.sha256(name.encode()).hexdigest()[:12]
            for transformation,value,raw in zip(('mom','yoy'),values,cells[1:3]):
                rows.append(dict(month=month,target_id=f'{sid}_{transformation}',series_id=sid,target_name_zh=name,component_type=section,transformation=transformation,value=value,unit='percent',raw_value=raw,publication_at=published,available_at=published,publication_precision='date_conservative_eod' if date_only else 'minute',source_url=url,source_sha256=sha,vintage='dated_release_page_retrieved_now',revision_status='original_dated_page_not_archival_snapshot',retrieved_at=datetime.now(timezone.utc).isoformat()))
    if not rows: raise ValueError('No numeric sector target rows')
    return rows

def run(pages=67, refresh=False):
    OUT.mkdir(parents=True,exist_ok=True); (OUT/'html').mkdir(exist_ok=True)
    linkfile=OUT/'discovered_links.json'
    links=json.loads(linkfile.read_text()) if linkfile.exists() else discover(pages)
    if refresh: links.update(discover(min(pages,4)))
    linkfile.write_text(json.dumps(links,ensure_ascii=False,indent=2))
    def one(item):
        url,title=item
        try:
            key=hashlib.sha256(url.encode()).hexdigest(); cache=OUT/'html'/f'{key}.html'
            payload=cache.read_bytes() if cache.exists() else fetch(url)
            if b'Please enable JavaScript' in payload or b'<table' not in payload:
                if cache.exists():
                    rejected=OUT/'html'/('rejected_'+hashlib.sha256(payload).hexdigest()+'.html')
                    if not rejected.exists(): rejected.write_bytes(payload)
                payload=fetch(url)
                cache.write_bytes(payload)
            if not cache.exists(): cache.write_bytes(payload)
            rows=parse(payload,url,title)
            return rows,dict(source_url=url,title=title,status='parsed',rows=len(rows),month=rows[0]['month'],publication_at=rows[0]['publication_at'],source_sha256=rows[0]['source_sha256'],cache_path=str(cache.relative_to(ROOT)))
        except Exception as exc: return [],dict(source_url=url,title=title,status='failed',error=str(exc))
    rows=[]; logs=[]
    with ThreadPoolExecutor(max_workers=16) as pool:
        for data,log in pool.map(one,links.items()): rows.extend(data); logs.append(log)
    data=pd.DataFrame(rows).sort_values(['month','target_id','publication_at'])
    data['provenance_type']='official_dated_release_page'
    data.to_csv(OUT/'sector_targets_long.csv',index=False)
    pd.DataFrame(logs).to_csv(OUT/'source_audit.csv',index=False)
    duplicates=data[data.duplicated(['month','target_id'],keep=False)]
    duplicates.to_csv(OUT/'duplicate_targets.csv',index=False)
    chosen=data.drop_duplicates(['month','target_id'],keep='first')
    chosen.pivot(index='month',columns='target_id',values='value').to_csv(OUT/'sector_targets_wide.csv')
    chosen.groupby(['target_id','target_name_zh']).agg(start=('month','min'),end=('month','max'),months=('month','nunique')).to_csv(OUT/'series_coverage.csv')
    print(json.dumps({'releases':len(logs),'parsed':sum(x['status']=='parsed' for x in logs),'observations':len(data),'months':data.month.nunique(),'targets':data.target_id.nunique(),'start':data.month.min(),'end':data.month.max()},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--pages',type=int,default=67);p.add_argument('--refresh',action='store_true');a=p.parse_args();run(a.pages,a.refresh)

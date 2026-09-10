"""Dated NBS industry revenue weights; explicit economic proxies, not PPI weights."""
from pathlib import Path
import hashlib,json,re
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from lxml import html
import v2_collect_sector_targets as sources

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/v2/weights'

def parse(payload,url,title):
    d=html.fromstring(payload.decode('utf8'));dates=d.xpath('//meta[@name="PubDate"]/@content')
    if not dates:
        m=re.search(r'(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\s+(\d{1,2}:\d{2})',d.text_content())
        if m:dates=[m[1]+' '+m[2]]
    if not dates:raise ValueError('Missing publication metadata')
    available=pd.Timestamp(str(dates[0])).tz_localize('Asia/Shanghai').isoformat()
    rows=[]
    for t in d.xpath('//table'):
        if '煤炭开采和洗选业' not in t.text_content() or '营业收入' not in t.text_content():continue
        for tr in t.xpath('.//tr'):
            cells=[re.sub(r'\s+','',c.text_content()) for c in tr.xpath('./td|./th')]
            if len(cells)<7:continue
            try: revenue=float(cells[1].replace(',',''))
            except ValueError:continue
            rows.append(dict(industry_name=cells[0],revenue_100m_cny=revenue,available_at=available,release_title=title,source_url=url,source_sha256=hashlib.sha256(payload).hexdigest(),weight_type='industry_operating_revenue_proxy_not_official_ppi_weight'))
    if not rows:raise ValueError('No industry revenue table')
    result=pd.DataFrame(rows).drop_duplicates(['industry_name','available_at'])
    total=result.loc[result.industry_name.eq('总计'),'revenue_100m_cny']
    if total.empty:raise ValueError('No total denominator')
    result['economic_weight']=result.revenue_100m_cny/total.iloc[0]
    return result.loc[~result.industry_name.eq('总计')]

def main():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'html').mkdir(exist_ok=True)
    linksfile=OUT/'links.json'
    if linksfile.exists():links=json.loads(linksfile.read_text())
    else:
        sources.PATTERN=re.compile(r'20\d{2}年.*规模以上工业企业利润')
        links=sources.discover(67);linksfile.write_text(json.dumps(links,ensure_ascii=False,indent=2))
    def one(item):
        url,title=item;cache=OUT/'html'/(hashlib.sha256(url.encode()).hexdigest()+'.html')
        try:
            data=cache.read_bytes() if cache.exists() else sources.fetch(url)
            if not cache.exists():cache.write_bytes(data)
            frame=parse(data,url,title);return frame,dict(source_url=url,status='parsed',n=len(frame))
        except Exception as e:return pd.DataFrame(),dict(source_url=url,status='failed',error=str(e))
    frames=[];logs=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        for frame,log in pool.map(one,links.items()):
            if len(frame):frames.append(frame)
            logs.append(log)
    pd.DataFrame(logs).to_csv(OUT/'source_audit.csv',index=False)
    if not frames:raise RuntimeError('No verified economic weights')
    result=pd.concat(frames).sort_values('available_at');result.to_csv(OUT/'industry_revenue_weights.csv',index=False)
    print(json.dumps(dict(releases=sum(x['status']=='parsed' for x in logs),rows=len(result),start=result.available_at.min(),end=result.available_at.max())))

if __name__=='__main__':main()

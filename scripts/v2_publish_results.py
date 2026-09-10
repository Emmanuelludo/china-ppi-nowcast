"""Create a standalone readable research report from actual v2 forecast rows."""
from pathlib import Path
import base64, hashlib, html, io, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/v2'

def chart_image(fig, name):
    path=OUT/(name+'.png');fig.savefig(path,dpi=150,bbox_inches='tight');plt.close(fig)
    return '<img alt="'+html.escape(name)+'" src="data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()+'">'

def table(frame):
    return frame.to_html(index=False,escape=True,float_format=lambda v:f'{v:.3f}',border=0)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    folder=ROOT/'data/v2/models'
    f=pd.read_csv(folder/'rolling_forecasts.csv')
    scores=pd.read_csv(folder/'leaderboard.csv')
    current=pd.read_csv(folder/'current_nowcasts.csv')
    target=pd.read_csv(ROOT/'data/v2/targets/sector_targets_long.csv')
    names=target.drop_duplicates('target_id').set_index('target_id').target_name_zh.to_dict()
    scores['target_name']=scores.target_id.map(names)
    headline=scores[(scores.target_id=='headline_ppi_mom')&(scores.window=='expanding')].copy()
    # Ridge is prespecified here; the chart must not silently select the ex-post best.
    chosen=f[(f.target_id=='headline_ppi_mom')&(f.window=='expanding')&(f.model=='ridge')].copy()
    selected=chosen[chosen.vintage=='final'].sort_values('target_month')
    figures=[]
    fig,ax=plt.subplots(figsize=(11,4.7))
    for v,g in chosen.groupby('vintage'):
        g=g.sort_values('target_month');ax.plot(pd.to_datetime(g.target_month),g.forecast,label=v,alpha=.8)
    a=chosen.drop_duplicates('target_month').sort_values('target_month')
    ax.plot(pd.to_datetime(a.target_month),a.actual,color='black',linewidth=2,label='Official PPI MoM')
    ax.axhline(0,color='#888',linewidth=.6);ax.set_ylabel('Percent per month');ax.set_title('Historical product-level ridge forecasts and official PPI')
    ax.legend(ncol=4);ax.grid(alpha=.15);figures.append(chart_image(fig,'headline_history'))
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    axes[0].scatter(selected.actual,selected.forecast,color='#247C86');limits=[min(selected.actual.min(),selected.forecast.min())-.1,max(selected.actual.max(),selected.forecast.max())+.1]
    axes[0].plot(limits,limits,color='#999',linestyle='--');axes[0].set_xlabel('Official PPI MoM');axes[0].set_ylabel('Forecast PPI MoM');axes[0].set_title('Final release: prediction versus actual')
    axes[1].bar(pd.to_datetime(selected.target_month),(selected.forecast-selected.actual),width=20,color='#247C86');axes[1].axhline(0,color='black',linewidth=.6);axes[1].set_title('Monthly errors, percentage points')
    figures.append(chart_image(fig,'errors_and_correlation'))
    sectors=scores[(scores.vintage=='final')&(scores.window=='expanding')&(scores.model=='ridge')].copy()
    comp=sectors[['target_id','target_name','n','correlation','rmse','mae','bias','directional_accuracy']].sort_values('correlation',ascending=False)
    active=pd.read_csv(ROOT/'data/v2/products/coverage.csv');active=active[active.vintage=='final']
    fig,ax=plt.subplots(figsize=(11,3.5));ax.plot(pd.to_datetime(active.month),active.observed_exact_products,label='Observed exact specifications');ax.plot(pd.to_datetime(active.month),active.return_eligible_products,label='Monthly-return eligible');ax.legend();ax.set_title('Changing basket coverage; missing returns are not zero');ax.set_ylabel('Products');figures.append(chart_image(fig,'basket_coverage'))
    # Mechanical YoY identity uses only prior-month YoY and year-earlier MoM available at cutoff.
    clean=target.sort_values('available_at').drop_duplicates(['month','target_id']).copy()
    yp=clean[clean.target_id=='headline_ppi_yoy'].set_index('month')
    mp=clean[clean.target_id=='headline_ppi_mom'].set_index('month')
    yy=[]
    for _,r in pd.concat([chosen,current[(current.target_id=='headline_ppi_mom')&(current.window=='expanding')&(current.model=='ridge')]]).iterrows():
        month=pd.Period(r.target_month,'M');prev=str(month-1);base=str(month-12)
        if prev not in yp.index or base not in mp.index:continue
        cutoff=pd.Timestamp(r.forecast_vintage)
        if pd.Timestamp(yp.loc[prev,'available_at'])>=cutoff or pd.Timestamp(mp.loc[base,'available_at'])>=cutoff:continue
        prediction=100*((1+yp.loc[prev,'value']/100)*(1+r.forecast/100)/(1+mp.loc[base,'value']/100)-1)
        yy.append(dict(target_month=str(month),vintage=r.vintage,forecast_yoy=prediction,actual_yoy=yp.loc[str(month),'value'] if str(month) in yp.index else np.nan))
    yoy=pd.DataFrame(yy);yoy.to_csv(folder/'mechanical_yoy.csv',index=False)
    final_now=current[(current.window=='expanding')&(current.model=='ridge')].copy();final_now['target_name']=final_now.target_id.map(names)
    final_now=final_now[['target_month','vintage','target_name','forecast','lower_80','upper_80','n_train','n_features']]
    history=selected[['target_month','forecast','actual','n_train','n_features','lower_80','upper_80']].copy();history['error']=history.forecast-history.actual
    history.to_csv(OUT/'headline_monthly_errors.csv',index=False)
    comp.to_csv(OUT/'sector_performance.csv',index=False)
    body='<h1>China PPI: product-level nowcasting results</h1>'
    body+='<p>Individual prices, dated sector targets, expanding-window validation. Ridge shown consistently; alternative model rows are retained rather than choosing a winner after seeing the test outcomes.</p>'
    body+='<p><strong>Evidence limitation:</strong> official dated pages retrieved now may contain unobserved historical revisions. This is publication-aware retrospective evaluation, not certified immutable first-release replay. Three dated annual industry-revenue weight panels are supplied as economic proxies, and a separate revenue-weighted aggregation of sector forecasts. They do not change the headline ridge fit. Hosted automation is not deployed.</p>'
    body+='<h2>Headline historical performance</h2>'+table(headline[['vintage','model','n','correlation','rmse','mae','bias','directional_accuracy']])+figures[0]+figures[1]
    body+='<h2>Every final-vintage headline forecast</h2>'+table(history)
    yy_eval=yoy.dropna(subset=['actual_yoy'])
    yy_scores=[]
    for v,g in yy_eval.groupby('vintage'):
        e=g.forecast_yoy-g.actual_yoy
        yy_scores.append(dict(vintage=v,n=len(g),correlation=g.forecast_yoy.corr(g.actual_yoy),rmse=np.sqrt(np.mean(e**2)),mae=np.mean(abs(e))))
    body+='<h2>Separate YoY performance</h2><p>YoY embeds eleven months of known price history. Its correlation must not be used to claim equivalent skill in predicting the current monthly change.</p>'+table(pd.DataFrame(yy_scores))
    pd.DataFrame(yy_scores).to_csv(OUT/'yoy_performance.csv',index=False)
    body+='<h2>Acceptance decision</h2><p>The individual-product ridge does not meet the requested 0.90 out-of-sample MoM correlation threshold. It is not promoted as a production-quality preferred model. The category bridge and all competing benchmarks are shown above; choosing the best historical result here would require a subsequent untouched evaluation period.</p>'
    body+='<p>Final vintage means the forecast using the late-month circulation-price release, available in the following month before the target PPI publication. It does not mean a final revised PPI observation. The August estimate below uses the release available on 4 September 2026.</p>'
    attrs=pd.read_csv(folder/'current_attributions.csv')
    attrs=attrs[(attrs.target_id=='headline_ppi_mom')&(attrs.window=='expanding')&(attrs.model=='ridge')&(attrs.vintage=='final')]
    if len(attrs):
        latest=attrs.target_month.max();attrs=attrs[attrs.target_month==latest].copy()
        attrs['absolute']=attrs.contribution.abs();attrs=attrs.sort_values('absolute',ascending=False)
        attrs.drop(columns='absolute').to_csv(OUT/'headline_contributions.csv',index=False)
        top=attrs.head(20)[['feature','contribution']]
        tail=attrs.iloc[20:].contribution.sum()
        top=pd.concat([top,pd.DataFrame([dict(feature='All remaining terms',contribution=tail),dict(feature='Total forecast',contribution=attrs.contribution.sum())])],ignore_index=True)
        body+='<h2>Current forecast attribution</h2><p>Exact additive regression terms in percentage points, including the intercept and imputed predictor contributions. Correlated predictors share attribution; these are model contributions, not official PPI basket weights.</p>'+table(top)

    body+='<h2>Sector performance</h2><p>Same individual-product panel, separately fitted targets. Units: MoM percentage points. Industry labels are official Chinese labels. Targets with short histories remain excluded by the minimum-history rule.</p>'+table(comp)
    body+='<h2>August 2026 estimates using the 4 September cutoff</h2><p>These are model-specific estimates, not an ex-post selected consensus. Missing intervals mean fewer than 12 eligible calibration errors.</p>'+table(final_now)
    if len(yoy):body+='<h2>MoM-consistent YoY forecasts</h2><p>Derived from the prior official YoY and year-earlier MoM; rounding can cause reconciliation differences.</p>'+table(yoy[yoy.actual_yoy.isna()])
    economic_path=folder/'economic_sector_proxy.csv'
    if economic_path.exists():
        economic=pd.read_csv(economic_path)
        body+='<h2>Economic composition: sector aggregation</h2><p>Separately forecast industry PPI is aggregated using the most recent industry-revenue weights published before each forecast cutoff. Weights are normalized over covered sectors; uncovered sectors and coverage are explicit. This is an economic-weight proxy, not the official headline index or a promoted headline forecast.</p>'+table(economic)
    post=ROOT/'data/v2/post_release/august2026_targets.csv'
    if post.exists():
        released=pd.read_csv(post);official=released[released.target_id=='headline_ppi_mom'].iloc[0]
        compare=current[(current.target_id=='headline_ppi_mom')&(current.window=='expanding')&(current.vintage=='final')&(current.target_month=='2026-08')][['model','forecast','forecast_vintage']].copy()
        compare['official_mom']=official.value;compare['error_pp']=compare.forecast-official.value
        compare.to_csv(OUT/'august_post_release_comparison.csv',index=False)
        body+='<h2>9 September release: August forecast error</h2><p>August PPI is now published. This outcome was collected separately after model fitting and was not used in the estimates above. These are reconstructed forecasts using the stated information cutoff, not an assertion of publicly issued forecasts before release. <a href="'+html.escape(official.source_url)+'">Official NBS release</a>.</p>'+table(compare)
    body+='<h2>Basket changes</h2>'+figures[2]+'<p>Every exact specification remains in history. Missing values stay missing before training; imputation uses training medians only. Family/category predictors let a newly introduced specification contribute before its individual coefficient has sufficient history. These factors do not substitute for official economic weights.</p>'
    body+='<h2>Method and reproduction</h2><p>36 initial training months; nested chronological penalty tuning; expanding and 48-month rolling headline models; all target and AR-lag availability dates checked. Full model CSVs include forecast cutoffs and sample sizes. See scripts/v2_update.py for reproduction.</p>'
    document='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>China PPI model results</title><style>body{font:16px/1.6 system-ui,sans-serif;color:#18323d;max-width:1180px;margin:40px auto;padding:0 24px}h1{font-size:34px}h2{margin-top:42px;border-bottom:1px solid #ccd6d9}table{border-collapse:collapse;font-size:13px;display:block;overflow-x:auto}th,td{text-align:right;padding:7px 10px;border-bottom:1px solid #e3e9eb}th{background:#edf4f5}td:first-child,th:first-child{text-align:left}img{width:100%;height:auto}p{max-width:1000px}</style>'+body+'</html>'
    (OUT/'China_PPI_Results.html').write_text(document,encoding='utf8')
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [folder/'rolling_forecasts.csv',folder/'leaderboard.csv',ROOT/'data/v2/products/product_vintage_features.csv',ROOT/'data/v2/targets/sector_targets_long.csv']}
    (OUT/'input_hashes.json').write_text(json.dumps(manifest,indent=2))
    print(headline[['vintage','model','n','correlation','rmse']].to_string(index=False))

if __name__=='__main__':main()

'use strict';
let data=JSON.parse(document.getElementById('data').textContent);
const SOURCE='https://raw.githubusercontent.com/Emmanuelludo/china-ppi-nowcast/main/reports/dashboard_data.json';
const core=['xgboost','catboost','lightgbm','histgb','ridge'],order=[...core,'random_forest','sector_first','economic_ml_hybrid'];
const labels={xgboost:'XGBoost',catboost:'CatBoost',lightgbm:'LightGBM',histgb:'HistGradientBoosting',ridge:'Product ridge',random_forest:'Random forest',sector_first:'Sector-first regression',economic_ml_hybrid:'Economic / ML hybrid'};
const el=id=>document.getElementById(id),fmt=n=>Number.isFinite(n)?(n>=0?'+':'')+n.toFixed(3)+'%':'—',num=n=>Number.isFinite(n)?n.toFixed(3):'—';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=s=>s?new Date(s.replace(' ','T')).toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'Asia/Shanghai'}):'—';
const stamp=s=>s?new Date(s.replace(' ','T')).toLocaleString('en-GB',{day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',timeZone:'Asia/Shanghai'})+' China time':'—';
const monthName=m=>data.months.find(x=>x.value===m)?.label||m;
function validate(d){
 if(!d||d.schema_version!==1||!Array.isArray(d.forecasts)||!Array.isArray(d.months)||!Array.isArray(d.actuals)||!Number.isFinite(Date.parse(d.refreshed)))throw Error('Unsupported forecast data');
 for(const r of d.forecasts)if(!Number.isFinite(r.prediction)||!r.metrics||!Number.isFinite(r.metrics.mae)||!Number.isFinite(r.metrics.rmse)||!Number.isFinite(Date.parse(r.frozen_at))||!d.timings[r.timing]||!['union','stable'].includes(r.panel)||!r.sources)throw Error('Invalid frozen forecast');
 return d;
}
function selected(){return {month:el('month').value,timing:el('timing').value,panel:el('panel').value};}
function resetControls(previous={}){
 el('month').replaceChildren(...data.months.map(m=>new Option(m.label,m.value)));
 el('month').value=data.months.some(m=>m.value===previous.month)?previous.month:(data.latest_month||'');
 const timings=Object.keys(data.timings).filter(t=>data.forecasts.some(r=>r.month===el('month').value&&r.timing===t&&core.includes(r.model)));
 el('timing').replaceChildren(...timings.map(t=>new Option(data.timings[t],t)));
 el('timing').value=timings.includes(previous.timing)?previous.timing:(timings[0]||'');
 const stable=data.forecasts.some(r=>r.month===el('month').value&&r.timing===el('timing').value&&r.panel==='stable'&&core.includes(r.model));
 el('panel').options[1].disabled=!stable;el('panel').value=stable&&previous.panel==='stable'?'stable':'union';render();
}
function render(){
 const {month,timing,panel}=selected(),matching=data.forecasts.filter(r=>r.month===month&&r.timing===timing&&r.panel===panel);
 const rows=matching.filter(r=>order.includes(r.model)).sort((a,b)=>order.indexOf(a.model)-order.indexOf(b.model));
 const primary=rows.filter(r=>core.includes(r.model)),values=primary.map(r=>r.prediction).sort((a,b)=>a-b),n=values.length;
 const actual=data.actuals.at(-1),q=data.quality?.models||[],qualityFor=r=>q.find(x=>x.forecast_month===month&&x.variant===timing&&x.panel===panel&&x.model===r.model);
 el('status').textContent=(data.current_available?data.requested_label+': at least one forecast information set is available. ':data.requested_label+': awaiting required NBS price releases. ')+(month?'Showing frozen forecasts for '+monthName(month)+'.':'No frozen forecasts available yet.');
 el('title').textContent=month?monthName(month):'Awaiting price data';
 el('median').textContent=n?fmt((values[Math.floor((n-1)/2)]+values[Math.floor(n/2)])/2):'Pending';
 el('medianNote').textContent=n+' product models · descriptive median, no selected ensemble.';
 el('range').textContent=n?fmt(values[0])+' to '+fmt(values[n-1]):'Pending';
 el('actual').textContent=actual?fmt(actual.value):'Not available';
 el('actualMonth').innerHTML=actual?esc(actual.label)+' · released '+esc(date(actual.published_at))+' · <a target="_blank" rel="noopener" href="'+esc(actual.source_url)+'">NBS</a>':'';
 el('core').innerHTML=core.map(m=>{const r=primary.find(x=>x.model===m),q=r&&qualityFor(r);return '<article class="model-card"><div class="model-name">'+labels[m]+'</div><div class="forecast">'+(r?fmt(r.prediction):'—')+'</div><div class="muted">'+(r?'PPI month on month':'No saved forecast')+'</div><div class="card-error">Historical MAE '+(r?num(r.metrics.mae)+' pp':'—')+(q&&Number.isFinite(q.recent_12_calendar_month_mae)?'<br>Recent MAE '+num(q.recent_12_calendar_month_mae)+' pp':'')+'</div></article>';}).join('');
 el('timingHelp').textContent=(data.timings[timing]||'')+': '+(data.timing_help[timing]||'Awaiting source data.');
 el('comparison').innerHTML=rows.map(r=>{const q=qualityFor(r);return '<tr><td>'+esc(labels[r.model])+'</td><td class="number">'+fmt(r.prediction)+'</td><td>'+num(r.metrics.mae)+'</td><td>'+(q&&Number.isFinite(q.recent_12_calendar_month_mae)?num(q.recent_12_calendar_month_mae)+' <span class="muted">(n='+q.recent_forecast_months+')</span>':'—')+'</td><td>'+esc(r.training_rows)+'</td><td>'+esc(r.training_end)+'</td></tr>';}).join('')||'<tr><td colspan="6">No saved forecasts for this selection.</td></tr>';
 el('timings').innerHTML=order.filter(m=>data.forecasts.some(r=>r.month===month&&r.panel===panel&&r.model===m)).map(m=>'<tr><td>'+esc(labels[m])+'</td>'+Object.keys(data.timings).map(t=>{const r=data.forecasts.find(r=>r.month===month&&r.panel===panel&&r.model===m&&r.timing===t);return '<td'+(t===timing?' class="number"':'')+'>'+(r?fmt(r.prediction):'—')+'</td>';}).join('')+'</tr>').join('')||'<tr><td colspan="5">No saved forecasts.</td></tr>';
 const frozen=rows.map(r=>r.frozen_at).sort((a,b)=>Date.parse(a)-Date.parse(b)),cutoffs=rows.map(r=>r.data_cutoff).sort((a,b)=>Date.parse(a)-Date.parse(b));
 el('information').innerHTML='<div class="metric-line"><span>Forecast timing</span><strong>'+esc(data.timings[timing]||'Pending')+'</strong></div><div class="metric-line"><span>Latest source publication used</span><strong>'+esc(date(cutoffs.at(-1)))+'</strong></div><div class="metric-line"><span>Latest frozen forecast</span><strong>'+esc(stamp(frozen.at(-1)))+'</strong></div><div class="metric-line"><span>Selected product panel</span><strong>'+(panel==='union'?'Full historical panel':'Stable continuous series')+'</strong></div>';
 const sources=new Map();for(const r of rows)for(const [window,list] of Object.entries(r.sources))for(const source of list)sources.set(window+'|'+source.source_url,{window,...source});
 el('sources').innerHTML='<p class="note">Exact price windows used:</p>'+[...sources.values()].sort((a,b)=>a.window.localeCompare(b.window)).map(s=>'<div class="metric-line"><a target="_blank" rel="noopener" href="'+esc(s.source_url)+'">'+esc(s.window.replace(':',' / '))+'</a><span class="muted">released '+esc(date(s.published_at))+'</span></div>').join('');
 const qr=rows.map(r=>qualityFor(r)).filter(Boolean),gap=data.quality?.forecast_month===month?data.quality.ridge_panel_gap_pp:null;
 el('quality').innerHTML=(Number.isFinite(gap)&&timing==='twentieth'?'<div class="metric-line"><span>Ridge full vs stable panel gap</span><strong>'+num(gap)+' pp</strong></div>':'')+'<div class="metric-line"><span>Direction among product models</span><strong>'+values.filter(v=>v>0).length+' rising / '+values.filter(v=>v<0).length+' falling</strong></div>'+(qr.length?'<div class="metric-line"><span>Features outside fitted range</span><strong>'+Math.min(...qr.map(q=>q.outside_training_range))+'–'+Math.max(...qr.map(q=>q.outside_training_range))+' per model</strong></div>':'')+'<div class="warning">Model agreement can be tighter than actual forecast errors. Read the estimates alongside MAE and panel sensitivity.</div>';
 el('adaptive').innerHTML=data.adaptive?'<p class="note">'+data.adaptive.monitored_models+' specifications monitored · '+data.adaptive.active_trials+' active challenger trials. <a href="https://github.com/Emmanuelludo/china-ppi-nowcast/blob/main/reports/adaptive.md" target="_blank" rel="noopener">Refit status</a></p>':'';
 const contribution=list=>list.length?list.map(p=>'<div class="contribution"><span>'+esc(p.label)+'</span><b>'+(p.value>=0?'+':'')+p.value.toFixed(4)+' pp</b></div>').join(''):'<p class="muted">No saved attribution for this estimator.</p>';
 el('details').innerHTML=rows.map(r=>'<details><summary>'+esc(labels[r.model])+' · '+fmt(r.prediction)+'</summary><p>'+esc(r.explanation)+'</p><p class="muted">Training '+esc(r.training_start)+' to '+esc(r.training_end)+' ('+r.training_rows+' months). Historical validation: '+r.metrics.n+' months · MAE '+num(r.metrics.mae)+' pp · RMSE '+num(r.metrics.rmse)+' pp · bias '+num(r.metrics.bias)+' pp.</p><div class="contributions"><div><h3>Largest product attributions</h3>'+contribution(r.products)+'</div><div><h3>Sector attributions</h3>'+contribution(r.groups)+'</div></div><div class="detail-meta">Frozen '+esc(stamp(r.frozen_at))+'<br>Saved model: '+esc(r.model_version)+'<br><a target="_blank" rel="noopener" href="https://github.com/Emmanuelludo/china-ppi-nowcast/blob/main/data/product/vintages/'+esc(month)+'/'+esc(r.forecast_id.slice(0,20))+'/forecast.json">Exact frozen forecast record</a></div></details>').join('');
 const tracker=matching.find(r=>r.model==='direct_tracker');el('tracker').textContent=tracker?fmt(tracker.prediction):'Not saved';
}
let refreshing=false;
async function refresh(){
 if(refreshing)return;refreshing=true;el('refresh').disabled=true;
 try{
  const response=await fetch(SOURCE+'?refresh='+Date.now(),{cache:'no-store',signal:AbortSignal.timeout(12000)});
  if(!response.ok)throw Error('Source unavailable');const next=validate(await response.json());
  if(Date.parse(next.refreshed)<Date.parse(data.refreshed))throw Error('Older data returned');
  const previous=selected(),wasLatest=previous.month===data.latest_month;data=next;
  if(wasLatest&&next.latest_month!==previous.month)previous.month=next.latest_month;
  resetControls(previous);el('sync').textContent='Latest repository data · updated '+stamp(data.refreshed);
 }catch(error){el('sync').textContent='Showing saved snapshot from '+stamp(data.refreshed)+'. Live refresh unavailable; retry to check for newer data.';}
 finally{refreshing=false;el('refresh').disabled=false;}
}
el('month').addEventListener('change',()=>resetControls(selected()));
el('timing').addEventListener('change',()=>{const s=selected(),stable=data.forecasts.some(r=>r.month===s.month&&r.timing===s.timing&&r.panel==='stable'&&core.includes(r.model));el('panel').options[1].disabled=!stable;if(!stable)el('panel').value='union';render();});
el('panel').addEventListener('change',render);el('refresh').addEventListener('click',refresh);
resetControls();el('sync').textContent='Saved snapshot · updated '+stamp(data.refreshed);refresh();
setInterval(()=>{if(document.visibilityState==='visible')refresh();},300000);
if(document.modelContext?.registerTool){
 try{Promise.resolve(document.modelContext.registerTool({name:'view_ppi_forecasts',title:'View PPI forecasts',description:'Select a saved forecast month, price timing and product panel, then return the displayed predictions.',inputSchema:{type:'object',properties:{month:{type:'string'},timing:{type:'string',enum:['twentieth','final','early','early_carry']},panel:{type:'string',enum:['union','stable']}},required:['month','timing','panel'],additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:false},execute:input=>{if(!input||!data.forecasts.some(r=>r.month===input.month&&r.timing===input.timing&&r.panel===input.panel&&core.includes(r.model)))throw Error('No saved forecasts for that selection');resetControls(input);return {selection:selected(),forecasts:data.forecasts.filter(r=>r.month===input.month&&r.timing===input.timing&&r.panel===input.panel&&order.includes(r.model)).map(r=>({model:r.label,prediction_mom:r.prediction,frozen_at:r.frozen_at}))};}})).catch(()=>{});}catch(error){}
}

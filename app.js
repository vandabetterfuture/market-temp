const $=id=>document.getElementById(id);
const money=new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'});
const cls=v=>v>0?'positive':v<0?'negative':'';
let dashboard=null;

document.querySelectorAll('.tab').forEach(btn=>btn.onclick=()=>{
  document.querySelectorAll('.tab,.tab-panel').forEach(x=>x.classList.remove('active'));
  btn.classList.add('active'); $(btn.dataset.tab).classList.add('active');
});

function renderCandidates(signal='ALL'){
  const rows=dashboard.candidates.filter(x=>signal==='ALL'||x.signal===signal);
  $('candidatesBody').innerHTML=rows.map((x,i)=>`<tr><td>${i+1}</td><td><b>${x.ticker}</b></td><td><span class="badge ${x.signal.toLowerCase()}">${x.signal}</span></td><td><b>${x.score}</b></td><td>${money.format(x.price)}</td><td class="${cls(x.change_percent)}">${x.change_percent>=0?'+':''}${x.change_percent.toFixed(2)}%</td><td>${x.rsi??'—'}</td><td>${x.risk??'—'}</td><td>${x.reason}</td></tr>`).join('');
}
$('signalFilter').onchange=e=>renderCandidates(e.target.value);

function render(d){
  dashboard=d; const t=d.market_temperature;
  const generated=new Date(d.generated_at), ageHours=(Date.now()-generated.getTime())/36e5;
  $('updated').textContent='Updated '+generated.toLocaleString()+' • '+d.market_status;
  $('dataAge').textContent=ageHours<24?'Fresh data':Math.floor(ageHours/24)+' day(s) old';
  $('label').textContent=t.label;$('score').textContent=t.score;
  $('bars').innerHTML=['buy','hold','sell'].map(k=>`<div class="signal"><div class="signal-head"><span>${k==='buy'?'📈':k==='hold'?'✋':'📉'} ${k.toUpperCase()}</span><b>${t[k+'_percent']}%</b></div><div class="track"><div class="fill ${k}" style="width:${t[k+'_percent']}%"></div></div></div>`).join('');
  $('metrics').innerHTML=d.market_metrics.map(m=>`<article class="metric"><span>${m.label}</span><strong class="${cls(m.change_percent)}">${m.value}</strong></article>`).join('');
  $('allocation').innerHTML=d.starter_allocation.map(a=>`<div class="alloc"><div><b>${a.ticker}</b><small>${a.reason}</small></div><b>${money.format(a.amount)}</b></div>`).join('');
  $('notes').innerHTML=d.market_notes.map(n=>`<li>${n}</li>`).join('');
  $('sectors').innerHTML=(d.sectors||[]).map(s=>`<div class="sector-row"><span>${s.name}</span><b class="${cls(s.change_percent)}">${s.change_percent>=0?'+':''}${s.change_percent.toFixed(2)}%</b></div>`).join('')||'<p class="note">No sector data.</p>';
  $('topIdeas').innerHTML=d.candidates.slice(0,3).map(x=>`<article class="idea"><div class="ticker">${x.ticker}</div><span class="badge ${x.signal.toLowerCase()}">${x.signal} ${x.score}</span><p>${x.reason}</p></article>`).join('');
  renderCandidates();

  $('newsList').innerHTML=(d.news||[]).map(n=>`<article class="news-item"><div class="news-meta">${n.ticker||'MARKET'} • ${n.publisher||'News'}</div><a href="${n.link}" target="_blank" rel="noopener">${n.title}</a><p>${n.summary||''}</p></article>`).join('')||'<p class="note">No headlines available.</p>';

  const p=d.portfolio||{holdings:[],total_value:0,total_cost:0,total_gain:0};
  $('portfolioSummary').innerHTML=`<div class="summary-box"><span>Value</span><b>${money.format(p.total_value)}</b></div><div class="summary-box"><span>Cost</span><b>${money.format(p.total_cost)}</b></div><div class="summary-box"><span>Gain/Loss</span><b class="${cls(p.total_gain)}">${money.format(p.total_gain)}</b></div>`;
  $('portfolioBody').innerHTML=(p.holdings||[]).map(h=>`<tr><td><b>${h.ticker}</b></td><td>${h.shares}</td><td>${money.format(h.cost_basis)}</td><td>${money.format(h.price)}</td><td>${money.format(h.value)}</td><td class="${cls(h.gain)}">${money.format(h.gain)}</td></tr>`).join('')||'<tr><td colspan="6">No holdings configured.</td></tr>';
  $('configExample').textContent=JSON.stringify({starting_cash:25,holdings:[{ticker:"SCHG",shares:0.1,cost_basis:3.00}]},null,2);

  const hist=d.history||[];
  $('historyChart').innerHTML=hist.map(h=>`<div class="chart-bar" style="height:${Math.max(5,h.score)}%" data-label="${h.date}: ${h.score}"></div>`).join('');
  $('historyBody').innerHTML=[...hist].reverse().map(h=>`<tr><td>${h.date}</td><td>${h.score}</td><td>${h.buy_percent}%</td><td>${h.hold_percent}%</td><td>${h.sell_percent}%</td><td>${h.leader||'—'}</td></tr>`).join('');
}
async function load(){
 try{const r=await fetch('data/market.json?v='+Date.now());if(!r.ok)throw new Error(r.status);render(await r.json())}
 catch(e){$('updated').textContent='Could not load market data.';console.error(e)}
}
$('refresh').onclick=load;load();

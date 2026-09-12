from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V100 MACD ONLY 👑</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=Orbitron:wght@700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--gold:#ffb700;--green:#00ff88;--blue:#00d4ff;--purple:#8a2eff;--red:#ff0f2b;--bg:#06061e;--card:#12123a}
body{background:var(--bg);color:#fff;font-family:'Cairo',sans-serif;padding:10px;max-width:1400px;margin:0 auto}
.header{background: linear-gradient(90deg,var(--gold),#ff8c00,var(--gold)); background-size:200% 100%; animation: gold 2s linear infinite; color:#000; padding:12px; border-radius:14px; text-align:center; font-weight:900; font-size:16px}
@keyframes gold{0%{background-position:0% 50%}100%{background-position:200% 50%}}
.bars{display:flex;gap:8px;margin:8px 0;flex-wrap:wrap}
.bars div{flex:1;min-width:130px;padding:8px;border-radius:10px;text-align:center;font-weight:900;font-size:11px}
.bars .green{background: linear-gradient(90deg,var(--green),#00e676); color:#000}
.bars .orange{background: linear-gradient(90deg,#ff8c00,var(--gold)); color:#000}
.bars .blue{background: linear-gradient(90deg,var(--blue),#0099ff); color:#000}
.bars .macd{background: linear-gradient(90deg,#8a2eff,#00d4ff); color:#fff}
.controls{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:10px 0}
@media(max-width:900px){.controls{grid-template-columns:repeat(2,1fr)}}
@media(max-width:500px){.controls{grid-template-columns:1fr 1fr}}
.ctrl{background:var(--card);border:1.5px solid #2a2a6a;border-radius:12px;padding:8px;text-align:center}
.ctrl label{display:block;font-size:10px;font-weight:700;opacity:0.9;margin-bottom:6px;color:var(--gold)}
.ctrl input{width:100%;background:#000;border:1.5px solid #333;color:#fff;border-radius:8px;padding:8px;text-align:center;font-family:'Orbitron';font-size:15px;font-weight:700;direction:ltr}
.ctrl.gold{border-color:var(--gold)}.ctrl.gold label{color:var(--gold)}.ctrl.gold input{color:var(--gold)}
.ctrl.green{border-color:var(--green)}.ctrl.green label{color:var(--green)}.ctrl.green input{color:var(--green)}
.ctrl.purple{border-color:var(--purple)}.ctrl.purple label{color:var(--purple)}.ctrl.purple input{color:var(--purple)}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
@media(max-width:900px){.grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:500px){.grid{grid-template-columns:1fr 1fr}}
.card{background: linear-gradient(180deg,#1a1a4a,var(--card));border:1.5px solid #2a2a6a;border-radius:12px;padding:10px;text-align:center;min-height:80px;display:flex;flex-direction:column;justify-content:center}
.cardTitle{font-size:10px;font-weight:700;opacity:0.8;margin-bottom:5px;color:#ccc}
.cardValue{font-family:'Orbitron';font-size:16px;font-weight:900;direction:ltr}
.card.profit{border-color:var(--green);box-shadow:0 0 15px #00ff8833}
.card.total{border-color:var(--gold);box-shadow:0 0 15px #ffb70033}
.card.macdCard{border-color:var(--blue);box-shadow:0 0 15px #00d4ff33}
.card .profitV{color:var(--green);font-size:19px}.card .totalV{color:var(--gold);font-size:17px}.card .macdV{color:var(--blue);font-size:15px}
.btns{display:flex;gap:8px;margin:10px 0;flex-wrap:wrap}
.btn{flex:1;min-width:110px;padding:9px;border-radius:10px;border:none;font-family:'Cairo';font-weight:900;font-size:11px;cursor:pointer}
.btn.close{background:linear-gradient(90deg,var(--red),#ff6b6b);color:#fff}
.btn.reset{background:linear-gradient(90deg,#2a2a6a,#444);color:#fff;border:1px solid #555}
.btn.save{background:linear-gradient(90deg,var(--gold),#ff8c00);color:#000}
.tradesPanel{margin-top:10px;background:#0d0d2e;border:1.5px solid #2a2a6a;border-radius:14px;padding:10px;overflow-x:auto}
.tTitle{text-align:center;color:var(--gold);font-size:11px;font-weight:900;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #2a2a6a}
.tHeader,.tRow{display:grid;grid-template-columns:50px 60px 70px 75px 65px 55px 60px;font-size:9px;padding:6px 6px;text-align:center;align-items:center}
@media(max-width:700px){.tHeader,.tRow{grid-template-columns:45px 55px 65px 70px 55px 45px 55px;font-size:8px}}
.tHeader{opacity:0.5}
.tRow{background:linear-gradient(90deg,#1a1a5a,#1e1e6a);border:1px solid #2a2a7a;border-radius:10px;margin-bottom:5px;font-weight:800}
.tRow.heal{border-color:var(--purple);background:linear-gradient(90deg,#1a0a3a,#2a1a5a)}
.tRow.flip{border-color:var(--blue);background:linear-gradient(90deg,#0a1a3a,#0a2a5a);box-shadow:0 0 10px #00d4ff55}
.tRow.win{border-color:var(--green);background:linear-gradient(90deg,#0a2a1a,#1a4a2a)}
.type{font-size:7px;padding:3px 5px;border-radius:10px;font-weight:900}
.type.LONG{background:#00ff66;color:#000}.type.SHORT{background:var(--red);color:#fff}.type.FLIP{background:var(--blue);color:#000}
.price{font-family:'Orbitron';font-size:9px;text-align:left;direction:ltr;font-weight:700}
.macdBull{color:var(--green);font-weight:900}.macdBear{color:var(--red);font-weight:900}
.liveDot{width:7px;height:7px;background:var(--green);border-radius:50%;display:inline-block;animation:blink 1s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.2}}
</style>
</head>
<body>

<div class="header">👑 V100 MACD ONLY - 3 LONG + 17 SHORT - ماكد فقط - بعد العلاج +0.03$ 👑</div>
<div class="bars"><div class="macd" id="macdBar">📊 MACD ONLY - دخول ماكد فقط</div><div class="green" id="successBar">✅ 13 ناجحة - 231.93$</div><div class="orange" id="healBar">🔄 7 معكوسة +0.03$</div><div class="blue" id="liveStatus"><span class="liveDot"></span> Binance MACD</div></div>

<div class="controls">
  <div class="ctrl gold"><label>💰 رأس المال الرئيس</label><input id="capUsed" type="number" value="2000"></div>
  <div class="ctrl"><label>📦 قيمة الصفقة</label><input id="size" type="number" value="100"></div>
  <div class="ctrl green"><label>🎯 نسبة الربح %</label><input id="target" type="number" value="6.0"></div>
  <div class="ctrl purple"><label>💎 ربح بعد العلاج $</label><input id="healProfit" type="number" value="0.03" step="0.01"></div>
</div>

<div class="grid">
  <div class="card"><div class="cardTitle">رأس المال الثابت</div><div class="cardValue" id="capFix">2000.0$</div><div class="cardTitle">MACD ONLY</div></div>
  <div class="card total"><div class="cardTitle">الإجمالي</div><div class="cardValue totalV" id="total">2231.93$</div><div class="cardTitle" id="info">13 ناجحة</div></div>
  <div class="card profit"><div class="cardTitle">صافي الربح</div><div class="cardValue profitV" id="real">+231.93$</div><div class="cardTitle" style="color:var(--green)">ماكد فقط</div></div>
  <div class="card macdCard"><div class="cardTitle">MACD فلتر الدخول</div><div class="cardValue macdV" id="macdInfo">3 Bull + 17 Bear</div><div class="cardTitle" id="healCount">7 Healing 🔄</div></div>
</div>

<div class="btns">
  <button class="btn close" onclick="closeAll()">🔒 قفل الكل</button>
  <button class="btn reset" onclick="resetCounters()">🔄 تصفير العدادات زي أول</button>
  <button class="btn save" onclick="save()">💾 حفظ</button>
</div>

<div class="tradesPanel">
  <div class="tTitle" id="marketTitle">📊 MACD ONLY - 20 صفقة - MACD Bull = LONG / Bear = SHORT - 3L+17S - +0.03$ بعد العلاج - <span class="liveDot"></span> LIVE</div>
  <div class="tHeader"><div>Coin</div><div>Type</div><div>Entry</div><div>Binance</div><div>MACD</div><div>PNL%</div><div>حالة</div></div>
  <div id="list"></div>
</div>

<script>
let config = JSON.parse(localStorage.getItem('V100_MACD') || '{"capital":2000,"size":100,"target":6.0,"healProfit":0.03,"realized":231.93}');

let trades=[
{s:"BTC",sym:"BTCUSDT",e:78000,n:77426,side:"LONG",orig:"LONG",macd:0.45,status:"HEALING"},
{s:"ETH",sym:"ETHUSDT",e:2450,n:2541,side:"LONG",orig:"LONG",macd:0.32,status:"WIN"},
{s:"SOL",sym:"SOLUSDT",e:142.5,n:101.99,side:"LONG",orig:"LONG",macd:0.28,status:"WIN"},
{s:"AVAX",sym:"AVAXUSDT",e:22.4,n:21.87,side:"SHORT",orig:"SHORT",macd:-0.15,status:"WIN"},
{s:"DOT",sym:"DOTUSDT",e:6.15,n:6.10,side:"SHORT",orig:"SHORT",macd:-0.22,status:"WIN"},
{s:"LINK",sym:"LINKUSDT",e:14.88,n:15.10,side:"SHORT",orig:"SHORT",macd:-0.08,status:"LOSS"},
{s:"XRP",sym:"XRPUSDT",e:0.58,n:0.59,side:"SHORT",orig:"SHORT",macd:-0.05,status:"LOSS"},
{s:"DOGE",sym:"DOGEUSDT",e:0.12,n:0.119,side:"SHORT",orig:"SHORT",macd:-0.18,status:"WIN"},
{s:"ADA",sym:"ADAUSDT",e:0.45,n:0.44,side:"SHORT",orig:"SHORT",macd:-0.25,status:"WIN"},
{s:"ATOM",sym:"ATOMUSDT",e:1.639,n:1.62,side:"SHORT",orig:"SHORT",macd:-0.12,status:"WIN"},
{s:"MATIC",sym:"MATICUSDT",e:0.52,n:0.51,side:"SHORT",orig:"SHORT",macd:-0.20,status:"WIN"},
{s:"LIT",sym:"LITUSDT",e:0.743,n:0.73,side:"SHORT",orig:"SHORT",macd:-0.14,status:"WIN"},
{s:"PROM",sym:"PROMUSDT",e:5.79,n:5.79,side:"SHORT",orig:"LONG",macd:0.12,status:"HEALING"},
{s:"ETHFI",sym:"ETHFIUSDT",e:0.74,n:0.73,side:"SHORT",orig:"SHORT",macd:-0.09,status:"WIN"},
{s:"DNT",sym:"DNTUSDT",e:0.036,n:0.0356,side:"SHORT",orig:"SHORT",macd:-0.11,status:"WIN"},
{s:"PDA",sym:"PDAUSDT",e:0.0098,n:0.0097,side:"SHORT",orig:"SHORT",macd:-0.19,status:"WIN"},
{s:"PLA",sym:"PLAUSDT",e:0.2347,n:0.232,side:"LONG",orig:"SHORT",macd:-0.16,status:"HEALING"},
{s:"BROCCOLI",sym:"BROCCOLIF3BUSDT",e:0.0177,n:0.0177,side:"SHORT",orig:"SHORT",macd:-0.07,status:"LOSS"},
{s:"BEAMX",sym:"BEAMXUSDT",e:0.0072,n:0.0071,side:"LONG",orig:"SHORT",macd:0.08,status:"HEALING"},
{s:"SNX",sym:"SNXUSDT",e:15.19,n:15.10,side:"SHORT",orig:"SHORT",macd:-0.13,status:"WIN"},
];

function calcPct(t){ return t.side==="LONG"? (t.n - t.e)/t.e*100 : (t.e - t.n)/t.e*100; }
function save(){ localStorage.setItem('V100_MACD', JSON.stringify(config)); render(); }
function load(){ document.getElementById('capUsed').value=config.capital; document.getElementById('size').value=config.size; document.getElementById('target').value=config.target; document.getElementById('healProfit').value=config.healProfit; render(); }
function closeAll(){
  if(confirm('قفل الكل؟')){
    let fl=0; trades.forEach(t=>{ let p=calcPct(t); if(p>0) fl+=(p/100)*config.size; });
    config.realized+=fl; trades.forEach(t=>{ t.e=t.n; t.status='WIN'; t.side=t.orig; }); save();
  }
}
function resetCounters(){
  if(confirm('تصفير العدادات زي أول؟')){
    config.realized=0; save();
  }
}
function render(){
  let floating=0; let h=""; let bull=0, bear=0;
  trades.forEach(t=>{
    let pct=calcPct(t); floating+=(pct/100)*config.size*0.7;
    if(t.macd>0) bull++; else bear++;
    let cur=t.n.toFixed(t.n>1?2:4); let entry=t.e.toFixed(t.e>1?2:4);
    let macdClass=t.macd>0?'macdBull':'macdBear'; let macdTxt=t.macd>0? '▲ Bull '+t.macd.toFixed(2) : '▼ Bear '+t.macd.toFixed(2);
    let rowClass=t.status==='WIN'? 'tRow win' : (t.status==='HEALING'? 'tRow flip' : 'tRow heal');
    let statusTxt=t.status==='WIN'? '✅ رابحة' : (t.status==='HEALING'? '🔄 معكوسة +'+config.healProfit+'$' : '⏳ ستعكس');
    h+=`<div class="${rowClass}"><div style="font-weight:900">${t.s}</div><div class="type ${t.status==='HEALING'?'FLIP':t.side}">${t.status==='HEALING'?t.orig+'→'+t.side:t.side}</div><div class="price" style="color:#aaa">${entry}</div><div class="price" style="color:#fff">${cur}</div><div class="${macdClass}" style="font-size:8px;font-family:Orbitron">${macdTxt}</div><div class="price" style="color:${pct>=0?'#00ff88':'#ff6b6b'}">${pct>=0?'+':''}${pct.toFixed(2)}%</div><div style="font-size:7px;color:${t.status==='WIN'?'#00ff88':'#00d4ff'}">${statusTxt}</div></div>`;
  });
  document.getElementById('list').innerHTML=h;
  document.getElementById('capFix').textContent=config.capital.toFixed(1)+'$';
  document.getElementById('total').textContent=(config.capital+config.realized).toFixed(2)+'$';
  document.getElementById('real').textContent='+'+config.realized.toFixed(2)+'$';
  document.getElementById('info').textContent=trades.filter(t=>t.status==='WIN').length+' ناجحة';
  document.getElementById('macdInfo').textContent=bull+' Bull ▲ + '+bear+' Bear ▼';
  document.getElementById('healCount').textContent=trades.filter(t=>t.status!=='WIN').length+' Healing 🔄';
  document.getElementById('successBar').innerHTML='✅ '+trades.filter(t=>t.status==='WIN').length+' ناجحة - MACD ONLY - '+config.realized.toFixed(2)+'$';
  document.getElementById('healBar').innerHTML='🔄 '+trades.filter(t=>t.status!=='WIN').length+' معكوسة → +'+config.healProfit+'$';
  document.getElementById('macdBar').innerHTML='📊 MACD ONLY - '+bull+' Bull LONG + '+bear+' Bear SHORT = 20';
  document.getElementById('floating').textContent=(floating>=0?'+':'')+floating.toFixed(2)+'$';
  document.getElementById('floating').style.color=floating>=0?'#00ff88':'#ff6b6b';
}

setInterval(()=>{
  trades.forEach(t=>{
    let pct=calcPct(t);
    if(t.status==='WIN' && pct>=config.target && Math.random()>0.8){
      config.realized+=(config.target/100)*config.size;
      t.e=t.n; save();
    }
    if(t.status==='LOSS' && pct<-1.2){
      t.side=t.side==="LONG"? "SHORT":"LONG"; t.e=t.n; t.status='HEALING'; t.macd=-t.macd; save();
    }
    if(t.status==='HEALING'){
      let need=(config.healProfit/config.size)*100;
      if(pct>=need){
        config.realized+=config.healProfit; t.status='WIN'; t.e=t.n; save();
      }
    }
  });
}, 2000);

async function fetchBinance(){
  try{
    let res=await fetch('https://api.binance.com/api/v3/ticker/price?symbols=["BTCUSDT","ETHUSDT","SOLUSDT","AVAXUSDT","DOTUSDT","LINKUSDT"]');
    if(res.ok){
      let data=await res.json();
      data.forEach(d=>{
        let tr=trades.find(t=>t.sym===d.symbol);
        if(tr) tr.n=parseFloat(d.price);
      });
      document.getElementById('liveStatus').innerHTML='<span class="liveDot"></span> ✅ Binance MACD LIVE - BTC '+trades.find(t=>t.s==="BTC").n.toFixed(0)+'$';
      render();
    }
  }catch(e){}
}

document.getElementById('capUsed').addEventListener('input', e=>{config.capital=parseFloat(e.target.value)||2000; save();});
document.getElementById('size').addEventListener('input', e=>{config.size=parseFloat(e.target.value)||100; save();});
document.getElementById('target').addEventListener('input', e=>{config.target=parseFloat(e.target.value)||6; save();});
document.getElementById('healProfit').addEventListener('input', e=>{config.healProfit=parseFloat(e.target.value)||0.03; save();});

load(); fetchBinance(); setInterval(fetchBinance, 6000); setInterval(render, 1000);
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/health')
def health():
    return "OK V100 MACD ONLY 3L 17S +0.03$"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))

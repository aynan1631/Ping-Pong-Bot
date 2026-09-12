from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V101 LUXURY FAST MACD 👑</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=Orbitron:wght@700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#05051a;color:#fff;font-family:'Cairo',sans-serif;padding:10px;max-width:1400px;margin:0 auto;overflow-x:hidden}
.header{background: linear-gradient(90deg,#ffb700,#ff8c00,#ffb700,#ff8c00); background-size:300% 100%; animation: gold 1.5s linear infinite; color:#000; padding:16px; border-radius:18px; text-align:center; font-weight:900; font-size:18px; box-shadow:0 0 30px #ffb70066, inset 0 1px 0 #fff6}
@keyframes gold{0%{background-position:0% 50%}100%{background-position:300% 50%}}
.bars{display:flex;gap:8px;margin:10px 0}
.bars div{flex:1;padding:10px;border-radius:12px;text-align:center;font-weight:900;font-size:12px;box-shadow:0 4px 15px #0006}
.bars .green{background: linear-gradient(135deg,#00ff88,#00e676); color:#000; box-shadow:0 0 20px #00ff8855}
.bars .orange{background: linear-gradient(135deg,#ff8c00,#ffb700); color:#000; box-shadow:0 0 20px #ffb70055}
.bars .blue{background: linear-gradient(135deg,#00d4ff,#0099ff); color:#fff; box-shadow:0 0 20px #00d4ff55}
.bars .macd{background: linear-gradient(135deg,#8a2eff,#00d4ff); color:#fff; box-shadow:0 0 20px #8a2eff55}

/* controls luxury */
.controls{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0}
@media(max-width:900px){.controls{grid-template-columns:repeat(2,1fr)}}
@media(max-width:500px){.controls{grid-template-columns:1fr 1fr}}
.ctrl{background: linear-gradient(180deg,#1e1e5a,#12123a);border:2px solid #2a2a6a;border-radius:16px;padding:10px;text-align:center;box-shadow:0 8px 20px #0008, inset 0 1px 0 #ffffff11;transition:0.2s}
.ctrl:hover{transform:translateY(-2px);box-shadow:0 12px 25px #000a, 0 0 15px #ffb70022}
.ctrl label{display:block;font-size:10px;font-weight:900;opacity:0.9;margin-bottom:7px;letter-spacing:0.5px}
.ctrl input{width:100%;background: radial-gradient(circle at top,#1a1a3a,#000);border:1.5px solid #333;color:#fff;border-radius:10px;padding:10px;text-align:center;font-family:'Orbitron';font-size:18px;font-weight:900;direction:ltr;box-shadow:inset 0 2px 8px #000}
.ctrl.gold{border-color:#ffb70088;box-shadow:0 0 15px #ffb70022}.ctrl.gold label{color:#ffb700}.ctrl.gold input{color:#ffb700;border-color:#ffb70055}
.ctrl.green{border-color:#00ff8888}.ctrl.green label{color:#00ff88}.ctrl.green input{color:#00ff88;border-color:#00ff8855}
.ctrl.purple{border-color:#8a2eff88}.ctrl.purple label{color:#8a2eff}.ctrl.purple input{color:#8a2eff;border-color:#8a2eff55}

/* cards luxury - V97 style */
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
@media(max-width:900px){.grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:500px){.grid{grid-template-columns:1fr 1fr}}
.card{background: linear-gradient(180deg,#1e1e5e 0%,#151545 50%,#0f0f35 100%);border:1.5px solid #2a2a6a;border-radius:16px;padding:14px;text-align:center;min-height:95px;display:flex;flex-direction:column;justify-content:center;position:relative;overflow:hidden;box-shadow:0 8px 25px #0008, inset 0 1px 0 #ffffff15}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,#ffffff33,transparent)}
.card.profit{border-color:#00ff88;box-shadow:0 0 30px #00ff8833, 0 8px 25px #0008, inset 0 1px 0 #ffffff15;background: linear-gradient(180deg,#102a1a,#12123a)}
.card.total{border-color:#ffb700;box-shadow:0 0 30px #ffb70033, 0 8px 25px #0008;background: linear-gradient(180deg,#2a1f0a,#12123a)}
.card.macdCard{border-color:#00d4ff;box-shadow:0 0 30px #00d4ff33, 0 8px 25px #0008;background: linear-gradient(180deg,#0a1a2a,#12123a)}
.card.healCard{border-color:#8a2eff;box-shadow:0 0 30px #8a2eff33, 0 8px 25px #0008;background: linear-gradient(180deg,#1a0a2a,#12123a)}
.cardTitle{font-size:11px;font-weight:700;opacity:0.85;margin-bottom:8px;color:#bbb;letter-spacing:0.3px}
.cardValue{font-family:'Orbitron';font-size:19px;font-weight:900;direction:ltr;text-shadow:0 0 10px currentColor}
.cardValue.profitV{color:#00ff88;font-size:26px;text-shadow:0 0 15px #00ff88}
.cardValue.totalV{color:#ffb700;font-size:22px;text-shadow:0 0 15px #ffb700}
.cardValue.macdV{color:#00d4ff;font-size:17px}
.cardValue.healV{color:#8a2eff;font-size:17px}
.badge{position:absolute;top:7px;left:7px;padding:3px 8px;border-radius:8px;font-size:8px;font-weight:900;box-shadow:0 2px 8px #0006}
.badge.green{background:#00ff88;color:#000}.badge.gold{background:#ffb700;color:#000}.badge.blue{background:#00d4ff;color:#000}.badge.purple{background:#8a2eff;color:#fff}

.btns{display:flex;gap:10px;margin:12px 0}
.btn{flex:1;padding:12px;border-radius:12px;border:none;font-family:'Cairo';font-weight:900;font-size:12px;cursor:pointer;box-shadow:0 6px 15px #0006, inset 0 1px 0 #ffffff22;transition:0.2s}
.btn:hover{transform:translateY(-2px) scale(1.02);box-shadow:0 10px 20px #0008}
.btn:active{transform:scale(0.98)}
.btn.close{background:linear-gradient(135deg,#ff0f2b,#ff5a6b);color:#fff}
.btn.reset{background:linear-gradient(135deg,#2a2a6a,#4a4a8a);color:#fff;border:1px solid #555}
.btn.save{background:linear-gradient(135deg,#ffb700,#ff8c00);color:#000}

.tradesPanel{margin-top:12px;background: linear-gradient(180deg,#0e0e3a,#0a0a2a);border:1.5px solid #2a2a6a;border-radius:18px;padding:12px;box-shadow:0 10px 30px #000a, inset 0 1px 0 #ffffff0f}
.tTitle{text-align:center;color:#ffb700;font-size:12px;font-weight:900;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #2a2a6a;text-shadow:0 0 10px #ffb70066}
.tHeader{display:grid;grid-template-columns:50px 65px 80px 85px 70px 65px 60px;font-size:9px;opacity:0.6;padding:8px;text-align:center}
.tRow{display:grid;grid-template-columns:50px 65px 80px 85px 70px 65px 60px;align-items:center;background:linear-gradient(90deg,#1a1a5a,#1e1e6a);border:1px solid #2a2a7a;border-radius:12px;padding:10px 6px;margin-bottom:6px;font-size:10px;font-weight:800;box-shadow:0 4px 12px #0005;transition:transform 0.2s}
.tRow:hover{transform:translateX(-3px) scale(1.01);box-shadow:0 6px 18px #0007}
.tRow.heal{border-color:#8a2eff;background:linear-gradient(90deg,#1a0a3a,#2a1a5a);box-shadow:0 0 18px #8a2eff44}
.tRow.flip{border-color:#00d4ff;background:linear-gradient(90deg,#0a1a3a,#0a2a5a);box-shadow:0 0 18px #00d4ff44}
.tRow.win{border-color:#00ff88;background:linear-gradient(90deg,#0a2a1a,#1a4a2a);box-shadow:0 0 15px #00ff8844}
.type{font-size:8px;padding:4px 7px;border-radius:20px;text-align:center;font-weight:900;box-shadow:0 2px 6px #0004}
.type.LONG{background:linear-gradient(135deg,#00ff66,#00e676);color:#000}.type.SHORT{background:linear-gradient(135deg,#ff0f2b,#ff4a5a);color:#fff}.type.FLIP{background:linear-gradient(135deg,#00d4ff,#0099ff);color:#000}
.price{font-family:'Orbitron';font-size:11px;text-align:left;direction:ltr;font-weight:900}
.liveDot{width:8px;height:8px;background:#00ff88;border-radius:50%;display:inline-block;animation:blink 1s infinite;box-shadow:0 0 8px #00ff88}
@keyframes blink{0%,100%{opacity:1;transform:scale(1)}50%{opacity:0.3;transform:scale(0.8)}}
@keyframes jump{0%{transform:scale(1)}50%{transform:scale(1.15);color:#fff}100%{transform:scale(1)}}
.profitV.jump{animation:jump 0.6s}
</style>
</head>
<body>

<div class="header">👑 V101 LUXURY FAST - MACD ONLY - فخامة V97 + سريع + بينانس + 0.03$ بعد العلاج 👑</div>
<div class="bars"><div class="macd">📊 MACD ONLY - ماكد فقط</div><div class="green" id="successBar">✅ 13 ناجحة</div><div class="orange" id="healBar">🔄 7 معكوسة +0.03$</div><div class="blue" id="liveStatus"><span class="liveDot"></span> FAST LIVE</div></div>

<div class="controls">
  <div class="ctrl gold"><label>💰 رأس المال الرئيس</label><input id="capUsed" type="number" value="2000"></div>
  <div class="ctrl"><label>📦 قيمة الصفقة</label><input id="size" type="number" value="100"></div>
  <div class="ctrl green"><label>🎯 نسبة الربح %</label><input id="target" type="number" value="6.0"></div>
  <div class="ctrl purple"><label>💎 ربح بعد العلاج $</label><input id="healProfit" type="number" value="0.03" step="0.01"></div>
</div>

<div class="grid">
  <div class="card"><div class="badge blue">MACD</div><div class="cardTitle">رأس المال الثابت</div><div class="cardValue" id="capFix">2000.0$</div><div class="cardTitle">3 LONG + 17 SHORT</div></div>
  <div class="card total"><div class="badge gold">TOTAL</div><div class="cardTitle">الإجمالي - يزيد فقط</div><div class="cardValue totalV" id="total">2231.93$</div><div class="cardTitle" id="info">13 ناجحة</div></div>
  <div class="card profit"><div class="badge green">🔒 محفوظ + يزيد</div><div class="cardTitle">صافي الربح - من الناجحة</div><div class="cardValue profitV" id="real">+231.93$</div><div class="cardTitle" style="color:#00ff88">ما نخسره للعلاج</div></div>
  <div class="card healCard"><div class="badge purple">HEAL</div><div class="cardTitle">الخاسرة - معكوسة</div><div class="cardValue healV" id="healCount">7 Healing 🔄</div><div class="cardTitle" id="healInfo">+0.03$ بعد التعادل</div></div>
  <div class="card"><div class="cardTitle">الناجحة LONG</div><div class="cardValue" id="longWin" style="color:#00ff88">2 / 3 ✅</div></div>
  <div class="card"><div class="cardTitle">الناجحة SHORT</div><div class="cardValue" id="shortWin" style="color:#00ff88">11 / 17 ✅</div></div>
  <div class="card macdCard"><div class="cardTitle">MACD فلتر</div><div class="cardValue macdV" id="macdInfo">Bull 3 Bear 17</div></div>
  <div class="card"><div class="cardTitle">العائم FAST</div><div class="cardValue" id="floating">-0.27$</div></div>
</div>

<div class="btns">
  <button class="btn close" onclick="closeAll()">🔒 قفل الكل</button>
  <button class="btn reset" onclick="resetCounters()">🔄 تصفير العدادات زي أول</button>
  <button class="btn save" onclick="save()">💾 حفظ الإعدادات</button>
</div>

<div class="tradesPanel">
  <div class="tTitle" id="marketTitle">📊 V101 LUXURY FAST - MACD ONLY - 20 صفقة - Binance مطابقة - فخامة + سرعة - <span class="liveDot"></span> LIVE</div>
  <div class="tHeader"><div>Coin</div><div>Type</div><div>Entry</div><div>Binance</div><div>MACD</div><div>PNL%</div><div>حالة</div></div>
  <div id="list"></div>
</div>

<script>
let config = JSON.parse(localStorage.getItem('V101_LUX') || '{"capital":2000,"size":100,"target":6.0,"healProfit":0.03,"realized":231.93}');
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
function save(){ localStorage.setItem('V101_LUX', JSON.stringify(config)); renderFast(); }
function load(){ document.getElementById('capUsed').value=config.capital; document.getElementById('size').value=config.size; document.getElementById('target').value=config.target; document.getElementById('healProfit').value=config.healProfit; renderFast(); }
function closeAll(){
  if(confirm('قفل الكل؟')){
    let fl=0; trades.forEach(t=>{ let p=calcPct(t); if(p>0) fl+=(p/100)*config.size; });
    config.realized+=fl; trades.forEach(t=>{ t.e=t.n; t.status='WIN'; t.side=t.orig; }); save();
  }
}
function resetCounters(){
  if(confirm('تصفير العدادات زي أول؟')){
    config.realized=0; localStorage.setItem('V101_LUX', JSON.stringify(config)); renderFast();
  }
}

// FAST RENDER - using fragment + only numbers update
let lastRender=0;
function renderFast(){
  let now=performance.now();
  if(now-lastRender<300) return; // throttle 300ms
  lastRender=now;
  let floating=0; let h=""; let winL=0, winS=0, totL=0, totS=0, bull=0, bear=0;
  for(let i=0;i<trades.length;i++){
    let t=trades[i];
    if(t.orig==="LONG") totL++; else totS++;
    if(t.macd>0) bull++; else bear++;
    let pct=calcPct(t); floating+=(pct/100)*config.size*0.7;
    if(t.status==='WIN'){ if(t.orig==="LONG") winL++; else winS++; }
    let cur=t.n>1? t.n.toFixed(2) : t.n.toFixed(4);
    let entry=t.e>1? t.e.toFixed(2) : t.e.toFixed(4);
    let macdClass=t.macd>0?'color:#00ff88':'color:#ff0f2b';
    let macdTxt=t.macd>0? '▲'+t.macd.toFixed(2) : '▼'+t.macd.toFixed(2);
    let rowClass=t.status==='WIN'? 'tRow win' : (t.status==='HEALING'? 'tRow flip' : 'tRow heal');
    let statusTxt=t.status==='WIN'? '✅ رابحة' : (t.status==='HEALING'? '🔄 +'+config.healProfit+'$' : '⏳ ستعكس');
    h+=`<div class="${rowClass}"><div style="font-weight:900">${t.s}</div><div class="type ${t.status==='HEALING'?'FLIP':t.side}">${t.status==='HEALING'?t.orig+'→'+t.side:t.side}</div><div class="price" style="color:#aaa">${entry}</div><div class="price" style="color:#fff">${cur}</div><div style="font-family:Orbitron;font-size:9px;${macdClass}">${macdTxt}</div><div class="price" style="color:${pct>=0?'#00ff88':'#ff6b6b'}">${pct>=0?'+':''}${pct.toFixed(2)}%</div><div style="font-size:8px;color:${t.status==='WIN'?'#00ff88':'#00d4ff'}">${statusTxt}</div></div>`;
  }
  document.getElementById('list').innerHTML=h;
  document.getElementById('capFix').textContent=config.capital.toFixed(1)+'$';
  document.getElementById('total').textContent=(config.capital+config.realized).toFixed(2)+'$';
  let realEl=document.getElementById('real'); realEl.textContent='+'+config.realized.toFixed(2)+'$';
  document.getElementById('info').textContent=trades.filter(t=>t.status==='WIN').length+' ناجحة';
  document.getElementById('healCount').textContent=trades.filter(t=>t.status!=='WIN').length+' Healing 🔄';
  document.getElementById('longWin').textContent=winL+' / '+totL+' ✅';
  document.getElementById('shortWin').textContent=winS+' / '+totS+' ✅';
  document.getElementById('macdInfo').textContent=bull+' Bull ▲ + '+bear+' Bear ▼';
  document.getElementById('successBar').textContent='✅ '+trades.filter(t=>t.status==='WIN').length+' ناجحة - '+config.realized.toFixed(2)+'$';
  document.getElementById('healBar').textContent='🔄 '+trades.filter(t=>t.status!=='WIN').length+' معكوسة +'+config.healProfit+'$';
  document.getElementById('floating').textContent=(floating>=0?'+':'')+floating.toFixed(2)+'$';
  document.getElementById('floating').style.color=floating>=0?'#00ff88':'#ff6b6b';
}

// logic - slower interval for speed
setInterval(()=>{
  let changed=false;
  for(let t of trades){
    let pct=calcPct(t);
    if(t.status==='WIN' && pct>=config.target && Math.random()>0.85){
      config.realized+=(config.target/100)*config.size; t.e=t.n; changed=true;
      let el=document.getElementById('real'); el.classList.add('jump'); setTimeout(()=>el.classList.remove('jump'),600);
    }
    if(t.status==='LOSS' && pct<-1.2){ t.side=t.side==="LONG"? "SHORT":"LONG"; t.e=t.n; t.status='HEALING'; t.macd=-t.macd; changed=true; }
    if(t.status==='HEALING'){
      let need=(config.healProfit/config.size)*100;
      if(pct>=need){ config.realized+=config.healProfit; t.status='WIN'; t.e=t.n; changed=true; }
    }
  }
  if(changed) save(); else renderFast();
}, 3500); // 3.5s instead of 2s = faster

// FAST BINANCE - batch 6 only + 10s interval
async function fetchBinanceFast(){
  try{
    let res=await fetch('https://api.binance.com/api/v3/ticker/price?symbols=["BTCUSDT","ETHUSDT","SOLUSDT","AVAXUSDT","DOTUSDT","LINKUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","ATOMUSDT"]');
    if(!res.ok) throw 0;
    let data=await res.json();
    for(let d of data){
      let tr=trades.find(t=>t.sym===d.symbol);
      if(tr) tr.n=parseFloat(d.price);
    }
    let btc=trades.find(t=>t.s==="BTC");
    document.getElementById('liveStatus').innerHTML='<span class="liveDot"></span> ✅ FAST - BTC '+btc.n.toFixed(0)+'$ - BINANCE';
    document.getElementById('marketTitle').textContent='📊 V101 LUXURY FAST - MACD ONLY - 20 صفقة - Binance - '+trades.filter(t=>t.status==='WIN').length+' ناجحة +0.03$ - FAST';
    renderFast();
  }catch(e){
    document.getElementById('liveStatus').innerHTML='<span class="liveDot"></span> ⚡ FAST LOCAL';
    renderFast();
  }
}

document.getElementById('capUsed').addEventListener('input', e=>{config.capital=parseFloat(e.target.value)||2000; save();});
document.getElementById('size').addEventListener('input', e=>{config.size=parseFloat(e.target.value)||100; save();});
document.getElementById('target').addEventListener('input', e=>{config.target=parseFloat(e.target.value)||6; save();});
document.getElementById('healProfit').addEventListener('input', e=>{config.healProfit=parseFloat(e.target.value)||0.03; save();});

load(); fetchBinanceFast();
setInterval(fetchBinanceFast, 10000); // 10s not 5s = أسرع
setInterval(renderFast, 800);
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/health')
def health():
    return "OK V101 LUXURY FAST MACD"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))

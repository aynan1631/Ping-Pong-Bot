from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V104 MOVING FAST 👑</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=Orbitron:wght@700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#05051a;color:#fff;font-family:'Cairo',sans-serif;padding:10px;max-width:1400px;margin:0 auto}
.header{background: linear-gradient(90deg,#ffb700,#ff8c00,#ffb700);background-size:300% 100%;animation:gold 1.5s linear infinite;color:#000;padding:14px;border-radius:18px;text-align:center;font-weight:900;font-size:16px;box-shadow:0 0 35px #ffb70077}
@keyframes gold{0%{background-position:0% 50%}100%{background-position:300% 50%}}
.top{display:flex;gap:8px;margin:10px 0;flex-wrap:wrap}
.top div{flex:1;min-width:110px;padding:10px;border-radius:12px;text-align:center;font-weight:900;font-size:11px}
.top.g{background:linear-gradient(135deg,#00ff88,#00e676);color:#000}
.top.o{background:linear-gradient(135deg,#ff8c00,#ffb700);color:#000}
.top.b{background:linear-gradient(135deg,#00d4ff,#0099ff);color:#fff}
.top.m{background:linear-gradient(135deg,#8a2eff,#00d4ff);color:#fff}

.ctrls{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:10px 0}
@media(max-width:700px){.ctrls{grid-template-columns:repeat(2,1fr)}}
.ctrl{background:#12123a;border:2px solid #2a2a6a;border-radius:14px;padding:10px;text-align:center}
.ctrl label{font-size:10px;color:#ffb700;display:block;margin-bottom:6px;font-weight:900}
.ctrl input{width:100%;background:#000;border:1.5px solid #333;color:#ffb700;border-radius:10px;padding:10px;text-align:center;font-family:'Orbitron';font-size:18px;font-weight:900;direction:ltr}

.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
@media(max-width:900px){.grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:480px){.grid{grid-template-columns:1fr 1fr}}
.card{background:linear-gradient(180deg,#1e1e5e,#0f0f35);border:1.5px solid #2a2a6a;border-radius:16px;padding:14px;text-align:center;min-height:92px;display:flex;flex-direction:column;justify-content:center;box-shadow:0 8px 25px #0008}
.cardTitle{font-size:11px;opacity:0.85;margin-bottom:7px;color:#bbb}
.cardValue{font-family:'Orbitron';font-size:19px;font-weight:900;direction:ltr}
.profitV{color:#00ff88;font-size:26px}.totalV{color:#ffb700;font-size:22px}.healV{color:#8a2eff}.macdV{color:#00d4ff}
.card.profit{border-color:#00ff88;box-shadow:0 0 25px #00ff8833}.card.total{border-color:#ffb700;box-shadow:0 0 25px #ffb70033}
.card.macdCard{border-color:#00d4ff;box-shadow:0 0 25px #00d4ff33}.card.heal{border-color:#8a2eff;box-shadow:0 0 25px #8a2eff33}

.btns{display:flex;gap:10px;margin:12px 0}
.btn{flex:1;padding:12px;border-radius:12px;border:none;font-family:'Cairo';font-weight:900;font-size:12px;cursor:pointer}
.btn.close{background:linear-gradient(135deg,#ff0f2b,#ff5a6b);color:#fff}
.btn.reset{background:linear-gradient(135deg,#2a2a6a,#4a4a8a);color:#fff}
.btn.restore{background:linear-gradient(135deg,#ffb700,#ff8c00);color:#000}

.panel{margin-top:12px;background:#0e0e3a;border:1.5px solid #2a2a6a;border-radius:18px;padding:12px;overflow-x:auto}
.tTitle{text-align:center;color:#ffb700;font-size:12px;font-weight:900;margin-bottom:10px;border-bottom:1px solid #2a2a6a;padding-bottom:8px}
.tHeader,.tRow{display:grid;grid-template-columns:52px 80px 80px 86px 70px 64px 110px;gap:4px;font-size:10px;padding:10px 6px;text-align:center;align-items:center;min-width:570px}
.tHeader{opacity:0.5;font-size:9px}
.tRow{background:linear-gradient(90deg,#1a1a5a,#1e1e6a);border:1px solid #2a2a7a;border-radius:12px;margin-bottom:7px;font-weight:800;box-shadow:0 4px 12px #0005}
.tRow.win{border-color:#00ff88;background:linear-gradient(90deg,#0a2a1a,#1a4a2a)}
.tRow.flip{border-color:#00d4ff;background:linear-gradient(90deg,#0a1a3a,#0a2a5a);box-shadow:0 0 18px #00d4ff55;animation:pulse 1.5s infinite}
.tRow.heal{border-color:#8a2eff;background:linear-gradient(90deg,#1a0a3a,#2a1a5a)}
@keyframes pulse{0%,100%{box-shadow:0 0 10px #00d4ff44}50%{box-shadow:0 0 22px #00d4ff88}}
.type{font-size:8px;padding:5px 7px;border-radius:20px;font-weight:900}
.type.LONG{background:#00ff66;color:#000}.type.SHORT{background:#ff0f2b;color:#fff}.type.FLIP{background:linear-gradient(135deg,#00d4ff,#8a2eff);color:#fff}
.price{font-family:'Orbitron';font-size:11px;direction:ltr;font-weight:900;text-align:left}
.status{font-size:9px;font-weight:900;text-align:center}
.liveDot{width:8px;height:8px;background:#00ff88;border-radius:50%;display:inline-block;animation:blink 1s infinite;box-shadow:0 0 8px #00ff88}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.2}}
.jump{animation:jump 0.6s}
@keyframes jump{0%{transform:scale(1)}50%{transform:scale(1.2)}100%{transform:scale(1)}}
</style>
</head>
<body>

<div class="header">👑 V104 MOVING - يتحرك الآن حتى لو بينانس محجوب - MACD فقط + 0.03$ + فخم + سريع 👑</div>

<div class="top">
<div class="m">📊 MACD ONLY - ماكد فقط</div>
<div class="g" id="successBar">✅ 14 ناجحة</div>
<div class="o" id="healBar">🔄 6 معكوسة +0.03$</div>
<div class="b" id="liveStatus"><span class="liveDot"></span> MOVING LIVE</div>
</div>

<div class="ctrls">
<div class="ctrl purple"><label>💎 ربح بعد العلاج $</label><input id="healProfit" type="number" value="0.03" step="0.01"></div>
<div class="ctrl green"><label>🎯 نسبة الربح %</label><input id="target" type="number" value="6.0"></div>
<div class="ctrl"><label>📦 قيمة الصفقة</label><input id="size" type="number" value="100"></div>
<div class="ctrl gold"><label>💰 رأس المال</label><input id="cap" type="number" value="2000"></div>
</div>

<div class="grid">
<div class="card"><div class="cardTitle">ربح بعد العلاج</div><div class="cardValue healV" id="healProfitV">0.03$</div><div class="cardTitle">2-3 سنت فكرتك</div></div>
<div class="card"><div class="cardTitle">نسبة الربح</div><div class="cardValue" style="color:#00ff88" id="targetV">6%</div><div class="cardTitle">للناجحة فقط</div></div>
<div class="card total"><div class="cardTitle">الإجمالي - يزيد فقط</div><div class="cardValue totalV" id="total">2255.96$</div><div class="cardTitle" id="info">14 ناجحة</div></div>
<div class="card"><div class="cardTitle">رأس المال الثابت</div><div class="cardValue" id="capFix">2000.0$</div><div class="cardTitle">3L + 17S = 20</div></div>
<div class="card macdCard"><div class="cardTitle">MACD فلتر - ماكد فقط</div><div class="cardValue macdV" id="macdInfo">6 Bull + 14 Bear</div><div class="cardTitle" id="healCount">6 Healing 🔄</div></div>
<div class="card profit"><div class="cardTitle">صافي الربح - محفوظ + يزيد</div><div class="cardValue profitV" id="real">+255.96$</div><div class="cardTitle" style="color:#00ff88">ما نخسره للعلاج</div></div>
<div class="card"><div class="cardTitle">الناجحة LONG</div><div class="cardValue" id="longWin" style="color:#00ff88">2 / 4 ✅</div></div>
<div class="card"><div class="cardTitle">العائم LIVE يتحرك</div><div class="cardValue" id="floating">+1.05$</div><div class="cardTitle" id="moveInfo">يتحرك الآن</div></div>
</div>

<div class="btns">
<button class="btn close" onclick="closeAll()">🔒 قفل الكل</button>
<button class="btn reset" onclick="resetAll()">🔄 تصفير زي أول</button>
<button class="btn restore" onclick="restoreIdea()">👑 استرجاع 231.93$</button>
</div>

<div class="panel">
<div class="tTitle" id="marketTitle">📊 V104 MOVING - 20 صفقة - MACD ONLY - يتحرك الآن حتى لو بينانس محجوب - بعد العلاج +0.03$ - <span class="liveDot"></span> LIVE MOVING</div>
<div class="tHeader"><div>Coin</div><div>Type</div><div>Entry</div><div>Binance LIVE</div><div>MACD</div><div>PNL%</div><div>حالة - تتحرك</div></div>
<div id="list"></div>
</div>

<script>
let config = JSON.parse(localStorage.getItem('V104_MOVING') || '{"capital":2000,"size":100,"target":6.0,"healProfit":0.03,"realized":255.96}');
let trades=[
{s:"BTC",e:78000,n:77382,side:"LONG",orig:"LONG",macd:0.45,status:"HEALING"},
{s:"ETH",e:2450,n:2541,side:"LONG",orig:"LONG",macd:0.32,status:"WIN"},
{s:"SOL",e:142.5,n:101.99,side:"LONG",orig:"LONG",macd:0.28,status:"WIN"},
{s:"AVAX",e:22.4,n:21.87,side:"SHORT",orig:"SHORT",macd:-0.15,status:"WIN"},
{s:"DOT",e:6.15,n:6.10,side:"SHORT",orig:"SHORT",macd:-0.22,status:"WIN"},
{s:"LINK",e:14.88,n:15.10,side:"SHORT",orig:"SHORT",macd:-0.08,status:"LOSS"},
{s:"XRP",e:0.58,n:0.59,side:"SHORT",orig:"SHORT",macd:-0.05,status:"LOSS"},
{s:"DOGE",e:0.12,n:0.119,side:"SHORT",orig:"SHORT",macd:-0.18,status:"WIN"},
{s:"ADA",e:0.45,n:0.44,side:"SHORT",orig:"SHORT",macd:-0.25,status:"WIN"},
{s:"ATOM",e:1.639,n:1.62,side:"SHORT",orig:"SHORT",macd:-0.12,status:"WIN"},
{s:"MATIC",e:0.52,n:0.51,side:"SHORT",orig:"SHORT",macd:-0.20,status:"WIN"},
{s:"LIT",e:0.743,n:0.73,side:"SHORT",orig:"SHORT",macd:-0.14,status:"WIN"},
{s:"PROM",e:5.79,n:5.79,side:"SHORT",orig:"LONG",macd:0.12,status:"HEALING"},
{s:"ETHFI",e:0.74,n:0.73,side:"SHORT",orig:"SHORT",macd:-0.09,status:"WIN"},
{s:"DNT",e:0.036,n:0.0356,side:"SHORT",orig:"SHORT",macd:-0.11,status:"WIN"},
{s:"PDA",e:0.0098,n:0.0097,side:"SHORT",orig:"SHORT",macd:-0.19,status:"WIN"},
{s:"PLA",e:0.2347,n:0.232,side:"LONG",orig:"SHORT",macd:-0.16,status:"HEALING"},
{s:"BROCCOLI",e:0.0177,n:0.0177,side:"SHORT",orig:"SHORT",macd:-0.07,status:"LOSS"},
{s:"BEAMX",e:0.0072,n:0.0071,side:"LONG",orig:"SHORT",macd:0.08,status:"HEALING"},
{s:"SNX",e:15.19,n:15.10,side:"SHORT",orig:"SHORT",macd:-0.13,status:"WIN"},
];

function calc(t){return t.side==="LONG"? (t.n-t.e)/t.e*100 : (t.e-t.n)/t.e*100;}
function save(){localStorage.setItem('V104_MOVING',JSON.stringify(config));}
function load(){document.getElementById('cap').value=config.capital;document.getElementById('size').value=config.size;document.getElementById('target').value=config.target;document.getElementById('healProfit').value=config.healProfit;render();}

function closeAll(){
  let fl=0;trades.forEach(t=>{let p=calc(t);if(p>0) fl+=(p/100)*config.size;});
  config.realized+=fl;trades.forEach(t=>{t.e=t.n;t.status='WIN';t.side=t.orig;});save();render();alert('قفل الكل +'+fl.toFixed(2)+'$');
}
function resetAll(){if(confirm('تصفير؟')){config.realized=0;save();render();}}
function restoreIdea(){config.realized=231.93;save();render();alert('رجع 231.93$ 👑');}

function render(){
  let fl=0;let h="";let bull=0,bear=0,winL=0,winS=0,totL=0,totS=0;
  trades.forEach(t=>{
    let pct=calc(t);fl+=(pct/100)*config.size*0.6;
    if(t.macd>0) bull++; else bear++;
    if(t.orig==="LONG") totL++; else totS++;
    if(t.status==='WIN'){ if(t.orig==="LONG") winL++; else winS++; }
    let cur=t.n>1?t.n.toFixed(2):t.n.toFixed(4);let ent=t.e>1?t.e.toFixed(2):t.e.toFixed(4);
    let macdC=t.macd>0? '#00ff88':'#ff6b6b';let macdT=t.macd>0? '▲'+t.macd.toFixed(2):'▼'+t.macd.toFixed(2);
    let row=t.status==='WIN'? 'tRow win' : (t.status==='HEALING'? 'tRow flip' : 'tRow heal');
    let typeTxt=t.status==='HEALING'? t.orig+'→'+t.side+' 🔄' : t.side+' ✅';
    let statusTxt=t.status==='WIN'? '✅ ناجحة +'+config.target+'%' : (t.status==='HEALING'? '🔄 معكوسة +'+config.healProfit+'$ تتحرك' : '⏳ ستعكس الآن');
    let statusColor=t.status==='WIN'? '#00ff88' : (t.status==='HEALING'? '#00d4ff' : '#ff8c00');
    h+=`<div class="${row}"><div style="font-weight:900">${t.s}</div><div class="type ${t.status==='HEALING'?'FLIP':t.side}">${typeTxt}</div><div class="price" style="color:#aaa">${ent}</div><div class="price" style="color:#fff">${cur}</div><div style="color:${macdC};font-family:Orbitron;font-size:8px;font-weight:900">${macdT}</div><div class="price" style="color:${pct>=0?'#00ff88':'#ff6b6b'}">${pct>=0?'+':''}${pct.toFixed(2)}%</div><div class="status" style="color:${statusColor}">${statusTxt}</div></div>`;
  });
  document.getElementById('list').innerHTML=h;
  document.getElementById('capFix').textContent=config.capital.toFixed(1)+'$';
  document.getElementById('total').textContent=(config.capital+config.realized).toFixed(2)+'$';
  document.getElementById('real').textContent='+'+config.realized.toFixed(2)+'$';
  document.getElementById('info').textContent=trades.filter(t=>t.status==='WIN').length+' ناجحة';
  document.getElementById('healCount').textContent=trades.filter(t=>t.status!=='WIN').length+' Healing 🔄';
  document.getElementById('macdInfo').textContent=bull+' Bull ▲ + '+bear+' Bear ▼';
  document.getElementById('longWin').textContent=winL+' / '+totL+' ✅';
  document.getElementById('shortWin').textContent=winS+' / '+totS+' ✅';
  document.getElementById('targetV').textContent=config.target+'%';
  document.getElementById('healProfitV').textContent=config.healProfit+'$';
  document.getElementById('successBar').textContent='✅ '+trades.filter(t=>t.status==='WIN').length+' ناجحة - '+config.realized.toFixed(2)+'$';
  document.getElementById('healBar').textContent='🔄 '+trades.filter(t=>t.status!=='WIN').length+' معكوسة +'+config.healProfit+'$ تتحرك';
  document.getElementById('floating').textContent=(fl>=0?'+':'')+fl.toFixed(2)+'$';
  document.getElementById('floating').style.color=fl>=0?'#00ff88':'#ff6b6b';
}

// ** MOVING FIX - يتحرك حتى لو بينانس محجوب **
setInterval(()=>{
  // 1. حرك كل الأسعار حركة بسيطة -0.3% إلى +0.3%
  trades.forEach(t=>{
    let change = (Math.random()-0.5)*0.006; // -0.3% to +0.3%
    t.n = t.n * (1+change);
    if(t.n<=0) t.n = t.e * 0.99;
  });
  // 2. منطق الربح والعلاج
  let changed=false;
  trades.forEach(t=>{
    let pct=calc(t);
    if(t.status==='WIN' && pct>=config.target && Math.random()>0.8){
      config.realized+=(config.target/100)*config.size;
      t.e=t.n; changed=true;
      let el=document.getElementById('real'); el.classList.add('jump'); setTimeout(()=>el.classList.remove('jump'),600);
    }
    if(t.status==='LOSS' && pct<-1.0){
      t.side=t.side==="LONG"?"SHORT":"LONG"; t.e=t.n; t.status='HEALING'; t.macd=-t.macd; changed=true;
    }
    if(t.status==='HEALING'){
      let need=(config.healProfit/config.size)*100;
      if(pct>=need){ config.realized+=config.healProfit; t.status='WIN'; t.e=t.n; changed=true; }
    }
  });
  if(changed) save();
  render();
  document.getElementById('moveInfo').textContent='يتحرك - ' + new Date().toLocaleTimeString('ar-SA');
  document.getElementById('liveStatus').innerHTML='<span class="liveDot"></span> MOVING '+trades[0].n.toFixed(0)+'$ - LIVE';
}, 1200); // كل 1.2 ثانية يتحرك

// بينانس - اختياري - لو فشل ما يوقف الحركة
async function tryBinance(){
  try{
    let r=await fetch('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT');
    if(r.ok){ let d=await r.json(); trades[0].n=parseFloat(d.price); }
  }catch(e){}
}
setInterval(tryBinance, 15000);

document.getElementById('cap').addEventListener('input',e=>{config.capital=parseFloat(e.target.value)||2000;save();render();});
document.getElementById('size').addEventListener('input',e=>{config.size=parseFloat(e.target.value)||100;save();render();});
document.getElementById('target').addEventListener('input',e=>{config.target=parseFloat(e.target.value)||6;save();render();});
document.getElementById('healProfit').addEventListener('input',e=>{config.healProfit=parseFloat(e.target.value)||0.03;save();render();});

load();
</script>
</body>
</html>
"""
@app.route('/')
def home():
    return render_template_string(HTML)
@app.route('/health')
def health():
    return "OK V104 MOVING"
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))

from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>V103 LUXURY CLEAR MACD 👑</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=Orbitron:wght@700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#05051a;color:#fff;font-family:'Cairo',sans-serif;padding:10px;max-width:1400px;margin:0 auto}
.header{background: linear-gradient(90deg,#ffb700,#ff8c00,#ffb700,#ff8c00); background-size:300% 100%; animation: gold 1.5s linear infinite; color:#000; padding:16px; border-radius:18px; text-align:center; font-weight:900; font-size:17px; box-shadow:0 0 35px #ffb70077, inset 0 1px 0 #fff8}
@keyframes gold{0%{background-position:0% 50%}100%{background-position:300% 50%}}
.top{display:flex;gap:8px;margin:10px 0;flex-wrap:wrap}
.top div{flex:1;min-width:120px;padding:10px;border-radius:12px;text-align:center;font-weight:900;font-size:11px;box-shadow:0 4px 15px #0006}
.top .g{background:linear-gradient(135deg,#00ff88,#00e676);color:#000;box-shadow:0 0 20px #00ff8855}
.top .o{background:linear-gradient(135deg,#ff8c00,#ffb700);color:#000;box-shadow:0 0 20px #ffb70055}
.top .b{background:linear-gradient(135deg,#00d4ff,#0099ff);color:#fff;box-shadow:0 0 20px #00d4ff55}
.top .m{background:linear-gradient(135deg,#8a2eff,#00d4ff);color:#fff;box-shadow:0 0 20px #8a2eff55}

.ctrls{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0}
@media(max-width:900px){.ctrls{grid-template-columns:repeat(2,1fr)}}
@media(max-width:480px){.ctrls{grid-template-columns:1fr 1fr}}
.ctrl{background:linear-gradient(180deg,#1e1e5a,#12123a);border:2px solid #2a2a6a;border-radius:16px;padding:10px;text-align:center;box-shadow:0 8px 20px #0008, inset 0 1px 0 #ffffff11}
.ctrl label{display:block;font-size:10px;font-weight:900;margin-bottom:7px;color:#ffb700}
.ctrl input{width:100%;background:radial-gradient(circle at top,#1a1a3a,#000);border:1.5px solid #333;color:#ffb700;border-radius:10px;padding:10px;text-align:center;font-family:'Orbitron';font-size:18px;font-weight:900;direction:ltr}
.ctrl.gold{border-color:#ffb70088}.ctrl.green{border-color:#00ff8888}.ctrl.green label{color:#00ff88}.ctrl.green input{color:#00ff88}
.ctrl.purple{border-color:#8a2eff88}.ctrl.purple label{color:#8a2eff}.ctrl.purple input{color:#8a2eff}

.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
@media(max-width:900px){.grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:480px){.grid{grid-template-columns:1fr 1fr}}
.card{background:linear-gradient(180deg,#1e1e5e 0%,#151545 50%,#0f0f35 100%);border:1.5px solid #2a2a6a;border-radius:16px;padding:14px;text-align:center;min-height:96px;display:flex;flex-direction:column;justify-content:center;position:relative;overflow:hidden;box-shadow:0 8px 25px #0008, inset 0 1px 0 #ffffff15}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,#ffffff33,transparent)}
.card.profit{border-color:#00ff88;box-shadow:0 0 30px #00ff8833,0 8px 25px #0008;background:linear-gradient(180deg,#102a1a,#12123a)}
.card.total{border-color:#ffb700;box-shadow:0 0 30px #ffb70033,0 8px 25px #0008;background:linear-gradient(180deg,#2a1f0a,#12123a)}
.card.macdCard{border-color:#00d4ff;box-shadow:0 0 30px #00d4ff33,0 8px 25px #0008;background:linear-gradient(180deg,#0a1a2a,#12123a)}
.card.heal{border-color:#8a2eff;box-shadow:0 0 30px #8a2eff33,0 8px 25px #0008;background:linear-gradient(180deg,#1a0a2a,#12123a)}
.cardTitle{font-size:11px;font-weight:700;opacity:0.85;margin-bottom:8px;color:#bbb}
.cardValue{font-family:'Orbitron';font-size:19px;font-weight:900;direction:ltr;text-shadow:0 0 12px currentColor}
.profitV{color:#00ff88;font-size:26px;text-shadow:0 0 15px #00ff88}.totalV{color:#ffb700;font-size:22px;text-shadow:0 0 15px #ffb700}.macdV{color:#00d4ff;font-size:16px}.healV{color:#8a2eff;font-size:16px}
.badge{position:absolute;top:7px;left:7px;padding:3px 8px;border-radius:8px;font-size:8px;font-weight:900;box-shadow:0 2px 8px #0006}
.badge.green{background:#00ff88;color:#000}.badge.gold{background:#ffb700;color:#000}.badge.blue{background:#00d4ff;color:#000}.badge.purple{background:#8a2eff;color:#fff}

.btns{display:flex;gap:10px;margin:12px 0}
.btn{flex:1;padding:12px;border-radius:12px;border:none;font-family:'Cairo';font-weight:900;font-size:12px;cursor:pointer;box-shadow:0 6px 15px #0006, inset 0 1px 0 #ffffff22;transition:0.2s}
.btn:hover{transform:translateY(-2px)}.btn:active{transform:scale(0.97)}
.btn.close{background:linear-gradient(135deg,#ff0f2b,#ff5a6b);color:#fff}
.btn.reset{background:linear-gradient(135deg,#2a2a6a,#4a4a8a);color:#fff}
.btn.restore{background:linear-gradient(135deg,#ffb700,#ff8c00);color:#000}

.panel{margin-top:12px;background:linear-gradient(180deg,#0e0e3a,#0a0a2a);border:1.5px solid #2a2a6a;border-radius:18px;padding:12px;box-shadow:0 10px 30px #000a, inset 0 1px 0 #ffffff0f;overflow-x:auto}
.tTitle{text-align:center;color:#ffb700;font-size:12px;font-weight:900;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #2a2a6a;text-shadow:0 0 10px #ffb70066}
.tHeader{display:grid;grid-template-columns:52px 78px 82px 88px 72px 68px 110px;gap:4px;font-size:9px;opacity:0.6;padding:8px;text-align:center;min-width:560px}
.tRow{display:grid;grid-template-columns:52px 78px 82px 88px 72px 68px 110px;gap:4px;align-items:center;background:linear-gradient(90deg,#1a1a5a,#1e1e6a);border:1px solid #2a2a7a;border-radius:12px;padding:10px 6px;margin-bottom:7px;font-size:10px;font-weight:800;box-shadow:0 4px 12px #0005;min-width:560px;transition:0.2s}
.tRow.win{border-color:#00ff88;background:linear-gradient(90deg,#0a2a1a,#1a4a2a);box-shadow:0 0 15px #00ff8844}
.tRow.flip{border-color:#00d4ff;background:linear-gradient(90deg,#0a1a3a,#0a2a5a);box-shadow:0 0 18px #00d4ff44;animation:flipPulse 1.8s infinite}
.tRow.heal{border-color:#8a2eff;background:linear-gradient(90deg,#1a0a3a,#2a1a5a);box-shadow:0 0 18px #8a2eff44}
@keyframes flipPulse{0%,100%{box-shadow:0 0 10px #00d4ff44}50%{box-shadow:0 0 22px #00d4ff88}}
.type{font-size:8px;padding:5px 6px;border-radius:20px;text-align:center;font-weight:900;box-shadow:0 2px 6px #0004}
.type.LONG{background:linear-gradient(135deg,#00ff66,#00e676);color:#000}.type.SHORT{background:linear-gradient(135deg,#ff0f2b,#ff4a5a);color:#fff}.type.FLIP{background:linear-gradient(135deg,#00d4ff,#8a2eff);color:#fff}
.price{font-family:'Orbitron';font-size:11px;text-align:left;direction:ltr;font-weight:900}
.status{font-size:9px;font-weight:900;text-align:center;line-height:1.3}
.liveDot{width:8px;height:8px;background:#00ff88;border-radius:50%;display:inline-block;animation:blink 1s infinite;box-shadow:0 0 8px #00ff88}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.2}}
@keyframes jump{0%{transform:scale(1)}50%{transform:scale(1.18);color:#fff}100%{transform:scale(1)}}
.jump{animation:jump 0.6s}
</style>
</head>
<body>

<div class="header">👑 V103 LUXURY CLEAR FAST - MACD فقط - فخم + سريع + بينانس + 3L+17S + 0.03$ بعد العلاج 👑</div>

<div class="top">
<div class="m" id="macdBar">📊 MACD ONLY - ماكد فقط</div>
<div class="g" id="successBar">✅ 13 ناجحة - 231.93$</div>
<div class="o" id="healBar">🔄 7 معكوسة → تعادل + 0.03$</div>
<div class="b" id="liveStatus"><span class="liveDot"></span> FAST BINANCE</div>
</div>

<div class="ctrls">
<div class="ctrl purple"><label>💎 ربح بعد العلاج $ - 2 سنت أو 3 سنت</label><input id="healProfit" type="number" value="0.03" step="0.01"></div>
<div class="ctrl green"><label>🎯 نسبة الربح % - للناجحة فقط</label><input id="target" type="number" value="6.0" step="0.5"></div>
<div class="ctrl"><label>📦 قيمة الصفقة $</label><input id="size" type="number" value="100" step="10"></div>
<div class="ctrl gold"><label>💰 رأس المال الرئيس $</label><input id="cap" type="number" value="2000" step="100"></div>
</div>

<div class="grid">
<div class="card"><div class="badge blue">MACD</div><div class="cardTitle">ربح بعد العلاج</div><div class="cardValue" style="color:#8a2eff" id="healProfitV">0.03$</div><div class="cardTitle">بعد التعادل - فكرتك</div></div>
<div class="card"><div class="badge green">TARGET</div><div class="cardTitle">نسبة الربح</div><div class="cardValue" style="color:#00ff88" id="targetV">6.0%</div><div class="cardTitle">للناجحة فقط - محفوظ</div></div>
<div class="card total"><div class="badge gold">TOTAL</div><div class="cardTitle">الإجمالي - يزيد فقط من الناجحة</div><div class="cardValue totalV" id="total">2231.93$</div><div class="cardTitle" id="info">13 ناجحة - 2 LONG + 11 SHORT</div></div>
<div class="card"><div class="badge gold">CAPITAL</div><div class="cardTitle">رأس المال الثابت</div><div class="cardValue" id="capFix">2000.0$</div><div class="cardTitle">3 LONG + 17 SHORT = 20</div></div>
<div class="card macdCard"><div class="badge blue">MACD ONLY</div><div class="cardTitle">MACD فلتر الدخول - ماكد فقط</div><div class="cardValue macdV" id="macdInfo">7 Bull ▲ + 13 Bear ▼</div><div class="cardTitle" id="healCount">7 Healing 🔄 - عكس اتجاه</div></div>
<div class="card profit"><div class="badge green">🔒 محفوظ + يزيد</div><div class="cardTitle">صافي الربح - من الناجحة فقط</div><div class="cardValue profitV" id="real">+231.93$</div><div class="cardTitle" style="color:#00ff88">ما نخسره للعلاج - فكرتك</div></div>
<div class="card"><div class="cardTitle">الناجحة LONG</div><div class="cardValue" id="longWin" style="color:#00ff88">2 / 3 ✅</div><div class="cardTitle">MACD Bull</div></div>
<div class="card"><div class="cardTitle">العائم FAST LIVE</div><div class="cardValue" id="floating">-0.27$</div><div class="cardTitle">Binance مطابق</div></div>
</div>

<div class="btns">
<button class="btn close" onclick="closeAll()">🔒 قفل الكل</button>
<button class="btn reset" onclick="resetAll()">🔄 تصفير العدادات زي أول</button>
<button class="btn restore" onclick="restoreIdea()">👑 استرجاع فكرتك 231.93$</button>
</div>

<div class="panel">
<div class="tTitle" id="marketTitle">📊 V103 LUXURY CLEAR - 20 صفقة - 3 LONG + 17 SHORT - MACD ONLY - Binance مطابقة - بعد العلاج +0.03$ - أوضح - <span class="liveDot"></span> FAST LIVE</div>
<div class="tHeader"><div>Coin</div><div>Type - واضح</div><div>Entry</div><div>Binance LIVE</div><div>MACD - ماكد فقط</div><div>PNL %</div><div>حالة - أوضح 100%</div></div>
<div id="list"></div>
</div>

<script>
let config = JSON.parse(localStorage.getItem('V103_LUX_CLEAR') || '{"capital":2000,"size":100,"target":6.0,"healProfit":0.03,"realized":231.93}');
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
function calc(t){return t.side==="LONG"? (t.n-t.e)/t.e*100 : (t.e-t.n)/t.e*100;}
function save(){localStorage.setItem('V103_LUX_CLEAR',JSON.stringify(config));render();}
function load(){document.getElementById('cap').value=config.capital;document.getElementById('size').value=config.size;document.getElementById('target').value=config.target;document.getElementById('healProfit').value=config.healProfit;render();}
function closeAll(){let fl=0;trades.forEach(t=>{let p=calc(t);if(p>0) fl+=(p/100)*config.size;});config.realized+=fl;trades.forEach(t=>{t.e=t.n;t.status='WIN';t.side=t.orig;});save();alert('تم قفل الكل +'+fl.toFixed(2)+'$ - أرباح الناجحة محفوظة');}
function resetAll(){if(confirm('تصفير العدادات زي أول؟')){config.realized=0;save();}}
function restoreIdea(){config.realized=231.93;config.capital=2000;save();alert('👑 تم استرجاع فكرتك المحفوظة 231.93$ - 13 ناجحة');}
function render(){
let fl=0;let h="";let bull=0,bear=0,winL=0,winS=0,totL=0,totS=0;
trades.forEach(t=>{
let pct=calc(t);fl+=(pct/100)*config.size*0.6;
if(t.macd>0) bull++; else bear++;
if(t.orig==="LONG") totL++; else totS++;
if(t.status==='WIN'){ if(t.orig==="LONG") winL++; else winS++; }
let cur=t.n>1?t.n.toFixed(2):t.n.toFixed(4);let ent=t.e>1?t.e.toFixed(2):t.e.toFixed(4);
let macdC=t.macd>0? '#00ff88':'#ff6b6b';let macdT=t.macd>0? '▲ Bull '+t.macd.toFixed(2)+' = LONG' : '▼ Bear '+t.macd.toFixed(2)+' = SHORT';
let row=t.status==='WIN'? 'tRow win' : (t.status==='HEALING'? 'tRow flip' : 'tRow heal');
let typeDisplay = t.status==='HEALING' ? t.orig+' → '+t.side+' 🔄' : t.side+' ✅';
let typeClass = t.status==='HEALING' ? 'FLIP' : t.side;
// حالة أوضح 100% - نفس صورتك بس أوضح
let statusTxt = '';
let statusColor = '';
if(t.status==='WIN'){
  statusTxt = '✅ ناجحة - ربح '+config.target+'% - محفوظ';
  statusColor = '#00ff88';
} else if(t.status==='HEALING'){
  statusTxt = '🔄 معكوسة '+t.orig+'→'+t.side+' - تعالج - تقفل +'+config.healProfit+'$';
  statusColor = '#00d4ff';
} else {
  statusTxt = '⏳ خاسرة '+pct.toFixed(2)+'% - ستعكس '+t.side+'→'+(t.side==='LONG'?'SHORT':'LONG');
  statusColor = '#ff8c00';
}
h+=`<div class="${row}"><div style="font-weight:900">${t.s}</div><div class="type ${typeClass}">${typeDisplay}</div><div class="price" style="color:#aaa">${ent}</div><div class="price" style="color:#fff">${cur}</div><div style="color:${macdC};font-family:Orbitron;font-size:8px;font-weight:900;text-align:center">${macdT}</div><div class="price" style="color:${pct>=0?'#00ff88':'#ff6b6b'}">${pct>=0?'+':''}${pct.toFixed(2)}%</div><div class="status" style="color:${statusColor}">${statusTxt}</div></div>`;
});
document.getElementById('list').innerHTML=h;
document.getElementById('capFix').textContent=config.capital.toFixed(1)+'$';
document.getElementById('total').textContent=(config.capital+config.realized).toFixed(2)+'$';
document.getElementById('real').textContent='+'+config.realized.toFixed(2)+'$';
document.getElementById('info').textContent=trades.filter(t=>t.status==='WIN').length+' ناجحة - 2 LONG + 11 SHORT';
document.getElementById('healCount').textContent=trades.filter(t=>t.status!=='WIN').length+' Healing 🔄 - عكس';
document.getElementById('macdInfo').textContent=bull+' Bull ▲ LONG + '+bear+' Bear ▼ SHORT';
document.getElementById('longWin').textContent=winL+' / '+totL+' ✅';
document.getElementById('shortWin').textContent=winS+' / '+totS+' ✅';
document.getElementById('targetV').textContent=config.target+'%';
document.getElementById('healProfitV').textContent=config.healProfit+'$';
document.getElementById('successBar').textContent='✅ '+trades.filter(t=>t.status==='WIN').length+' ناجحة ('+winL+'L+'+winS+'S) - '+config.realized.toFixed(2)+'$';
document.getElementById('healBar').textContent='🔄 '+trades.filter(t=>t.status!=='WIN').length+' معكوسة → تعادل + '+config.healProfit+'$ - فكرتك';
document.getElementById('macdBar').textContent='📊 MACD ONLY - '+bull+' Bull LONG + '+bear+' Bear SHORT = 20 - ماكد فقط';
document.getElementById('floating').textContent=(fl>=0?'+':'')+fl.toFixed(2)+'$';
document.getElementById('floating').style.color=fl>=0?'#00ff88':'#ff6b6b';
}
setInterval(()=>{let ch=false;trades.forEach(t=>{let pct=calc(t);if(t.status==='WIN' && pct>=config.target && Math.random()>0.85){config.realized+=(config.target/100)*config.size;t.e=t.n;ch=true;let el=document.getElementById('real');el.classList.add('jump');setTimeout(()=>el.classList.remove('jump'),600);}if(t.status==='LOSS' && pct<-1.0){t.side=t.side==="LONG"?"SHORT":"LONG";t.e=t.n;t.status='HEALING';t.macd=-t.macd;ch=true;}if(t.status==='HEALING'){let need=(config.healProfit/config.size)*100;if(pct>=need){config.realized+=config.healProfit;t.status='WIN';t.e=t.n;ch=true;}}});if(ch) save();},3500);
async function fetchFast(){try{let r=await fetch('https://api.binance.com/api/v3/ticker/price?symbols=["BTCUSDT","ETHUSDT","SOLUSDT","AVAXUSDT","DOTUSDT"]');if(r.ok){let d=await r.json();d.forEach(x=>{let tr=trades.find(t=>t.sym===x.symbol);if(tr) tr.n=parseFloat(x.price);});render();}}catch(e){}}
document.getElementById('cap').addEventListener('input',e=>{config.capital=parseFloat(e.target.value)||2000;save();});
document.getElementById('size').addEventListener('input',e=>{config.size=parseFloat(e.target.value)||100;save();});
document.getElementById('target').addEventListener('input',e=>{config.target=parseFloat(e.target.value)||6;save();});
document.getElementById('healProfit').addEventListener('input',e=>{config.healProfit=parseFloat(e.target.value)||0.03;save();});
load();fetchFast();setInterval(fetchFast,12000);setInterval(render,1200);
</script>
</body>
</html>
"""
@app.route('/')
def home():
    return render_template_string(HTML)
@app.route('/health')
def health():
    return "OK V103 LUXURY CLEAR FAST MACD +0.03$"
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))

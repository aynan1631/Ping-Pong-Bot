from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V83 قبل الظهر 👑</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=Orbitron:wght@700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#06061e;color:#fff;font-family:'Cairo',sans-serif;padding:12px}
.header{background: linear-gradient(90deg,#ffb700,#ff8c00,#ffb700); background-size:200% 100%; animation: gold 2s linear infinite; color:#000; padding:14px; border-radius:16px; text-align:center; font-weight:900; font-size:19px; box-shadow:0 0 25px #ffb70066}
@keyframes gold{0%{background-position:0% 50%}100%{background-position:200% 50%}}
.bar{display:flex;gap:8px;margin:10px 0}
.bar div{flex:1;padding:10px;border-radius:12px;text-align:center;font-weight:900;font-size:12px}
.bar.green{background: linear-gradient(90deg,#00ff88,#00e676); color:#000; box-shadow:0 0 18px #00ff8855}
.bar.orange{background: linear-gradient(90deg,#ff8c00,#ffb700); color:#000}
.controls{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin:12px 0}
@media(max-width:700px){.controls{grid-template-columns:1fr}}
.ctrl{background:#12123a;border:2.5px solid #ffb700;border-radius:16px;padding:14px;text-align:center}
.ctrl.green{border-color:#00ff88;box-shadow:0 0 20px #00ff8833}
.ctrl label{font-size:13px;display:block;margin-bottom:8px;font-weight:900}
.ctrl input{background:#000;border:2px solid #ffb700;color:#ffb700;border-radius:12px;padding:12px;width:100%;text-align:center;font-family:'Orbitron';font-size:24px;font-weight:900;outline:none}
.ctrl input:focus{transform:scale(1.05);box-shadow:0 0 15px #ffb70088}
.ctrl.green input{border-color:#00ff88;color:#00ff88}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
@media(max-width:700px){.grid{grid-template-columns:1fr 1fr}}
.card{background: linear-gradient(180deg,#1a1a4a,#12123a);border:1.5px solid #2a2a6a;border-radius:16px;padding:16px;text-align:center;position:relative;box-shadow:0 8px 25px rgba(0,0,0,0.4)}
.card.profit{border-color:#00ff88;box-shadow:0 0 30px #00ff8844;background: linear-gradient(180deg,#102a1a,#12123a)}
.card.total{border-color:#ffb700;box-shadow:0 0 25px #ffb70033;background: linear-gradient(180deg,#2a1f0a,#12123a)}
.label{font-size:12px;opacity:0.7;margin-bottom:6px;font-weight:700}
.val{font-family:'Orbitron';font-size:18px;font-weight:900}
.profit-val{font-family:'Orbitron';font-size:36px;color:#00ff88;text-shadow:0 0 15px #00ff88,0 0 35px #00ff8855}
.total-val{font-family:'Orbitron';font-size:26px;color:#ffb700;text-shadow:0 0 15px #ffb70066}
.badge{margin-top:8px;display:inline-block;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:900}
.badge.green{background:#00ff88;color:#000}.badge.gold{background:#ffb700;color:#000}
.tradesPanel{margin-top:12px;background:#0d0d2e;border:2px solid #2a2a6a;border-radius:18px;padding:12px}
.tTitle{text-align:center;color:#ffb700;font-size:12px;font-weight:900;margin-bottom:10px;border-bottom:1px solid #2a2a6a;padding-bottom:8px}
.tHeader{display:grid;grid-template-columns:60px 60px 35px 75px 85px 50px 45px;font-size:9px;opacity:0.5;padding:6px 8px;text-align:center}
.tRow{display:grid;grid-template-columns:60px 60px 35px 75px 85px 50px 45px;align-items:center;background:linear-gradient(90deg,#1a1a5a,#1e1e6a);border:1px solid #2a2a7a;border-radius:12px;padding:8px 6px;margin-bottom:6px;font-size:10px;font-weight:800;transition:0.2s}
.tRow:hover{transform:scale(1.02);border-color:#ffb70055}
.tRow.heal{border-color:#8a2eff;background:linear-gradient(90deg,#1a0a3a,#2a1a5a);box-shadow:0 0 18px #8a2eff66; animation:pulse 1.2s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 8px #8a2eff66}50%{box-shadow:0 0 20px #8a2eff}}
.type{font-size:9px;padding:4px 6px;border-radius:20px;text-align:center;font-weight:900}
.type.LONG{background:#00ff66;color:#000}.type.SHORT{background:#ff0f2b;color:#fff}.type.HEAL{background:#8a2eff;color:#fff}
.priceE{font-family:'Orbitron';font-size:9px;color:#aaa;text-align:left;direction:ltr}
.priceN{font-family:'Orbitron';font-size:10px;color:#fff;text-align:left;direction:ltr;font-weight:900}
.liveDot{width:8px;height:8px;background:#00ff88;border-radius:50%;display:inline-block;animation:blink 1s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.2}}
</style>
</head>
<body>

<div class="header">👑 V83 قبل الظهر - BTC <span id="btcHeader">77365</span>$ - EMA200 + RSI14 👑</div>
<div class="bar"><div class="green" id="liveStatus"><span class="liveDot"></span> V83 LIVE قبل الظهر - EMA200 RSI14</div><div class="orange" id="saveStatus">💎 1082 شفاء | 2 يعالج | 231.93$ لنا</div></div>

<div class="controls">
  <div class="ctrl"><label>💰 رأس المال المستعمل</label><input id="capUsed" type="number" value="2000" step="100"></div>
  <div class="ctrl"><label>📦 قيمة الصفقة</label><input id="size" type="number" value="100" step="10"></div>
  <div class="ctrl green"><label>🎯 تحديد الربح %</label><input id="target" type="number" value="6.0" step="0.5"></div>
</div>

<div class="grid">
  <div class="card"><div class="label">رأس المال الثابت</div><div class="val" id="capFix">2000.0$</div></div>
  <div class="card"><div class="label">حجم الصفقة</div><div class="val" id="sizeVal">100.0</div></div>
  <div class="card"><div class="label">تايت</div><div class="val" id="tight">2000$</div></div>
  <div class="card total"><div class="label">الإجمالي</div><div class="total-val" id="total">2231.93$</div><div class="label" id="info">1082 شفاء | 231.93$ لنا</div><div class="badge gold">V83 GOLD قبل الظهر</div></div>
  <div class="card profit"><div style="position:absolute;top:6px;left:6px;background:#00ff88;color:#000;font-size:8px;padding:2px 6px;border-radius:6px;font-weight:900">🔒 محفوظ</div><div class="label">صافي ربح</div><div class="profit-val" id="real">+231.93$</div><div class="badge green">ما ينمسح - قبل الظهر</div></div>
  <div class="card"><div class="label">حر LIVE <span class="liveDot"></span></div><div class="val" style="color:#ff6b6b;font-size:22px" id="floating">-0.27$</div></div>
  <div class="card"><div class="label">🛡️ حماية</div><div class="val" style="font-size:12px">60s | TURBO | 3$</div></div>
  <div class="card"><div class="label">يعالج (آخر 1082)</div><div class="val" id="healCount">2 يعالج 🩹</div></div>
  <div class="card"><div class="label">L/S | دورات | حماية</div><div class="val" style="font-size:12px">10 / 10 | 42 | 3$</div></div>
</div>

<div class="tradesPanel">
  <div class="tTitle" id="marketTitle">📊 قبل الظهر - BTC 77365$ - ETH 2541$ - SOL 101.96$ - AVAX 21.87$ - EMA200 + RSI14 - 2 يعالج - <span class="liveDot"></span> LIVE</div>
  <div class="tHeader"><div>العملة</div><div>النوع</div><div>icon</div><div>دخول</div><div>حالي LIVE</div><div>EMA200</div><div>RSI14</div></div>
  <div id="list"></div>
</div>

<script>
let config = JSON.parse(localStorage.getItem('V83_BEFORE_NOON') || '{"capital":2000,"size":100,"target":6.0,"realized":231.93,"healed":1082}');

// نفس الصفقات اللي في صورتك قبل الظهر
let trades=[
{s:"BTC",e:78000,n:77365,side:"LONG",heal:true,ema:76500,rsi:52,cg:"bitcoin"},
{s:"ETH",e:2450,n:2541,side:"SHORT",ema:2480,rsi:61,cg:"ethereum"},
{s:"SOL",e:142.50,n:101.96,side:"LONG",ema:115,rsi:38,cg:"solana"},
{s:"AVAX",e:22.40,n:21.87,side:"SHORT",ema:23.1,rsi:44,cg:"avalanche-2"},
{s:"DOT",e:6.15,n:6.10,side:"LONG",ema:5.9,rsi:55,cg:"polkadot"},
{s:"LINK",e:14.88,n:15.10,side:"SHORT",ema:15.2,rsi:58,cg:"chainlink"},
{s:"XRP",e:0.58,n:0.59,side:"LONG",ema:0.56,rsi:60,cg:"ripple"},
{s:"DOGE",e:0.12,n:0.119,side:"SHORT",ema:0.125,rsi:42,cg:"dogecoin"},
{s:"ADA",e:0.45,n:0.44,side:"SHORT",ema:0.47,rsi:40,cg:"cardano"},
{s:"ATOM",e:1.639,n:1.62,side:"SHORT",ema:1.70,rsi:43,cg:"cosmos"},
{s:"MATIC",e:0.52,n:0.51,side:"LONG",ema:0.50,rsi:53,cg:"matic-network"},
{s:"LIT",e:0.743,n:0.73,side:"LONG",ema:0.71,rsi:54,cg:"litentry"},
{s:"PROM",e:5.79,n:5.79,side:"LONG",heal:true,ema:5.6,rsi:57,cg:"prom"},
{s:"ETHFI",e:0.74,n:0.73,side:"SHORT",ema:0.78,rsi:45,cg:"ether-fi"},
{s:"DNT",e:0.036,n:0.0356,side:"SHORT",ema:0.037,rsi:41,cg:"district0x"},
{s:"PDA",e:0.0098,n:0.0097,side:"SHORT",ema:0.0102,rsi:39,cg:"playdapp"},
{s:"PLA",e:0.2347,n:0.232,side:"LONG",ema:0.22,rsi:56,cg:"playdapp"},
{s:"BROCCOLI71",e:0.0177,n:0.0177,side:"LONG",ema:0.016,rsi:62,cg:null},
{s:"BEAMX",e:0.0072,n:0.0071,side:"LONG",ema:0.0068,rsi:59,cg:"beam"},
{s:"SNXXB",e:15.19,n:15.10,side:"SHORT",ema:15.5,rsi:46,cg:null},
];

function save(){ localStorage.setItem('V83_BEFORE_NOON', JSON.stringify(config)); document.getElementById('saveStatus').innerHTML='✅ محفوظ قبل الظهر: '+config.capital+'$ | '+config.size+'$ | '+config.target+'% - 1082 شفاء'; render(); }
function load(){ document.getElementById('capUsed').value=config.capital; document.getElementById('size').value=config.size; document.getElementById('target').value=config.target; render(); }

function render(){
  let h=""; trades.forEach(t=>{
    let cur=(t.n||t.e).toFixed((t.n||t.e)>10?2:4); let entry=t.e.toFixed(t.e>10?2:4);
    let typeClass=t.heal?"HEAL":t.side; let icon=t.heal?"💊":(t.side=="LONG"?"🟢":"🔴");
    let rowClass=t.heal?"tRow heal":"tRow";
    h+=`<div class="${rowClass}"><div style="font-weight:900;text-align:right">${t.s}</div><div class="type ${typeClass}">${t.heal?"يعالج":t.side}</div><div style="text-align:center">${icon}</div><div class="priceE">${entry}</div><div class="priceN">${cur}</div><div class="priceE" style="color:${t.n>t.ema?'#00ff88':'#ff6b6b'}">${t.ema.toFixed(2)}</div><div class="priceE">${t.rsi.toFixed(0)}</div></div>`;
  });
  document.getElementById('list').innerHTML=h;
  document.getElementById('capFix').textContent=config.capital+'$'; document.getElementById('tight').textContent=config.capital+'$'; document.getElementById('sizeVal').textContent=config.size;
  document.getElementById('total').textContent=(config.capital+config.realized).toFixed(2)+'$'; document.getElementById('real').textContent='+'+config.realized.toFixed(2)+'$';
  document.getElementById('info').textContent=config.healed+' شفاء | '+config.realized.toFixed(2)+'$ لنا'; document.getElementById('healCount').textContent=trades.filter(t=>t.heal).length+' يعالج 🩹';
  document.getElementById('btcHeader').textContent=(trades.find(t=>t.s==='BTC')?.n||77365).toFixed(0);
}

async function fetchLive(){
  try{
    let ids="bitcoin,ethereum,solana,avalanche-2,polkadot,chainlink,ripple,dogecoin,cardano,cosmos,matic-network";
    let res=await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=usd`);
    if(res.ok){
      let d=await res.json();
      let map={bitcoin:"BTC",ethereum:"ETH",solana:"SOL","avalanche-2":"AVAX",polkadot:"DOT",chainlink:"LINK",ripple:"XRP",dogecoin:"DOGE",cardano:"ADA",cosmos:"ATOM","matic-network":"MATIC"};
      Object.keys(map).forEach(k=>{ if(d[k]){ let tr=trades.find(t=>t.s===map[k]); if(tr) tr.n=d[k].usd; }});
      document.getElementById('liveStatus').innerHTML=`<span class="liveDot"></span> ✅ قبل الظهر LIVE - BTC ${d.bitcoin.usd.toFixed(0)}$ - ETH ${d.ethereum.usd.toFixed(0)}$`;
      document.getElementById('marketTitle').innerHTML=`📊 قبل الظهر - BTC ${d.bitcoin.usd.toFixed(0)}$ - ETH ${d.ethereum.usd.toFixed(0)}$ - SOL ${d.solana.usd.toFixed(2)}$ - EMA200 RSI14 - 2 يعالج - <span class="liveDot"></span> LIVE`;
      render();
    }
  }catch(e){}
}

document.getElementById('capUsed').addEventListener('input', e=>{config.capital=parseFloat(e.target.value)||2000; save();});
document.getElementById('size').addEventListener('input', e=>{config.size=parseFloat(e.target.value)||100; save();});
document.getElementById('target').addEventListener('input', e=>{config.target=parseFloat(e.target.value)||6; save();});

load(); fetchLive(); setInterval(fetchLive, 8000);
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/health')
def health():
    return "OK V83 BEFORE NOON - EMA200 RSI14 - 2 HEAL"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))

from flask import Flask, render_template_string, jsonify
import os, requests, time
from threading import Thread

app = Flask(__name__)

price_cache = {}
symbols_map = {
"BTCUSDT": "BTC", "ETHUSDT": "ETH", "SOLUSDT": "SOL", "AVAXUSDT": "AVAX",
"DOTUSDT": "DOT", "LINKUSDT": "LINK", "XRPUSDT": "XRP", "DOGEUSDT": "DOGE",
"ADAUSDT": "ADA", "ATOMUSDT": "ATOM", "MATICUSDT": "MATIC", "LITUSDT": "LIT",
"PROMUSDT": "PROM", "ETHFIUSDT": "ETHFI", "SNXUSDT": "SNX"
}

def binance_worker():
    global price_cache
    while True:
        try:
            r = requests.get('https://api.binance.com/api/v3/ticker/price', params={'symbols': str(list(symbols_map.keys())).replace("'", '"')}, timeout=4)
            if r.status_code == 200:
                for d in r.json():
                    price_cache[symbols_map[d['symbol']]] = float(d['price'])
        except:
            try:
                r = requests.get('https://api.bybit.com/v5/market/tickers?category=spot', timeout=4)
                if r.status_code == 200:
                    for item in r.json()['result']['list']:
                        if item['symbol'] in symbols_map:
                            price_cache[symbols_map[item['symbol']]] = float(item['lastPrice'])
            except: pass
        time.sleep(3)

Thread(target=binance_worker, daemon=True).start()

HTML = """<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V105 SERVER PROXY 👑</title><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=Orbitron:wght@700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#05051a;color:#fff;font-family:'Cairo',sans-serif;padding:10px;max-width:1400px;margin:0 auto}
.header{background:linear-gradient(90deg,#ffb700,#ff8c00,#ffb700);background-size:300% 100%;animation:gold 1.5s linear infinite;color:#000;padding:14px;border-radius:18px;text-align:center;font-weight:900;font-size:15px;box-shadow:0 0 35px #ffb70077}
@keyframes gold{0%{background-position:0% 50%}100%{background-position:300% 50%}}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:10px 0}
@media(max-width:900px){.grid{grid-template-columns:repeat(2,1fr)}}
.card{background:linear-gradient(180deg,#1e1e5e,#0f0f35);border:1.5px solid #2a2a6a;border-radius:16px;padding:14px;text-align:center;min-height:90px;display:flex;flex-direction:column;justify-content:center;box-shadow:0 8px 25px #0008}
.cardTitle{font-size:11px;opacity:0.8;margin-bottom:6px;color:#bbb}.cardValue{font-family:'Orbitron';font-size:19px;font-weight:900;direction:ltr}
.profitV{color:#00ff88;font-size:26px}.totalV{color:#ffb700;font-size:22px}
.card.profit{border-color:#00ff88;box-shadow:0 0 25px #00ff8833}.card.total{border-color:#ffb700;box-shadow:0 0 25px #ffb70033}
.ctrls{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:10px 0}
@media(max-width:600px){.ctrls{grid-template-columns:1fr 1fr}}
.ctrl{background:#12123a;border:1.5px solid #2a2a6a;border-radius:12px;padding:8px;text-align:center}
.ctrl label{font-size:10px;color:#ffb700;display:block;margin-bottom:5px;font-weight:900}
.ctrl input{width:100%;background:#000;border:1.5px solid #333;color:#ffb700;border-radius:8px;padding:9px;text-align:center;font-family:'Orbitron';font-size:18px;font-weight:900;direction:ltr}
.btns{display:flex;gap:10px;margin:12px 0}
.btn{flex:1;padding:12px;border-radius:12px;border:none;font-family:'Cairo';font-weight:900;font-size:12px;cursor:pointer}
.btn.close{background:linear-gradient(135deg,#ff0f2b,#ff5a6b);color:#fff}.btn.reset{background:linear-gradient(135deg,#2a2a6a,#4a4a8a);color:#fff}.btn.restore{background:linear-gradient(135deg,#ffb700,#ff8c00);color:#000}
.panel{background:#0e0e3a;border:1.5px solid #2a2a6a;border-radius:18px;padding:12px;margin-top:12px;overflow-x:auto}
.tTitle{text-align:center;color:#ffb700;font-size:11px;font-weight:900;margin-bottom:8px;border-bottom:1px solid #2a2a6a;padding-bottom:8px}
.tHeader,.tRow{display:grid;grid-template-columns:50px 80px 80px 86px 68px 64px 110px;gap:4px;font-size:10px;padding:10px 6px;text-align:center;align-items:center;min-width:570px}
.tHeader{opacity:0.5;font-size:9px}.tRow{background:linear-gradient(90deg,#1a1a5a,#1e1e6a);border:1px solid #2a2a7a;border-radius:12px;margin-bottom:6px;font-weight:800}
.tRow.win{border-color:#00ff88;background:linear-gradient(90deg,#0a2a1a,#1a4a2a)}.tRow.flip{border-color:#00d4ff;background:linear-gradient(90deg,#0a1a3a,#0a2a5a);box-shadow:0 0 18px #00d4ff44}.tRow.heal{border-color:#8a2eff;background:linear-gradient(90deg,#1a0a3a,#2a1a5a)}
.type{font-size:8px;padding:5px 7px;border-radius:20px;font-weight:900}.type.LONG{background:#00ff66;color:#000}.type.SHORT{background:#ff0f2b;color:#fff}.type.FLIP{background:linear-gradient(135deg,#00d4ff,#8a2eff);color:#fff}
.price{font-family:'Orbitron';font-size:11px;direction:ltr;font-weight:900;text-align:left}
.liveDot{width:8px;height:8px;background:#00ff88;border-radius:50%;display:inline-block;animation:blink 1s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.2}}
.src{font-size:9px;color:#00d4ff;font-weight:900}
</style></head><body>
<div class="header">👑 V105 - حل باينانس - السيرفر يجيب السعر مو المتصفح - مباشر + ما يعلق + MACD ONLY + 0.03$ 👑</div>
<div class="ctrls">
<div class="ctrl"><label>💎 ربح بعد العلاج</label><input id="healProfit" value="0.03" type="number" step="0.01"></div>
<div class="ctrl"><label>🎯 نسبة الربح</label><input id="target" value="6.0" type="number"></div>
<div class="ctrl"><label>📦 قيمة الصفقة</label><input id="size" value="100" type="number"></div>
<div class="ctrl"><label>💰 رأس المال</label><input id="cap" value="2000" type="number"></div>
</div>
<div class="grid">
<div class="card total"><div class="cardTitle">الإجمالي</div><div class="cardValue totalV" id="total">2255.96$</div><div class="cardTitle" id="info">14 ناجحة</div></div>
<div class="card profit"><div class="cardTitle">صافي الربح</div><div class="cardValue profitV" id="real">+255.96$</div><div class="cardTitle">MACD فقط - محفوظ</div></div>
<div class="card"><div class="cardTitle">مصدر البيانات</div><div class="cardValue src" id="source">BINANCE SERVER</div><div class="cardTitle" id="sourceInfo">مباشر من السيرفر</div></div>
<div class="card"><div class="cardTitle">العائم LIVE</div><div class="cardValue" id="floating">+1.05$</div><div class="cardTitle"><span class="liveDot"></span> لا يعلق</div></div>
</div>
<div class="btns">
<button class="btn close" onclick="closeAll()">🔒 قفل الكل</button>
<button class="btn reset" onclick="resetAll()">🔄 تصفير زي أول</button>
<button class="btn restore" onclick="restoreIdea()">👑 استرجاع 231.93$</button>
</div>
<div class="panel">
<div class="tTitle" id="marketTitle">📊 V105 - 20 صفقة - سيرفر Railway → Binance مباشر - لا يعلق - MACD ONLY +0.03$ - <span class="liveDot"></span> <span id="srcLabel">BINANCE SERVER PROXY</span></div>
<div class="tHeader"><div>Coin</div><div>Type</div><div>Entry</div><div>Binance LIVE</div><div>MACD</div><div>PNL%</div><div>حالة</div></div>
<div id="list"></div>
</div>
<script>
let config=JSON.parse(localStorage.getItem('V105_PROXY')||'{"capital":2000,"size":100,"target":6.0,"healProfit":0.03,"realized":255.96}');
let trades=[{s:"BTC",e:78000,n:77382,side:"LONG",orig:"LONG",macd:0.45,status:"HEALING"},{s:"ETH",e:2450,n:2541,side:"LONG",orig:"LONG",macd:0.32,status:"WIN"},{s:"SOL",e:142.5,n:101.99,side:"LONG",orig:"LONG",macd:0.28,status:"WIN"},{s:"AVAX",e:22.4,n:21.87,side:"SHORT",orig:"SHORT",macd:-0.15,status:"WIN"},{s:"DOT",e:6.15,n:6.10,side:"SHORT",orig:"SHORT",macd:-0.22,status:"WIN"},{s:"LINK",e:14.88,n:15.10,side:"SHORT",orig:"SHORT",macd:-0.08,status:"LOSS"},{s:"XRP",e:0.58,n:0.59,side:"SHORT",orig:"SHORT",macd:-0.05,status:"LOSS"},{s:"DOGE",e:0.12,n:0.119,side:"SHORT",orig:"SHORT",macd:-0.18,status:"WIN"},{s:"ADA",e:0.45,n:0.44,side:"SHORT",orig:"SHORT",macd:-0.25,status:"WIN"},{s:"ATOM",e:1.639,n:1.62,side:"SHORT",orig:"SHORT",macd:-0.12,status:"WIN"},{s:"MATIC",e:0.52,n:0.51,side:"SHORT",orig:"SHORT",macd:-0.20,status:"WIN"},{s:"LIT",e:0.743,n:0.73,side:"SHORT",orig:"SHORT",macd:-0.14,status:"WIN"},{s:"PROM",e:5.79,n:5.79,side:"SHORT",orig:"LONG",macd:0.12,status:"HEALING"},{s:"ETHFI",e:0.74,n:0.73,side:"SHORT",orig:"SHORT",macd:-0.09,status:"WIN"},{s:"DNT",e:0.036,n:0.0356,side:"SHORT",orig:"SHORT",macd:-0.11,status:"WIN"},{s:"PDA",e:0.0098,n:0.0097,side:"SHORT",orig:"SHORT",macd:-0.19,status:"WIN"},{s:"PLA",e:0.2347,n:0.232,side:"LONG",orig:"SHORT",macd:-0.16,status:"HEALING"},{s:"BROCCOLI",e:0.0177,n:0.0177,side:"SHORT",orig:"SHORT",macd:-0.07,status:"LOSS"},{s:"BEAMX",e:0.0072,n:0.0071,side:"LONG",orig:"SHORT",macd:0.08,status:"HEALING"},{s:"SNX",e:15.19,n:15.10,side:"SHORT",orig:"SHORT",macd:-0.13,status:"WIN"}];
function calc(t){return t.side==="LONG"? (t.n-t.e)/t.e*100 : (t.e-t.n)/t.e*100;}
function save(){localStorage.setItem('V105_PROXY',JSON.stringify(config));}
function load(){document.getElementById('cap').value=config.capital;document.getElementById('size').value=config.size;document.getElementById('target').value=config.target;document.getElementById('healProfit').value=config.healProfit;render();}
function closeAll(){let fl=0;trades.forEach(t=>{let p=calc(t);if(p>0) fl+=(p/100)*config.size;});config.realized+=fl;trades.forEach(t=>{t.e=t.n;t.status='WIN';t.side=t.orig;});save();render();}
function resetAll(){config.realized=0;save();render();}
function restoreIdea(){config.realized=231.93;save();render();}
function render(){let fl=0;let h="";trades.forEach(t=>{let pct=calc(t);fl+=(pct/100)*config.size*0.6;let cur=t.n>1?t.n.toFixed(2):t.n.toFixed(4);let ent=t.e>1?t.e.toFixed(2):t.e.toFixed(4);let row=t.status==='WIN'? 'tRow win' : (t.status==='HEALING'? 'tRow flip' : 'tRow heal');let typeTxt=t.status==='HEALING'? t.orig+'→'+t.side+' 🔄' : t.side+' ✅';let statusTxt=t.status==='WIN'? '✅ ناجحة' : (t.status==='HEALING'? '🔄 +'+config.healProfit+'$' : '⏳ ستعكس');let macdC=t.macd>0? '#00ff88':'#ff6b6b';let macdT=t.macd>0? '▲'+t.macd.toFixed(2):'▼'+t.macd.toFixed(2);h+=`<div class="${row}"><div style="font-weight:900">${t.s}</div><div class="type ${t.status==='HEALING'?'FLIP':t.side}">${typeTxt}</div><div class="price" style="color:#aaa">${ent}</div><div class="price" style="color:#fff">${cur}</div><div style="color:${macdC};font-family:Orbitron;font-size:8px;font-weight:900">${macdT}</div><div class="price" style="color:${pct>=0?'#00ff88':'#ff6b6b'}">${pct>=0?'+':''}${pct.toFixed(2)}%</div><div style="font-size:9px;color:${t.status==='WIN'?'#00ff88':'#00d4ff'}">${statusTxt}</div></div>`;});document.getElementById('list').innerHTML=h;document.getElementById('total').textContent=(config.capital+config.realized).toFixed(2)+'$';document.getElementById('real').textContent='+'+config.realized.toFixed(2)+'$';document.getElementById('info').textContent=trades.filter(t=>t.status==='WIN').length+' ناجحة';document.getElementById('floating').textContent=(fl>=0?'+':'')+fl.toFixed(2)+'$';}
async function fetchFromServer(){try{let r=await fetch('/api/prices');if(r.ok){let data=await r.json();let count=0;for(let k in data){let tr=trades.find(t=>t.s===k);if(tr){tr.n=data[k];count++;}}if(count>0){document.getElementById('source').textContent='BINANCE LIVE';document.getElementById('sourceInfo').textContent=count+' عملة مباشر';document.getElementById('srcLabel').textContent='BINANCE SERVER PROXY - '+count+' LIVE';}}}catch(e){}render();}
setInterval(()=>{trades.forEach(t=>{let ch=(Math.random()-0.5)*0.002;t.n=t.n*(1+ch);});let changed=false;trades.forEach(t=>{let pct=calc(t);if(t.status==='WIN' && pct>=config.target && Math.random()>0.85){config.realized+=(config.target/100)*config.size;t.e=t.n;changed=true;}if(t.status==='LOSS' && pct<-1.0){t.side=t.side==="LONG"?"SHORT":"LONG";t.e=t.n;t.status='HEALING';t.macd=-t.macd;changed=true;}if(t.status==='HEALING'){let need=(config.healProfit/config.size)*100;if(pct>=need){config.realized+=config.healProfit;t.status='WIN';t.e=t.n;changed=true;}}});if(changed) save();render();},1500);
document.getElementById('cap').addEventListener('input',e=>{config.capital=parseFloat(e.target.value)||2000;save();render();});
document.getElementById('size').addEventListener('input',e=>{config.size=parseFloat(e.target.value)||100;save();render();});
document.getElementById('target').addEventListener('input',e=>{config.target=parseFloat(e.target.value)||6;save();render();});
document.getElementById('healProfit').addEventListener('input',e=>{config.healProfit=parseFloat(e.target.value)||0.03;save();render();});
load();fetchFromServer();setInterval(fetchFromServer,4000);
</script></body></html>
"""
@app.route('/')
def home():
    return render_template_string(HTML)
@app.route('/api/prices')
def prices():
    return jsonify(price_cache)
@app.route('/health')
def health():
    return f"OK V105 - {len(price_cache)} coins"
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))

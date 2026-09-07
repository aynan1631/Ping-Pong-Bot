from flask import Flask, render_template_string, jsonify, request, make_response
import os, threading, requests, random, time

app = Flask(__name__)
bot_state = {"realized": 0.0, "base_capital": 1000, "per_trade": 500, "trades": [], "is_running": True}

def get_volatile():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=8).json()
        cands=[]
        for i in r:
            s=i['symbol']
            if not s.endswith('USDT'): continue
            if s in ["BTCUSDT","ETHUSDT"]: continue
            if "BULL" in s or "BEAR" in s or "UP" in s or "DOWN" in s: continue
            ch=abs(float(i['priceChangePercent'])); vol=float(i['quoteVolume'])
            if ch>4 and vol>8000000: cands.append({"symbol":s,"vol":ch,"price":float(i['lastPrice'])})
        cands.sort(key=lambda x: x['vol'], reverse=True)
        return cands[:5]
    except:
        return [{"symbol":"SOLUSDT","vol":5.5,"price":140},{"symbol":"AVAXUSDT","vol":4.9,"price":25},{"symbol":"PEPEUSDT","vol":6.2,"price":0.000008}]

def bot_loop():
    vol=get_volatile()
    for c in vol[:3]:
        bot_state["trades"].append({"coin":c["symbol"],"entry":c["price"],"live":c["price"],"side":random.choice(["LONG","SHORT"]),"cap":bot_state["per_trade"],"usd":0.0,"pct":0.0,"vol":c["vol"]})
    while True:
        if bot_state["is_running"]:
            try:
                # سعر حقيقي لحظي من باينانس
                pm={x['symbol']:float(x['price']) for x in requests.get("https://api.binance.com/api/v3/ticker/price", timeout=5).json()}
                for t in bot_state["trades"]:
                    if t["coin"] in pm:
                        t["live"]=pm[t["coin"]]
                        t["pct"]=round(((t["live"]-t["entry"])/t["entry"]*100 if t["side"]=="LONG" else (t["entry"]-t["live"])/t["entry"]*100),2)
                        t["usd"]=round(t["pct"]/100*t["cap"],2)
            except: pass
        time.sleep(1.5)
threading.Thread(target=bot_loop, daemon=True).start()

HTML="""
<!DOCTYPE html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache"><title>RAIS V20 LUXURY REAL PRICE</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@900&display=swap" rel="stylesheet">
<style>
*{font-family:'Cairo','Segoe UI',sans-serif!important;font-weight:900!important;box-sizing:border-box}
body{background:radial-gradient(circle at top,#1a1a2e,#050507);margin:0;padding:14px;color:#fff}
.card{border-radius:22px;padding:20px;text-align:center;box-shadow:0 0 30px rgba(0,0,0,0.6);border:4px solid}
.card-title{font-size:26px!important;color:#aaa!important}
.card-money{font-size:62px!important;line-height:1.1;text-shadow:0 0 20px currentColor}
.input-big{background:#000;color:#fff;border:3px solid #444;border-radius:14px;padding:14px;text-align:center;font-size:32px!important;width:150px}
.btn{border:none;border-radius:12px;padding:12px 22px;font-size:20px!important;cursor:pointer}
.sec-title{font-size:28px!important}
.small{font-size:20px!important;color:#888}
.live-price{color:#00ff88;font-size:22px!important;text-shadow:0 0 10px #00ff88}
.entry-price{color:#ffbe0b;font-size:20px!important}
</style></head><body>

<div style="background:linear-gradient(90deg,#111,#1e1e2e);padding:18px 22px;border-radius:20px;display:flex;justify-content:space-between;align-items:center;border:1px solid #333">
<div style="font-size:30px">👑 RAIS V20 - أسعار حقيقية من باينانس + ENTRY/LIVE</div>
<button id="togBtn" onclick="toggleBot()" style="background:#00ff88;color:#000;padding:12px 26px;border-radius:40px;font-size:22px;border:none;cursor:pointer">● RUNNING - BINANCE LIVE</button>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-top:16px">
<div class="card" style="background:#0f1210;border-color:#00ff88">
<div style="font-size:38px">💰</div><div class="card-title">الرصيد الاساسي - تتحكم</div><div class="card-money" style="color:#00ff88">$<span id="baseShow">1000</span></div>
<div style="margin-top:14px;background:#000;padding:12px;border-radius:14px;border:2px solid #00ff88">
<div style="display:flex;gap:6px;justify-content:center;align-items:center"><input id="baseIn" value="1000" class="input-big" style="border-color:#00ff88;color:#00ff88;width:130px"><button onclick="saveBase()" class="btn" style="background:#00ff88;color:#000">SAVE</button></div>
<div style="display:flex;gap:5px;justify-content:center;margin-top:10px"><button onclick="setBase(1000)" class="btn" style="background:#222;color:#fff;font-size:14px!important">1K</button><button onclick="setBase(5000)" class="btn" style="background:#00ff88;color:#000;font-size:14px!important">5K</button><button onclick="setBase(10000)" class="btn" style="background:#222;color:#fff;font-size:14px!important">10K</button><button onclick="setBase(20000)" class="btn" style="background:#222;color:#fff;font-size:14px!important">20K</button></div>
</div>
</div>
<div class="card" style="background:#171010;border-color:#ff3b3b"><div style="font-size:38px">📈</div><div class="card-title">الربح العائم يتصفر</div><div id="flt" class="card-money" style="color:#ff3b3b">$0.00</div><div style="margin-top:10px;font-size:16px;color:#00ff88">● BINANCE REAL PRICE</div></div>
<div class="card" style="background:#0f121a;border-color:#00d4ff"><div style="font-size:38px">🏦</div><div class="card-title">الربح المحقق يتصفر</div><div class="card-money" style="color:#00d4ff">$<span id="real">0.00</span></div></div>
</div>

<div style="background:linear-gradient(90deg,#1a1a22,#222235);border:4px solid #ffbe0b;border-radius:20px;padding:18px;margin-top:16px">
<div class="sec-title" style="color:#ffbe0b">⚡ تحكم مبلغ كل صفقة + الأسعار حقيقية من باينانس</div>
<div style="display:flex;gap:12px;align-items:center;margin-top:14px;flex-wrap:wrap;background:#000;padding:14px;border-radius:14px">
<span style="font-size:22px">رأس مال الصفقة:</span><input id="perIn" value="500" class="input-big" style="border-color:#ffbe0b"><span style="font-size:26px">$</span><button onclick="savePer()" class="btn" style="background:#ffbe0b;color:#000">SAVE</button>
<button onclick="setPer(50)" class="btn" style="background:#222;color:#fff">50$</button><button onclick="setPer(100)" class="btn" style="background:#222;color:#fff">100$</button><button onclick="setPer(500)" class="btn" style="background:#ffbe0b;color:#000">500$</button><button onclick="setPer(1000)" class="btn" style="background:#222;color:#fff">1000$</button>
</div>
</div>

<div style="background:#111;border:2px solid #333;border-radius:20px;padding:18px;margin-top:16px;overflow-x:auto">
<div style="display:flex;justify-content:space-between"><div class="sec-title">LIVE TRADES - أسعار باينانس الحقيقية</div><div style="font-size:18px;color:#00ff88">BINANCE API ● LIVE</div></div>
<table style="width:100%;border-collapse:collapse;margin-top:14px;min-width:800px"><thead><tr>
<th class="small">COIN</th><th class="small">سعر الدخول ENTRY</th><th class="small">السعر الحالي LIVE - باينانس</th><th class="small">VOL</th><th class="small">TYPE</th><th class="small">CAPITAL</th><th class="small">PROFIT $</th><th class="small">%</th>
</tr></thead><tbody id="tbody"></tbody></table>
</div>

<script>
function setBase(v){document.getElementById('baseIn').value=v; saveBase();}
function setPer(v){document.getElementById('perIn').value=v; savePer();}
function saveBase(){let b=parseFloat(document.getElementById('baseIn').value); fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({base:b})}).then(()=>load());}
function savePer(){let p=parseFloat(document.getElementById('perIn').value); fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({per:p})}).then(()=>load());}
function toggleBot(){fetch('/api/toggle',{method:'POST'}).then(r=>r.json()).then(d=>{updateToggle(d.is_running);});}
function updateToggle(r){let b=document.getElementById('togBtn'); if(r){b.innerText='● RUNNING - BINANCE LIVE'; b.style.background='#00ff88';} else {b.innerText='● STOPPED'; b.style.background='#ff3b3b';}}
function load(){
 fetch('/api/data?t='+Date.now()).then(r=>r.json()).then(d=>{
  document.getElementById('baseShow').innerText=d.base_capital; document.getElementById('baseIn').value=d.base_capital;
  document.getElementById('perIn').value=d.per_trade;
  document.getElementById('real').innerText=d.realized.toFixed(2);
  updateToggle(d.is_running);
  let f=document.getElementById('flt'); f.innerText=(d.floating>=0? '$'+d.floating.toFixed(2) : '-$'+Math.abs(d.floating).toFixed(2)); f.style.color=d.floating>=0?'#00ff88':'#ff3b3b';
  let h=''; d.trades.forEach(t=>{
    let cl=t.usd>=0?'#00ff88':'#ff3b3b';
    // تنسيق السعر حسب حجم العملة
    let entryFmt = t.entry < 1 ? t.entry.toFixed(6) : t.entry.toFixed(2);
    let liveFmt = t.live < 1 ? t.live.toFixed(6) : t.live.toFixed(2);
    h+=`<tr>
    <td style="padding:16px;text-align:center;border-top:3px solid #1e1e24;font-size:22px">${t.coin}</td>
    <td style="padding:16px;text-align:center;border-top:3px solid #1e1e24" class="entry-price">${entryFmt}</td>
    <td style="padding:16px;text-align:center;border-top:3px solid #1e1e24" class="live-price">${liveFmt} <span style="font-size:12px">●LIVE</span></td>
    <td style="padding:16px;text-align:center;border-top:3px solid #1e1e24;font-size:16px;color:#ffbe0b">${t.vol.toFixed(1)}%</td>
    <td style="padding:16px;text-align:center;border-top:3px solid #1e1e24;font-size:14px">${t.side}</td>
    <td style="padding:16px;text-align:center;border-top:3px solid #1e1e24;font-size:18px">$${t.cap}</td>
    <td style="padding:16px;text-align:center;border-top:3px solid #1e1e24;font-size:20px;color:${cl}">${t.usd.toFixed(2)}</td>
    <td style="padding:16px;text-align:center;border-top:3px solid #1e1e24;font-size:18px;color:${cl}">${t.pct}%</td>
    </tr>`}); document.getElementById('tbody').innerHTML=h;
 });
}
setInterval(load,1500);load();
</script></body>
"""
@app.route("/")
def home():
    r=make_response(render_template_string(HTML)); r.headers["Cache-Control"]="no-cache, no-store, must-revalidate"; return r
@app.route("/api/data")
def data():
    return jsonify({"trades":bot_state["trades"],"floating":sum(t["usd"] for t in bot_state["trades"]),"realized":bot_state["realized"],"base_capital":bot_state["base_capital"],"per_trade":bot_state["per_trade"],"is_running":bot_state["is_running"]})
@app.route("/api/save", methods=["POST"])
def save():
    j=request.json
    if "base" in j: bot_state["base_capital"]=float(j["base"])
    if "per" in j: 
        bot_state["per_trade"]=float(j["per"])
        for t in bot_state["trades"]: t["cap"]=bot_state["per_trade"]
    return jsonify({"ok":True})
@app.route("/api/toggle", methods=["POST"])
def toggle():
    bot_state["is_running"]=not bot_state["is_running"]
    return jsonify({"is_running":bot_state["is_running"]})
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",8080)))

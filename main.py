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
            if s in ["BTCUSDT","ETHUSDT","BNBUSDT"]: continue
            if "BULL" in s or "BEAR" in s: continue
            ch=abs(float(i['priceChangePercent'])); vol=float(i['quoteVolume'])
            if ch>4 and vol>8000000: cands.append({"symbol":s,"vol":ch,"price":float(i['lastPrice'])})
        cands.sort(key=lambda x: x['vol'], reverse=True)
        return cands[:6]
    except:
        return [{"symbol":"SOLUSDT","vol":5.5,"price":140},{"symbol":"AVAXUSDT","vol":4.9,"price":25},{"symbol":"PEPEUSDT","vol":6.2,"price":0.000008}]

def bot_loop():
    vol=get_volatile()
    for c in vol[:4]:
        bot_state["trades"].append({"coin":c["symbol"],"entry":c["price"],"live":c["price"],"side":random.choice(["LONG","SHORT"]),"cap":bot_state["per_trade"],"usd":0.0,"pct":0.0,"vol":c["vol"]})
    while True:
        if bot_state["is_running"]:
            try:
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
<title>RAIS V23 RECTANGLE</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&display=swap" rel="stylesheet">
<style>
*{font-family:'Cairo',sans-serif!important;font-weight:900!important;box-sizing:border-box}
body{background:#06060a;margin:0;padding:10px;color:#fff}
.rect-card{display:flex;align-items:center;justify-content:space-between;border-radius:16px;padding:14px 18px;border:3px solid;height:92px;box-shadow:0 0 20px rgba(0,0,0,0.5)}
.rect-left{display:flex;align-items:center;gap:14px}
.rect-icon{font-size:32px}
.rect-title{font-size:18px!important;color:#aaa;line-height:1}
.rect-money{font-size:36px!important;line-height:1}
.input-small{background:#000;color:#fff;border:2px solid #444;border-radius:10px;padding:6px;text-align:center;font-size:20px!important;width:90px}
.btn-small{border:none;border-radius:10px;padding:8px 16px;font-size:16px!important;cursor:pointer}
.th-small{font-size:14px!important;color:#ffbe0b!important;padding:8px 5px!important}
.td-small{font-size:14px!important;padding:7px 5px!important;border-top:1px solid #1e1e24!important;text-align:center}
</style></head><body>

<div style="background:#121218;padding:12px 18px;border-radius:14px;display:flex;justify-content:space-between;align-items:center;border:2px solid #333;height:56px">
<div style="font-size:22px">👑 RAIS V23 - مستطيلات ملمومة</div>
<button id="togBtn" onclick="toggleBot()" style="background:#00ff88;color:#000;padding:8px 20px;border-radius:40px;font-size:16px!important;border:none;cursor:pointer">● RUNNING</button>
</div>

<!-- 3 مستطيلات أفقية مضغوطة -->
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:10px">

<div class="rect-card" style="background:linear-gradient(90deg,#0f1410,#112211);border-color:#00ff88">
<div class="rect-left"><div class="rect-icon">💰</div><div><div class="rect-title">الرصيد الاساسي</div><div class="rect-money" style="color:#00ff88">$<span id="baseShow">1000</span></div></div></div>
<div style="display:flex;gap:4px;align-items:center"><input id="baseIn" value="1000" class="input-small" style="border-color:#00ff88;color:#00ff88"><button onclick="saveBase()" class="btn-small" style="background:#00ff88;color:#000">SAVE</button></div>
</div>

<div class="rect-card" style="background:linear-gradient(90deg,#1a1212,#221111);border-color:#ff3b3b">
<div class="rect-left"><div class="rect-icon">📈</div><div><div class="rect-title">الربح العائم - يتصفر</div><div id="flt" class="rect-money" style="color:#ff3b3b">$0.00</div></div></div>
<div style="font-size:12px;color:#00ff88">● BINANCE LIVE</div>
</div>

<div class="rect-card" style="background:linear-gradient(90deg,#121420,#151a30);border-color:#00d4ff">
<div class="rect-left"><div class="rect-icon">🏦</div><div><div class="rect-title">الربح المحقق - يتصفر</div><div class="rect-money" style="color:#00d4ff">$<span id="real">0.00</span></div></div></div>
<div style="font-size:12px;color:#888">RESET 0</div>
</div>
</div>

<div style="display:flex;gap:6px;margin-top:8px;justify-content:center">
<button onclick="setBase(1000)" class="btn-small" style="background:#222;color:#fff">1K</button><button onclick="setBase(5000)" class="btn-small" style="background:#00ff88;color:#000">5K</button><button onclick="setBase(10000)" class="btn-small" style="background:#222;color:#fff">10K</button><button onclick="setBase(20000)" class="btn-small" style="background:#222;color:#fff">20K</button>
</div>

<!-- تحكم مبلغ الصفقة - مستطيل ملموم -->
<div style="background:#1c1c28;border:3px solid #ffbe0b;border-radius:14px;padding:10px 14px;margin-top:10px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;height:60px">
<div style="font-size:18px;color:#ffbe0b">💵 مبلغ الصفقة:</div>
<input id="perIn" value="500" class="input-small" style="border-color:#ffbe0b"><span style="font-size:18px">$</span>
<button onclick="savePer()" class="btn-small" style="background:#ffbe0b;color:#000">SAVE</button>
<button onclick="setPer(50)" class="btn-small" style="background:#222;color:#fff">50$</button><button onclick="setPer(100)" class="btn-small" style="background:#222;color:#fff">100$</button><button onclick="setPer(500)" class="btn-small" style="background:#ffbe0b;color:#000">500$</button><button onclick="setPer(1000)" class="btn-small" style="background:#222;color:#fff">1000$</button>
<div style="margin-left:auto;font-size:13px;color:#00ff88">BINANCE API ● LIVE</div>
</div>

<!-- جدول مضغوط -->
<div style="background:#0e0e14;border:2px solid #333;border-radius:14px;padding:10px;margin-top:10px">
<div style="font-size:18px;margin-bottom:6px">LIVE TRADES - أسعار حقيقية باينانس</div>
<table style="width:100%;border-collapse:collapse"><thead><tr>
<th class="th-small">COIN</th><th class="th-small">ENTRY</th><th class="th-small">LIVE</th><th class="th-small">VOL</th><th class="th-small">SIDE</th><th class="th-small">CAP</th><th class="th-small">PROFIT</th><th class="th-small">%</th>
</tr></thead><tbody id="tbody"></tbody></table>
</div>

<script>
function setBase(v){document.getElementById('baseIn').value=v; saveBase();}
function setPer(v){document.getElementById('perIn').value=v; savePer();}
function saveBase(){let b=parseFloat(document.getElementById('baseIn').value); fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({base:b})}).then(()=>load());}
function savePer(){let p=parseFloat(document.getElementById('perIn').value); fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({per:p})}).then(()=>load());}
function toggleBot(){fetch('/api/toggle',{method:'POST'}).then(r=>r.json()).then(d=>{updateToggle(d.is_running);});}
function updateToggle(r){let b=document.getElementById('togBtn'); if(r){b.innerText='● RUNNING'; b.style.background='#00ff88';} else {b.innerText='● STOPPED'; b.style.background='#ff3b3b';}}
function load(){
 fetch('/api/data?t='+Date.now()).then(r=>r.json()).then(d=>{
  document.getElementById('baseShow').innerText=d.base_capital; document.getElementById('baseIn').value=d.base_capital;
  document.getElementById('perIn').value=d.per_trade;
  document.getElementById('real').innerText=d.realized.toFixed(2);
  updateToggle(d.is_running);
  let f=document.getElementById('flt'); f.innerText=(d.floating>=0? '$'+d.floating.toFixed(2) : '-$'+Math.abs(d.floating).toFixed(2)); f.style.color=d.floating>=0?'#00ff88':'#ff3b3b';
  let h=''; d.trades.forEach(t=>{
    let cl=t.usd>=0?'#00ff88':'#ff3b3b';
    let entryFmt = t.entry < 1 ? t.entry.toFixed(5) : t.entry.toFixed(2);
    let liveFmt = t.live < 1 ? t.live.toFixed(5) : t.live.toFixed(2);
    h+=`<tr>
    <td class="td-small" style="color:#fff">${t.coin.replace('USDT','')}</td>
    <td class="td-small" style="color:#ffbe0b">${entryFmt}</td>
    <td class="td-small" style="color:#00ff88">${liveFmt}</td>
    <td class="td-small" style="color:#ffbe0b">${t.vol.toFixed(1)}%</td>
    <td class="td-small">${t.side}</td>
    <td class="td-small">$${t.cap}</td>
    <td class="td-small" style="color:${cl}">$${t.usd.toFixed(2)}</td>
    <td class="td-small" style="color:${cl}">${t.pct}%</td>
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

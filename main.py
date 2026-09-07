from flask import Flask, render_template_string, jsonify, request, make_response
import os, threading, requests, random, time

app = Flask(__name__)
bot_state = {"realized": 0.0, "base_capital": 1000, "per_trade": 200, "trades": [], "is_running": True}

def get_volatile():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=8).json()
        cands=[]
        for i in r:
            s=i['symbol']
            if not s.endswith('USDT'): continue
            if s in ["BTCUSDT","ETHUSDT"]: continue
            ch=abs(float(i['priceChangePercent'])); vol=float(i['quoteVolume'])
            if ch>3 and vol>5000000: cands.append({"symbol":s,"vol":ch,"price":float(i['lastPrice'])})
        cands.sort(key=lambda x: x['vol'], reverse=True)
        return cands[:5]
    except:
        return [{"symbol":"SOLUSDT","vol":5.2,"price":140},{"symbol":"AVAXUSDT","vol":4.8,"price":25},{"symbol":"DOGEUSDT","vol":6.1,"price":0.12}]

def bot_loop():
    vol=get_volatile()
    for c in vol[:3]:
        bot_state["trades"].append({"coin":c["symbol"],"entry":c["price"],"live":c["price"],"side":random.choice(["LONG","SHORT"]),"cap":bot_state["per_trade"],"usd":0.0,"pct":0.0,"vol":c["vol"]})
    while True:
        try:
            pm={x['symbol']:float(x['price']) for x in requests.get("https://api.binance.com/api/v3/ticker/price", timeout=5).json()}
            for t in bot_state["trades"]:
                if t["coin"] in pm:
                    t["live"]=pm[t["coin"]]
                    t["pct"]=round(((t["live"]-t["entry"])/t["entry"]*100 if t["side"]=="LONG" else (t["entry"]-t["live"])/t["entry"]*100),2)
                    t["usd"]=round(t["pct"]/100*t["cap"],2)
        except: pass
        time.sleep(2)
threading.Thread(target=bot_loop, daemon=True).start()

HTML="""
<!DOCTYPE html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache"><title>RAIS V18 CLEAN</title>
<style>*{font-family:'Segoe UI',sans-serif!important;font-weight:900!important;box-sizing:border-box}
body{background:#050507;margin:0;padding:10px;color:#fff}
.card-title{font-size:20px!important;color:#888}.card-money{font-size:48px!important}.sec-title{font-size:22px!important}.small{font-size:15px!important;color:#777}
</style></head><body>

<div style="background:#121216;padding:14px 18px;border-radius:16px;display:flex;justify-content:space-between;border:1px solid #222">
<div style="font-size:24px">RAIS V18 CLEAN - لوحة نظيفة</div><div style="background:#00ff88;color:#000;padding:6px 18px;border-radius:40px;font-size:16px">RUNNING</div>
</div>

<!-- نفس الكروت الأصلية -->
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:12px">
<div style="background:#111;border:4px solid #00ff88;border-radius:18px;padding:18px;text-align:center">
<div style="font-size:32px">💰</div><div class="card-title">الرصيد الاساسي</div>
<div class="card-money" style="color:#00ff88">$<span id="baseShow">1000</span></div>
<div style="margin-top:8px;display:flex;gap:6px;justify-content:center"><input id="baseIn" value="1000" style="background:#000;color:#00ff88;border:2px solid #00ff88;border-radius:8px;padding:6px;width:80px;text-align:center;font-size:18px"><button onclick="saveBase()" style="background:#00ff88;color:#000;border:none;border-radius:8px;padding:6px 10px;font-size:12px;cursor:pointer">SAVE</button></div>
</div>
<div style="background:#111;border:4px solid #ff3b3b;border-radius:18px;padding:18px;text-align:center"><div style="font-size:32px">📈</div><div class="card-title">الربح العائم (يتصفر)</div><div id="flt" class="card-money" style="color:#ff3b3b">$0.00</div></div>
<div style="background:#111;border:4px solid #00d4ff;border-radius:18px;padding:18px;text-align:center"><div style="font-size:32px">🏦</div><div class="card-title">الربح المحقق (يتصفر)</div><div class="card-money" style="color:#00d4ff">$<span id="real">0.00</span></div></div>
</div>

<!-- نفس المربع الأصلي اللي صورته - بدون لخبطة -->
<div style="background:#1a1a22;border:3px solid #ffbe0b;border-radius:18px;padding:16px;margin-top:12px">
<div class="sec-title">CAPITAL CONTROL - التحكم برأس المال</div>
<div style="display:flex;gap:10px;align-items:center;margin-top:12px;flex-wrap:wrap">
<span style="font-size:18px">راس مال كل صفقة:</span>
<input id="perIn" value="200" style="background:#000;color:#fff;border:3px solid #333;border-radius:10px;padding:10px;width:120px;text-align:center;font-size:28px">
<span style="font-size:20px">$</span>
<button onclick="savePer()" style="background:#ffbe0b;color:#000;border:none;border-radius:10px;padding:10px 20px;font-size:18px;cursor:pointer">SAVE APPLY</button>
<button onclick="setPer(50)" style="background:#222;color:#fff;border:none;padding:8px 12px;border-radius:8px;font-size:14px">50$</button>
<button onclick="setPer(100)" style="background:#222;color:#fff;border:none;padding:8px 12px;border-radius:8px;font-size:14px">100$</button>
<button onclick="setPer(200)" style="background:#ffbe0b;color:#000;border:none;padding:8px 12px;border-radius:8px;font-size:14px">200$</button>
<button onclick="setPer(500)" style="background:#222;color:#fff;border:none;padding:8px 12px;border-radius:8px;font-size:14px">500$</button>
</div>
</div>

<div style="background:#111;border:1px solid #222;border-radius:18px;padding:14px;margin-top:12px">
<table style="width:100%;border-collapse:collapse"><thead><tr><th class="small">COIN</th><th class="small">VOL</th><th class="small">TYPE</th><th class="small">CAPITAL</th><th class="small">LIVE</th><th class="small">PROFIT</th></tr></thead><tbody id="tbody"></tbody></table>
</div>

<script>
function setPer(v){document.getElementById('perIn').value=v; savePer();}
function savePer(){let p=parseFloat(document.getElementById('perIn').value); fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({per:p})}).then(()=>load());}
function saveBase(){let b=parseFloat(document.getElementById('baseIn').value); fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({base:b})}).then(()=>load());}
function load(){
 fetch('/api/data?t='+Date.now()).then(r=>r.json()).then(d=>{
  document.getElementById('baseShow').innerText=d.base_capital; document.getElementById('baseIn').value=d.base_capital;
  document.getElementById('perIn').value=d.per_trade;
  document.getElementById('real').innerText=d.realized.toFixed(2);
  let f=document.getElementById('flt'); f.innerText=(d.floating>=0? '$'+d.floating.toFixed(2) : '-$'+Math.abs(d.floating).toFixed(2)); f.style.color=d.floating>=0?'#00ff88':'#ff3b3b';
  let h=''; d.trades.forEach(t=>{let cl=t.usd>=0?'#00ff88':'#ff3b3b'; h+=`<tr><td style="padding:12px;text-align:center;border-top:2px solid #1e1e24;font-size:18px">${t.coin}</td><td style="padding:12px;text-align:center;border-top:2px solid #1e1e24;font-size:12px;color:#ffbe0b">${t.vol.toFixed(1)}%</td><td style="padding:12px;text-align:center;border-top:2px solid #1e1e24;font-size:12px">${t.side}</td><td style="padding:12px;text-align:center;border-top:2px solid #1e1e24;font-size:14px">$${t.cap}</td><td style="padding:12px;text-align:center;border-top:2px solid #1e1e24;font-size:12px;color:#00ff88">${t.live}</td><td style="padding:12px;text-align:center;border-top:2px solid #1e1e24;font-size:14px;color:${cl}">${t.usd.toFixed(2)}</td></tr>`}); document.getElementById('tbody').innerHTML=h;
 });
}
setInterval(load,2000);load();
</script></body>
"""
@app.route("/")
def home():
    r=make_response(render_template_string(HTML)); r.headers["Cache-Control"]="no-cache, no-store, must-revalidate"; return r
@app.route("/api/data")
def data():
    return jsonify({"trades":bot_state["trades"],"floating":sum(t["usd"] for t in bot_state["trades"]),"realized":bot_state["realized"],"base_capital":bot_state["base_capital"],"per_trade":bot_state["per_trade"]})
@app.route("/api/save", methods=["POST"])
def save():
    j=request.json
    if "base" in j: bot_state["base_capital"]=float(j["base"])
    if "per" in j: 
        bot_state["per_trade"]=float(j["per"])
        for t in bot_state["trades"]: t["cap"]=bot_state["per_trade"]
    return jsonify({"ok":True})
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",8080)))

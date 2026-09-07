from flask import Flask, render_template_string, jsonify, request, make_response
import os, time, threading, requests, random

app = Flask(__name__)
bot_state = {"is_running": True, "trades": [], "realized_profit": 32.44, "capital_per_trade": 200}
COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]

def get_prices():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price", timeout=5).json()
        return {x['symbol']: float(x['price']) for x in r}
    except: return {"BTCUSDT": 79489, "ETHUSDT": 2500, "SOLUSDT": 140, "BNBUSDT": 600}

def bot_loop():
    while True:
        if bot_state["is_running"]:
            p = get_prices()
            if not bot_state["trades"] and p:
                for c in COINS[:3]:
                    if c in p:
                        bot_state["trades"].append({"coin":c,"entry":p[c],"live":p[c],"side":random.choice(["LONG","SHORT"]),"cap":bot_state["capital_per_trade"],"usd":0.0,"pct":0.0})
            for t in bot_state["trades"]:
                if t["coin"] in p:
                    t["live"] = p[t["coin"]]
                    t["pct"] = round(((t["live"]-t["entry"])/t["entry"]*100 if t["side"]=="LONG" else (t["entry"]-t["live"])/t["entry"]*100),2)
                    t["usd"] = round(t["pct"]/100 * t["cap"],2)
        time.sleep(2)
threading.Thread(target=bot_loop, daemon=True).start()

HTML = """
<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<title>RAIS V12 FULL UNIFIED</title>
<style>
*{font-family: 'Segoe UI', Tahoma, sans-serif!important; font-weight:900!important; box-sizing:border-box}
body{background:#050507;margin:0;padding:10px;color:#fff}
.card-title{font-size:20px!important;color:#888}
.card-money{font-size:48px!important;line-height:1.1}
.sec-title{font-size:26px!important}
.small{font-size:18px!important;color:#777}
.money-green{color:#00ff88}.money-red{color:#ff3b3b}.money-blue{color:#00d4ff}
</style></head>
<body>

<div style="background:#121216;padding:16px 20px;border-radius:16px;display:flex;justify-content:space-between;align-items:center;border:1px solid #222">
<div style="font-size:28px">RAIS V12 FULL - خط موحد كامل</div>
<div style="background:#00ff88;color:#000;padding:8px 20px;border-radius:40px;font-size:20px">RUNNING</div>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:12px">
<div style="background:#111;border:4px solid #00ff88;border-radius:18px;padding:20px;text-align:center"><div style="font-size:36px">💰</div><div class="card-title">الرصيد الاساسي</div><div class="card-money money-green">$1000</div></div>
<div style="background:#111;border:4px solid #ff3b3b;border-radius:18px;padding:20px;text-align:center"><div style="font-size:36px">📈</div><div class="card-title">الرصيد العائم</div><div id="flt" class="card-money money-red">$0.00</div></div>
<div style="background:#111;border:4px solid #00d4ff;border-radius:18px;padding:20px;text-align:center"><div style="font-size:36px">🏦</div><div class="card-title">الربح المحقق</div><div class="card-money money-blue">$<span id="real">32.44</span></div></div>
</div>

<div style="background:#1a1a22;border:3px solid #ffbe0b;border-radius:18px;padding:20px;margin-top:12px">
<div class="sec-title">CAPITAL CONTROL - التحكم براس المال</div>
<div style="display:flex;gap:10px;align-items:center;margin-top:12px;flex-wrap:wrap">
<span style="font-size:18px">راس مال كل صفقة:</span>
<input id="capIn" value="200" style="background:#000;color:#fff;border:3px solid #333;border-radius:12px;padding:12px;width:140px;text-align:center;font-size:36px">
<span style="font-size:24px">$</span>
<button onclick="saveCap()" style="background:#ffbe0b;color:#000;border:none;border-radius:12px;padding:12px 22px;font-size:20px;cursor:pointer">SAVE APPLY</button>
<button onclick="setCap(50)" style="background:#222;color:#fff;border:none;padding:10px 16px;border-radius:10px;font-size:18px">50$</button>
<button onclick="setCap(100)" style="background:#222;color:#fff;border:none;padding:10px 16px;border-radius:10px;font-size:18px">100$</button>
<button onclick="setCap(200)" style="background:#ffbe0b;color:#000;border:none;padding:10px 16px;border-radius:10px;font-size:18px">200$</button>
<button onclick="setCap(500)" style="background:#222;color:#fff;border:none;padding:10px 16px;border-radius:10px;font-size:18px">500$</button>
</div>
</div>

<div style="background:#111;border:1px solid #222;border-radius:18px;padding:16px;margin-top:12px">
<div style="display:flex;gap:10px;margin-bottom:14px">
<button id="tog" onclick="toggleBot()" style="background:#ff1a1a;color:#fff;border:none;border-radius:12px;padding:12px 24px;font-size:20px;cursor:pointer">STOP BOT</button>
<button onclick="closeAll()" style="background:#fff;color:#000;border:none;border-radius:12px;padding:12px 24px;font-size:20px;cursor:pointer;width:100%">LOCK & COLLECT PROFIT</button>
</div>
<div class="sec-title" style="margin-bottom:10px">LIVE TRADES - راس المال $<span id="capShow">200</span> لكل صفقة</div>
<table style="width:100%;border-collapse:collapse"><thead><tr>
<th class="small">COIN</th><th class="small">TYPE</th><th class="small">CAPITAL</th><th class="small">ENTRY</th><th class="small">LIVE PRICE</th><th class="small">PROFIT $</th><th class="small">%</th>
</tr></thead><tbody id="tbody"></tbody></table>
</div>

<script>
function setCap(v){document.getElementById('capIn').value=v; saveCap();}
function saveCap(){
 let v=document.getElementById('capIn').value;
 fetch('/api/set_capital',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capital:parseFloat(v)})}).then(()=>load());
}
function load(){
 fetch('/api/data?t='+Date.now()).then(r=>r.json()).then(d=>{
  document.getElementById('capIn').value=d.capital_per_trade;
  document.getElementById('capShow').innerText=d.capital_per_trade;
  document.getElementById('real').innerText=d.realized_profit.toFixed(2);
  let f=document.getElementById('flt');
  f.innerText=(d.floating>=0? '$'+d.floating.toFixed(2) : '-$'+Math.abs(d.floating).toFixed(2));
  f.style.color=d.floating>=0?'#00ff88':'#ff3b3b';
  let h=''; d.trades.forEach(t=>{
    let cl=t.usd>=0?'#00ff88':'#ff3b3b';
    h+=`<tr>
    <td style="padding:16px;text-align:center;border-top:2px solid #1e1e24;font-size:22px">${t.coin}</td>
    <td style="padding:16px;text-align:center;border-top:2px solid #1e1e24;font-size:18px">${t.side}</td>
    <td style="padding:16px;text-align:center;border-top:2px solid #1e1e24;font-size:20px">$${t.cap}</td>
    <td style="padding:16px;text-align:center;border-top:2px solid #1e1e24;font-size:18px">${t.entry.toFixed(2)}</td>
    <td style="padding:16px;text-align:center;border-top:2px solid #1e1e24;font-size:18px;color:#00ff88">${t.live.toFixed(2)}</td>
    <td style="padding:16px;text-align:center;border-top:2px solid #1e1e24;font-size:20px;color:${cl}">${t.usd>=0?'+':''}$${t.usd.toFixed(2)}</td>
    <td style="padding:16px;text-align:center;border-top:2px solid #1e1e24;font-size:20px;color:${cl}">${t.pct}%</td>
    </tr>`;
  });
  document.getElementById('tbody').innerHTML=h;
 });
}
function toggleBot(){fetch('/api/toggle',{method:'POST'}).then(()=>load())}
function closeAll(){fetch('/api/close',{method:'POST'}).then(()=>load())}
setInterval(load,2000);load();
</script>
</body></html>
"""

@app.route("/")
def home():
    resp = make_response(render_template_string(HTML))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp

@app.route("/api/data")
def data():
    floating = sum(t["usd"] for t in bot_state["trades"])
    return jsonify({"trades": bot_state["trades"], "floating": floating, "realized_profit": bot_state["realized_profit"], "capital_per_trade": bot_state["capital_per_trade"]})

@app.route("/api/set_capital", methods=["POST"])
def set_cap():
    bot_state["capital_per_trade"] = float(request.json.get("capital",200))
    for t in bot_state["trades"]: t["cap"] = bot_state["capital_per_trade"]
    return jsonify({"ok":True})

@app.route("/api/toggle", methods=["POST"])
def tog():
    bot_state["is_running"] = not bot_state["is_running"]
    return jsonify({"ok":True})

@app.route("/api/close", methods=["POST"])
def close():
    f = sum(t["usd"] for t in bot_state["trades"])
    bot_state["realized_profit"] += f
    bot_state["trades"] = []
    return jsonify({"ok":True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))

from flask import Flask, render_template_string, jsonify, request
import random, time, threading, requests, os

app = Flask(__name__)
bot_state = {"is_running": True, "trades": [], "realized_profit": 32.44, "capital_per_trade": 200}
COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]

def get_real_prices():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price", timeout=5).json()
        return {item['symbol']: float(item['price']) for item in r}
    except: return {}

def bot_loop():
    real = get_real_prices()
    if not bot_state["trades"] and real:
        for coin in COINS[:3]:
            if coin in real:
                bot_state["trades"].append({"coin":coin,"entry_price":real[coin],"current_price":real[coin],"side":random.choice(["LONG","SHORT"]),"capital":bot_state["capital_per_trade"],"profit_usd":0.0,"profit_pct":0.0})
    while True:
        if bot_state["is_running"]:
            rp = get_real_prices()
            if rp:
                for t in bot_state["trades"]:
                    if t["coin"] in rp:
                        t["current_price"] = rp[t["coin"]]
                        t["profit_pct"] = round(((t["current_price"]-t["entry_price"])/t["entry_price"]*100 if t["side"]=="LONG" else (t["entry_price"]-t["current_price"])/t["entry_price"]*100),2)
                        t["profit_usd"] = round((t["profit_pct"]/100)*t["capital"],2)
        time.sleep(2)

threading.Thread(target=bot_loop, daemon=True).start()

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<title>V9.9 BIG</title>
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@900&display=swap" rel="stylesheet">
<style>
body{background:#050507;color:#fff;font-family:'Roboto',sans-serif!important;margin:0;padding:15px}
.header{background:#121216;padding:26px 32px;border-radius:22px;display:flex;justify-content:space-between;align-items:center;border:1px solid #222;margin-bottom:22px}
.header h1{font-size:42px!important;font-weight:900;margin:0}
.grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:22px;margin-bottom:22px}
.card{background:#111116;border-radius:32px;padding:30px;text-align:center}
.card.icon{font-size:70px!important}
.card.label{font-size:28px!important;color:#888;font-weight:900;margin:12px 0;display:block}
.card.money{font-size:72px!important;font-weight:900!important;line-height:1.1}
.control-panel{background:#1a1a22;border:4px solid #ffbe0b;border-radius:32px;padding:36px;margin-bottom:22px}
.control-panel h2{font-size:36px!important;margin:0 0 22px 0}
.input-box{padding:24px 32px;border-radius:20px;border:4px solid #333;background:#000;color:#fff;font-size:42px!important;font-weight:900;width:240px;text-align:center}
.btn{padding:22px 32px;border-radius:20px;border:none;font-weight:900;font-size:26px!important;cursor:pointer}
.btn-save{background:#ffbe0b;color:#000;font-size:28px!important}.btn-stop{background:#ff1a1a;color:#fff;width:320px;font-size:30px!important}.btn-start{background:#00ff88;color:#000;width:320px;font-size:30px!important}
.btn-lock{background:#fff;color:#000;width:100%;font-size:34px!important;padding:30px;margin-top:18px}
.table-wrap{background:#111116;border:2px solid #222;border-radius:32px;padding:36px}
table{width:100%;border-collapse:collapse} th{color:#777;font-size:24px!important;padding:22px 10px} td{padding:34px 14px;font-size:32px!important;font-weight:900;border-top:3px solid #1e1e24;text-align:center}
.pos{color:#00ff88}.neg{color:#ff3b3b}
</style>
</head>
<body>
<div class="header"><h1>RAIS V9.9 BIG FIX</h1><div id="status" style="font-size:32px!important;font-weight:900;background:#00ff88;color:#000;padding:16px 36px;border-radius:50px">RUNNING</div></div>

<div class="grid">
<div class="card" style="border:6px solid #00ff88"><div class="icon">💰</div><div class="label">الرصيد الأساسي</div><div class="money" style="color:#00ff88">$1000</div></div>
<div class="card" id="floatingCard" style="border:6px solid #ffbe0b"><div class="icon">📈</div><div class="label">الرصيد العائم</div><div class="money" id="floatingMoney">$0.00</div></div>
<div class="card" style="border:6px solid #00d4ff"><div class="icon">🏦</div><div class="label">الربح المحقق</div><div class="money" style="color:#00d4ff">$<span id="realized">0</span></div></div>
</div>

<div class="control-panel">
<h2>التحكم برأس المال - CAPITAL CONTROL</h2>
<div style="display:flex;gap:18px;align-items:center;flex-wrap:wrap">
<span style="font-size:28px;font-weight:900">رأس مال كل صفقة:</span>
<input type="text" inputmode="numeric" id="capitalInput" class="input-box" value="200">
<span style="font-size:36px;font-weight:900">$</span>
<button class="btn btn-save" onclick="saveCapital()">SAVE APPLY</button>
</div>
<div style="margin-top:20px;display:flex;gap:14px">
<button class="btn" style="background:#222;color:#fff" onclick="setCap(50)">50$</button>
<button class="btn" style="background:#222;color:#fff" onclick="setCap(100)">100$</button>
<button class="btn" style="background:#ffbe0b;color:#000" onclick="setCap(200)">200$</button>
<button class="btn" style="background:#222;color:#fff" onclick="setCap(500)">500$</button>
</div>
</div>

<div class="table-wrap">
<button id="toggleBtn" class="btn btn-stop" onclick="toggleBot()">STOP BOT</button>
<button class="btn btn-lock" onclick="closeAll()">LOCK & COLLECT PROFIT</button>
<h2 style="font-size:38px;margin:40px 0 18px 0">LIVE TRADES - CAPITAL $<span id="capDisplay">200</span> EACH</h2>
<table><thead><tr><th>COIN</th><th>TYPE</th><th>CAPITAL</th><th>ENTRY</th><th>LIVE PRICE</th><th>PROFIT $</th><th>%</th></tr></thead><tbody id="tradesBody"></tbody></table>
</div>

<script>
function setCap(v){document.getElementById('capitalInput').value=v; saveCapital();}
function saveCapital(){
  let v=document.getElementById('capitalInput').value;
  fetch('/api/set_capital',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capital:parseFloat(v)})}).then(r=>r.json()).then(d=>{
    document.getElementById('capDisplay').innerText=v;load();
  });
}
function load(){
fetch('/api/data?t='+Date.now()).then(r=>r.json()).then(d=>{
 document.getElementById('capitalInput').value=d.capital_per_trade;
 document.getElementById('capDisplay').innerText=d.capital_per_trade;
 document.getElementById('realized').innerText=d.realized_profit.toFixed(2);
 let floatingEl=document.getElementById('floatingMoney');
 let floatingCard=document.getElementById('floatingCard');
 let val=d.floating;
 floatingEl.innerText=(val>=0? '$'+val.toFixed(2) : '-$'+Math.abs(val).toFixed(2));
 if(val>0){floatingEl.style.color='#00ff88';floatingCard.style.borderColor='#00ff88';floatingCard.style.boxShadow='0 0 35px rgba(0,255,136,0.6)'}
 else if(val<0){floatingEl.style.color='#ff3b3b';floatingCard.style.borderColor='#ff3b3b';floatingCard.style.boxShadow='0 0 35px rgba(255,59,59,0.6)'}
 else{floatingEl.style.color='#ffbe0b';floatingCard.style.borderColor='#ffbe0b';floatingCard.style.boxShadow='none'}
 let html=''; d.trades.forEach(t=>{
  let cls=t.profit_usd>=0?'pos':'neg';
  html+=`<tr><td>${t.coin}</td><td>${t.side}</td><td>$${t.capital}</td><td>${t.entry_price.toFixed(2)}</td><td style="color:#00ff88">${t.current_price.toFixed(2)}</td><td class="${cls}">${t.profit_usd>=0?'+':''}$${t.profit_usd.toFixed(2)}</td><td class="${cls}">${t.profit_pct}%</td></tr>`;
 }); document.getElementById('tradesBody').innerHTML=html;
})
}
function toggleBot(){fetch('/api/toggle',{method:'POST'}).then(()=>load())}
function closeAll(){if(confirm('Close all?')){fetch('/api/close_all',{method:'POST'}).then(()=>load())}}
setInterval(load,2000);load();
</script>
</body>
</html>
"""

@app.route("/")
def home(): return render_template_string(HTML)
@app.route("/api/data")
def data():
    floating = sum(t["profit_usd"] for t in bot_state["trades"])
    return jsonify({"is_running": bot_state["is_running"], "trades": bot_state["trades"], "floating": floating, "realized_profit": bot_state["realized_profit"], "capital_per_trade": bot_state["capital_per_trade"]})
@app.route("/api/set_capital", methods=["POST"])
def set_capital():
    cap = request.json.get("capital", 200)
    bot_state["capital_per_trade"] = float(cap)
    return jsonify({"ok": True})
@app.route("/api/toggle", methods=["POST"])
def toggle():
    bot_state["is_running"] = not bot_state["is_running"]
    return jsonify({"ok": True})
@app.route("/api/close_all", methods=["POST"])
def close_all():
    floating = sum(t["profit_usd"] for t in bot_state["trades"])
    bot_state["realized_profit"] += floating
    bot_state["trades"] = []
    real = get_real_prices()
    for coin in COINS[:2]:
        if coin in real:
            bot_state["trades"].append({"coin":coin,"entry_price":real[coin],"current_price":real[coin],"side":random.choice(["LONG","SHORT"]),"capital":bot_state["capital_per_trade"],"profit_usd":0.0,"profit_pct":0.0})
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

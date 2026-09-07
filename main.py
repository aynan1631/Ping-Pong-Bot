from flask import Flask, render_template_string, jsonify
import random, time, threading, requests, os

app = Flask(__name__)
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "")
BALANCE_REAL = 1000.0

bot_state = {"is_running": True, "trades": [], "realized_profit": 32.44}
COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"]

# جلب الأسعار الحقيقية من بايننس
def get_real_prices():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price", timeout=5).json()
        prices = {item['symbol']: float(item['price']) for item in r}
        return prices
    except:
        return {}

def bot_loop():
    # صفقة بداية بسعر حقيقي
    real = get_real_prices()
    if not bot_state["trades"] and real:
        for coin in COINS[:2]:
            if coin in real:
                bot_state["trades"].append({
                    "coin": coin,
                    "entry_price": real[coin],
                    "current_price": real[coin],
                    "side": random.choice(["LONG", "SHORT"]),
                    "profit_usd": 0.0,
                    "profit_pct": 0.0
                })

    while True:
        if bot_state["is_running"]:
            real_prices = get_real_prices()
            if real_prices:
                for t in bot_state["trades"]:
                    if t["coin"] in real_prices:
                        t["current_price"] = real_prices[t["coin"]]
                        if t["side"] == "LONG":
                            t["profit_pct"] = round(((t["current_price"] - t["entry_price"]) / t["entry_price"]) * 100, 2)
                        else:
                            t["profit_pct"] = round(((t["entry_price"] - t["current_price"]) / t["entry_price"]) * 100, 2)
                        t["profit_usd"] = round(t["profit_pct"] * 5, 2) # كل 1% = 5 دولار

        time.sleep(3)

threading.Thread(target=bot_loop, daemon=True).start()

HTML = """
<!DOCTYPE html>
<html dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>V9.3 LIVE</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box} body{background:#08080a;color:#fff;font-family:'Cairo',sans-serif;margin:0;padding:20px}
.header{display:flex;justify-content:space-between;align-items:center;background:#121216;padding:15px 25px;border-radius:18px;margin-bottom:25px;border:1px solid #222}
.header h1{margin:0;font-size:24px}.live{color:#00ff88;font-size:14px;animation:blink 1s infinite}
@keyframes blink{0%{opacity:1}50%{opacity:0.3}}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-bottom:25px}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
.card{background:#121216;border:2px solid #222;border-radius:24px;padding:30px;text-align:center}
.card.money{font-size:40px;font-weight:900}
.table-card{background:#121216;border:1px solid #222;border-radius:24px;padding:25px}
table{width:100%;border-collapse:collapse} th{color:#555;font-size:14px;padding:16px} td{padding:20px 10px;font-size:18px;font-weight:800;border-top:1px solid #222;text-align:center}
.pos{color:#00ff88}.neg{color:#ff4d4d}
.btn{flex:1;padding:18px;border-radius:16px;border:none;font-family:'Cairo';font-weight:900;font-size:19px;cursor:pointer}
.btn-stop{background:#ff2a2a;color:#fff}.btn-start{background:#00ff88;color:#000}.btn-lock{background:#fff;color:#000;width:100%;font-size:20px;margin-top:10px}
.status{font-size:18px;font-weight:900;padding:8px 18px;border-radius:30px}.status.on{background:#00ff88;color:#000}.status.off{background:#ff2a2a;color:#fff}
</style>
</head>
<body>
<div class="header">
<h1>👑 لوحة الريس V9.3 <span class="live">● LIVE من بايننس</span></h1>
<div id="status" class="status on">🟢 شغال</div>
</div>
<div class="grid">
<div class="card" style="border-color:#00ff88"><div>💰 الأساسي</div><div class="money" style="color:#00ff88">$1000</div></div>
<div class="card" style="border-color:#ffb700"><div>📈 العائم</div><div class="money" style="color:#ffb700">$<span id="floating">0</span></div></div>
<div class="card" style="border-color:#00b7ff"><div>🏦 المحقق</div><div class="money" style="color:#00b7ff">$<span id="realized">0</span></div></div>
</div>
<div class="table-card">
<button id="toggleBtn" class="btn btn-stop" onclick="toggleBot()">إيقاف</button>
<button class="btn btn-lock" onclick="closeAll()">🔒 قفل الصفقات</button>
<h2>💎 الصفقات الحية - أسعار حقيقية</h2>
<table><thead><tr><th>العملة</th><th>النوع</th><th>دخول</th><th>حالي LIVE</th><th>ربح $</th><th>%</th></tr></thead><tbody id="tradesBody"></tbody></table>
</div>
<script>
function load(){
fetch('/api/data').then(r=>r.json()).then(d=>{
 document.getElementById('status').innerText = d.is_running? '🟢 شغال' : '🔴 متوقف';
 document.getElementById('toggleBtn').innerText = d.is_running? '⏸️ إيقاف' : '▶️ تشغيل';
 document.getElementById('floating').innerText = d.floating.toFixed(2);
 document.getElementById('realized').innerText = d.realized_profit.toFixed(2);
 let html=''; d.trades.forEach(t=>{
  let cls=t.profit_usd>=0?'pos':'neg';
  html+=`<tr><td>${t.coin}</td><td>${t.side}</td><td>${t.entry_price}</td><td style="color:#00ff88">${t.current_price}</td><td class="${cls}">$${t.profit_usd}</td><td class="${cls}">${t.profit_pct}%</td></tr>`;
 }); document.getElementById('tradesBody').innerHTML=html;
})
}
function toggleBot(){fetch('/api/toggle',{method:'POST'}).then(()=>load())}
function closeAll(){if(confirm('تقفل؟')){fetch('/api/close_all',{method:'POST'}).then(()=>load())}}
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
    return jsonify({"is_running": bot_state["is_running"], "trades": bot_state["trades"], "floating": floating, "realized_profit": bot_state["realized_profit"]})

@app.route("/api/toggle", methods=["POST"])
def toggle():
    bot_state["is_running"] = not bot_state["is_running"]
    return jsonify({"ok": True})

@app.route("/api/close_all", methods=["POST"])
def close_all():
    floating = sum(t["profit_usd"] for t in bot_state["trades"])
    bot_state["realized_profit"] += floating
    bot_state["trades"] = []
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

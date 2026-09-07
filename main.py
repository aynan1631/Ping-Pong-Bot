from flask import Flask, render_template_string, jsonify
import random, time, threading, requests, os

app = Flask(__name__)

bot_state = {"is_running": True, "trades": [], "realized_profit": 45.8}

COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
CAPITAL_PER_TRADE = 200  # رأس مال كل صفقة 200$

def get_real_prices():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price", timeout=5).json()
        return {item['symbol']: float(item['price']) for item in r}
    except:
        return {}

def bot_loop():
    real = get_real_prices()
    if not bot_state["trades"] and real:
        for coin in COINS[:3]:
            if coin in real:
                bot_state["trades"].append({
                    "coin": coin,
                    "entry_price": real[coin],
                    "current_price": real[coin],
                    "side": random.choice(["LONG", "SHORT"]),
                    "capital": CAPITAL_PER_TRADE,
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
                            t["profit_pct"] = ((t["current_price"] - t["entry_price"]) / t["entry_price"]) * 100
                        else:
                            t["profit_pct"] = ((t["entry_price"] - t["current_price"]) / t["entry_price"]) * 100
                        t["profit_pct"] = round(t["profit_pct"], 2)
                        t["profit_usd"] = round((t["profit_pct"]/100) * t["capital"], 2)
        time.sleep(2)

threading.Thread(target=bot_loop, daemon=True).start()

HTML = """
<!DOCTYPE html>
<html dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>V9.4 BIG</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&display=swap" rel="stylesheet">
<style>
body{background:#050507;color:#fff;font-family:'Cairo',sans-serif;margin:0;padding:15px}
.header{background:linear-gradient(90deg,#121216,#1a1a22);padding:22px 30px;border-radius:20px;display:flex;justify-content:space-between;align-items:center;border:1px solid #222;margin-bottom:20px}
.header h1{font-size:32px;font-weight:900;margin:0}
.grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin-bottom:20px}
.card{background:#111116;border:3px solid #222;border-radius:28px;padding:35px;text-align:center}
.card .icon{font-size:50px}
.card .label{font-size:18px;color:#888;font-weight:800;margin:12px 0}
.card .money{font-size:52px;font-weight:900;line-height:1}
.table-wrap{background:#111116;border:1px solid #222;border-radius:28px;padding:30px}
table{width:100%;border-collapse:collapse}
th{color:#666;font-size:17px;padding:18px 10px;font-weight:900}
td{padding:24px 12px;font-size:21px;font-weight:900;border-top:2px solid #1e1e24;text-align:center}
.pos{color:#00ff88;font-size:22px} .neg{color:#ff3b3b;font-size:22px}
.capital-badge{background:#222;padding:8px 16px;border-radius:12px;color:#fff;font-size:18px}
.btn{padding:20px;border-radius:18px;border:none;font-family:'Cairo';font-weight:900;font-size:22px;cursor:pointer}
.btn-stop{background:#ff1a1a;color:#fff;width:220px}.btn-start{background:#00ff88;color:#000;width:220px}
.btn-lock{background:#fff;color:#000;width:100%;font-size:24px;padding:22px;margin-top:15px}
.live{color:#00ff88;font-size:16px;margin-right:15px}
</style>
</head>
<body>
<div class="header">
<h1>👑 لوحة الريس <span class="live">● LIVE بايننس</span></h1>
<div id="status" style="font-size:22px;font-weight:900;background:#00ff88;color:#000;padding:10px 22px;border-radius:40px">🟢 شغال</div>
</div>

<div class="grid">
<div class="card" style="border-color:#00ff88"><div class="icon">💰</div><div class="label">💰 الرصيد الأساسي</div><div class="money" style="color:#00ff88">$1000</div></div>
<div class="card" style="border-color:#ffbe0b"><div class="icon">📈</div><div class="label">📈 الرصيد العائم</div><div class="money" style="color:#ffbe0b">$<span id="floating">0</span></div></div>
<div class="card" style="border-color:#00d4ff"><div class="icon">🏦</div><div class="label">🏦 الربح المحقق</div><div class="money" style="color:#00d4ff">$<span id="realized">0</span></div></div>
</div>

<div class="table-wrap">
<div style="display:flex;gap:15px">
<button id="toggleBtn" class="btn btn-stop" onclick="toggleBot()">⏸️ إيقاف البوت</button>
</div>
<button class="btn btn-lock" onclick="closeAll()">🔒 قفل الصفقات وتحويل العائم إلى محقق</button>

<h2 style="font-size:30px;margin:35px 0 15px 0">💎 الصفقات الحية - رأس مال كل صفقة ${CAPITAL}$</h2>
<table>
<thead><tr><th>🪙 العملة</th><th>⚡ النوع</th><th>💵 رأس المال</th><th>🎯 دخول</th><th>💲 الحالي LIVE</th><th>💰 ربح $</th><th>📊 %</th></tr></thead>
<tbody id="tradesBody"></tbody>
</table>
</div>

<script>
function load(){
fetch('/api/data').then(r=>r.json()).then(d=>{
 document.getElementById('status').innerText = d.is_running ? '🟢 شغال' : '🔴 متوقف';
 document.getElementById('toggleBtn').innerText = d.is_running ? '⏸️ إيقاف البوت' : '▶️ تشغيل البوت';
 document.getElementById('floating').innerText = d.floating.toFixed(2);
 document.getElementById('realized').innerText = d.realized_profit.toFixed(2);
 let html='';
 d.trades.forEach(t=>{
  let cls=t.profit_usd>=0?'pos':'neg';
  html+=`<tr><td>${t.coin}</td><td>${t.side}</td><td><span class="capital-badge">$${t.capital}</span></td><td>${t.entry_price}</td><td style="color:#00ff88">${t.current_price}</td><td class="${cls}">$${t.profit_usd}</td><td class="${cls}">${t.profit_pct}%</td></tr>`;
 });
 document.getElementById('tradesBody').innerHTML=html;
})
}
function toggleBot(){fetch('/api/toggle',{method:'POST'}).then(()=>load())}
function closeAll(){if(confirm('تقفل الكل؟')){fetch('/api/close_all',{method:'POST'}).then(()=>load())}}
setInterval(load,2000);load();
</script>
</body>
</html>
"""

@app.route("/")
def home(): return render_template_string(HTML, CAPITAL=CAPITAL_PER_TRADE)

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

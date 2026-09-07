from flask import Flask, render_template_string, jsonify, request
import random, time, threading, requests, os

app = Flask(__name__)

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "")
BALANCE_REAL = 1000.0

bot_state = {
    "is_running": True,
    "trades": [],
    "realized_profit": 0.0
}

COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT"]

def bot_loop():
    while True:
        if bot_state["is_running"]:
            if len(bot_state["trades"]) < 6 and random.random() > 0.65:
                coin = random.choice(COINS)
                entry = random.uniform(100, 68000)
                trade = {
                    "coin": coin,
                    "entry_price": round(entry, 2),
                    "current_price": round(entry, 2),
                    "side": random.choice(["LONG", "SHORT"]),
                    "profit_usd": 0.0,
                    "profit_pct": 0.0
                }
                bot_state["trades"].append(trade)
                try:
                    if DISCORD_WEBHOOK:
                        requests.post(DISCORD_WEBHOOK, json={"content": f"🚀 فتح صفقة {trade['side']} {coin} دخول {trade['entry_price']}"}, timeout=3)
                except: pass

            for t in bot_state["trades"]:
                change = random.uniform(-1.2, 1.2)
                t["current_price"] = round(t["current_price"] * (1 + change/100), 2)
                if t["side"] == "LONG":
                    t["profit_pct"] = round(((t["current_price"] - t["entry_price"]) / t["entry_price"]) * 100, 2)
                else:
                    t["profit_pct"] = round(((t["entry_price"] - t["current_price"]) / t["entry_price"]) * 100, 2)
                t["profit_usd"] = round(t["profit_pct"] * 1.8, 2)
        time.sleep(2)

threading.Thread(target=bot_loop, daemon=True).start()

HTML_PAGE = """
<!DOCTYPE html>
<html dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>V9.1 ULTRA</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap" rel="stylesheet">
<style>
body{background:#070709;color:#fff;font-family:'Cairo',Tahoma;margin:0;padding:15px}
.top-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:15px;margin-bottom:20px}
@media(max-width:700px){.top-grid{grid-template-columns:1fr}}
.card{background:linear-gradient(145deg,#15151a,#0f0f12);border:1px solid #222;border-radius:22px;padding:22px;box-shadow:0 10px 30px rgba(0,0,0,0.5)}
.card h3{margin:0 0 10px 0;color:#888;font-size:13px;letter-spacing:1px}
.card .value{font-size:34px;font-weight:900}
.icon{font-size:28px;margin-bottom:8px}
.card-balance{border-color:#00ff88} .card-balance .value{color:#00ff88}
.card-floating{border-color:#ffaa00} .card-floating .value{color:#ffaa00}
.card-realized{border-color:#00aaff} .card-realized .value{color:#00aaff}
table{width:100%;border-collapse:collapse;margin-top:10px}
th{color:#666;font-size:13px;padding:14px 8px}
td{padding:16px 8px;font-size:16px;font-weight:700;border-top:1px solid #1d1d1d;text-align:center}
.profit-pos{color:#00ff88;text-shadow:0 0 10px rgba(0,255,136,0.4)} 
.profit-neg{color:#ff4d4d}
.btn{padding:16px 28px;border-radius:14px;border:none;font-weight:900;font-family:'Cairo';cursor:pointer;font-size:16px;transition:0.2s}
.btn-on{background:#00ff88;color:#000;box-shadow:0 0 20px rgba(0,255,136,0.4)} 
.btn-off{background:#ff2e2e;color:#fff}
.btn-close{background:#fff;color:#000;width:100%;margin-top:20px;font-size:18px}
.badge{padding:5px 12px;border-radius:20px;font-size:12px}
.badge-long{background:rgba(0,255,136,0.15);color:#00ff88}
.badge-short{background:rgba(255,77,77,0.15);color:#ff4d4d}
</style>
</head>
<body>
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
<h1 style="margin:0;font-size:28px">👑 لوحة الريس V9.1</h1>
<div><span id="statusDot"></span> <span id="statusText" style="font-weight:900;font-size:18px"></span></div>
</div>

<div class="top-grid">
  <div class="card card-balance"><div class="icon">💰</div><h3>الرصيد الأساسي</h3><div class="value">${{BALANCE}}</div></div>
  <div class="card card-floating"><div class="icon">📈</div><h3>الرصيد العائم</h3><div class="value">$<span id="floating">0.00</span></div></div>
  <div class="card card-realized"><div class="icon">🏦</div><h3>الربح المحقق</h3><div class="value">$<span id="realized">0.00</span></div></div>
</div>

<div class="card">
<div style="display:flex;gap:10px;margin-bottom:5px">
<button id="toggleBtn" class="btn" onclick="toggleBot()"></button>
</div>
<button class="btn btn-close" onclick="closeAll()">🔒 قفل الصفقات وتحويل العائم إلى محقق</button>
</div>

<div class="card" style="margin-top:15px">
<h2 style="margin:0 0 10px 0">💎 الصفقات الحية</h2>
<table>
<thead><tr><th>🪙 العملة</th><th>⚡ النوع</th><th>🎯 دخول</th><th>💲 الحالي</th><th>💵 ربح $</th><th>📊 %</th></tr></thead>
<tbody id="tradesBody"></tbody>
</table>
</div>

<script>
function load(){
fetch('/api/data').then(r=>r.json()).then(d=>{
 document.getElementById('statusText').innerText = d.is_running ? 'شغال' : 'متوقف';
 document.getElementById('statusDot').innerText = d.is_running ? '🟢' : '🔴';
 document.getElementById('toggleBtn').innerText = d.is_running ? '⏸️ إيقاف البوت' : '▶️ تشغيل البوت';
 document.getElementById('toggleBtn').className = 'btn ' + (d.is_running ? 'btn-off' : 'btn-on');
 document.getElementById('floating').innerText = d.floating.toFixed(2);
 document.getElementById('realized').innerText = d.realized_profit.toFixed(2);
 let html='';
 if(d.trades.length==0) html='<tr><td colspan=6 style="color:#555;padding:30px">لا يوجد صفقات حاليا .. البوت يبحث 🔍</td></tr>';
 d.trades.forEach(t=>{
   let cls = t.profit_usd >=0 ? 'profit-pos' : 'profit-neg';
   let badge = t.side=='LONG' ? '<span class="badge badge-long">LONG 🚀</span>' : '<span class="badge badge-short">SHORT 📉</span>';
   html+=`<tr><td>${t.coin}</td><td>${badge}</td><td>${t.entry_price}</td><td>${t.current_price}</td><td class="${cls}">$${t.profit_usd}</td><td class="${cls}">${t.profit_pct}%</td></tr>`;
 });
 document.getElementById('tradesBody').innerHTML=html;
})
}
function toggleBot(){ fetch('/api/toggle', {method:'POST'}).then(()=>load()) }
function closeAll(){ if(confirm('متأكد تبي تقفل الكل وتحول العائم لمحقق؟')){ fetch('/api/close_all', {method:'POST'}).then(()=>load()) } }
setInterval(load, 2000); load();
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE, BALANCE=BALANCE_REAL)

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
    try:
        if DISCORD_WEBHOOK:
            requests.post(DISCORD_WEBHOOK, json={"content": f"🔒 تم قفل التداول! تم تحويل ${floating:.2f} من عائم إلى محقق. المحقق الآن ${bot_state['realized_profit']:.2f}"}, timeout=3)
    except: pass
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

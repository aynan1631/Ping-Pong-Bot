import os, random, threading, time, requests
from flask import Flask, render_template_string
from datetime import datetime

app = Flask(__name__)
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK", "").strip()

DATA = {
    "total_balance": 1000.0,
    "realized": 12.5,
    "floating": 19.65,
    "positions": {"BTCUSDT": {"qty": 0.002, "pnl": 12.5}},
    "btc_status": "صاعد 🟢"
}

def send_discord(text):
    if not WEBHOOK_URL: return
    try: requests.post(WEBHOOK_URL, json={"content": text, "username": "V8 PRO Bot"}, timeout=10)
    except: pass

def bot_loop():
    coins = ["DASHUSDT","BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT"]
    while True:
        try:
            time.sleep(20)
            coin = random.choice(coins)
            profit = random.randint(60, 220)
            rsi = random.randint(30, 70)
            vol = random.randint(80, 160)
            DATA["floating"] = round(DATA["floating"] + random.uniform(-1.5, 3.5), 2)
            DATA["positions"][coin] = {"qty": round(random.uniform(0.01,1),4), "pnl": round(random.uniform(2,15),2)}

            msg = f"🚀 **LONG صاروخ {coin}**\nM الربح {profit}% | الحجم {vol}M\nEMA50-EMA100 ✅ RSI {rsi}\nBTC 79662 100 فلح ✅\nاللوحة: robust-simplicity-production.up.railway.app"
            send_discord(msg)
        except: time.sleep(10)

threading.Thread(target=bot_loop, daemon=True).start()

HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="5">
<title>V8 PRO + Discord</title>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700;800&display=swap" rel="stylesheet">
<style>
*{font-family:'Tajawal',sans-serif;box-sizing:border-box}
body{margin:0;background:#070b14;color:#fff}
.header{background:#0f172a;padding:16px 22px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1e293b}
.logo{font-weight:800;font-size:22px;background:linear-gradient(90deg,#22c55e,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.badge{background:#16a34a;padding:4px 12px;border-radius:20px;font-size:13px}
.container{padding:22px;max-width:1200px;margin:auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
.card{background:linear-gradient(145deg,#151c2f,#1a233e);border:1px solid #243049;border-radius:18px;padding:20px;box-shadow:0 10px 30px rgba(0,0,0,.3)}
.value{font-size:30px;font-weight:800;margin-top:6px}
.green{color:#22c55e}.blue{color:#38bdf8}
.status{grid-column:1/-1;background:#11192e;border-radius:16px;padding:16px;border:1px solid #243049;display:flex;justify-content:space-between}
.live{width:10px;height:10px;background:#22c55e;border-radius:50%;display:inline-block;animation:pulse 1.5s infinite}
@keyframes pulse{0%{opacity:1}50%{opacity:.3}100%{opacity:1}}
table{width:100%;border-collapse:collapse;margin-top:10px}
th{color:#64748b;text-align:right;padding:8px;border-bottom:1px solid #243049}
td{padding:10px 8px;border-bottom:1px solid #1e293b}
</style></head>
<body>
<div class="header">
<div class="logo">V8 PRO • DEMO + Discord</div>
<div class="badge"><span class="live"></span> {{data.btc_status}} | ONLINE</div>
</div>
<div class="container">
<div class="card"><small>💰 الرصيد الكلي</small><div class="value">${{data.total_balance}}</div><small>{{now}}</small></div>
<div class="card"><small>📈 الربح المحقق</small><div class="value green">+${{data.realized}}</div><small>Realized</small></div>
<div class="card"><small>💹 الربح العائم</small><div class="value blue">${{data.floating}}</div><small>يتحرك كل 5 ثواني</small></div>
<div class="status">
<span>🔗 حالة الديسكورد: <b style="color:#22c55e">{{'مربوط ✅ يرسل كل 20 ثانية' if webhook else 'مو مربوط ❌'}}</b></span>
<span>🌐 robust-simplicity-production.up.railway.app</span>
</div>
<div class="card" style="grid-column:1/-1">
<h3 style="margin:0 0 12px 0">📊 الصفقات النشطة</h3>
<table><tr><th>العملة</th><th>الكمية</th><th>PnL</th></tr>
{% for coin, info in data.positions.items() %}
<tr><td><b>{{coin}}</b></td><td>{{info.qty}}</td><td class="green">{{info.pnl}}$</td></tr>
{% endfor %}
</table>
</div>
</div>
</body></html>
"""

@app.route('/')
def home():
    return render_template_string(HTML, data=DATA, webhook=bool(WEBHOOK_URL), now=datetime.now().strftime("%H:%M:%S"))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",8080)))

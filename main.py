import os, random, threading, time
from flask import Flask, render_template_string, jsonify
from datetime import datetime

app = Flask(__name__)

DATA = {
    "total_balance": 1000.0,
    "realized": 0.0,
    "floating": 12.5,
    "used": 150.0,
    "total": 1000.0,
    "btc_status": "صاعد فوق BTC 100 🟢",
    "positions": {"BTCUSDT": {"qty": 0.002, "pnl": 12.5}},
    "closed": []
}

COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]

def simulator():
    while True:
        try:
            # حركة الربح العائم
            change = random.uniform(-2.5, 3.5)
            DATA["floating"] = round(max(0, DATA["floating"] + change), 2)

            for coin in DATA["positions"]:
                DATA["positions"][coin]["pnl"] = round(DATA["positions"][coin]["pnl"] + random.uniform(-1, 2), 2)

            # احيانا يفتح صفقة جديدة
            if random.random() > 0.85 and len(DATA["positions"]) < 3:
                new_coin = random.choice(COINS)
                if new_coin not in DATA["positions"]:
                    DATA["positions"][new_coin] = {"qty": round(random.uniform(0.001, 0.5), 3), "pnl": round(random.uniform(-2, 5), 2)}

            # احيانا يقفل صفقة
            if random.random() > 0.9 and len(DATA["positions"]) > 0:
                coin_to_close = random.choice(list(DATA["positions"].keys()))
                pnl = DATA["positions"][coin_to_close]["pnl"]
                DATA["realized"] = round(DATA["realized"] + pnl, 2)
                DATA["total_balance"] = round(DATA["total_balance"] + pnl, 2)
                del DATA["positions"][coin_to_close]
                DATA["closed"].append({"coin": coin_to_close, "pnl": pnl})

            DATA["btc_status"] = random.choice(["صاعد فوق BTC 100 🟢", "هابط تحت BTC 100 🔴", "مستقر 🟡"])
            time.sleep(4)
        except: time.sleep(5)

threading.Thread(target=simulator, daemon=True).start()

PRO_HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>V8 PRO DEMO</title>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700;800&display=swap" rel="stylesheet">
<style>
*{font-family:'Tajawal',sans-serif;box-sizing:border-box}
body{margin:0;background:#070b14;color:#fff}
.header{background:#0f172a;padding:16px 20px;display:flex;justify-content:space-between;border-bottom:1px solid #1e293b}
.logo{font-weight:800;font-size:20px;background:linear-gradient(90deg,#22c55e,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.container{padding:20px;max-width:1100px;margin:auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.card{background:linear-gradient(145deg,#151c2f,#1a233e);border:1px solid #243049;border-radius:16px;padding:18px}
.value{font-size:26px;font-weight:800}
.green{color:#22c55e}.blue{color:#38bdf8}
.table{grid-column:1/-1;background:#11192e;border-radius:16px;padding:18px;border:1px solid #243049;margin-top:5px}
.live{width:10px;height:10px;background:#22c55e;border-radius:50%;display:inline-block;animation:pulse 1.5s infinite}
@keyframes pulse{0%{opacity:1}50%{opacity:.3}100%{opacity:1}}
</style>
<script>setTimeout(()=>location.reload(), 5000);</script>
</head>
<body>
<div class="header"><div class="logo">V8 PRO • DEMO MODE 🧪</div><div><span class="live"></span> تجريبي - {{data.btc_status}}</div></div>
<div class="container">
<div class="card"><small>الرصيد الكلي</small><div class="value">${{data.total_balance}}</div><small>{{time}}</small></div>
<div class="card"><small>الربح المحقق</small><div class="value green">+${{data.realized}}</div><small>Realized</small></div>
<div class="card"><small>الربح العائم</small><div class="value blue">${{data.floating}}</div><small>Floating - يتحرك لحاله</small></div>
<div class="card"><small>الهامش المستخدم</small><div class="value">${{data.used}} / ${{data.total}}</div></div>
<div class="table">
<h3 style="margin:0 0 10px 0">📊 الصفقات النشطة - تتغير كل 5 ثواني</h3>
<table style="width:100%;text-align:right;border-collapse:collapse">
<tr style="color:#64748b;border-bottom:1px solid #243049"><th>العملة</th><th>الكمية</th><th>PnL</th></tr>
{% for coin, info in data.positions.items() %}
<tr style="border-bottom:1px solid #1e293b"><td>{{coin}}</td><td>{{info.qty}}</td><td class="green">{{info.pnl}}$</td></tr>
{% else %}
<tr><td colspan=3 style="text-align:center;padding:15px;color:#64748b">ينتظر اشارة...</td></tr>
{% endfor %}
</table>
</div>
</div>
</body></html>
"""

@app.route('/')
def home():
    return render_template_string(PRO_HTML, data=DATA, time=datetime.now().strftime("%H:%M:%S"))

@app.route('/api/data')
def api(): return jsonify(DATA)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

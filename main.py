import os
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
    "closed": [{"coin": "ETH", "pnl": 5.2, "time": "20:15"}]
}

PRO_HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>V8 PRO Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;800&display=swap" rel="stylesheet">
<style>
*{font-family:'Tajawal',sans-serif;box-sizing:border-box}
body{margin:0;background:#070b14;color:#fff;min-height:100vh}
.header{background:linear-gradient(90deg,#0f172a,#1e293b);padding:18px 25px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1e293b}
.logo{font-weight:800;font-size:22px;background:linear-gradient(90deg,#22c55e,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.container{padding:20px;max-width:1100px;margin:auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:15px}
.card{background:linear-gradient(145deg,#151c2f,#1a233e);border:1px solid #243049;border-radius:18px;padding:20px;box-shadow:0 10px 30px rgba(0,0,0,.4)}
.card h3{margin:0 0 10px 0;color:#94a3b8;font-size:14px}
.value{font-size:28px;font-weight:800}
.green{color:#22c55e}.red{color:#ef4444}.blue{color:#38bdf8}
.badge{display:inline-block;padding:5px 12px;border-radius:20px;background:#132a1f;color:#22c55e;font-size:12px;font-weight:700}
.table{grid-column:1/-1;background:#11192e;border-radius:18px;padding:20px;border:1px solid #243049}
.live-dot{width:10px;height:10px;background:#22c55e;border-radius:50%;display:inline-block;box-shadow:0 0 10px #22c55e;animation:pulse 1.5s infinite}
@keyframes pulse{0%{opacity:1}50%{opacity:.4}100%{opacity:1}}
</style>
<script>setTimeout(()=>location.reload(), 15000);</script>
</head>
<body>
<div class="header">
<div class="logo">V8 PRO • TRADING BOT</div>
<div><span class="live-dot"></span> متصل <span class="badge">{{data.btc_status}}</span></div>
</div>

<div class="container">
<div class="card"><h3>الرصيد الكلي</h3><div class="value">${{data.total_balance}}</div><small style="color:#64748b">{{time}}</small></div>
<div class="card"><h3>الربح المحقق</h3><div class="value green">+${{data.realized}}</div><small>Realized PnL</small></div>
<div class="card"><h3>الربح العائم</h3><div class="value blue">${{data.floating}}</div><small>Floating PnL</small></div>
<div class="card"><h3>الهامش المستخدم</h3><div class="value">${{data.used}} / ${{data.total}}</div><div style="background:#1e293b;height:6px;border-radius:10px;margin-top:10px"><div style="width:15%;height:100%;background:#3b82f6;border-radius:10px"></div></div></div>

<div class="table">
<h3>📊 الصفقات النشطة</h3>
<div style="overflow:auto">
<table style="width:100%;text-align:right;border-collapse:collapse;margin-top:10px">
<tr style="color:#64748b;border-bottom:1px solid #243049"><th>العملة</th><th>الكمية</th><th>PnL</th></tr>
{% for coin, info in data.positions.items() %}
<tr style="border-bottom:1px solid #1e293b"><td>{{coin}}</td><td>{{info.qty}}</td><td class="green">{{info.pnl}}$</td></tr>
{% else %}
<tr><td colspan="3" style="text-align:center;color:#64748b;padding:15px">لا يوجد صفقات حاليا - البوت ينتظر اشارة</td></tr>
{% endfor %}
</table>
</div>
</div>
</div>
</body></html>
"""

@app.route('/')
def home():
    return render_template_string(PRO_HTML, data=DATA, time=datetime.now().strftime("%H:%M:%S %d-%m-%Y"))

@app.route('/api/data')
def api():
    return jsonify(DATA)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

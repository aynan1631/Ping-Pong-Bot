import os
import threading
from flask import Flask, render_template_string
from datetime import datetime

app = Flask(__name__)

# ================== بيانات اللوحة ==================
DATA = {
    "total_balance": 1000.0,
    "realized": 0.0,
    "floating": 0.0,
    "used": 0.0,
    "total": 1000.0,
    "btc_status": "BTC فوق 100k صاعد 🟢",
    "positions": {},  # بوتك يحدثها -> {"BTCUSDT": {"side":"LONG","entry_price":...}}
    "closed": []
}

HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>V8 Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700&display=swap" rel="stylesheet">
<style>
*{font-family:'Cairo',Tahoma;box-sizing:border-box}
body{background:#070a12;color:#fff;margin:0;padding:12px}
.header{background:linear-gradient(90deg,#00ff88,#00c6ff);color:#000;padding:14px 18px;border-radius:14px;display:flex;justify-content:space-between;font-weight:700}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}
.card{background:#141a27;border:1px solid #1e273a;border-radius:14px;padding:12px;text-align:center}
.card b{display:block;font-size:22px;margin-top:4px}
table{width:100%;border-collapse:collapse;background:#141a27;border-radius:14px;overflow:hidden}
th{background:#0f1420;color:#7a869e;padding:10px 6px;font-size:11px}
td{padding:12px 6px;text-align:center;border-top:1px solid #1e273a;font-size:12px}
.LONG{background:#00ff88;color:#000;padding:4px 12px;border-radius:20px;font-weight:700;font-size:11px}
.SHORT{background:#ff2e55;color:#fff;padding:4px 12px;border-radius:20px;font-weight:700;font-size:11px}
.profit{color:#00ff88}.loss{color:#ff2e55}
</style>
<meta http-equiv="refresh" content="5">
</head>
<body>
<div class="header"><span>🚀 لوحة المتابعة الخرافية V8</span><span>{{btc_status}}</span></div>

<div class="grid">
<div class="card">الرصيد الكلي<b>${{total_balance}}</b></div>
<div class="card">الربح المحقق<b class="{{'profit' if realized>=0 else 'loss'}}">${{realized}}</b></div>
<div class="card">الربح العائم<b class="{{'profit' if floating>=0 else 'loss'}}">${{floating}}</b></div>
<div class="card">المستخدم<b>${{used}}</b></div>
</div>

<table>
<tr><th>شراء/بيع</th><th>اسم العملة</th><th>سعر الدخول</th><th>السعر الحالي</th><th>الربح العائم</th><th>النسبة</th></tr>
{% for sym, d in positions.items() %}
<tr>
<td><span class="{{d.side}}">{{'شراء' if d.side=='LONG' else 'بيع'}}</span></td>
<td>{{sym}}</td>
<td>{{d.entry_price}}</td>
<td>{{d.current_price}}</td>
<td class="{{'profit' if d.pnl>=0 else 'loss'}}">{{d.pnl}}$</td>
<td class="{{'profit' if d.pnl>=0 else 'loss'}}">{{d.pnl_pct}}%</td>
</tr>
{% else %}
<tr><td colspan="6" style="padding:30px;color:#555">لا يوجد صفقات حالية - بانتظار إشارات البوت...</td></tr>
{% endfor %}
</table>

<br>
<table>
<tr><th>العملة</th><th>دخول → خروج</th><th>الربح المحقق</th><th>الوقت</th></tr>
{% for t in closed[-10:]|reverse %}
<tr><td>{{t.symbol}}</td><td>{{t.entry}} → {{t.exit}}</td><td class="{{'profit' if t.pnl>=0 else 'loss'}}">{{t.pnl}}$</td><td>{{t.time}}</td></tr>
{% else %}
<tr><td colspan="4" style="color:#555">لا يوجد صفقات مغلقة</td></tr>
{% endfor %}
</table>
</body>
</html>
"""

@app.route("/")
def home():
    return "V8 Bot Online - Go to /dashboard"

@app.route("/dashboard")
def dashboard():
    return render_template_string(HTML, **DATA)

def run_web():
    # هذا هو السطر اللي يحل مشكلة Generate Domain
    port = int(os.environ.get("PORT", 8080))
    print(f"✅ V8 Dashboard running on port {port}", flush=True)
    app.run(host="0.0.0.0", port=port)

# شغل الويب في الخلفية
threading.Thread(target=run_web, daemon=True).start()

# ======= هنا كود بوت الديسكورد حقك =======
# مثال:
# import discord
# bot = discord.Client(...)
# bot.run(os.getenv("DISCORD_TOKEN"))

# عشان Railway ما يطفي
if __name__ == "__main__":
    import time
    while True:
        time.sleep(60)

import os, asyncio, threading
from flask import Flask, render_template_string
import discord
from discord.ext import commands

app = Flask(__name__)

# ===== بيانات وهمية للتجربة - بوتك يحدثها =====
DATA = {
    "total_balance": 1000,
    "realized": 0,
    "floating": 0,
    "used": 0,
    "total": 1000,
    "btc_status": "BTC فوق 100 صاعد 🟢",
    "positions": {},
    "closed": []
}

DASHBOARD_HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>لوحة المتابعة الخرافية</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700&display=swap" rel="stylesheet">
<style>
*{font-family:Cairo,Tahoma}body{background:#080b10;color:#fff;margin:0;padding:10px}
.hdr{background:linear-gradient(90deg,#00ff88,#00b4ff);color:#000;padding:14px;border-radius:14px;font-weight:700;display:flex;justify-content:space-between}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}
.c{background:#151b26;border-radius:12px;padding:10px;text-align:center;border:1px solid #222}
.c b{font-size:20px;display:block}
table{width:100%;border-collapse:collapse;background:#151b26;border-radius:12px;overflow:hidden}
th{background:#0f121a;padding:10px;font-size:11px;color:#888}
td{padding:12px 6px;text-align:center;border-bottom:1px solid #222;font-size:12px}
.LONG{background:#00ff88;color:#000;padding:4px 10px;border-radius:20px;font-weight:700}
.SHORT{background:#ff2d55;color:#fff;padding:4px 10px;border-radius:20px;font-weight:700}
.profit{color:#00ff88}.loss{color:#ff2d55}
</style><meta http-equiv="refresh" content="5">
</head>
<body>
<div class="hdr"><span>🚀 V8 - العملات السريعة LIVE</span><span>{{btc_status}}</span></div>
<div class="cards">
<div class="c">الرصيد الكلي<b>{{total_balance}}$</b></div>
<div class="c">المحققة<b class="{{'profit' if realized>=0 else 'loss'}}">{{realized}}$</b></div>
<div class="c">العائمة<b class="{{'profit' if floating>=0 else 'loss'}}">{{floating}}$</b></div>
<div class="c">المستخدم<b>{{used}}$</b></div>
</div>
<table>
<tr><th>شراء/بيع</th><th>العملة</th><th>دخول</th><th>حالي</th><th>الربح العائم</th><th>النسبة</th></tr>
{% for s,d in positions.items() %}
<tr><td><span class="{{d.side}}">{{'شراء' if d.side=='LONG' else 'بيع'}}</span></td><td>{{s}}</td><td>{{d.entry_price}}</td><td>{{d.current_price}}</td><td class="{{'profit' if d.pnl>=0 else 'loss'}}">{{d.pnl}}$</td><td class="{{'profit' if d.pnl>=0 else 'loss'}}">{{d.pnl_pct}}%</td></tr>
{% else %}<tr><td colspan=6 style="padding:25px;color:#666">لا يوجد صفقات - بانتظار الإشارات...</td></tr>{% endfor %}
</table>
<br>
<table>
<tr><th>العملة</th><th>دخول→خروج</th><th>المحقق</th><th>الوقت</th></tr>
{% for t in closed[-10:]|reverse %}<tr><td>{{t.symbol}}</td><td>{{t.entry}}→{{t.exit}}</td><td class="{{'profit' if t.pnl>=0 else 'loss'}}">{{t.pnl}}$</td><td>{{t.time}}</td></tr>{% else %}<tr><td colspan=4 style="color:#666">لا يوجد</td></tr>{% endfor %}
</table>
</body></html>
"""

@app.route("/")
def home(): return "Bot Running"
@app.route("/dashboard")
def dash(): return render_template_string(DASHBOARD_HTML, **DATA)

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    print(f"V8 Dashboard ready on port {port}", flush=True)
    app.run(host="0.0.0.0", port=port)

# ===== شغل الويب + الديسكورد =====
threading.Thread(target=run_flask, daemon=True).start()

# بوت الديسكورد (اذا عندك)
# bot = commands.Bot(...)
# bot.run(os.getenv("DISCORD_TOKEN"))

# لو ما عندك بوت ديسكورد وتبي اللوحة فقط، خلي الكود شغال كذا
if __name__ == "__main__":
    while True: 
        import time; time.sleep(60)

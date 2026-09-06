import os, random, threading, time, requests
from flask import Flask, render_template_string
from datetime import datetime

app = Flask(__name__)
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK", "").strip()

DATA = {
    "total_balance": 1000.0,
    "realized": 0.0,
    "floating": 12.5,
    "positions": {"BTCUSDT": {"qty": 0.002, "pnl": 12.5}},
    "btc_status": "صاعد 🟢"
}

def send_discord(text):
    if not WEBHOOK_URL: return
    try:
        requests.post(WEBHOOK_URL, json={"content": text, "username": "V8 PRO Bot"}, timeout=10)
    except Exception as e:
        print(f"Discord error: {e}")

def bot_loop():
    coins = ["DASHUSDT","BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT"]
    while True:
        try:
            time.sleep(20) # كل 20 ثانية يرسل اشارة تجريبية
            coin = random.choice(coins)
            pnl = random.randint(60, 220)
            rsi = random.randint(30, 75)
            DATA["floating"] = round(DATA["floating"] + random.uniform(-1.5, 3), 2)
            
            msg = f"🚀 **LONG صاروخ {coin}**\nالربح {pnl}% | الحجم {random.randint(70,150)}M\nEMA50-EMA100 ✅ RSI {rsi}\nBTC 79662 100 فلح ✅\nاللوحة: robust-simplicity-production.up.railway.app"
            send_discord(msg)
            print("Sent to Discord")
        except: time.sleep(10)

threading.Thread(target=bot_loop, daemon=True).start()

HTML = """
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="5">
<title>V8 PRO + Discord</title>
<style>
body{margin:0;background:#070b14;color:#fff;font-family:tahoma}
.header{background:#0f172a;padding:15px;display:flex;justify-content:space-between;border-bottom:1px solid #1e293b}
.card{background:#151c2f;border:1px solid #243049;border-radius:12px;padding:15px;margin:10px}
.green{color:#22c55e}
</style></head><body>
<div class="header"><b>V8 PRO 🧪 + Discord ✅</b><span>{{data.btc_status}}</span></div>
<div style="display:grid;grid-template-columns:1fr 1fr">
<div class="card">الرصيد<br><b>${{data.total_balance}}</b></div>
<div class="card">العائم<br><b class="green">${{data.floating}}</b></div>
</div>
<div class="card">حالة الديسكورد: {{'مربوط ✅ يرسل كل 20 ثانية' if webhook else 'مو مربوط ❌'}}</div>
<div class="card">الصفقات:<br>{{data.positions}}</div>
</body></html>
"""

@app.route('/')
def home():
    return render_template_string(HTML, data=DATA, webhook=bool(WEBHOOK_URL), time=datetime.now().strftime("%H:%M:%S"))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",8080)))

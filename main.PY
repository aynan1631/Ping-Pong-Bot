import os, requests, time
from threading import Thread
from flask import Flask
from datetime import datetime

WEBHOOK_URL = "حط رابطك هنا"
SYMBOL = "BTCUSDT"
INTERVAL = "5m"
position = None

app = Flask('')
@app.route('/')
def home():
    return f"Bot Live! Pos:{position}"

def ema(prices, period):
    k = 2 / (period + 1)
    e = prices[0]
    for p in prices[1:]: e = p*k + e*(1-k)
    return e

def send(msg):
    try:
        requests.post(WEBHOOK_URL, json={"content": msg}, timeout=10)
        print(msg, flush=True)
    except: pass

def bot_loop():
    global position
    print("=== BOT V2 - NO LOSS CLOSE ===", flush=True)
    send("✅ **البوت اشتغل - V2 - ما يقفل على خسارة**")

    while True:
        try:
            url = f"https://data-api.binance.vision/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit=50"
            data = requests.get(url, timeout=15).json()
            closes = [float(c[4]) for c in data]
            closed = closes[:-1]
            last_close = closed[-1]
            curr = closes[-1]
            ema9 = ema(closed, 9)
            ema21 = ema(closed, 21)

            print(f"CHECK {last_close:.2f} EMA9 {ema9:.2f} EMA21 {ema21:.2f} Pos={position}", flush=True)

            # === دخول ===
            if position is None:
                if last_close > ema9 and ema9 > ema21: # ترند صاعد قوي
                    position = {'side':'LONG','entry':curr, 'time': datetime.now()}
                    send(f"""
🟢 **دخول LONG**
💰 العملة: {SYMBOL}
📈 سعر الدخول: {curr:.2f}$
📊 EMA9: {ema9:.2f} | EMA21: {ema21:.2f}
⏰ الوقت: {datetime.now().strftime('%I:%M %p')}
السبب: السعر فوق EMA9 والترند صاعد
""")
                elif last_close < ema9 and ema9 < ema21: # ترند هابط قوي
                    position = {'side':'SHORT','entry':curr, 'time': datetime.now()}
                    send(f"""
🔴 **دخول SHORT**
💰 العملة: {SYMBOL}
📉 سعر الدخول: {curr:.2f}$
📊 EMA9: {ema9:.2f} | EMA21: {ema21:.2f}
⏰ الوقت: {datetime.now().strftime('%I:%M %p')}
السبب: السعر تحت EMA9 والترند هابط
""")

            # === خروج ===
            else:
                entry = position['entry']
                side = position['side']
                if side == 'LONG':
                    pnl = ((curr - entry)/entry)*100
                    # لا يقفل الا اذا ربحان +0.3% او خسران اكثر من -1.5% وقف خسارة
                    if last_close < ema21:
                        if pnl > 0.3:
                            send(f"""
✅ **اغلاق LONG بربح**
💵 دخول: {entry:.2f}$ | خروج: {curr:.2f}$
💹 الربح: +{pnl:.2f}%
📉 السبب: تقاطع تحت EMA21
""")
                            position = None
                        elif pnl < -1.5:
                            send(f"""
⛔ **وقف خسارة LONG**
💵 دخول: {entry:.2f}$ | خروج: {curr:.2f}$
📉 الخسارة: {pnl:.2f}%
""")
                            position = None
                        else:
                            print(f"HOLD LONG loss {pnl:.2f}% - waiting profit", flush=True)

                else: # SHORT
                    pnl = ((entry - curr)/entry)*100
                    if last_close > ema21:
                        if pnl > 0.3:
                            send(f"""
✅ **اغلاق SHORT بربح**
💵 دخول: {entry:.2f}$ | خروج: {curr:.2f}$
💹 الربح: +{pnl:.2f}%
📈 السبب: تقاطع فوق EMA21
""")
                            position = None
                        elif pnl < -1.5:
                            send(f"""
⛔ **وقف خسارة SHORT**
💵 دخول: {entry:.2f}$ | خروج: {curr:.2f}$
📉 الخسارة: {pnl:.2f}%
""")
                            position = None
                        else:
                            print(f"HOLD SHORT loss {pnl:.2f}% - waiting profit", flush=True)

            time.sleep(60)
        except Exception as e:
            print(f"Error: {e}", flush=True)
            time.sleep(10)

Thread(target=bot_loop, daemon=True).start()
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

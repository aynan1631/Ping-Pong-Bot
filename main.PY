import os, requests, time
from threading import Thread
from flask import Flask
from datetime import datetime

WEBHOOK_URL = "حط رابط الديسكورد هنا"
SYMBOL = "BTCUSDT"
INTERVAL = "5m"
position = None

app = Flask('')
@app.route('/')
def home():
    return f"Bot Live! Pos:{position} Time:{datetime.now()} - OK"

def ema(prices, period):
    k = 2 / (period + 1)
    e = prices[0]
    for p in prices[1:]:
        e = p * k + e * (1-k)
    return e

def send(msg):
    try:
        requests.post(WEBHOOK_URL, json={"content": msg}, timeout=10)
        print(f"Discord OK: {msg}", flush=True)
    except Exception as e:
        print(f"Discord Fail: {e}", flush=True)

def bot_loop():
    global position
    print("=== BOT LOOP STARTED ===", flush=True)
    time.sleep(3)
    send("✅ البوت اشتغل - النسخة المصلحة EMA9/21")

    while True:
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit=50"
            r = requests.get(url, timeout=15)
            data = r.json()
            closes = [float(c[4]) for c in data]

            closed = closes[:-1]
            last_close = closed[-1]
            ema9 = ema(closed, 9)
            ema21 = ema(closed, 21)
            curr = closes[-1]

            print(f"CHECK Close={last_close:.2f} EMA9={ema9:.2f} EMA21={ema21:.2f} Pos={position}", flush=True)

            if position is None:
                if last_close > ema9:
                    position = {'side':'LONG','entry':curr}
                    send(f"🟢 دخول LONG {curr:.2f}")
                elif last_close < ema9:
                    position = {'side':'SHORT','entry':curr}
                    send(f"🔴 دخول SHORT {curr:.2f}")
            elif position['side']=='LONG' and last_close < ema21:
                pnl = ((curr-position['entry'])/position['entry'])*100
                send(f"✅ اغلاق LONG ربح {pnl:.2f}%")
                position = None
            elif position['side']=='SHORT' and last_close > ema21:
                pnl = ((position['entry']-curr)/position['entry'])*100
                send(f"✅ اغلاق SHORT ربح {pnl:.2f}%")
                position = None

            time.sleep(60)
        except Exception as e:
            print(f"ERROR in loop: {e}", flush=True)
            time.sleep(10)

# هنا الحل: البوت في الخلفية، و Flask في الأمام
Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

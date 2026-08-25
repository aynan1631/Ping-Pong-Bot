import os
import requests
import time
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
    return f"Bot Live! Pos: {position} Time: {datetime.now()}"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def ema(prices, period):
    k = 2 / (period + 1)
    ema_val = prices[0]
    for price in prices[1:]:
        ema_val = price * k + ema_val * (1 - k)
    return ema_val

def get_data():
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit=50"
        r = requests.get(url, timeout=10)
        data = r.json()
        closes = [float(c[4]) for c in data]
        return closes
    except Exception as e:
        print(f"Binance Error: {e}")
        return None

def send(msg):
    try:
        requests.post(WEBHOOK_URL, json={"content": msg}, timeout=10)
        print(f"Sent to Discord: {msg}")
    except Exception as e:
        print(f"Discord Error: {e}")

def bot_logic():
    global position
    print("BOT THREAD STARTED!")
    time.sleep(5)
    send("✅ البوت اشتغل - EMA9/21 - Render Live")

    while True:
        try:
            closes = get_data()
            if not closes or len(closes) < 22:
                print("No data, retry in 10s")
                time.sleep(10)
                continue

            closed_closes = closes[:-1]
            last_close = closed_closes[-1]
            ema9 = ema(closed_closes, 9)
            ema21 = ema(closed_closes, 21)
            curr_price = closes[-1]

            print(f"CHECK | Close:{last_close:.2f} EMA9:{ema9:.2f} EMA21:{ema21:.2f} Pos:{position}", flush=True)

            if position is None:
                if last_close > ema9:
                    position = {'side': 'LONG', 'entry': curr_price}
                    send(f"🟢 **دخول LONG** السعر: {curr_price}")
                elif last_close < ema9:
                    position = {'side': 'SHORT', 'entry': curr_price}
                    send(f"🔴 **دخول SHORT** السعر: {curr_price}")
            elif position['side'] == 'LONG' and last_close < ema21:
                pnl = ((curr_price - position['entry']) / position['entry']) * 100
                send(f"✅ **اغلاق LONG** ربح: %{pnl:.2f}")
                position = None
            elif position['side'] == 'SHORT' and last_close > ema21:
                pnl = ((position['entry'] - curr_price) / position['entry']) * 100
                send(f"✅ **اغلاق SHORT** ربح: %{pnl:.2f}")
                position = None

            time.sleep(60)
        except Exception as e:
            print(f"Logic Error: {e}")
            time.sleep(10)

Thread(target=run_server, daemon=True).start()
bot_logic()

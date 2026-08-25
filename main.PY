import os
import requests
import time
from threading import Thread
from flask import Flask
from datetime import datetime

# --- إعداداتك ---
WEBHOOK_URL = "https://discord.com/api/webhooks/ ضع حقك هنا"
SYMBOL = "BTCUSDT"
INTERVAL = "5m"

position = None

# --- سيرفر عشان Render و UptimeRobot ما يطفيه ---
app = Flask('')
@app.route('/')
def home():
    return "Bot is Live! EMA9/21 Strategy"

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
    url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit=50"
    data = requests.get(url).json()
    closes = [float(c[4]) for c in data]
    return closes

def send(msg):
    try:
        requests.post(WEBHOOK_URL, json={"content": msg})
    except: pass

def bot_logic():
    global position
    print("Bot started - EMA9/21 No TP")
    send("✅ البوت اشتغل - استراتيجية EMA9/21 بربح مفتوح")

    while True:
        try:
            closes = get_data()
            if len(closes) < 22:
                time.sleep(10)
                continue

            closed_closes = closes[:-1]
            last_close = closed_closes[-1]
            ema9 = ema(closed_closes, 9)
            ema21 = ema(closed_closes, 21)
            curr_price = closes[-1]

            print(f"{datetime.now()} | Close:{last_close:.2f} EMA9:{ema9:.2f} EMA21:{ema21:.2f} Pos:{position}")

            if position is None:
                if last_close > ema9:
                    position = {'side': 'LONG', 'entry': curr_price}
                    send(f"🟢 **دخول LONG**\nالسعر: {curr_price}\nاغلاق {last_close:.2f} فوق EMA9")
                elif last_close < ema9:
                    position = {'side': 'SHORT', 'entry': curr_price}
                    send(f"🔴 **دخول SHORT**\nالسعر: {curr_price}\nاغلاق {last_close:.2f} تحت EMA9")

            elif position['side'] == 'LONG':
                if last_close < ema21:
                    entry = position['entry']
                    pnl = ((curr_price - entry) / entry) * 100
                    send(f"✅ **اغلاق LONG**\nخروج: {curr_price:.2f}\nالسبب: اغلاق تحت EMA21\nربح: %{pnl:.2f}")
                    position = None

            elif position['side'] == 'SHORT':
                if last_close > ema21:
                    entry = position['entry']
                    pnl = ((entry - curr_price) / entry) * 100
                    send(f"✅ **اغلاق SHORT**\nخروج: {curr_price:.2f}\nالسبب: اغلاق فوق EMA21\nربح: %{pnl:.2f}")
                    position = None

            time.sleep(60)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

Thread(target=run_server).start()
bot_logic()

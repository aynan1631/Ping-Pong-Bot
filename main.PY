import os, requests, time
from threading import Thread
from flask import Flask

WEBHOOK_URL = "حط رابط الويبهوك هنا"
SYMBOL = "BTCUSDT"
INTERVAL = "5m"
position = None

app = Flask('')
@app.route('/')
def home(): return "Bot Working"

def ema(prices, period):
    k = 2 / (period + 1)
    e = prices[0]
    for p in prices[1:]: e = p*k + e*(1-k)
    return e

def send(msg):
    requests.post(WEBHOOK_URL, json={"content": msg})

def bot_loop():
    global position
    print("Bot Started - Buy & Sell Only")
    send("✅ **البوت اشتغل - يراقب شراء وبيع**")

    while True:
        try:
            data = requests.get(f"https://data-api.binance.vision/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit=50", timeout=15).json()
            closes = [float(c[4]) for c in data]
            closed = closes[:-1] # شمعة مقفلة
            curr = closes[-1] # سعر لحظي
            last = closed[-1]

            ema9 = ema(closed, 9)
            ema21 = ema(closed, 21)

            # ما فيه صفقة -> دور دخول
            if position is None:
                if last > ema9 and ema9 > ema21:
                    position = {'side':'LONG','entry':curr}
                    send(f"🟢 **شراء LONG**\nالسعر: {curr:.2f}$\nEMA9 فوق EMA21")

                elif last < ema9 and ema9 < ema21:
                    position = {'side':'SHORT','entry':curr}
                    send(f"🔴 **بيع SHORT**\nالسعر: {curr:.2f}$\nEMA9 تحت EMA21")

            # فيه صفقة -> دور خروج
            else:
                if position['side'] == 'LONG' and last < ema21:
                    pnl = ((curr - position['entry'])/position['entry'])*100
                    # ما يقفل على خسارة الا اذا ربحان او خسران كثير
                    if pnl > 0.2 or pnl < -1.5:
                        send(f"⚪ **اغلاق شراء**\nخروج: {curr:.2f}$\nالربح: {pnl:.2f}%")
                        position = None

                if position['side'] == 'SHORT' and last > ema21:
                    pnl = ((position['entry'] - curr)/position['entry'])*100
                    if pnl > 0.2 or pnl < -1.5:
                        send(f"⚪ **اغلاق بيع**\nخروج: {curr:.2f}$\nالربح: {pnl:.2f}%")
                        position = None

            print(f"{last:.2f} EMA9 {ema9:.2f} EMA21 {ema21:.2f} Pos {position}")
            time.sleep(60)

        except Exception as e:
            print(f"Error {e}")
            time.sleep(10)

Thread(target=bot_loop, daemon=True).start()
app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

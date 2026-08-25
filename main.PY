import os, requests, time
from threading import Thread
from flask import Flask
from datetime import datetime

# حط رابطك الحقيقي هنا بين القوسين
WEBHOOK_URL = "https://discord.com/api/webhooks/ضع_الرابط_الحقيقي_هنا"
SYMBOL = "BTCUSDT"
INTERVAL = "5m"
position = None

app = Flask('')
@app.route('/')
def home():
    return f"Bot Live! Pos:{position} Time:{datetime.now()}"

def ema(prices, period):
    k = 2 / (period + 1)
    e = prices[0]
    for p in prices[1:]:
        e = p * k + e * (1-k)
    return e

def send(msg):
    try:
        # لا ترسل اذا الرابط وهمي
        if "ضع_الرابط" in WEBHOOK_URL or "حط رابط" in WEBHOOK_URL:
            print("!!! حط رابط الديسكورد الحقيقي!!!", flush=True)
            return
        requests.post(WEBHOOK_URL, json={"content": msg}, timeout=10)
        print(f"Discord Sent: {msg}", flush=True)
    except Exception as e:
        print(f"Discord Fail: {e}", flush=True)

def bot_loop():
    global position
    print("=== BOT LOOP STARTED - Fix Binance US ===", flush=True)
    time.sleep(3)
    send("✅ البوت اشتغل - تم اصلاح مشكلة بينانس")

    while True:
        try:
            # هذا الرابط يشتغل في امريكا، الأول محجوب
            urls = [
                f"https://data-api.binance.vision/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit=50",
                f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit=50"
            ]
            data = None
            for url in urls:
                try:
                    r = requests.get(url, timeout=15)
                    j = r.json()
                    # تأكد انه مصفوفة شموع مو رسالة خطأ
                    if isinstance(j, list) and len(j) > 20:
                        data = j
                        break
                    else:
                        print(f"Binance response not list: {j}", flush=True)
                except Exception as e:
                    print(f"Try {url} failed: {e}", flush=True)

            if not data:
                print("No valid data, retry 15s", flush=True)
                time.sleep(15)
                continue

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

Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

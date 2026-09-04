import random
import time
import requests
from datetime import datetime

# ========== إعداداتك القديمة ==========
TRADE_SIZE = 500
TP_DOLLAR = 5.0
SL_DOLLAR = -5.0
DISCORD_WEBHOOK = "" # حط رابط الديسكورد هنا لو عندك
COINS_LIST = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "AVAXUSDT", "ADAUSDT", "SHIBUSDT"]

positions = []
total_pnl = 0
trade_count = 0

# ========== دالة جديدة 1: فلتر الحماية من الانعكاس ==========
def is_bull_market():
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=200"
        data = requests.get(url, timeout=10).json()
        closes = [float(k[4]) for k in data]
        ema200 = sum(closes) / len(closes)
        current = closes[-1]
        is_bull = current > ema200
        print(f"[{datetime.now().strftime('%H:%M:%S')}] فحص اتجاه BTC: {current:.2f} vs EMA200 {ema200:.2f} -> {'صاعد ✅' if is_bull else 'هابط ⛔'}")
        return is_bull
    except:
        return True

def send_discord(msg):
    if DISCORD_WEBHOOK:
        try:
            requests.post(DISCORD_WEBHOOK, json={"content": msg})
        except:
            pass

# ========== دوالك القديمة نفسها ==========
def get_movers():
    # هنا الفلتر الجديد
    if not is_bull_market():
        print("السوق هابط حاليا، البوت متوقف مؤقتا لحماية رأس المال")
        send_discord("⛔ السوق هابط (BTC تحت EMA200) - البوت متوقف للحماية")
        return []

    movers = random.sample(COINS_LIST, 2)
    result = []
    for coin in movers:
        result.append({
            "symbol": coin,
            "pnl": 0.0,
            "entry": datetime.now()
        })
        print(f"فتح صفقة: {coin}")
    return result

def update_pnl(pos):
    # محاكاة PnL تجريبي مثل كودك
    pos["pnl"] += random.uniform(-0.8, 1.2)
    return pos["pnl"]

# ========== اللوب الرئيسي نفسه ==========
print("=== البوت بدأ - عشوائي + حماية من الانعكاس ===")
send_discord("🚀 البوت بدأ - عشوائي + فلتر حماية من الهبوط")

while True:
    if len(positions) < 2:
        positions.extend(get_movers())

    for pos in positions[:]:
        pnl = update_pnl(pos)

        if pnl >= TP_DOLLAR:
            total_pnl += pnl
            trade_count += 1
            msg = f"🟢 ربح | {pos['symbol']} | {pnl:.2f}$ | الصافي {total_pnl:.2f}$ | العدد {trade_count}"
            print(msg)
            send_discord(msg)
            positions.remove(pos)

        elif pnl <= SL_DOLLAR:
            total_pnl += pnl
            trade_count += 1
            msg = f"🔴 خسارة | {pos['symbol']} | {pnl:.2f}$ | الصافي {total_pnl:.2f}$ | العدد {trade_count}"
            print(msg)
            send_discord(msg)
            positions.remove(pos)

    time.sleep(5)

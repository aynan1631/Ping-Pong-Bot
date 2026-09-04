import random
import time
import requests
from datetime import datetime

# === الإعدادات ===
TRADE_SIZE = 500
TP = 5
SL = -5
COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "AVAXUSDT"]

positions = []
closed_trades = []
total_pnl = 0

def is_bull_market():
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=200"
        r = requests.get(url, timeout=5).json()
        closes = [float(c[4]) for c in r]
        ema200 = sum(closes) / 200
        price = closes[-1]
        print(f"فحص السوق: BTC={price:.1f} / EMA200={ema200:.1f} -> {'صاعد ✅' if price > ema200 else 'هابط ⛔'}")
        return price > ema200
    except Exception as e:
        print(f"خطأ فحص السوق: {e} - سأسمح بالدخول")
        return True

def get_movers():
    # فلتر الحماية من الانعكاس
    if not is_bull_market():
        print("⛔ السوق هابط - البوت متوقف للحماية - ما راح يفتح صفقات")
        return []

    # دخول عشوائي مثل ما طلبت
    selected = random.sample(COINS, 2)
    new_pos = []
    for coin in selected:
        pos = {
            "symbol": coin,
            "entry_time": datetime.now(),
            "pnl": 0
        }
        new_pos.append(pos)
        print(f"✅ فتح صفقة شراء عشوائية: {coin} بـ {TRADE_SIZE}$")
    return new_pos

def check_pnl(pos):
    # محاكاة حركة الربح والخسارة واقعية
    change = random.uniform(-0.9, 1.1)
    pos["pnl"] += change
    return pos["pnl"]

def close_position(pos, reason):
    global total_pnl
    pnl = pos["pnl"]
    total_pnl += pnl
    closed_trades.append(pnl)
    win = "🟢 ربح" if pnl > 0 else "🔴 خسارة"
    print(f"{win} | {pos['symbol']} | {pnl:.2f}$ | {reason} | الصافي: {total_pnl:.2f}$ | العدد: {len(closed_trades)}")

# === اللوب الرئيسي ===
print("البوت بدأ - دخول عشوائي + فلتر حماية من الهبوط")
while True:
    # 1. افتح صفقات جديدة اذا مافي صفقات مفتوحة
    if len(positions) < 2:
        positions.extend(get_movers())

    # 2. راجع الصفقات المفتوحة
    for pos in positions[:]:
        pnl = check_pnl(pos)

        if pnl >= TP:
            close_position(pos, f"وصل للهدف +{TP}$")
            positions.remove(pos)
        elif pnl <= SL:
            close_position(pos, f"وقف خسارة {SL}$")
            positions.remove(pos)

    time.sleep(60) # كل دقيقة

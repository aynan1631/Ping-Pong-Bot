# V102 PRO - نظام الريس الذهبي الكامل
# 76.24$ - 7 غرف - 10 سنت - MACD - بدون قيد مراقبة
# يشتري - يبيع - يحول للمستشفى - يرسل للطبيب

import os, time, math
from binance.client import Client
import pandas as pd

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(API_KEY, API_SECRET)

# ========= إعدادات الريس =========
TOTAL_BALANCE = 76.24
ROOM_SIZE = 10.0
MAX_ROOMS = 7
TARGET_PROFIT = 0.10
HOSPITAL_SL = -0.20
DOCTOR_FEE = 0.05

# قيد مراقبة - بلوك حتى لو سيولتها 100 مليون
BLACKLIST = ["ALGOUSDT","BTSUSDT","DREPUSDT","PAXGUSDT","TORNUSDT","WAVESUSDT","XMRUSDT","ZECUSDT","LUNAUSDT","LUNCUSDT"]

# عملات قوية فقط
STRONG_LIST = [
    "BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","LINKUSDT",
    "AVAXUSDT","ADAUSDT","DOGEUSDT","SUIUSDT","ARBUSDT","OPUSDT",
    "LTCUSDT","BCHUSDT","ETCUSDT","FILUSDT","NEARUSDT","APTUSDT",
    "DOTUSDT","TRXUSDT","MATICUSDT","ATOMUSDT","UNIUSDT"
]

hospital = []
pharmacy = 0.0
real_profit = 0.0
active = []

def get_balance_usdt():
    try:
        bal = client.get_asset_balance(asset='USDT')
        return float(bal['free'])
    except:
        return 65.23

def is_macd_green(symbol):
    try:
        klines = client.get_klines(symbol=symbol, interval='15m', limit=100)
        closes = pd.Series([float(k[4]) for k in klines])
        ema12 = closes.ewm(span=12).mean()
        ema26 = closes.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        # اخضر وصاعد
        return macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-1] > 0 and macd.iloc[-1] > macd.iloc[-2]
    except:
        return False

def get_strongest_coin():
    print("🔍 يفحص أقوى عملة MACD أخضر...")
    candidates = []
    for sym in STRONG_LIST:
        if sym in BLACKLIST:
            continue
        if is_macd_green(sym):
            # قوة الصعود
            try:
                ticker = client.get_24hr_ticker(symbol=sym)
                change = float(ticker['priceChangePercent'])
                if change > 1: # صاعدة أكثر من 1%
                    candidates.append((sym, change))
            except:
                continue
    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        print(f"✅ الأقوى: {candidates[0][0]} +{candidates[0][1]:.2f}%")
        return candidates[0][0]
    print("⚠️ ما فيه MACD أخضر، يأخذ BTC")
    return "BTCUSDT"

def buy(symbol, usdt_amount):
    try:
        price = float(client.get_symbol_ticker(symbol=symbol)['price'])
        qty = round(usdt_amount / price, 6)
        # تصحيح الكمية
        info = client.get_symbol_info(symbol)
        lot = [f for f in info['filters'] if f['filterType'] == 'LOT_SIZE'][0]
        step = float(lot['stepSize'])
        qty = math.floor(qty / step) * step
        qty = round(qty, 6)

        order = client.order_market_buy(symbol=symbol, quantity=qty)
        print(f"🟢 شراء {symbol} | كمية {qty} | سعر {price} | بـ {usdt_amount}$")
        return {"symbol": symbol, "qty": qty, "entry": price, "usdt": usdt_amount, "time": time.time(), "is_doctor": False}
    except Exception as e:
        print(f"❌ فشل شراء {symbol}: {e}")
        return None

def sell(pos, reason="ربح"):
    try:
        client.order_market_sell(symbol=pos["symbol"], quantity=pos["qty"])
        curr = float(client.get_symbol_ticker(symbol=pos["symbol"])['price'])
        pnl = (curr - pos["entry"]) * pos["qty"]
        print(f"🔴 بيع {pos['symbol']} | {reason} | PnL {pnl:.3f}$")
        return pnl
    except Exception as e:
        print(f"❌ فشل بيع {pos['symbol']}: {e}")
        return None

print(f"🔥 V102 اشتغل يا ريس")
print(f"💰 الرصيد: {TOTAL_BALANCE}$ | غرف: {MAX_ROOMS} x {ROOM_SIZE}$ | هدف: {TARGET_PROFIT}$")
print(f"🚫 قيد المراقبة بلوك | ✅ MACD أخضر فقط")

while True:
    try:
        usdt_free = get_balance_usdt()
        print(f"\n--- فحص | USDT حر: {usdt_free:.2f}$ | نشط: {len(active)} | مستشفى: {len(hospital)}/7 | صافي: {real_profit:.3f}$ ---")

        # 1. فحص الأرباح والخسائر
        for pos in active[:]:
            curr_price = float(client.get_symbol_ticker(symbol=pos["symbol"])['price'])
            pnl = (curr_price - pos["entry"]) * pos["qty"]

            # حالة الطبيب يعالج مريض
            if pos.get("is_doctor"):
                if pnl >= pos["heal_target"]:
                    # شفاء!
                    patient = pos["patient"]
                    # بيع الطبيب والمريض
                    sell(pos, f"شفاء مريض {patient['symbol']}")
                    sell(patient, f"شفى بفضل {pos['symbol']}")
                    hospital.remove(patient)
                    active.remove(pos)
                    real_profit += TARGET_PROFIT
                    pharmacy += abs((patient["entry"] - float(client.get_symbol_ticker(symbol=patient["symbol"])['price'])) * patient["qty"]
                    print(f"🏥💊 شفى {patient['symbol']} +{TARGET_PROFIT}$ | صافي: {real_profit:.3f}$ | مستشفى: {len(hospital)}/7")
                    continue

            # ربح عادي 10 سنت
            if not pos.get("is_doctor") and pnl >= TARGET_PROFIT:
                sell(pos, "10 سنت ونمشي")
                active.remove(pos)
                real_profit += pnl
                print(f"✅ +{pnl:.3f}$ | صافي: {real_profit:.3f}$")

            # خسارة - ودّه المستشفى
            elif not pos.get("is_doctor") and pnl <= HOSPITAL_SL:
                hospital.append(pos)
                active.remove(pos)
                print(f"🏥 دخل المستشفى {pos['symbol']} خسارة {pnl:.3f}$ | المستشفى {len(hospital)}/7")
                if len(hospital) >= MAX_ROOMS:
                    print("⛔ المستشفى فل 7/7 - يوقف شراء جديد حتى يعالج")

        # 2. علاج - كل مريض له طبيب خاص
        if len(hospital) > 0 and len(active) < MAX_ROOMS:
            if usdt_free >= ROOM_SIZE:
                # أقدم مريض
                hospital_sorted = sorted(hospital, key=lambda x: x["time"])
                patient = hospital_sorted[0]
                curr_p = float(client.get_symbol_ticker(symbol=patient["symbol"])['price'])
                invoice = abs((curr_p - patient["entry"]) * patient["qty"])
                heal_target = invoice + TARGET_PROFIT + DOCTOR_FEE

                doctor_coin = get_strongest_coin()
                print(f"👨‍⚕️ مريض {patient['symbol']} فاتورة {invoice:.3f}$ | الطبيب {doctor_coin} هدفه {heal_target:.3f}$")

                doctor_pos = buy(doctor_coin, ROOM_SIZE)
                if doctor_pos:
                    doctor_pos["is_doctor"] = True
                    doctor_pos["patient"] = patient
                    doctor_pos["heal_target"] = heal_target
                    active.append(doctor_pos)
            else:
                print(f"⚠️ ما فيه سيولة للعلاج USDT {usdt_free:.2f}$ < {ROOM_SIZE}$")

        # 3. طحن عادي اذا المستشفى فاضي
        if len(hospital) == 0 and len(active) < MAX_ROOMS and usdt_free >= ROOM_SIZE:
            coin = get_strongest_coin()
            pos = buy(coin, ROOM_SIZE)
            if pos:
                active.append(pos)

        time.sleep(15)

    except Exception as e:
        print(f"⚠️ خطأ عام: {e}")
        time.sleep(10)

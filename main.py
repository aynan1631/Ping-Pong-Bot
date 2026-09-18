import os
import time
from flask import Flask, jsonify
from binance.client import Client

app = Flask(__name__)

# ========== إعدادات المشفى - رأس مالك الحالي 76.43 ==========
TOTAL_CAPITAL = 76.43969999
MAX_OPEN_TRADES = 2          # أقصى صفقتين مفتوحة فقط
TRADE_PERCENT = 25            # كل صفقة 25% = 19.10$
RESERVE_PERCENT = 50          # احتياطي علاج 50% = 38.21$ ما ينلمس أبداً

TRADE_SIZE = round(TOTAL_CAPITAL * TRADE_PERCENT / 100, 2)  # 19.11
RESERVE_AMOUNT = round(TOTAL_CAPITAL * RESERVE_PERCENT / 100, 2) # 38.22
MAX_USABLE = TOTAL_CAPITAL - RESERVE_AMOUNT  # 38.21 المسموح تتداول فيه فقط

# ========== اتصال بايننس مع البروكسي ==========
PROXY_URL = os.getenv("PROXY_URL", "").strip()
proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(API_KEY, API_SECRET, {"proxies": proxies, "timeout": 30})

print(f"✅ نظام المشفى شغال")
print(f"💰 رأس المال الكلي: {TOTAL_CAPITAL}$")
print(f"🔹 حجم الصفقة: {TRADE_SIZE}$")
print(f"🔹 عدد الصفقات: {MAX_OPEN_TRADES} فقط")
print(f"🛡️ احتياطي العلاج المحفوظ: {RESERVE_AMOUNT}$ - ممنوع لمسه")
print(f"✅ المسموح للتداول: {MAX_USABLE}$ فقط")

# ذاكرة مؤقتة للصفقات المفتوحة (اربطها بقاعدة بياناتك لاحقاً)
open_trades_count = 0

def get_spot_balance():
    try:
        bal = client.get_asset_balance(asset='USDT')
        return float(bal['free'])
    except Exception as e:
        print(f"خطأ جلب الرصيد: {e}")
        return 0.0

@app.route("/")
def home():
    balance = get_spot_balance()
    # حماية الاحتياطي: إذا الرصيد نزل تحت الاحتياطي، وقف التداول
    can_trade = balance > RESERVE_AMOUNT and open_trades_count < MAX_OPEN_TRADES
    
    if balance <= RESERVE_AMOUNT:
        status = f"⛔ متوقف - وصلت لاحتياطي العلاج {RESERVE_AMOUNT}$"
    elif open_trades_count >= MAX_OPEN_TRADES:
        status = f"⏸️ مكتمل - عندك {open_trades_count} صفقات مفتوحة"
    else:
        status = f"✅ مسموح - تقدر تفتح صفقة جديدة بـ {TRADE_SIZE}$"

    return f"""
    <h2>🏥 نظام المشفى شغال</h2>
    <p>💰 الرصيد الفوري الحالي: <b>{balance}$</b></p>
    <p>🔹 حجم الصفقة الواحدة: <b>{TRADE_SIZE}$</b></p>
    <p>🔹 الحد الأقصى: <b>{MAX_OPEN_TRADES} صفقات</b> | المفتوح حالياً: {open_trades_count}</p>
    <p>🛡️ احتياطي العلاج المحفوظ: <b>{RESERVE_AMOUNT}$</b></p>
    <p>✅ المسموح تتداوله: <b>{MAX_USABLE}$</b></p>
    <hr>
    <p><b>الحالة:</b> {status}</p>
    <p>IP: {PROXY_URL[:20]}... | USDT OK</p>
    """

@app.route("/balance")
def balance():
    bal = get_spot_balance()
    return jsonify({
        "total_capital": TOTAL_CAPITAL,
        "spot_free": bal,
        "trade_size": TRADE_SIZE,
        "reserve_protected": RESERVE_AMOUNT,
        "max_usable_for_trading": MAX_USABLE,
        "max_trades": MAX_OPEN_TRADES,
        "open_trades_now": open_trades_count,
        "can_open_new_trade": bal > RESERVE_AMOUNT and open_trades_count < MAX_OPEN_TRADES
    })

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

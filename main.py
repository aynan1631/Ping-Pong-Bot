import time
import ccxt
from datetime import datetime, timedelta

# ===== إعدادات Binance =====
API_KEY = "ضع مفتاحك هنا"
API_SECRET = "ضع سرك هنا"

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
})

# ===== إعدادات V84 - المستشفى التخصصي =====
CAPITAL = 1000.0
STOP_LOSS = 0.50  # وقف الخسارة
TAKE_PROFIT = 0.70 # هدف الربح

MAX_PHARMACY = 12   # نقفل الاستقبال عند 12
MIN_PHARMACY = 4    # نفتح عند 4
MAX_HOLD_HOURS = 36 # تصفية بعد 36 ساعة

ALLOW_NEW_TRADES = True

def get_pharmacy():
    balance = exchange.fetch_balance()
    positions = []
    # قراءة الصفقات المفتوحة من الـ Dashboard
    # ... (كودك الحالي هنا)
    return positions

def close_patient(symbol, reason):
    try:
        exchange.create_market_sell_order(symbol, 0) # كود الإغلاق الحالي عندك
        print(f"✅ تم تصفية {symbol} - السبب: {reason}")
    except Exception as e:
        print(f"خطأ في تصفية {symbol}: {e}")

def get_hold_hours(patient):
    # يحسب كم ساعة المريض في الصيدلية
    open_time = datetime.fromisoformat(patient['timestamp'])
    return (datetime.now() - open_time).total_seconds() / 3600

def trading_loop():
    global ALLOW_NEW_TRADES
    
    while True:
        try:
            pharmacy = get_pharmacy()
            pharmacy_count = len(pharmacy)
            
            print(f"\n--- فحص {datetime.now()} ---")
            print(f"الصيدلية: {pharmacy_count} مرضى")

            # ===== 1. مرحلة التصفية التخصصية =====
            for patient in pharmacy:
                hold_hours = get_hold_hours(patient)
                if hold_hours >= MAX_HOLD_HOURS:
                    close_patient(patient['symbol'], f"تجاوز {MAX_HOLD_HOURS} ساعة - تصفية من الأرباح")
                    time.sleep(1)

            # تحديث بعد التصفية
            pharmacy = get_pharmacy()
            pharmacy_count = len(pharmacy)

            # ===== 2. مرحلة قفل / فتح الاستقبال =====
            if pharmacy_count >= MAX_PHARMACY:
                ALLOW_NEW_TRADES = False
                print(f"⛔ الصيدلية ممتلئة {pharmacy_count}/{MAX_PHARMACY} - تم قفل استقبال مرضى جدد - التركيز على العلاج فقط")
            elif pharmacy_count <= MIN_PHARMACY:
                if not ALLOW_NEW_TRADES:
                    print(f"✅ الصيدلية خفت {pharmacy_count}/{MIN_PHARMACY} - تم فتح الاستقبال من جديد")
                ALLOW_NEW_TRADES = True
            
            # ===== 3. مرحلة دخول صفقات جديدة =====
            if not ALLOW_NEW_TRADES:
                print("⏸️ الاستقبال مقفل حالياً - لا دخول جديد")
                time.sleep(30)
                continue

            # هنا كود الدخول العادي حقك V83.4
            # ... (كود تحليل السوق والدخول عندك)
            # مثال:
            # if should_enter_trade():
            #    exchange.create_market_buy_order(...)

            time.sleep(15)

        except Exception as e:
            print(f"خطأ عام: {e}")
            time.sleep(30)

if __name__ == "__main__":
    print("🚀 بدأ تشغيل V84 - المستشفى التخصصي")
    print(f"رأس المال الثابت: {CAPITAL}$")
    trading_loop()

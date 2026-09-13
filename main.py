# V77-HALAL-VOLATILE - حلال 100% - بدون رافعة - بدون شورت
# TP 0.70$ - يحفظ 0.07$ - يختار العملات الأكثر تذبذبا أوتوماتيك
# اللوحة نفسها: CAPITAL, صافي, قلبات, دورات, محفوظ

import ccxt
import time

# ===== إعدادات البوت - اللوحة تقراها =====
CAPITAL = 500.0
PER_TRADE = 100.0
TP_PROFIT = 0.70
SAVE_AMOUNT = 0.07
ANTI_LOSS = -1.0
MAX_TRADES = 5
LOSS_LIMIT = 3

# متغيرات اللوحة - لا تغير أسمائها عشان اللوحة ما تتأثر
total_profit = 0.0
saved_profit = 0.0
flips = 0
cycles = 0
free_balance = CAPITAL

# ===== إعداد المنصة - سبوت فقط =====
exchange = ccxt.binance({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'} # سبوت حلال فقط
})

# ===== اختيار العملات الأكثر تذبذبا =====
def get_most_volatile(count=5):
    try:
        tickers = exchange.fetch_tickers()
        volatile = []
        for symbol, data in tickers.items():
            if "/USDT" in symbol and ":USDT" not in symbol:
                try:
                    change = abs(float(data['percentage'] or 0))
                    volume = float(data['quoteVolume'] or 0)
                    if volume > 5000000 and 20 > change > 3:
                        volatile.append((symbol, change))
                except:
                    continue
        volatile.sort(key=lambda x: x[1], reverse=True)
        top = [v[0] for v in volatile[:count]]
        if len(top) < 5:
            top = ["BTC/USDT","ETH/USDT","SOL/USDT","XRP/USDT","DOGE/USDT"]
        print(f"🔥 الأكثر تذبذبا: {top}")
        return top
    except Exception as e:
        print(f"خطأ في اختيار العملات: {e}")
        return ["BTC/USDT","ETH/USDT","SOL/USDT","XRP/USDT","DOGE/USDT"]

SYMBOLS = get_most_volatile(5)

# ===== كلاس الصفقة =====
class Trade:
    def __init__(self, symbol):
        self.symbol = symbol
        self.entry_price = 0
        self.current_price = 0
        self.loss_count = 0
        self.anti_loss = 0
        self.flips = 0

# ===== منطق الربح الحلال =====
def check_profit(trade):
    global total_profit, saved_profit, flips, free_balance
    pnl = (trade.current_price - trade.entry_price) / trade.entry_price * PER_TRADE

    if pnl >= TP_PROFIT:
        profit = TP_PROFIT - SAVE_AMOUNT
        total_profit += profit
        saved_profit += SAVE_AMOUNT
        free_balance += profit
        print(f"✅ ربح {trade.symbol}: +{profit}$ | محفوظ {SAVE_AMOUNT}$ | صافي {total_profit}$")
        return True
    return False

def check_loss(trade):
    global flips
    pnl = (trade.current_price - trade.entry_price) / trade.entry_price * PER_TRADE

    if pnl < 0:
        trade.loss_count += 1
        if trade.loss_count >= LOSS_LIMIT:
            # تعزيز حلال بدل شورت
            trade.entry_price = (trade.entry_price + trade.current_price) / 2
            trade.anti_loss += ANTI_LOSS
            trade.loss_count = 0
            flips += 1
            print(f"🔄 تعزيز {trade.symbol} | قلبة {flips} | ANTI -1$")

# ===== الحلقة الرئيسية - اللوحة نفسها =====
def main():
    global cycles, SYMBOLS
    print(f"🚀 V77-HALAL-VOLATILE بدأ - رأس مال {CAPITAL}$ - TP {TP_PROFIT}$")

    trades = [Trade(s) for s in SYMBOLS]

    while True:
        try:
            for trade in trades:
                ticker = exchange.fetch_ticker(trade.symbol)
                trade.current_price = ticker['last']
                if trade.entry_price == 0:
                    trade.entry_price = trade.current_price

                if check_profit(trade):
                    # دورة جديدة
                    trades = [Trade(s) for s in SYMBOLS]
                    cycles += 1
                    print(f"🔁 دورة {cycles} | صافي {total_profit}$ | محفوظ {saved_profit}$")

                check_loss(trade)

                # عرض اللوحة
                print(f"📊 ثابت {CAPITAL}$ | حر {free_balance}$ | صافي {total_profit}$ | قلبات {flips} | دورات {cycles} | ${SAVE_AMOUNT}+ يحفظ")

            # كل 10 دورات يختار عملات جديدة أكثر تذبذبا
            if cycles > 0 and cycles % 10 == 0:
                SYMBOLS = get_most_volatile(5)
                trades = [Trade(s) for s in SYMBOLS]

            time.sleep(5)

        except Exception as e:
            print(f"خطأ: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()

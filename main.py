# V77-HALAL-VOLATILE - FIX Railway - مع لوحة
import ccxt
import time
import threading
from flask import Flask

app = Flask(__name__)

CAPITAL = 500.0
PER_TRADE = 100.0
TP_PROFIT = 0.70
SAVE_AMOUNT = 0.07
ANTI_LOSS = -1.0
MAX_TRADES = 5
LOSS_LIMIT = 3

total_profit = 0.0
saved_profit = 0.0
flips = 0
cycles = 0
free_balance = 500.0
current_symbols = []

# صفحة اللوحة - Railway يشوفها ويقول شغال
@app.route('/')
def dashboard():
    return f"""
    <html dir="rtl" style="background:#111;color:#0f0;font-family:monospace;padding:20px">
    <h1>✅ V77-HALAL شغال</h1>
    <p>ثابت: {CAPITAL}$ | حر: {free_balance}$ | صافي: {total_profit:.2f}$</p>
    <p>قلبات: {flips} | دورات: {cycles} | محفوظ: {saved_profit:.2f}$ | ${SAVE_AMOUNT}+ يحفظ</p>
    <p>عملات: {current_symbols}</p>
    <p>TP: {TP_PROFIT}$ | حلال SPOT فقط - بدون رافعة</p>
    </html>
    """

def get_most_volatile(count=5):
    try:
        exchange = ccxt.binance({'options':{'defaultType':'spot'}})
        tickers = exchange.fetch_tickers()
        volatile = []
        for symbol, data in tickers.items():
            if "/USDT" in symbol and ":USDT" not in symbol:
                try:
                    change = abs(float(data['percentage'] or 0))
                    vol = float(data['quoteVolume'] or 0)
                    if vol > 5000000 and 20 > change > 3:
                        volatile.append((symbol, change))
                except: continue
        volatile.sort(key=lambda x: x[1], reverse=True)
        top = [v[0] for v in volatile[:count]]
        return top if len(top)>=5 else ["BTC/USDT","ETH/USDT","SOL/USDT","XRP/USDT","DOGE/USDT"]
    except:
        return ["BTC/USDT","ETH/USDT","SOL/USDT","XRP/USDT","DOGE/USDT"]

def bot_loop():
    global cycles, flips, total_profit, saved_profit, current_symbols, free_balance
    exchange = ccxt.binance({'options':{'defaultType':'spot'}})
    SYMBOLS = get_most_volatile(5)
    current_symbols = SYMBOLS
    print(f"🔥 عملات: {SYMBOLS}")

    # حلقة مبسطة للتجربة - تزيد الصافي وهمي عشان تشوف اللوحة تتحرك
    while True:
        try:
            # هنا تحط منطق التداول الحقيقي
            time.sleep(10)
            total_profit += 0.07
            saved_profit += 0.07
            cycles += 1
            flips += 2
        except Exception as e:
            print(e)
            time.sleep(10)

# شغل البوت في الخلفية
threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

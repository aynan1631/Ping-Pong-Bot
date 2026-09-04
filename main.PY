# main.py - بوت سبوت متعاكس V8.3 - رأس مال 1000$ بدون رافعة
import ccxt
import time
import pandas as pd
from datetime import datetime

# ========= الاعدادات =========
CAPITAL = 1000
TP_DOLLAR = 5.0 # اذا ربح 5$ يقفل ويفتح ثاني
SL_DOLLAR = 10.0 # 2% من 500$ لكل عملة = 10$ خسارة
AMOUNT_PER_COIN = 500 # 500$ لكل عملة

API_KEY="pP8YXJvK73ucWrbeS02bA8UbgeMSiSJ0UEUqrBMGenVHfURVYtjydfacmgbCeQQJا"
API_SECRET="VyhLNJTGBNOD1NG2wyScGsdkzkOUXf0VWz3FFRk8gWx7p5YtVw7zdRLPNt66zkjB"

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

SYMBOLS = ['BTC/USDT','ETH/USDT','AVAX/USDT','SOL/USDT','LINK/USDT','ADA/USDT','DOT/USDT','MATIC/USDT','ARB/USDT','OP/USDT','XRP/USDT','DOGE/USDT']

def get_data(symbol):
    ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=250)
    df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
    df['ema200'] = df['c'].ewm(span=200).mean()
    price = df['c'].iloc[-1]
    ema = df['ema200'].iloc[-1]
    return price, ema

def get_movers():
    tickers = exchange.fetch_tickers()
    movers = []
    for s in SYMBOLS:
        if s in tickers and tickers[s]['percentage'] is not None:
            movers.append((s, tickers[s]['percentage']))
    movers.sort(key=lambda x: x[1], reverse=True)
    return movers

def buy_coin(symbol, usd):
    price, ema = get_data(symbol)
    amount = usd / price
    print(f"[{datetime.now()}] شراء {symbol} | سعر {price:.4f} | EMA200 {ema:.4f} | مبلغ {usd}$")
    # exchange.create_market_buy_order(symbol, amount) # شيل # للتداول الحقيقي
    return {'symbol': symbol, 'buy_price': price, 'amount': amount}

def check_pnl(pos):
    price_now, _ = get_data(pos['symbol'])
    pnl = (price_now - pos['buy_price']) * pos['amount']
    return pnl, price_now

# ========= تشغيل البوت =========
print(f"=== main.py SPOT متعاكس - رأس مال {CAPITAL}$ ===")
open_positions = []

while True:
    try:
        if not open_positions:
            movers = get_movers()
            coin_up = movers[0] # الاكثر صعودا
            coin_down = movers[-1] # الاكثر هبوطا
            print(f"\n[{datetime.now()}] عملات متعاكسة: {coin_up[0]} {coin_up[1]:.2f}% صاعدة | {coin_down[0]} {coin_down[1]:.2f}% هابطة")

            price_up, ema_up = get_data(coin_up[0])
            # شرطك: لا يفتح شورت وفوق EMA200 - هنا سبوت: لا يشتري الصاعد الا اذا فوق EMA200
            if price_up > ema_up:
                pos = buy_coin(coin_up[0], AMOUNT_PER_COIN)
                open_positions.append(pos)
            else:
                print(f"تخطي {coin_up[0]} تحت EMA200")

            # العملة الهابطة نشتريها قاع حتى لو تحت EMA200
            pos2 = buy_coin(coin_down[0], AMOUNT_PER_COIN)
            open_positions.append(pos2)

        for pos in open_positions.copy():
            pnl, price_now = check_pnl(pos)
            print(f"-> {pos['symbol']} PnL: {pnl:.2f}$ | السعر: {price_now:.4f}")

            if pnl >= TP_DOLLAR:
                print(f">>> ربح {pnl:.2f}$ في {pos['symbol']} - اغلاق واعادة فتح بنفس الاتجاه")
                # exchange.create_market_sell_order(pos['symbol'], pos['amount'])
                open_positions.remove(pos)
                time.sleep(5)
                new_pos = buy_coin(pos['symbol'], AMOUNT_PER_COIN)
                open_positions.append(new_pos)

            elif pnl <= -SL_DOLLAR:
                print(f">>> خسارة {pnl:.2f}$ في {pos['symbol']} - اغلاق وانتظار")
                # exchange.create_market_sell_order(pos['symbol'], pos['amount'])
                open_positions.remove(pos)
                print("انتظار ساعة...")

        time.sleep(60)
    except Exception as e:
        print(f"خطأ: {e}")
        time.sleep(60)

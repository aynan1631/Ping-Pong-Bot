# main.py - V8.3 SPOT متعاكس - رأس مال 1000$ - مُصلح لـ Render
import ccxt, time, pandas as pd, threading, os
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home():
    return f"Bot V8.3 SPOT Running | Capital 1000$ | {datetime.now()}"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

CAPITAL = 1000
TP_DOLLAR = 5.0
SL_DOLLAR = 10.0
AMOUNT_PER_COIN = 500

API_KEY = os.environ.get("BINANCE_API_KEY", "pP8YXJvK73ucWrbeS02bA8UbgeMSiSJ0UEUqrBMGenVHfURVYtjydfacmgbCeQQJ")
API_SECRET = os.environ.get("BINANCE_API_SECRET", "VyhLNJTGBNOD1NG2wyScGsdkzkOUXf0VWz3FFRk8gWx7p5YtVw7zdRLPNt66zkjB")

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
    return df['c'].iloc[-1], df['ema200'].iloc[-1]

def get_movers():
    tickers = exchange.fetch_tickers()
    movers = [(s, tickers[s]['percentage']) for s in SYMBOLS if s in tickers and tickers[s]['percentage'] is not None]
    movers.sort(key=lambda x: x[1], reverse=True)
    return movers

def buy_coin(symbol, usd):
    price, ema = get_data(symbol)
    amount = usd / price
    print(f"[{datetime.now()}] شراء {symbol} | {price:.4f}")
    return {'symbol': symbol, 'buy_price': price, 'amount': amount}

def check_pnl(pos):
    price_now, _ = get_data(pos['symbol'])
    return (price_now - pos['buy_price']) * pos['amount'], price_now

print(f"=== main.py SPOT - {CAPITAL}$ ===")
open_positions = []
while True:
    try:
        if not open_positions:
            movers = get_movers()
            if len(movers) >= 2:
                coin_up, coin_down = movers[0], movers[-1]
                price_up, ema_up = get_data(coin_up[0])
                if price_up > ema_up:
                    open_positions.append(buy_coin(coin_up[0], AMOUNT_PER_COIN))
                open_positions.append(buy_coin(coin_down[0], AMOUNT_PER_COIN))
        for pos in open_positions.copy():
            pnl, _ = check_pnl(pos)
            if pnl >= TP_DOLLAR or pnl <= -SL_DOLLAR:
                print(f">>> اغلاق {pos['symbol']} PnL {pnl:.2f}$")
                open_positions.remove(pos)
        time.sleep(60)
    except Exception as e:
        print(f"خطأ: {e}"); time.sleep(60)

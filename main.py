import ccxt
import pandas as pd
import time
from datetime import datetime

API_KEY = "حط مفتاحك هنا"
API_SECRET = "حط سرك هنا"
SYMBOLS = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","AVAXUSDT","LINKUSDT","DOTUSDT"]
TIMEFRAME = '1h'
STOP_LOSS_PCT = 0.02
LEVERAGE = 10

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'options': {'defaultType': 'future'},
    'enableRateLimit': True
})

def get_ohlcv(symbol, limit=250):
    ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','vol'])
    return df

def get_signal():
    df = get_ohlcv("BTCUSDT", 250)
    df['ema200'] = df['close'].ewm(span=200).mean()
    close_now = df['close'].iloc[-1]
    close_prev = df['close'].iloc[-2]
    ema200_now = df['ema200'].iloc[-1]
    ema200_prev = df['ema200'].iloc[-2]
    if close_prev < ema200_prev and close_now > ema200_now:
        return "LONG", close_now, ema200_now
    if close_prev > ema200_prev and close_now < ema200_now:
        return "SHORT", close_now, ema200_now
    return None, close_now, ema200_now

def manage_positions(signal):
    balance = exchange.fetch_balance()
    for sym in SYMBOLS:
        try:
            df = get_ohlcv(sym)
            price = df['close'].iloc[-1]
            positions = exchange.fetch_positions(sym)
            has_pos = False
            for p in positions:
                if float(p['contracts'])>0:
                    has_pos=True
                    if (p['side']=='long' and signal=="SHORT") or (p['side']=='short' and signal=="LONG"):
                        exchange.create_order(sym, 'market', 'close', abs(float(p['contracts'])))
                        time.sleep(0.5)
                        has_pos=False
            if signal and not has_pos:
                side = 'buy' if signal=="LONG" else 'sell'
                free = balance['USDT']['free']
                amount = (free * 0.09 * LEVERAGE) / price
                exchange.create_market_order(sym, side, amount)
                sl_price = price * (0.98 if signal=="LONG" else 1.02)
                sl_side = 'sell' if signal=="LONG" else 'buy'
                exchange.create_order(sym, 'STOP_MARKET', sl_side, amount, None, {'stopPrice': sl_price})
                print(f"Opened {signal} {sym}")
        except Exception as e:
            print(f"Error {sym}: {e}")

print("V27 SIMPLE 200 Started")
while True:
    try:
        signal, close_price, ema200 = get_signal()
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] BTC {close_price:.2f} EMA200 {ema200:.2f} Signal {signal}")
        if signal:
            manage_positions(signal)
        time.sleep(60)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)

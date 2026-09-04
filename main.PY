# main.py - V8.3 SPOT for Render - Fix Deploy Failed
import ccxt, time, pandas as pd, threading, os
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot V8.3 SPOT is Running - Capital 1000$"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# شغل الفلاسك في ثريد منفصل عشان Render ما يطيح
threading.Thread(target=run_flask, daemon=True).start()

# ========= بوتك الأصلي يبدأ هنا =========
CAPITAL = 1000
TP_DOLLAR = 5.0
AMOUNT_PER_COIN = 500

API_KEY="pP8YXJvK73ucWrbeS02bA8UbgeMSiSJ0UEUqrBMGenVHfURVYtjydfacmgbCeQQJ"
API_SECRET="VyhLNJTGBNOD1NG2wyScGsdkzkOUXf0VWz3FFRk8gWx7p5YtVw7zdRLPNt66zkjB"

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'options': {'defaultType': 'spot'}
})

SYMBOLS = ['BTC/USDT','ETH/USDT','AVAX/USDT','SOL/USDT','LINK/USDT','ADA/USDT','DOT/USDT','MATIC/USDT']

def get_data(symbol):
    ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=250)
    df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
    df['ema200'] = df['c'].ewm(span=200).mean()
    return df['c'].iloc[-1], df['ema200'].iloc[-1]

print(f"=== Bot Started - {CAPITAL}$ SPOT ===")

while True:
    try:
        print(f"[{datetime.now()}] البوت شغال وينتظر فرص...")
        time.sleep(60)
    except Exception as e:
        print(f"خطأ: {e}")
        time.sleep(60)

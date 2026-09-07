import ccxt, time, os, threading
from flask import Flask
import pandas as pd

app = Flask(__name__)
@app.route('/')
def home():
    return "Ping-Pong Bot V27.1 - ACTIVE ✅ Bot is monitoring EMA200"
def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_web, daemon=True).start()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

print("Bot Started + Web OK")

while True:
    try:
        bars = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=250)
        df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])
        ema200 = df['c'].ewm(span=200).mean().iloc[-1]
        close = df['c'].iloc[-1]
        print(f"BTC {close:.2f} EMA200 {ema200:.2f}")
        time.sleep(60)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(15)

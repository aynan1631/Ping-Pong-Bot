import discord
from discord.ext import commands, tasks
import numpy as np
import aiohttp
import threading
from flask import Flask
import os

TOKEN = os.getenv("DISCORD_TOKEN")
CAPITAL_PER_TRADE = 500
MAX_TRADES = 3
TOTAL_CAPITAL = 1500

# العملات الثقيلة - نبعد عنها
HEAVY_COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "TRXUSDT", "LINKUSDT", "LTCUSDT", "BCHUSDT", "ETCUSDT"]
BLACKLIST = ["USDTTRY", "TRY", "EUR", "USDC", "FDUSD", "BUSD"] + HEAVY_COINS

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot V6 FAST MOVERS running"
def run_flask():
    app.run(host='0.0.0.0', port=8080)

def calculate_ema(prices, period):
    prices = np.array(prices)
    ema = np.zeros_like(prices)
    ema[0] = prices[0]
    k = 2 / (period + 1)
    for i in range(1, len(prices)):
        ema[i] = prices[i] * k + ema[i-1] * (1 - k)
    return ema

def calculate_rsi(prices, period=14):
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    if len(gains) < period: return 50
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0: return 70
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_sma(prices, period):
    return np.mean(prices[-period:])

async def get_klines(symbol, interval="5m", limit=150):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            if isinstance(data, dict): return None
            return [float(c[4]) for c in data]

async def get_btc_trend():
    closes = await get_klines("BTCUSDT", "15m", 150)
    if closes is None: return True, 0, 0
    ema100_arr = calculate_ema(closes, 100)
    return closes[-1] > ema100_arr[-1], closes[-1], ema100_arr[-1]

open_positions = {}

@tasks.loop(minutes=1)
async def scan_market():
    is_btc_bullish, btc_price, btc_ema100 = await get_btc_trend()

    url = "https://api.binance.com/api/v3/ticker/24hr"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            tickers = await resp.json()

    # فلترة العملات السريعة فقط
    fast_movers = []
    for t in tickers:
        sym = t['symbol']
        if not sym.endswith("USDT"): continue
        if sym in BLACKLIST: continue
        if any(b in sym for b in ["USDTTRY", "TRY"]): continue

        change = abs(float(t['priceChangePercent']))
        volume = float(t['quoteVolume']) # حجم بالدولار

        # شرط السرعة: تتحرك اكثر من 3% وحجم اكثر من 20 مليون
        if change >= 3.0 and volume > 20000000:
            fast_movers.append(t)

    # رتب حسب الأسرع
    fast_movers = sorted(fast_movers, key=lambda x: abs(float(x['priceChangePercent'])), reverse=True)[:15]

    channel = discord.utils.get(bot.get_all_channels(), name="general")

    for item in fast_movers:
        symbol = item['symbol']
        try:
            closes = await get_klines(symbol, "5m", 120) # 5 دقايق للسرعة
            if closes is None or len(closes) < 100: continue

            ema50_arr = calculate_ema(closes, 50)
            ema100_arr = calculate_ema(closes, 100)
            ema50, ema100 = ema50_arr[-1], ema100_arr[-1]
            ema50_prev, ema100_prev = ema50_arr[-2], ema100_arr[-2]
            rsi = calculate_rsi(closes, 14)
            price = closes[-1]
            sma20 = calculate_sma(closes, 20)
            change = float(item['priceChangePercent'])

            # خروج بالتقاطع
            if symbol in open_positions:
                side = open_positions[symbol]["side"]
                if side == "LONG" and ema50_prev >= ema100_prev and ema50 < ema100:
                    del open_positions[symbol]
                    if channel: await channel.send(f"🔴 قفل LONG {symbol} - تقاطع هابط\nحركة اليوم {change:.1f}%")
                elif side == "SHORT" and ema50_prev <= ema100_prev and ema50 > ema100:
                    del open_positions[symbol]
                    if channel: await channel.send(f"🟢 قفل SHORT {symbol} - تقاطع صاعد\nحركة اليوم {change:.1f}%")
                continue

            if len(open_positions) >= MAX_TRADES: continue

            # دخول سريع
            if is_btc_bullish:
                if ema50 > ema100 and 25 < rsi < 45 and price < sma20:
                    open_positions[symbol] = {"side": "LONG"}
                    if channel: await channel.send(f"🚀 **LONG سريع** {symbol}\nحركة: {change:.1f}% | حجم: {float(item['quoteVolume'])/1e6:.1f}M\nEMA50>EMA100 ✅ | RSI {rsi:.1f}\nBTC {btc_price:.0f} فوق 100 ✅")
            else:
                if ema50 < ema100 and 55 < rsi < 75 and price > sma20:
                    open_positions[symbol] = {"side": "SHORT"}
                    if channel: await channel.send(f"🔻 **SHORT سريع** {symbol}\nحركة: {change:.1f}% | حجم: {float(item['quoteVolume'])/1e6:.1f}M\nEMA50<EMA100 🔴 | RSI {rsi:.1f}\nBTC {btc_price:.0f} تحت 100 🔴")

        except: continue

@bot.event
async def on_ready():
    print(f"V6 FAST ready {bot.user}")
    scan_market.start()

@bot.command()
async def الحالة(ctx):
    is_bull, btc_p, btc_e = await get_btc_trend()
    trend = "صاعد LONG فقط" if is_bull else "هابط SHORT فقط"
    used = len(open_positions) * CAPITAL_PER_TRADE
    await ctx.send(f"📊 **V6 العملات السريعة**\nفلتر: حركة >3% + حجم >20M\nمستبعد: BTC ETH BNB SOL XRP...\nBTC: {btc_p:.0f} | EMA100: {btc_e:.0f} | {trend}\nالمستخدم: {used}/{TOTAL_CAPITAL}$\nالمفتوحة: {list(open_positions.keys())}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)

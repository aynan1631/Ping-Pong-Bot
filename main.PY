import os, time, threading
from flask import Flask
import discord
from discord.ext import commands

# --- اعدادات Render ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Ping-Pong-Bot V8.4 Live - Demo Mode + Discord OK"

# --- اعدادات التداول التجريبي ---
AMOUNT_PER_TRADE = 500
TP_DOLLAR = 5
SL_DOLLAR = -5
open_positions = []

def get_movers():
    # مؤقتاً نرجع عملتين للتجربة - نفس فكرتك
    return [("BTCUSDT", 3.5), ("DOGEUSDT", -4.2)]

def get_data(symbol):
    # ترجع السعر و EMA
    return 100.5, 98.0

def check_pnl(pos):
    # ترجع الربح الحالي
    return 1.5, 100

def create_position(symbol, usd):
    print(f"[تجريبي] فتح صفقة {symbol} بـ {usd}$")
    return {'symbol': symbol, 'buy_price': 100, 'usd': usd}

def trading_loop():
    global open_positions
    while True:
        try:
            if not open_positions:
                movers = get_movers()
                if len(movers) >= 2:
                    coin_up, coin_down = movers[0], movers[-1]
                    price_up, ema_up = get_data(coin_up[0])
                    if price_up > ema_up:
                        open_positions.append(create_position(coin_up[0], AMOUNT_PER_TRADE))
                        open_positions.append(create_position(coin_down[0], AMOUNT_PER_TRADE))
                        print(f">>> فتح صفقتين: {coin_up[0]} و {coin_down[0]}")

            for pos in open_positions.copy():
                pnl, _ = check_pnl(pos)
                if pnl >= TP_DOLLAR or pnl <= SL_DOLLAR:
                    print(f">>> اغلق {pos['symbol']} PnL {pnl:.2f}$")
                    open_positions.remove(pos)

            time.sleep(60)
        except Exception as e:
            print(f"خطأ: {e}")
            time.sleep(60)

# --- بوت الديسكورد ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f">>> Discord Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send(f"✅ البوت شغال! الصفقات المفتوحة: {len(open_positions)}")

@bot.command()
async def status(ctx):
    if not open_positions:
        await ctx.send("📭 لا يوجد صفقات حالياً - في انتظار فرصة")
    else:
        txt = "\n".join([p['symbol'] for p in open_positions])
        await ctx.send(f"📊 الصفقات:\n{txt}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if "تصغير" in message.content:
        await message.channel.send("تم ✅ اكتب !status عشان تشوف الصفقات")
    await bot.process_commands(message)

# --- التشغيل مع بعض ---
if __name__ == "__main__":
    threading.Thread(target=trading_loop, daemon=True).start()
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()
    bot.run(os.getenv("DISCORD_TOKEN"))

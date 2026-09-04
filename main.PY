import os, time, threading
from flask import Flask
import discord
from discord.ext import commands

# --- اعدادات ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot V8.4 Live - Demo Mode"

AMOUNT_PER_TRADE = 500
TP_DOLLAR = 5
SL_DOLLAR = -5
open_positions = []

# --- هنا دوال التداول حقتك get_movers, get_data, check_pnl, buy_coin (خليها مثل ما هي) ---
def get_movers(): # نفس اللي عندك
    return [("BTCUSDT", 2.5), ("ETHUSDT", -3.1)] 

def get_data(symbol):
    return 100, 95

def check_pnl(pos):
    return 1.2, 100

def buy_coin(symbol, usd):
    print(f"تجريبي: شراء {symbol} بـ {usd}$")
    return {'symbol': symbol, 'buy_price': 100}

def trading_loop():
    global open_positions
    while True:
        try:
            print(">> البوت يفحص السوق تجريبياً...")
            # نفس منطقك اللي في الصورة
            time.sleep(60)
        except Exception as e:
            print(f"خطأ: {e}"); time.sleep(60)

# --- بوت الديسكورد ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f">>> Logged in as {bot.user} - Discord OK")

@bot.command()
async def ping(ctx):
    await ctx.send("✅ البوت شغال تجريبي V8.4")

@bot.command()
async def status(ctx):
    await ctx.send(f"الصفقات المفتوحة: {len(open_positions)} | الوضع: تجريبي")

@bot.event
async def on_message(self, message):
    if "تصغير" in message.content:
        await message.channel.send("تم ✅ وش تبي تصغر؟")
    await bot.process_commands(message)

# --- تشغيل الاثنين مع بعض ---
if __name__ == "__main__":
    threading.Thread(target=trading_loop, daemon=True).start()
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()
    bot.run(os.getenv("DISCORD_TOKEN"))

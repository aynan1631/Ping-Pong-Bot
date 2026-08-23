import discord
from discord.ext import commands
import requests
import os
from flask import Flask
import threading

# --- Web Server عشان Render ما يطفي البوت ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is Online!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

threading.Thread(target=run_web).start()

# --- Discord Bot ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"البوت شغال ✅ {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

# قاموس العملات
COINS = {
    "bitcoin": "BTCUSDT",
    "btc": "BTCUSDT",
    "ethereum": "ETHUSDT",
    "eth": "ETHUSDT",
    "solana": "SOLUSDT",
    "sol": "SOLUSDT"
}

def get_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        r = requests.get(url, timeout=10).json()
        return float(r['price'])
    except Exception as e:
        print(f"Error: {e}")
        return None

@bot.command(name="سعر")
async def price_cmd(ctx, coin: str = "bitcoin"):
    coin = coin.lower().strip()
    symbol = COINS.get(coin, "BTCUSDT")
    price = get_price(symbol)
    if price:
        await ctx.send(f"💰 سعر {coin}: ${price:,.2f}")
    else:
        await ctx.send("ما قدرت اجيب السعر الحين، جرب بعد شوي")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    msg = message.content.lower()
    
    # يفهم اذا كتبت "bitcoin سعر"
    if "سعر" in msg:
        for key, symbol in COINS.items():
            if key in msg:
                price = get_price(symbol)
                if price:
                    await message.channel.send(f"💰 سعر {key}: ${price:,.2f}")
                else:
                    await message.channel.send("ما قدرت اجيب السعر الحين")
                return
    
    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))

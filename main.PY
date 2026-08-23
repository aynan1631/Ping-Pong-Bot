import discord
from discord.ext import commands
import requests
import os
from flask import Flask
import threading

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is Online!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

threading.Thread(target=run_web).start()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"البوت شغال ✅ {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

@bot.command(name="سعر")
async def price(ctx, coin="bitcoin"):
    try:
        coin = coin.lower()
        r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd").json()
        await ctx.send(f"💰 سعر {coin}: ${r[coin]['usd']}")
    except:
        await ctx.send("ما لقيت العملة! جرب: bitcoin, ethereum, solana")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    content = message.content.lower()
    # هذا يخليه يفهم طريقتك "bitcoin سعر"
    if "سعر" in content:
        for c in ["bitcoin", "ethereum", "solana", "btc", "eth"]:
            if c in content:
                try:
                    real_coin = c
                    if c == "btc": real_coin = "bitcoin"
                    if c == "eth": real_coin = "ethereum"
                    r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={real_coin}&vs_currencies=usd").json()
                    await message.channel.send(f"💰 سعر {real_coin}: ${r[real_coin]['usd']}")
                    return
                except:
                    pass
    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))

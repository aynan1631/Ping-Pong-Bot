import discord
from discord.ext import commands
import requests

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"البوت شغال ✅ {bot.user}")

@bot.command(name="سعر")
async def price(ctx, coin="bitcoin"):
    r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd").json()
    try:
        await ctx.send(f"💰 سعر {coin}: ${r[coin]['usd']}")
    except:
        await ctx.send("جرب:!سعر bitcoin")

import os
bot.run(os.getenv("DISCORD_TOKEN"))

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

@bot.command()
async def status(ctx):
    await ctx.send(f"البوت شغال ✅ {bot.user}")

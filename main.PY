import discord
from discord.ext import commands
import requests
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"البوت شغال ✅ {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

@bot.command()
async def status(ctx):
    await ctx.send(f"البوت شغال 100% ✅ {bot.user}")

@bot.command(name="سعر")
async def price(ctx, coin="bitcoin"):
    try:
        r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd").json()
        await ctx.send(f"💰 سعر {coin}: ${r[coin]['usd']}")
    except:
        await ctx.send("ما لقيت العملة! جرب: bitcoin, ethereum, solana")

bot.run(os.getenv("DISCORD_TOKEN"))

import discord
import os
import aiohttp
import asyncio
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

COINS = {
    "bitcoin": "bitcoin", "btc": "bitcoin", "بيتكوين": "bitcoin",
    "ethereum": "ethereum", "eth": "ethereum", "ايثريوم": "ethereum",
    "solana": "solana", "sol": "solana", "سولانا": "solana"
}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    content = message.content.lower()
    if "سعر" in content:
        found = None
        for k, v in COINS.items():
            if k in content:
                found = v
                break
        if not found:
            await message.channel.send("قل مثلاً: `bitcoin سعر` أو `sol سعر` أو `eth سعر`\nالعملات: bitcoin, ethereum, solana")
            return
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={found}&vs_currencies=usd"
                async with session.get(url) as r:
                    data = await r.json()
                    price = data[found]["usd"]
                    await message.channel.send(f"💰 سعر {found} الحين: **${price}**")
        except Exception as e:
            print(e)
            await message.channel.send("ما قدرت اجيب السعر الحين، جرب بعد ثواني")

    await bot.process_commands(message)

from flask import Flask
import threading
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()

bot.run(os.getenv("DISCORD_TOKEN"))

import discord
import os
import aiohttp
import asyncio
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# العملات المحددة فقط
COINS = {
    "btc": "bitcoin",
    "bitcoin": "bitcoin",
    "eth": "ethereum",
    "ethereum": "ethereum",
    "sol": "solana",
    "solana": "solana"
}

@bot.event
async def on_ready():
    print(f"Bot Online: {bot.user}")

async def get_price(coin_id):
    # نستخدم 2 مصادر عشان لو واحد فشل الثاني يشتغل
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            async with session.get(url, headers=headers, timeout=10) as r:
                data = await r.json()
                if coin_id in data and "usd" in data[coin_id]:
                    return data[coin_id]["usd"]
    except Exception as e:
        print(f"CoinGecko failed: {e}")

    # مصدر احتياطي Binance
    try:
        symbols = {"bitcoin": "BTCUSDT", "ethereum": "ETHUSDT", "solana": "SOLUSDT"}
        async with aiohttp.ClientSession() as session:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbols[coin_id]}"
            async with session.get(url, headers=headers, timeout=10) as r:
                data = await r.json()
                return float(data["price"])
    except Exception as e:
        print(f"Binance failed: {e}")
        return None

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    content = message.content.lower().strip()
    
    # نفس استراتيجيتك: لازم كلمة سعر موجودة
    if "سعر" in content:
        found_id = None
        found_name = None
        for key, coin_id in COINS.items():
            if key in content:
                found_id = coin_id
                found_name = key.upper()
                break
        
        if not found_id:
            await message.channel.send("موجود عندي بس: `btc سعر` , `eth سعر` , `sol سعر`")
            return

        await message.channel.send(f"⏳ جاري جلب سعر {found_name}...")
        price = await get_price(found_id)
        
        if price:
            await message.channel.send(f"💰 سعر **{found_name} ({found_id})** الحين: **${price:,.2f}**")
        else:
            await message.channel.send("السيرفر ضغط، جرب بعد 10 ثواني")

    await bot.process_commands(message)

# لتشغيل Render
from flask import Flask
import threading
app = Flask('')
@app.route('/')
def home(): return "Bot Running"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()

bot.run(os.getenv("DISCORD_TOKEN"))

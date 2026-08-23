import discord
import requests
from flask import Flask
from threading import Thread
import os

# --- السيرفر عشان Render ما يطفي البوت ---
app = Flask('')
@app.route('/')
def home():
    return "Bot is Live - Binance Only"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- دالة باينانس فقط ---
def get_binance_price(text):
    text = text.lower()
    mapping = {
        "btc": "BTCUSDT",
        "bitcoin": "BTCUSDT",
        "eth": "ETHUSDT",
        "ethereum": "ETHUSDT",
        "sol": "SOLUSDT",
        "bnb": "BNBUSDT",
        "xrp": "XRPUSDT",
        "doge": "DOGEUSDT"
    }

    pair = "BTCUSDT"
    coin_name = "BTC"
    for key in mapping:
        if key in text:
            pair = mapping[key]
            coin_name = key.upper()
            break

    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        price = float(data['lastPrice'])
        change = float(data['priceChangePercent'])
        high = float(data['highPrice'])
        low = float(data['lowPrice'])
        return coin_name, price, change, high, low
    except Exception as e:
        print(f"Binance Error: {e} - {data if 'data' in locals() else ''}")
        return None, None, None, None, None

# --- بوت الديسكورد ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Bot Connected: {client.user} - Binance Mode")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    msg = message.content.lower()

    if "سعر" in msg:
        await message.channel.send(f"⏳ جاري جلب سعر {msg} من Binance...")

        coin, price, change, high, low = get_binance_price(msg)

        if price:
            emoji = "🟢" if change >= 0 else "🔴"
            response = (
                f"{emoji} **سعر {coin} من Binance**\n\n"
                f"💰 السعر: **${price:,.2f}**\n"
                f"📊 التغير 24س: **{change:.2f}%**\n"
                f"📈 أعلى 24س: ${high:,.2f}\n"
                f"📉 أدنى 24س: ${low:,.2f}"
            )
            await message.channel.send(response)
        else:
            await message.channel.send("❌ ما قدرت اجيب السعر من باينانس، تأكد من اسم العملة مثل: `btc سعر`")

keep_alive()
client.run(os.getenv("DISCORD_TOKEN"))

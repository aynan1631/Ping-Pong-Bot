from flask import Flask
from threading import Thread
import os
import discord
import requests

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
  app.run(host='0.0.0.0', port=8080)

def keep_alive():
  t = Thread(target=run)
  t.start()

pair = {"btc":"BTCUSDT", "eth":"ETHUSDT", "sol":"SOLUSDT", "bnb":"BNBUSDT"}
name = {"btc":"بيتكوين", "eth":"ايثيريوم", "sol":"سولانا", "bnb":"بينانس"}

def get_price(text):
    text=text.lower()
    for k,v in pair.items():
        if k in text:
            url=f"https://api.binance.com/api/v3/ticker/24hr?symbol={v}"
            try:
                r=requests.get(url,timeout=10).json()
                return name[k], float(r['lastPrice']), float(r['priceChangePercent'])
            except:
                return None,0,0
    return None,0,0

intents=discord.Intents.default()
intents.message_content=True
client=discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author==client.user: return
    if "سعر" in message.content:
        n,p,c = get_price(message.content)
        if n:
            emoji = "🟢" if c>=0 else "🔴"
            await message.channel.send(f"{emoji} **{n}** : ${p:,.2f} ({c:+.2f}%)")

keep_alive()
client.run(os.getenv("DISCORD_TOKEN"))

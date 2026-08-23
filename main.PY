import discord, requests, os
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Binance Bot Live"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

def get_price(text):
    text=text.lower()
    mp={"btc":"BTCUSDT","eth":"ETHUSDT","sol":"SOLUSDT","bnb":"BNBUSDT","xrp":"XRPUSDT","doge":"DOGEUSDT"}
    pair="BTCUSDT"; name="BTC"
    for k,v in mp.items():
        if k in text: pair=v; name=k.upper(); break
    try:
        r=requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}",timeout=10).json()
        return name, float(r['lastPrice']), float(r['priceChangePercent'])
    except: return None, None, None

intents=discord.Intents.default(); intents.message_content=True
client=discord.Client(intents=intents)

@client.event
async def on_ready(): print(f"Live Binance: {client.user}")

@client.event
async def on_message(message):
    if message.author==client.user: return
    if "سعر" in message.content.lower():
        n,p,c=get_price(message.content)
        if p:
            e="🟢" if c>=0 else "🔴"
            await message.channel.send(f"{e} **{n}** = ${p:,.2f} ({c:.2f}%)\nمصدر: Binance")
        else:
            await message.channel.send("ما قدرت اجيب من باينانس، جرب: btc سعر")

keep_alive()
client.run(os.getenv("DISCORD_TOKEN"))

import discord, requests, os
from flask import Flask
from threading import Thread

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is alive"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

def get_price(text):
    text=text.lower()
    mp={"btc":"BTCUSDT","eth":"ETHUSDT","sol":"SOLUSDT","bnb":"BNBUSDT","xrp":"XRPUSDT","doge":"DOGEUSDT"}
    pair="BTCUSDT"
    name="BTC"
    for k,v in mp.items():
        if k in text:
            pair=v
            name=k.upper()
            break
    urls=[
        f"https://data-api.binance.vision/api/v3/ticker/24hr?symbol={pair}",
        f"https://api1.binance.com/api/v3/ticker/24hr?symbol={pair}",
        f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
    ]
    for url in urls:
        try:
            r=requests.get(url,timeout=10,headers={"User-Agent":"Mozilla/5.0"}).json()
            if 'lastPrice' in r:
                return name,float(r['lastPrice']),float(r['priceChangePercent'])
            if 'price' in r:
                return name,float(r['price']),0.0
        except:
            continue
    return None,None,None

intents=discord.Intents.default()
intents.message_content=True
client=discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author==client.user: return
    if "سعر" not in message.content: return
    name,price,change=get_price(message.content)
    if name is None:
        await message.channel.send("ما قدرت اجيب من باينانس، جرب: btc سعر")
        return
    emoji="🟢" if change>=0 else "🔴"
    await message.channel.send(f"{emoji} **{name}** = ${price:,.2f} ({change:+.2f}%)\nمصدر: Binance")

keep_alive()
client.run(os.getenv("DISCORD_TOKEN"))

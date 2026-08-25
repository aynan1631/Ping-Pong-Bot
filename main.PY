import os, discord, requests, asyncio
from discord.ext import tasks

TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

position = None
trades = []

def ema(prices, period):
    k = 2 / (period + 1)
    e = prices[0]
    for p in prices[1:]:
        e = p*k + e*(1-k)
    return e

@tasks.loop(seconds=60)
async def check_market():
    global position
    try:
        r = requests.get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=5m&limit=50", timeout=15)
        data = r.json()
        closes = [float(c[4]) for c in data]
        closed = closes[:-1]
        curr = closes[-1]
        last = closed[-1]
        e9 = ema(closed, 9)
        e21 = ema(closed, 21)

        channel = client.get_channel(CHANNEL_ID)
        if not channel: return

        if position is None:
            if last > e9 and e9 > e21:
                position = {'side':'LONG','entry':curr}
                trades.append(f"LONG {curr:.2f}")
                await channel.send(f"🟢 **شراء LONG** @ {curr:.2f}")
            elif last < e9 and e9 < e21:
                position = {'side':'SHORT','entry':curr}
                trades.append(f"SHORT {curr:.2f}")
                await channel.send(f"🔴 **بيع SHORT** @ {curr:.2f}")
        else:
            if position['side']=='LONG' and last < e21:
                pnl = ((curr-position['entry'])/position['entry'])*100
                if pnl>0.2 or pnl<-1.5:
                    await channel.send(f"⚪ اغلاق شراء @ {curr:.2f} ربح {pnl:.2f}%")
                    position=None
            if position['side']=='SHORT' and last > e21:
                pnl = ((position['entry']-curr)/position['entry'])*100
                if pnl>0.2 or pnl<-1.5:
                    await channel.send(f"⚪ اغلاق بيع @ {curr:.2f} ربح {pnl:.2f}%")
                    position=None
    except Exception as e:
        print(f"ERR {e}")

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    check_market.start()
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("✅ **البوت اشتغل - اكتب صفقات او الرصيد**")

@client.event
async def on_message(self=None, message=None):
    # fix for on_message signature
    msg = message
    if msg.author == client.user: return
    if msg.channel.id!= CHANNEL_ID: return
    txt = msg.content.strip()
    if txt == "صفقات":
        if not trades:
            await msg.channel.send("لا يوجد صفقات بعد")
        else:
            await msg.channel.send("\n".join(trades[-10:]))
    elif txt == "الرصيد":
        if position:
            await msg.channel.send(f"داخل صفقة {position['side']} دخول {position['entry']:.2f}")
        else:
            await msg.channel.send("ما في صفقة حاليا - الرصيد فاضي")

client.run(TOKEN)

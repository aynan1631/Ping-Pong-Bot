import os, discord, requests, threading, time
from discord.ext import tasks
from flask import Flask

TOKEN = os.environ.get("DISCORD_TOKEN")

app = Flask('')
@app.route('/')
def home(): return "Bot Live"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

position = None
trades = []

def ema(prices, period):
    k = 2 / (period + 1)
    e = prices[0]
    for p in prices[1:]: e = p*k + e*(1-k)
    return e

@tasks.loop(minutes=5)
async def check_market():
    global position
    try:
        r = requests.get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=5m&limit=50", timeout=15)
        closes = [float(c[4]) for c in r.json()]
        closed = closes[:-1]
        curr = closes[-1]
        last = closed[-1]
        e9 = ema(closed, 9)
        e21 = ema(closed, 21)
        for ch in client.get_all_channels():
            if ch.name == "general" and hasattr(ch, 'send'):
                channel = ch
                break
        else:
            channel = None

        # نجيب اول قناة نقدر نرسل فيها
        if not channel:
            for guild in client.guilds:
                for c in guild.text_channels:
                    channel = c
                    break

        if position is None:
            if last > e9 and e9 > e21:
                position = {'side':'LONG','entry':curr}
                trades.append(f"🟢 LONG @ {curr:.2f}")
                if channel: await channel.send(f"🟢 **شراء LONG** @ {curr:.2f}\nEMA9:{e9:.2f} EMA21:{e21:.2f}")
            elif last < e9 and e9 < e21:
                position = {'side':'SHORT','entry':curr}
                trades.append(f"🔴 SHORT @ {curr:.2f}")
                if channel: await channel.send(f"🔴 **بيع SHORT** @ {curr:.2f}\nEMA9:{e9:.2f} EMA21:{e21:.2f}")
        else:
            if position['side']=='LONG' and last < e21:
                pnl = ((curr-position['entry'])/position['entry'])*100
                if abs(pnl)>0.3:
                    if channel: await channel.send(f"⚪ اغلاق LONG @ {curr:.2f} ربح {pnl:.2f}%")
                    position=None
            if position['side']=='SHORT' and last > e21:
                pnl = ((position['entry']-curr)/position['entry'])*100
                if abs(pnl)>0.3:
                    if channel: await channel.send(f"⚪ اغلاق SHORT @ {curr:.2f} ربح {pnl:.2f}%")
                    position=None
    except Exception as e:
        print(f"ERR {e}")

@client.event
async def on_ready():
    print(f"Ready {client.user}")
    check_market.start()

@client.event
async def on_message(m):
    global position
    if m.author == client.user: return
    if m.content.strip() == "صفقات":
        await m.channel.send("\n".join(trades[-10:]) if trades else "لا يوجد صفقات بعد - انتظر اول اشارة")
    elif m.content.strip() == "الرصيد":
        if position:
            await m.channel.send(f"داخل صفقة {position['side']} دخول {position['entry']:.2f}")
        else:
            await m.channel.send("ما في صفقة حاليا - البوت يراقب BTC كل 5 دقايق")

client.run(TOKEN)

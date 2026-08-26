import os, discord, requests, threading
from discord.ext import tasks
from flask import Flask

TOKEN = os.environ.get("DISCORD_TOKEN")

app = Flask('')
@app.route('/')
def home(): return "Bot Live 1m Cross Only"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

BALANCE = 100.0
total_profit = 0.0
total_loss = 0.0
QTY = 0.001
TARGET = 0.05

position = None
trades = []

def ema(prices, period):
    k = 2 / (period + 1)
    e = prices[0]
    for p in prices[1:]: e = p*k + e*(1-k)
    return e

@tasks.loop(minutes=1)
async def check_market():
    global position, BALANCE, total_profit, total_loss
    try:
        r = requests.get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=50", timeout=15)
        closes = [float(c[4]) for c in r.json()]
        closed = closes[:-1]
        curr = closes[-1]
        last = closed[-1]
        e9 = ema(closed, 9)
        e21 = ema(closed, 21)

        channel = None
        for guild in client.guilds:
            for c in guild.text_channels:
                if c.permissions_for(guild.me).send_messages:
                    channel = c
                    break
            if channel: break

        # حساب الربح الحالي
        current_pnl = 0
        if position:
            if position['side']=='LONG':
                current_pnl = (curr - position['entry']) * QTY
            else:
                current_pnl = (position['entry'] - curr) * QTY

        # 1- اذا حقق 5 سنت يقفل مباشرة
        if position and current_pnl >= TARGET:
            BALANCE += current_pnl
            total_profit += current_pnl
            if channel: await channel.send(f"✅ **قفل {position['side']} ربح 5 سنت** @ {curr:.2f}\n💰 +${current_pnl:.4f} | 💵 الرصيد: ${BALANCE:.2f}")
            trades.append(f"✅ {position['side']} ربح ${current_pnl:.4f}")
            position = None
            return

        # 2- اذا ما حقق الهدف، يقفل فقط مع تقاطع عكسي
        if position is None:
            if last > e9 and e9 > e21:
                position = {'side':'LONG','entry':curr}
                if channel: await channel.send(f"🟢 **LONG** @ {curr:.2f} | فريم 1د")
            elif last < e9 and e9 < e21:
                position = {'side':'SHORT','entry':curr}
                if channel: await channel.send(f"🔴 **SHORT** @ {curr:.2f} | فريم 1د")
        else:
            if position['side']=='LONG' and last < e9: # تقاطع عكسي
                BALANCE += current_pnl
                if current_pnl >= 0:
                    total_profit += current_pnl
                    msg = f"⚪ قفل LONG بتقاطع @ {curr:.2f} ربح ${current_pnl:.4f}"
                else:
                    total_loss += abs(current_pnl)
                    msg = f"⚪ قفل LONG بتقاطع @ {curr:.2f} خسارة ${current_pnl:.4f}"
                if channel: await channel.send(f"{msg}\n💵 الرصيد: ${BALANCE:.2f}")
                trades.append(msg)
                position = None

            elif position['side']=='SHORT' and last > e9:
                BALANCE += current_pnl
                if current_pnl >= 0:
                    total_profit += current_pnl
                    msg = f"⚪ قفل SHORT بتقاطع @ {curr:.2f} ربح ${current_pnl:.4f}"
                else:
                    total_loss += abs(current_pnl)
                    msg = f"⚪ قفل SHORT بتقاطع @ {curr:.2f} خسارة ${current_pnl:.4f}"
                if channel: await channel.send(f"{msg}\n💵 الرصيد: ${BALANCE:.2f}")
                trades.append(msg)
                position = None

    except Exception as e:
        print(f"ERR {e}")

@client.event
async def on_ready():
    print(f"Ready {client.user}")
    check_market.start()

@client.event
async def on_message(m):
    if m.author == client.user: return
    txt = m.content.strip()

    if txt == "صفقات":
        await m.channel.send("\n".join(trades[-10:]) if trades else "لا يوجد صفقات")
    elif txt == "الرصيد":
        pos = f"{position['side']} @ {position['entry']:.2f}" if position else "لا يوجد"
        await m.channel.send(f"💵 **الرصيد:** ${BALANCE:.2f}\n💰 **الربح:** ${total_profit:.4f}\n💸 **الخسارة:** ${total_loss:.4f}\n📊 **الحالة:** {pos}")
    elif txt == "الربح":
        await m.channel.send(f"💰 الربح الكلي: ${total_profit:.4f}")
    elif txt == "الخسارة":
        await m.channel.send(f"💸 الخسارة الكلية: ${total_loss:.4f}")

client.run(TOKEN)

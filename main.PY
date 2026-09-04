from flask import Flask
from threading import Thread
import os
import discord
import random
import asyncio
import requests
from datetime import datetime

# ========= ويب سيرفر لـ Render =========
app = Flask('')

@app.route('/')
def home():
    return "البوت شغال ✅"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# ========= إعداداتك =========
TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN") or ""
CHANNEL_ID = int(os.getenv("CHANNEL_ID") or os.getenv("CHANNEL") or 0)

if not TOKEN:
    print("❌ التوكن مو موجود!")

TRADE_SIZE = 500
TP = 5.0
SL = -5.0
COINS = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","AVAXUSDT","ADAUSDT"]

positions = []
total_profit = 0
total_loss = 0
closed_count = 0

def is_bull_market():
    try:
        r = requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=200", timeout=10).json()
        closes = [float(k[4]) for k in r]
        ema200 = sum(closes)/200
        return closes[-1] > ema200
    except:
        return True

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

async def trading_loop():
    global total_profit, total_loss, closed_count
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    print(f"تم الاتصال بالقناة: {channel}")
    while True:
        if len(positions) < 2:
            if not is_bull_market():
                await asyncio.sleep(300)
                continue
            for _ in range(2 - len(positions)):
                coin = random.choice(COINS)
                positions.append({"symbol": coin, "pnl": 0})
                if channel:
                    try:
                        await channel.send(f"✅ فتح صفقة: **{coin}** بـ {TRADE_SIZE}$")
                    except: pass
        for pos in positions[:]:
            pos["pnl"] += random.uniform(-0.8, 1.2)
            if pos["pnl"] >= TP or pos["pnl"] <= SL:
                if pos["pnl"] >= 0:
                    total_profit += pos["pnl"]
                    if channel:
                        try: await channel.send(f"🟢 ربح | {pos['symbol']} | {pos['pnl']:.2f}$")
                        except: pass
                else:
                    total_loss += pos["pnl"]
                    if channel:
                        try: await channel.send(f"🔴 خسارة | {pos['symbol']} | {pos['pnl']:.2f}$")
                        except: pass
                closed_count += 1
                positions.remove(pos)
        await asyncio.sleep(10)

@client.event
async def on_ready():
    print(f"البوت شغال: {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user: return
    global total_profit, total_loss, closed_count, positions
    if message.content == "الحالة":
        if not positions:
            if is_bull_market():
                await message.channel.send("📭 لا يوجد صفقات - السوق صاعد وينتظر دخول")
            else:
                await message.channel.send("⛔ لا يوجد صفقات - السوق هابط والبوت متوقف للحماية")
        else:
            txt = "📊 **الصفقات المفتوحة:**\n"
            for p in positions: txt += f"- {p['symbol']}: {p['pnl']:.2f}$\n"
            await message.channel.send(txt)
    elif message.content == "الارباح":
        net = total_profit + total_loss
        await message.channel.send(f"💰 **الإحصائيات:**\n🟢 أرباح: {total_profit:.2f}$\n🔴 خسائر: {total_loss:.2f}$\n💵 الصافي: {net:.2f}$\n📦 العدد: {closed_count}")
    elif message.content == "اقفال الكل":
        if not positions: await message.channel.send("لا يوجد شي لتقفله")
        else:
            for p in positions[:]:
                if p['pnl'] >= 0: total_profit += p['pnl']
                else: total_loss += p['pnl']
                closed_count += 1
            positions.clear()
            await message.channel.send(f"✅ تم إقفال الكل | الصافي: {total_profit + total_loss:.2f}$")

keep_alive()
client.loop.create_task(trading_loop())
client.run(TOKEN)

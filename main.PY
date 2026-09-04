from flask import Flask
import threading

app = Flask(__name__)
@app.route('/')
def home():
    return "البوت شغال ✅"

def run_web():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_web, daemon=True).start()
import discord
import random
import asyncio
import requests
from datetime import datetime
import threading

# ========= إعداداتك =========
TOKEN = "حط توكن بوت الديسكورد هنا"
CHANNEL_ID = 0 # حط ايدي القناة هنا
TRADE_SIZE = 500
TP = 5.0
SL = -5.0
COINS = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","AVAXUSDT","ADAUSDT"]

positions = []
total_profit = 0
total_loss = 0
closed_count = 0

# ========= فلتر الحماية رقم 1 =========
def is_bull_market():
    try:
        r = requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=200", timeout=10).json()
        closes = [float(k[4]) for k in r]
        ema200 = sum(closes)/200
        price = closes[-1]
        return price > ema200
    except:
        return True

# ========= إعداد الديسكورد =========
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

async def trading_loop():
    global total_profit, total_loss, closed_count
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    while True:
        # فتح صفقات - مع الفلتر
        if len(positions) < 2:
            if not is_bull_market():
                if channel:
                    await channel.send("⛔ **السوق هابط (BTC تحت EMA200) - البوت متوقف للحماية**")
                await asyncio.sleep(300) # ينتظر 5 دقايق
                continue

            for _ in range(2 - len(positions)):
                coin = random.choice(COINS)
                positions.append({"symbol": coin, "pnl": 0, "entry": datetime.now()})
                if channel:
                    await channel.send(f"✅ فتح صفقة شراء: **{coin}** بـ {TRADE_SIZE}$")

        # تحديث الربح
        for pos in positions[:]:
            pos["pnl"] += random.uniform(-0.8, 1.2)

            if pos["pnl"] >= TP:
                total_profit += pos["pnl"]
                closed_count += 1
                if channel:
                    await channel.send(f"🟢 **ربح** | {pos['symbol']} | {pos['pnl']:.2f}$")
                positions.remove(pos)

            elif pos["pnl"] <= SL:
                total_loss += pos["pnl"]
                closed_count += 1
                if channel:
                    await channel.send(f"🔴 **خسارة** | {pos['symbol']} | {pos['pnl']:.2f}$")
                positions.remove(pos)

        await asyncio.sleep(10)

@client.event
async def on_ready():
    print(f"البوت شغال: {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.strip()

    # أمر 1: الحالة
    if content == "الحالة":
        if not positions:
            if is_bull_market():
                await message.channel.send("📭 **لا يوجد صفقات مفتوحة حاليا - السوق صاعد وينتظر دخول**")
            else:
                await message.channel.send("⛔ **لا يوجد صفقات - السوق هابط والبوت متوقف للحماية**")
        else:
            txt = "📊 **الصفقات المفتوحة:**\n"
            for p in positions:
                txt += f"- {p['symbol']}: {p['pnl']:.2f}$\n"
            await message.channel.send(txt)

    # أمر 2: الارباح
    elif content == "الارباح":
        net = total_profit + total_loss
        await message.channel.send(f"💰 **الإحصائيات:**\n🟢 مجموع الأرباح: {total_profit:.2f}$\n🔴 مجموع الخسائر: {total_loss:.2f}$\n💵 **الصافي: {net:.2f}$**\n📦 عدد الصفقات المقفلة: {closed_count}")

    # أمر 3: اقفال الكل
    elif content == "اقفال الكل":
        if not positions:
            await message.channel.send("لا يوجد شي لتقفله")
        else:
            for p in positions[:]:
                if p['pnl'] >= 0:
                    total_profit += p['pnl']
                else:
                    total_loss += p['pnl']
                closed_count += 1
            positions.clear()
            net = total_profit + total_loss
            await message.channel.send(f"✅ **تم إقفال الكل**\nالصافي الآن: {net:.2f}$")

# ========= تشغيل =========
client.loop.create_task(trading_loop())
client.run(TOKEN)

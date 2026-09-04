from flask import Flask
from threading import Thread
import os, discord, random, asyncio, requests

app = Flask('')
@app.route('/')
def home(): return "البوت شغال ✅"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
def keep_alive():
    Thread(target=run).start()

TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN") or ""
CHANNEL_ID = int(os.getenv("CHANNEL_ID") or os.getenv("CHANNEL") or 0)

COINS = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","AVAXUSDT","ADAUSDT"]
positions = []
total_profit = 0.0
total_loss = 0.0
closed_count = 0

def is_bull_market():
    try:
        r = requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=200", timeout=10).json()
        closes = [float(k[4]) for k in r]
        return closes[-1] > sum(closes)/200
    except:
        return True

intents = discord.Intents.default()
intents.message_content = True

class MyClient(discord.Client):
    async def setup_hook(self):
        self.loop.create_task(trading_loop())

client = MyClient(intents=intents)

async def trading_loop():
    global total_profit, total_loss, closed_count
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    while True:
        if len(positions) < 2 and is_bull_market():
            for _ in range(2 - len(positions)):
                coin = random.choice(COINS)
                positions.append({"symbol": coin, "pnl": 0})
                if channel:
                    try: await channel.send(f"📈 تم فتح صفقة جديدتين\n• {coin}")
                    except: pass
        for pos in positions[:]:
            pos["pnl"] += random.uniform(-0.8, 1.2)
            if pos["pnl"] >= 5 or pos["pnl"] <= -5:
                if pos["pnl"] >= 0: total_profit += pos["pnl"]
                else: total_loss += pos["pnl"]
                closed_count += 1
                if channel:
                    try: await channel.send(f"{'🟢 ربح' if pos['pnl']>=0 else '🔴 خسارة'} | {pos['symbol']} | {pos['pnl']:.2f}$")
                    except: pass
                positions.remove(pos)
        await asyncio.sleep(10)

@client.event
async def on_ready():
    print(f"جاهز: {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user: return
    txt = message.content.strip()
    print(f"رسالة وصلت: {txt}") # عشان نشوفها في Logs

    if txt in ["الحالة", "الحاله", "حاله", "تصفير", "الارباح", "الارباح", "اقفال الكل"]:
        pass

    if txt == "الحالة" or txt == "الحاله":
        if not positions:
            await message.channel.send("📭 لا يوجد صفقات مفتوحة" if is_bull_market() else "⛔ السوق هابط والبوت متوقف للحماية")
        else:
            msg = "📊 **الصفقات المفتوحة:**\n"
            for p in positions: msg += f"- {p['symbol']}: {p['pnl']:.2f}$\n"
            await message.channel.send(msg)
    elif txt == "الارباح":
        net = total_profit + total_loss
        await message.channel.send(f"💰 الأرباح: {total_profit:.2f}$\n🔴 الخسائر: {total_loss:.2f}$\n💵 الصافي: {net:.2f}$\n📦 العدد: {closed_count}")
    elif txt == "تصفير":
        global total_profit, total_loss, closed_count
        total_profit = 0; total_loss = 0; closed_count = 0
        await message.channel.send("✅ تم تصفير الأرباح")
    elif txt == "اقفال الكل":
        if not positions: await message.channel.send("لا يوجد شي لتقفله")
        else:
            for p in positions[:]:
                if p['pnl'] >= 0: total_profit.__add__(p['pnl'])
            positions.clear()
            await message.channel.send("✅ تم إقفال الكل")

keep_alive()
client.run(TOKEN)

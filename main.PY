from flask import Flask
import threading, os, json, requests, asyncio, discord
from datetime import datetime

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Trading Live"
threading.Thread(target=lambda: app.run(host='0.0.0.0',port=8080),daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981 # ايدي قناتك

intents = discord.Intents.default()
intents.message_content = True
FILE = "paper_trades.json"

def load():
    try:
        with open(FILE,"r") as f: return json.load(f)
    except: return {"balance":1000.0,"open":None,"history":[]}

def save(d):
    with open(FILE,"w") as f: json.dump(d,f)

def klines():
    try:
        r = requests.get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=5m&limit=50",timeout=10).json()
        return [float(x[4]) for x in r]
    except: return None

def ema(prices,p):
    k=2/(p+1); e=prices[0]
    for x in prices[1:]: e=x*k+e*(1-k)
    return e

async def trading_loop(bot):
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    print(f">>> Trading started in {channel} <<<")
    while True:
        try:
            data = load()
            c = klines()
            if not c:
                await asyncio.sleep(30); continue

            price = c[-1]
            e9 = ema(c,9); e21 = ema(c,21)

            # اشارة دخول
            if not data["open"]:
                if e9 > e21: # صاعد
                    data["open"] = {"type":"LONG","entry":price,"time":str(datetime.now())}
                    save(data)
                    if channel: await channel.send(f"🟢 **دخول LONG**\nالسعر: {price}\nEMA9 > EMA21")
                elif e9 < e21: # هابط
                    data["open"] = {"type":"SHORT","entry":price,"time":str(datetime.now())}
                    save(data)
                    if channel: await channel.send(f"🔴 **دخول SHORT**\nالسعر: {price}\nEMA9 < EMA21")
            else: # خروج
                entry = data["open"]["entry"]; typ = data["open"]["type"]
                pnl = (price-entry)/entry*100 if typ=="LONG" else (entry-price)/entry*100
                if abs(pnl) > 1.0: # خروج على 1%
                    data["balance"] += data["balance"]*pnl/100*0.1 # 10% من الرصيد
                    data["history"].append({**data["open"],"exit":price,"pnl":pnl})
                    if channel: await channel.send(f"✅ **اغلاق {typ}**\nدخول: {entry}\nخروج: {price}\nالربح: {pnl:.2f}%\nالرصيد: ${data['balance']:.2f}")
                    data["open"]=None
                    save(data)
        except Exception as ex:
            print(f"Error: {ex}")
        await asyncio.sleep(60)

class MyBot(discord.Client):
    async def setup_hook(self):
        self.loop.create_task(trading_loop(self))
    async def on_message(self,m):
        if m.author.bot: return
        txt = m.content.strip()
        if txt == "ايدي":
            await m.channel.send(f"ايدي القناة: `{m.channel.id}`")
        elif txt in ["صفقات","الرصيد","رصيد"]:
            d=load()
            msg=f"💰 **الرصيد:** ${d['balance']:.2f}\n"
            if d["open"]:
                msg+=f"📌 **مفتوحة:** {d['open']['type']} من {d['open']['entry']}"
            else:
                msg+="📭 لا يوجد صفقة مفتوحة"
            await m.channel.send(msg)
        elif txt == "CHANNEL_ID = 0":
            await m.channel.send(f"تم التحديث! الايدي الجديد هو `{m.channel.id}`")

bot = MyBot(intents=intents)
bot.run(TOKEN)

from flask import Flask
import threading, os, json, requests, asyncio, discord
from datetime import datetime
app=Flask(__name__)
@app.route('/')
def home(): return "Bot alive"
threading.Thread(target=lambda: app.run(host='0.0.0.0',port=8080),daemon=True).start()
TOKEN=os.getenv("DISCORD_TOKEN")
intents=discord.Intents.default()
intents.message_content=True
FILE="paper_trades.json"
def load():
    try:
        with open(FILE,"r") as f: return json.load(f)
    except: return {"balance":1000.0,"open":None,"history":[]}
def save(d):
    with open(FILE,"w") as f: json.dump(d,f)
def klines():
    try:
        r=requests.get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=5m&limit=50",timeout=10).json()
        return [float(x[4]) for x in r]
    except: return None
def ema(prices,p):
    k=2/(p+1); e=prices[0]
    for x in prices[1:]: e=x*k+e*(1-k)
    return e
MY_CHANNEL=None
async def loop_trading():
    global MY_CHANNEL
    await asyncio.sleep(5)
    print(">>> Bot ready <<<")
    while True:
        try:
            if MY_CHANNEL:
                c=klines()
                if c:
                    print(f"Price {c[-1]}")
        except Exception as ex: print(ex)
        await asyncio.sleep(60)
class MyBot(discord.Client):
    async def setup_hook(self):
        self.loop.create_task(loop_trading())
    async def on_message(self,m):
        global MY_CHANNEL
        if m.author.bot: return
        # احفظ اول روم يكتب فيه احد
        if MY_CHANNEL is None:
            MY_CHANNEL=m.channel
            await m.channel.send(f"✅ تم حفظ هذه القناة! ايديها هو: `{m.channel.id}`\nانسخه وحطه في Render باسم CHANNEL_ID عشان يثبت")
        txt=m.content.strip()
        if txt=="ايدي":
            await m.channel.send(f"🆔 ايدي هذه القناة: `{m.channel.id}`")
        elif txt=="صفقات":
            await m.channel.send("📭 البوت شغال - اكتب الايدي اللي فوق في Render")
bot=MyBot(intents=intents)
bot.run(TOKEN)

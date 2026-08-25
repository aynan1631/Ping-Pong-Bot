from flask import Flask
import threading, os, json, requests, asyncio, discord
from datetime import datetime

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive - OK"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CID = os.getenv("CHANNEL_ID", "0")
CHANNEL_ID = int(CID) if CID.isdigit() else 0

intents = discord.Intents.default()
intents.message_content = True

DATA_FILE = "paper_trades.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f: return json.load(f)
    except: return {"balance":1000.0,"open":None,"history":[]}

def save_data(d):
    with open(DATA_FILE,"w") as f: json.dump(d,f)

def calc_ema(prices, period):
    k=2/(period+1)
    ema=prices[0]
    for p in prices[1:]: ema=p*k+ema*(1-k)
    return ema

def get_klines():
    try:
        r=requests.get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=5m&limit=50",timeout=10).json()
        return [float(x[4]) for x in r]
    except Exception as e:
        print(f"klines error {e}")
        return None

async def trading_loop():
    await asyncio.sleep(5)
    channel=bot.get_channel(CHANNEL_ID)
    print(">>> Bot ready - loop started <<<")
    if channel:
        try: await channel.send("🚀 البوت اشتغل - دخول فوري الآن")
        except: pass
    first=True
    while True:
        try:
            closes=get_klines()
            if not closes:
                await asyncio.sleep(30)
                continue
            price=closes[-1]
            ema9=calc_ema(closes[-9:],9)
            ema25=calc_ema(closes,25)
            print(f"Price {price:.2f} EMA9 {ema9:.2f} EMA25 {ema25:.2f}")
            data=load_data()
            if data['open'] is None and first:
                t="شراء" if ema9>ema25 else "بيع"
                data['open']={"type":t,"entry":price,"time":str(datetime.now())}
                save_data(data)
                if channel: await channel.send(f"{'🟢' if t=='شراء' else '🔴'} دخول فوري {t} @ {price:.2f}")
                print(f"فتحت {t}")
                first=False
        except Exception as e:
            print(f"loop err {e}")
        await asyncio.sleep(60)

class MyBot(discord.Client):
    async def setup_hook(self):
        self.loop.create_task(trading_loop())
    async def on_message(self,message):
        if message.author.bot: return
        data=load_data()
        m=message.content.strip()
        if m=="صفقات":
            if not data['open']: await message.channel.send("📭 لا يوجد")
            else:
                c=get_klines()
                p=c[-1] if c else 0
                e=data['open']['entry']
                pnl=(p-e)/e*100 if data['open']['type']=="شراء" else (e-p)/e*100
                await message.channel.send(f"📊 {data['open']['type']} @ {e:.2f} | الآن {p:.2f} | {pnl:.2f}%")
        elif m=="الرصيد":
            o=f"{data['open']['type']} @ {data['open']['entry']}" if data['open'] else "لا يوجد"
            await message.channel.send(f"💰 {data['balance']:.2f}$\n📌 {o}")

bot=MyBot(intents=intents)
bot.run(TOKEN)from flask import Flask
import threading, os, json, requests, asyncio, discord
from datetime import datetime

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive - OK"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CID = os.getenv("CHANNEL_ID", "0")
CHANNEL_ID = int(CID) if CID.isdigit() else 0

intents = discord.Intents.default()
intents.message_content = True

DATA_FILE = "paper_trades.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f: return json.load(f)
    except: return {"balance":1000.0,"open":None,"history":[]}

def save_data(d):
    with open(DATA_FILE,"w") as f: json.dump(d,f)

def calc_ema(prices, period):
    k=2/(period+1)
    ema=prices[0]
    for p in prices[1:]: ema=p*k+ema*(1-k)
    return ema

def get_klines():
    try:
        r=requests.get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=5m&limit=50",timeout=10).json()
        return [float(x[4]) for x in r]
    except Exception as e:
        print(f"klines error {e}")
        return None

async def trading_loop():
    await asyncio.sleep(5)
    channel=bot.get_channel(CHANNEL_ID)
    print(">>> Bot ready - loop started <<<")
    if channel:
        try: await channel.send("🚀 البوت اشتغل - دخول فوري الآن")
        except: pass
    first=True
    while True:
        try:
            closes=get_klines()
            if not closes:
                await asyncio.sleep(30)
                continue
            price=closes[-1]
            ema9=calc_ema(closes[-9:],9)
            ema25=calc_ema(closes,25)
            print(f"Price {price:.2f} EMA9 {ema9:.2f} EMA25 {ema25:.2f}")
            data=load_data()
            if data['open'] is None and first:
                t="شراء" if ema9>ema25 else "بيع"
                data['open']={"type":t,"entry":price,"time":str(datetime.now())}
                save_data(data)
                if channel: await channel.send(f"{'🟢' if t=='شراء' else '🔴'} دخول فوري {t} @ {price:.2f}")
                print(f"فتحت {t}")
                first=False
        except Exception as e:
            print(f"loop err {e}")
        await asyncio.sleep(60)

class MyBot(discord.Client):
    async def setup_hook(self):
        self.loop.create_task(trading_loop())
    async def on_message(self,message):
        if message.author.bot: return
        data=load_data()
        m=message.content.strip()
        if m=="صفقات":
            if not data['open']: await message.channel.send("📭 لا يوجد")
            else:
                c=get_klines()
                p=c[-1] if c else 0
                e=data['open']['entry']
                pnl=(p-e)/e*100 if data['open']['type']=="شراء" else (e-p)/e*100
                await message.channel.send(f"📊 {data['open']['type']} @ {e:.2f} | الآن {p:.2f} | {pnl:.2f}%")
        elif m=="الرصيد":
            o=f"{data['open']['type']} @ {data['open']['entry']}" if data['open'] else "لا يوجد"
            await message.channel.send(f"💰 {data['balance']:.2f}$\n📌 {o}")

bot=MyBot(intents=intents)
bot.run(TOKEN)

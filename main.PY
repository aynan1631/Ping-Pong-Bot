from flask import Flask
from threading import Thread
import os, discord, requests, asyncio, time
import pandas as pd

app = Flask('')
@app.route('/')
def home(): return "Scalping Bot Paper Trading LIVE!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.start()

# === اعدادات الاستراتيجية ===
COINS = {"BTCUSDT":"بيتكوين", "ETHUSDT":"ايثيريوم", "SOLUSDT":"سولانا"}
CAPITAL = 100 # راس المال الوهمي لكل عملة 100$
TP = 1.5 # هدف ربح 1.5%
SL = 0.8 # وقف خسارة 0.8%

paper_trades = {} # يحفظ الصفقات الوهمية

def get_klines(symbol, limit=100):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit={limit}"
        data = requests.get(url, timeout=10).json()
        df = pd.DataFrame(data, columns=['o','h','l','c','v','ct','q','n','tb','tq','ig'])
        df['c'] = df['c'].astype(float)
        return df
    except: return None

def calc_ema_rsi(df):
    df['EMA9'] = df['c'].ewm(span=9).mean()
    df['EMA21'] = df['c'].ewm(span=21).mean()
    delta = df['c'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df.iloc[-1]

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

async def scalping_loop():
    await client.wait_until_ready()
    channel = None
    while not client.is_closed():
        for symbol, name in COINS.items():
            df = get_klines(symbol)
            if df is None: continue
            last = calc_ema_rsi(df)
            price = last['c']
            ema9, ema21, rsi = last['EMA9'], last['EMA21'], last['RSI']

            # اذا ما عنده صفقة مفتوحة - يدور شراء
            if symbol not in paper_trades:
                if ema9 > ema21 and rsi < 35:
                    paper_trades[symbol] = {"buy": price, "time": time.time()}
                    msg = f"🟢 **دخول سكالب شراء وهمي**\n{name} ({symbol})\nالسعر: ${price:,.2f}\nEMA9: {ema9:.2f} > EMA21: {ema21:.2f}\nRSI: {rsi:.1f} (تشبع بيع)\nالهدف: +{TP}% | وقف: -{SL}%"
                    if channel: await channel.send(msg)
            else:
                buy_price = paper_trades[symbol]['buy']
                pnl = ((price - buy_price)/buy_price)*100
                if pnl >= TP or pnl <= -SL or (ema9 < ema21 and rsi > 65):
                    result = "✅ ربح" if pnl>0 else "❌ خسارة"
                    msg = f"{result} **خروج سكالب وهمي**\n{name}\nدخول: ${buy_price:,.2f} | خروج: ${price:,.2f}\nالربح: {pnl:+.2f}%"
                    del paper_trades[symbol]
                    if channel: await channel.send(msg)
        await asyncio.sleep(60) # يفحص كل دقيقة

@client.event
async def on_ready():
    print(f'Bot {client.user} is ready - Paper Trading Mode')
    client.loop.create_task(scalping_loop())

@client.event
async def on_message(message):
    if message.author == client.user: return
    if "رصيد" in message.content or "صفقات" in message.content:
        if not paper_trades:
            await message.channel.send("📭 لا يوجد صفقات مفتوحة حاليا")
        else:
            txt = "📊 **الصفقات المفتوحة (وهمي):**\n"
            for s, t in paper_trades.items():
                txt += f"- {s}: شراء ${t['buy']:,.2f}\n"
            await message.channel.send(txt)

keep_alive()
client.run(os.getenv("DISCORD_TOKEN"))

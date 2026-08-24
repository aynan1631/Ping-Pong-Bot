import discord, asyncio, os, json
import ccxt
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True

DATA_FILE = "paper_trades.json"
SYMBOL = "BTC/USDT"

def load_data():
    try:
        with open(DATA_FILE, "r") as f: return json.load(f)
    except: return {"balance": 1000.0, "open": None, "history": []}

def save_data(d):
    with open(DATA_FILE, "w") as f: json.dump(d, f)

exchange = ccxt.binance()

def calc_ema(prices, period):
    k = 2 / (period + 1)
    ema = prices[0]
    for p in prices[1:]: ema = p * k + ema * (1 - k)
    return ema

async def trading_loop():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    print("Bot is ready - Trading loop started")
    while True:
        try:
            ohlcv = exchange.fetch_ohlcv(SYMBOL, "5m", limit=50)
            closes = [x[4] for x in ohlcv]
            price = closes[-1]
            ema9 = calc_ema(closes[-9:], 9)
            ema25 = calc_ema(closes, 25)
            ema9_prev = calc_ema(closes[-10:-1], 9)
            ema25_prev = calc_ema(closes[:-1], 25)
            data = load_data()
            buy = ema9 > ema25 and ema9_prev <= ema25_prev
            sell = ema9 < ema25 and ema9_prev >= ema25_prev

            if data['open'] is None:
                if buy:
                    data['open'] = {"type":"شراء","entry":price,"time":str(datetime.now())}
                    save_data(data)
                    if channel: await channel.send(f"🟢 دخل شراء @ {price:.2f}")
                elif sell:
                    data['open'] = {"type":"بيع","entry":price,"time":str(datetime.now())}
                    save_data(data)
                    if channel: await channel.send(f"🔴 دخل بيع @ {price:.2f}")
            else:
                touch = abs(ema9 - ema25) / price * 100 < 0.05
                entry = data['open']['entry']
                pnl = (price-entry)/entry*100 if data['open']['type']=="شراء" else (entry-price)/entry*100
                if touch and pnl > 0:
                    data['balance'] += data['balance'] * 0.01 * pnl
                    data['history'].append({"type":data['open']['type'],"entry":entry,"exit":price,"pnl":round(pnl,2),"time":str(datetime.now())})
                    if channel: await channel.send(f"✅ قفل {data['open']['type']} @ {price:.2f} | ربح {pnl:.2f}%")
                    data['open'] = None
                    save_data(data)
        except Exception as e: print(f"Error: {e}")
        await asyncio.sleep(60)

class MyBot(discord.Client):
    async def setup_hook(self): self.loop.create_task(trading_loop())
    async def on_message(self, message):
        if message.author.bot: return
        data = load_data()
        m = message.content.strip()
        if m == "الرصيد":
            o = f"{data['open']['type']} @ {data['open']['entry']}" if data['open'] else "لا يوجد"
            await message.channel.send(f"💰 الرصيد: {data['balance']:.2f}$\n📌 مفتوحة: {o}")
        elif m == "صفقات":
            if not data['open']: await message.channel.send("📭 لا يوجد")
            else:
                p = exchange.fetch_ticker(SYMBOL)['last']
                e = data['open']['entry']
                pnl = (p-e)/e*100 if data['open']['type']=="شراء" else (e-p)/e*100
                await message.channel.send(f"📊 {data['open']['type']} @ {e:.2f} | الآن {p:.2f} | {pnl:.2f}%")
        elif m == "السجل":
            if not data['history']: await message.channel.send("📭 فاضي")
            else:
                txt = "📜 آخر 10:\n"
                for t in data['history'][-10:]: txt += f"{t['type']} {t['pnl']}% {t['entry']:.1f}->{t['exit']:.1f}\n"
                await message.channel.send(txt)

bot = MyBot(intents=intents)
bot.run(TOKEN)

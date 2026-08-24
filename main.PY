import discord, asyncio, os, json
import ccxt, pandas as pd
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True

DATA_FILE = "paper_trades.json"
SYMBOL = "BTC/USDT"
TIMEFRAME = "5m"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"balance": 1000.0, "open": None, "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f)

exchange = ccxt.binance()

def get_emas():
    ohlcv = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=100)
    df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
    df['ema9'] = df['c'].ewm(span=9).mean()
    df['ema25'] = df['c'].ewm(span=25).mean()
    return df.iloc[-3], df.iloc[-2], df.iloc[-1], df['c'].iloc[-1]

async def trading_loop():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    print("Bot is ready - Trading loop started")
    while True:
        try:
            prev2, prev1, last, price = get_emas()
            data = load_data()
            buy_signal = last['ema9'] > last['ema25'] and prev1['ema9'] <= prev1['ema25'] and last['c'] > last['ema9']
            sell_signal = last['ema9'] < last['ema25'] and prev1['ema9'] >= prev1['ema25'] and last['c'] < last['ema9']

            if data['open'] is None:
                if buy_signal:
                    data['open'] = {"type":"شراء","entry":price,"time":str(datetime.now())}
                    save_data(data)
                    if channel: await channel.send(f"🟢 **دخل شراء** {SYMBOL} @ {price:.2f}")
                elif sell_signal:
                    data['open'] = {"type":"بيع","entry":price,"time":str(datetime.now())}
                    save_data(data)
                    if channel: await channel.send(f"🔴 **دخل بيع** {SYMBOL} @ {price:.2f}")
            else:
                touch = abs(last['ema9'] - last['ema25']) / last['c'] * 100 < 0.05
                entry = data['open']['entry']
                pnl = (price - entry)/entry*100 if data['open']['type']=="شراء" else (entry - price)/entry*100
                if touch and pnl > 0:
                    data['balance'] += data['balance'] * 0.01 * pnl
                    data['history'].append({"type":data['open']['type'],"entry":entry,"exit":price,"pnl":round(pnl,2),"time":str(datetime.now())})
                    if channel: await channel.send(f"✅ **قفل {data['open']['type']}** @ {price:.2f} | ربح {pnl:.2f}%")
                    data['open'] = None
                    save_data(data)
        except Exception as e:
            print(f"Error: {e}")
        await asyncio.sleep(60)

class MyBot(discord.Client):
    async def setup_hook(self):
        self.loop.create_task(trading_loop())

    async def on_message(self, message):
        if message.author.bot: return
        data = load_data()
        msg = message.content.strip()
        if msg == "الرصيد":
            open_txt = f"{data['open']['type']} @ {data['open']['entry']}" if data['open'] else "لا يوجد"
            await message.channel.send(f"💰 **الرصيد:** {data['balance']:.2f}$\n📌 مفتوحة: {open_txt}\n📜 المقفلة: {len(data['history'])}")
        elif msg == "صفقات":
            if not data['open']:
                await message.channel.send("📭 لا يوجد صفقات مفتوحة")
            else:
                price = exchange.fetch_ticker(SYMBOL)['last']
                entry = data['open']['entry']
                pnl = (price-entry)/entry*100 if data['open']['type']=="شراء" else (entry-price)/entry*100
                await message.channel.send(f"📊 مفتوحة: {data['open']['type']} @ {entry:.2f} | الآن {price:.2f} | PnL {pnl:.2f}%")
        elif msg == "السجل":
            if not data['history']:
                await message.channel.send("📭 السجل فاضي")
            else:
                txt = "📜 **آخر 10:**\n"
                for t in data['history'][-10:]:
                    txt += f"{t['type']} | {t['pnl']}% | {t['entry']:.1f}->{t['exit']:.1f}\n"
                await message.channel.send(txt)
        elif msg == "احصائيات":
            h = data['history']
            if not h:
                await message.channel.send("📊 لا يوجد احصائيات بعد")
            else:
                wins = len([x for x in h if x['pnl']>0])
                avg = sum([x['pnl'] for x in h])/len(h)
                await message.channel.send(f"📊 إجمالي: {len(h)} | رابحة: {wins} | نسبة: {wins/len(h)*100:.1f}% | متوسط: {avg:.2f}%")

bot = MyBot(intents=intents)
bot.run(TOKEN)

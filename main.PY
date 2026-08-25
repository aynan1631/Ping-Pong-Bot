from flask import Flask
import threading
threading.Thread(target=lambda: Flask('').run(host='0.0.0.0', port=8080), daemon=True).start()

import discord, os, json, requests, asyncio
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True
DATA_FILE = "paper_trades.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f: return json.load(f)
    except: return {"balance": 1000.0, "open": None, "history": []}
def save_data(d):
    with open(DATA_FILE, "w") as f: json.dump(d, f)

def calc_ema(prices, period):
    k = 2 / (period + 1)
    ema = prices[0]
    for p in prices[1:]: ema = p * k + ema * (1 - k)
    return ema

def get_klines():
    # 3 مصادر، واحد منهم لازم يشتغل
    urls = [
        "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=5m&limit=50",
        "https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=5m&limit=50",
        "https://api.bybit.com/v5/market/kline?category=spot&symbol=BTCUSDT&interval=5&limit=50"
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=10).json()
            # Bybit format مختلف
            if "result" in r:
                closes = [float(x[4]) for x in r["result"]["list"][::-1]]
                return closes
            else:
                closes = [float(x[4]) for x in r]
                return closes
        except Exception as e:
            print(f"فشل {url} : {e}")
            continue
    return None

async def trading_loop():
    await asyncio.sleep(5)
    channel = bot.get_channel(CHANNEL_ID)
    print("Bot ready - loop started")
    if channel: await channel.send("🚀 البوت اشتغل - بفحص السوق الآن...")

    first_run = True
    while True:
        try:
            closes = get_klines()
            if not closes:
                print("ما قدرت اجيب السعر")
                await asyncio.sleep(30)
                continue

            price = closes[-1]
            ema9 = calc_ema(closes[-9:], 9)
            ema25 = calc_ema(closes, 25)
            ema9_prev = calc_ema(closes[-10:-1], 9)
            ema25_prev = calc_ema(closes[:-1], 25)

            print(f"Price {price:.2f} EMA9 {ema9:.2f} EMA25 {ema25:.2f}")
            data = load_data()

            # دخول فوري أول مرة
            if data['open'] is None and first_run:
                if ema9 > ema25:
                    data['open'] = {"type":"شراء","entry":price,"time":str(datetime.now())}
                    save_data(data)
                    if channel: await channel.send(f"🟢 دخول فوري شراء @ {price:.2f}\nEMA9 {ema9:.2f} > EMA25 {ema25:.2f}")
                else:
                    data['open'] = {"type":"بيع","entry":price,"time":str(datetime.now())}
                    save_data(data)
                    if channel: await channel.send(f"🔴 دخول فوري بيع @ {price:.2f}\nEMA9 {ema9:.2f} < EMA25 {ema25:.2f}")
                first_run = False
                print(f"تم فتح {'شراء' if ema9>ema25 else 'بيع'} فوري")

            elif data['open'] is None:
                buy_cross = ema9 > ema25 and ema9_prev <= ema25_prev
                sell_cross = ema9 < ema25 and ema9_prev >= ema25_prev
                if buy_cross:
                    data['open'] = {"type":"شراء","entry":price,"time":str(datetime.now())}
                    save_data(data)
                    if channel: await channel.send(f"🟢 دخل شراء @ {price:.2f}")
                elif sell_cross:
                    data['open'] = {"type":"بيع","entry":price,"time":str(datetime.now())}
                    save_data(data)
                    if channel: await channel.send(f"🔴 دخل بيع @ {price:.2f}")
            else:
                # قفل
                entry = data['open']['entry']
                pnl = (price-entry)/entry*100 if data['open']['type']=="شراء" else (entry-price)/entry*100
                touch = abs(ema9 - ema25) / price * 100 < 0.05
                print(f"مفتوحة {data['open']['type']} PnL {pnl:.2f}% touch {touch}")
                if touch and pnl > 0:
                    data['balance'] += data['balance'] * 0.01 * pnl
                    data['history'].append({"type":data['open']['type'],"entry":entry,"exit":price,"pnl":round(pnl,2),"time":str(datetime.now())})
                    if channel: await channel.send(f"✅ قفل {data['open']['type']} @ {price:.2f} | ربح {pnl:.2f}%")
                    data['open'] = None
                    save_data(data)

        except Exception as e:
            print(f"Error loop: {e}")
        await asyncio.sleep(60)

class MyBot(discord.Client):
    async def setup_hook(self):
        self.loop.create_task(trading_loop())
    async def on_message(self, message):
        if message.author.bot: return
        data = load_data()
        m = message.content.strip()
        if m == "الرصيد":
            o = f"{data['open']['type']} @ {data['open']['entry']}" if data['open'] else "لا يوجد"
            await message.channel.send(f"💰 {data['balance']:.2f}$\n📌 {o}")
        elif m == "صفقات":
            if not data['open']: await message.channel.send("📭 لا يوجد - اكتب افتح بيع او افتح شراء")
            else:
                closes = get_klines()
                p = closes[-1] if closes else 0
                e = data['open']['entry']
                pnl = (p-e)/e*100 if data['open']['type']=="شراء" else (e-p)/e*100
                await message.channel.send(f"📊 {data['open']['type']} @ {e:.2f} | الآن {p:.2f} | {pnl:.2f}%")
        elif m == "افتح بيع":
            data['open'] = {"type":"بيع","entry":get_klines()[-1],"time":str(datetime.now())}
            save_data(data)
            await message.channel.send(f"🔴 فتحت بيع يدوي @ {data['open']['entry']:.2f}")
        elif m == "افتح شراء":
            data['open'] = {"type":"شراء","entry":get_klines()[-1],"time":str(datetime.now())}
            save_data(data)
            await message.channel.send(f"🟢 فتحت شراء يدوي @ {data['open']['entry']:.2f}")
        elif m == "السجل":
            if not data['history']: await message.channel.send("📭 فاضي")
            else:
                txt = "📜 آخر 10:\n"
                for t in data['history'][-10:]: txt += f"{t['type']} {t['pnl']}% {t['entry']:.1f}->{t['exit']:.1f}\n"
                await message.channel.send(txt)

bot = MyBot(intents=intents)
bot.run(TOKEN)

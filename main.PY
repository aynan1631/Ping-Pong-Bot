import os, discord, requests, threading, random, time, asyncio
from discord.ext import tasks
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "CRAZY NO-SLEEP NO-429 ✅"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

threading.Thread(target=run_web, daemon=True).start()

# يصحي نفسه عشان Render ما ينيمه
def keep_alive():
    while True:
        try:
            url = os.getenv("RENDER_EXTERNAL_URL", "https://ping-pong-bot-1gzb.onrender.com")
            requests.get(url, timeout=5)
        except:
            pass
        time.sleep(280) # كل 4 دقايق ونص

threading.Thread(target=keep_alive, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981
CAPITAL = 250.0
MAX = 5

dashboard_msg = None
trades = {}
total_realized = 0.0
COINS = ["DOGEUSDT","SOLUSDT","AVAXUSDT","XRPUSDT","BNBUSDT","ADAUSDT","TRXUSDT","LTCUSDT","SHIBUSDT","PEPEUSDT"]
price_cache = {c: 0 for c in COINS}

last_edit = 0
last_text = ""

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def price_thread():
    while True:
        try:
            r = requests.get("https://www.okx.com/api/v5/market/tickers?instType=SPOT", timeout=2).json()
            for x in r.get('data', []):
                sym = x['instId'].replace('-', '')
                if sym in COINS:
                    price_cache[sym] = float(x['last'])
        except:
            pass
        time.sleep(0.5)

@bot.event
async def on_ready():
    print(f"Bot Ready {bot.user}")
    threading.Thread(target=price_thread, daemon=True).start()
    if not crazy_close.is_running():
        crazy_close.start()
    if not live_board.is_running():
        live_board.start()
    if not crazy_entry.is_running():
        crazy_entry.start()
    ch = bot.get_channel(CHANNEL_ID)
    if ch:
        await ch.send("🎲 مجنون صحى - اضرب واهرب 1$ جاهز")

@bot.event
async def on_message(msg):
    global trades, dashboard_msg, total_realized
    if msg.author == bot.user or msg.channel.id!= CHANNEL_ID:
        return
    if msg.content.strip().lower() in ["تصفير", "reset", "اصحى"]:
        trades.clear()
        total_realized = 0.0
        if dashboard_msg:
            try:
                await dashboard_msg.delete()
            except:
                pass
            dashboard_msg = None
        await msg.channel.send("✅ تصفير - فكيت البلوك وجاهز")

@tasks.loop(seconds=1.5)
async def crazy_entry():
    try:
        if len(trades) >= MAX:
            return
        avail = [c for c in COINS if c not in trades]
        if not avail:
            return
        sym = random.choice(avail)
        side = random.choice(["LONG", "SHORT"])
        cur = price_cache.get(sym, 0)
        if cur == 0:
            return
        trades[sym] = {"entry": cur, "side": side, "qty": CAPITAL / cur}
        ch = bot.get_channel(CHANNEL_ID)
        if ch:
            await ch.send(f"🎲 {sym} {side} -> {len(trades)}/{MAX}")
    except:
        pass

@tasks.loop(seconds=0.5)
async def crazy_close():
    global trades, total_realized
    try:
        if not trades:
            return
        sp = 0
        sl = 0
        for sym, d in list(trades.items()):
            cur = price_cache.get(sym, 0)
            if cur == 0:
                continue
            pnl = (cur - d['entry']) * d['qty'] if d['side'] == "LONG" else (d['entry'] - cur) * d['qty']
            if pnl >= 0:
                sp += pnl
            else:
                sl += abs(pnl)
        total_net = sp - sl
        if total_net >= 1.0:
            total_realized += total_net
            profit = total_net
            trades.clear()
            ch = bot.get_channel(CHANNEL_ID)
            if ch:
                await ch.send(f"💰 هروب مجنون صافي {profit:.2f}$ | مقفلة {total_realized:.2f}$ 🔥")
    except:
        pass

@tasks.loop(seconds=6)
async def live_board():
    global dashboard_msg, last_edit, last_text
    try:
        if time.time() - last_edit < 5:
            return
        ch = bot.get_channel(CHANNEL_ID)
        if not ch:
            return
        txt = ""
        sp = 0
        sl = 0
        for sym, d in list(trades.items()):
            cur = price_cache.get(sym, d['entry'])
            if cur == 0:
                cur = d['entry']
            pnl = (cur - d['entry']) * d['qty'] if d['side'] == "LONG" else (d['entry'] - cur) * d['qty']
            if pnl >= 0:
                sp += pnl
            else:
                sl += abs(pnl)
            if cur < 0.01:
                txt += f"{sym} {d['side']} دخول {d['entry']:.8f} حالي {cur:.8f} ربح {pnl:.2f}$\n\n"
            else:
                txt += f"{sym} {d['side']} دخول {d['entry']:.5f} حالي {cur:.5f} ربح {pnl:.2f}$\n\n"

        if not txt:
            txt = "🎲 جاهز للضربة المجنونة...\n"

        if txt == last_text and len(trades) > 0:
            return

        last_text = txt
        total_net = sp - sl
        l = sum(1 for v in trades.values() if v['side'] == 'LONG')
        s = sum(1 for v in trades.values() if v['side'] == 'SHORT')

        footer = f"مقفلة= ${total_realized:.2f}\nأرباح= ${sp:.2f} | خساير= ${sl:.2f}\nالصافي= ${total_net:.2f} | L:{l} S:{s} {len(trades)}/{MAX}\n\nاضرب واهرب 1$ - كل 6 ثواني تحديث\nToday at {datetime.now().strftime('%I:%M:%S %p')}"

        embed = discord.Embed(title=f"🎲 مجنون {len(trades)}/{MAX} | صافي {total_net:.2f}$", description=txt, color=0xff00ff)
        embed.add_field(name="\u200b", value=footer, inline=False)

        last_edit = time.time()
        if dashboard_msg:
            try:
                await dashboard_msg.edit(embed=embed)
            except Exception as e:
                if "429" in str(e):
                    await asyncio.sleep(7)
                else:
                    dashboard_msg = None
        else:
            async for m in ch.history(limit=5):
                if m.author == bot.user and m.embeds:
                    try:
                        await m.delete()
                    except:
                        pass
            dashboard_msg = await ch.send(embed=embed)
    except Exception as e:
        print(f"board error {e}")

# لو فصل يرجع لحاله
while True:
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"Crash {e} - restart in 5s")
        time.sleep(5)

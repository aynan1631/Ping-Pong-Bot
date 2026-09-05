import os, discord, threading, random, asyncio, aiohttp
from discord.ext import tasks
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "CRAZY HIT & RUN - صاحي 24/7 ✅"
def run_web(): 
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 141234567890123456  # تأكد هذا نفس الآيدي حقك 1538955402513747981
CAPITAL = 250.0
MAX = 5
dashboard_msg, trades = None, {}
total_realized = 0.0
COINS = ["DOGEUSDT","SOLUSDT","AVAXUSDT","XRPUSDT","BNBUSDT","ADAUSDT","TRXUSDT","LTCUSDT","SHIBUSDT","PEPEUSDT"]
price_cache = {c:0 for c in COINS}

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# سحب الأسعار بدون ما يعلق البوت
async def price_loop():
    global price_cache
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://www.okx.com/api/v5/market/tickers?instType=SPOT", timeout=10) as r:
                    data = await r.json()
                    for x in data.get('data', []):
                        sym = x['instId'].replace('-','')
                        if sym in COINS:
                            price_cache[sym] = float(x['last'])
        except Exception as e:
            print(f"price error: {e}")
        await asyncio.sleep(2)  # كل ثانيتين يكفي، 0.4 كان يقتله

@bot.event
async def on_ready():
    print(f"✅ البوت صاحي: {bot.user}")
    bot.loop.create_task(price_loop())
    if not crazy_close.is_running(): crazy_close.start()
    if not live_board.is_running(): live_board.start()
    if not crazy_entry.is_running(): crazy_entry.start()
    # عشان Render ما ينام
    if not keep_alive.is_running(): keep_alive.start()

@bot.event
async def on_message(msg):
    global trades, dashboard_msg, total_realized
    if msg.author==bot.user or msg.channel.id!=CHANNEL_ID: return
    if msg.content.strip().lower() in ["تصفير","reset"]:
        trades.clear(); total_realized=0.0
        if dashboard_msg:
            try: await dashboard_msg.delete()
            except: pass
            dashboard_msg=None
        await msg.channel.send("✅ تصفير - استراتيجية مجنونة جاهزة 🔥")

@tasks.loop(seconds=2)
async def crazy_entry():
    if len(trades)>=MAX: return
    avail=[c for c in COINS if c not in trades]
    if not avail: return
    sym=random.choice(avail)
    side=random.choice(["LONG","SHORT"])
    cur=price_cache.get(sym,0)
    if cur==0: return
    trades[sym]={"entry":cur,"side":side,"qty":CAPITAL/cur}
    ch=bot.get_channel(CHANNEL_ID)
    if ch: await ch.send(f"🎲 مجنون {sym} {side} -> {len(trades)}/{MAX}")

@tasks.loop(seconds=1)
async def crazy_close():
    global trades, total_realized
    if not trades: return
    ch=bot.get_channel(CHANNEL_ID)
    sp=0; sl=0
    for sym,d in list(trades.items()):
        cur=price_cache.get(sym,0)
        if cur==0: continue
        pnl=(cur-d['entry'])*d['qty'] if d['side']=='LONG' else (d['entry']-cur)*d['qty']
        if pnl>=0: sp+=pnl
        else: sl+=abs(pnl)
    total_net=sp-sl
    if total_net>=1.0:
        total_realized+=total_net
        trades.clear()
        if ch: await ch.send(f"💰 هروب مجنون صافي {total_net:.2f}$ | مقفلة {total_realized:.2f}$ 🔥")

@tasks.loop(seconds=3)
async def live_board():
    global dashboard_msg
    ch=bot.get_channel(CHANNEL_ID)
    if not ch: return
    txt=""; sp=0; sl=0
    for sym,d in list(trades.items()):
        cur=price_cache.get(sym, d['entry'])
        if cur==0: cur=d['entry']
        pnl=(cur-d['entry'])*d['qty'] if d['side']=='LONG' else (d['entry']-cur)*d['qty']
        if pnl>=0: sp+=pnl
        else: sl+=abs(pnl)
        if cur < 0.01:
            txt+=f"{sym} {d['side']}\nدخول {d['entry']:.8f} حالي {cur:.8f}\nربح {pnl:.2f}$\n\n"
        else:
            txt+=f"{sym} {d['side']}\nدخول {d['entry']:.5f} حالي {cur:.5f}\nربح {pnl:.2f}$\n\n"
    if not txt: txt="🎲 بانتظار ضربات مجنونة...\n"
    total_net=sp-sl
    l=sum(1 for v in trades.values() if v['side']=='LONG')
    s=sum(1 for v in trades.values() if v['side']=='SHORT')
    footer=f"مقفلة= ${total_realized:.2f}\nأرباح= ${sp:.2f} | خساير= ${sl:.2f}\nالصافي= ${total_net:.2f} | L:{l} S:{s}\n\nاستراتيجية مجنونة - اضرب واهرب 1$\nToday at {datetime.now().strftime('%I:%M %p')}"
    embed=discord.Embed(title=f"🎲 مجنون {len(trades)}/{MAX} | صافي {total_net:.2f}$", description=txt, color=0xff00ff)
    embed.add_field(name="\u200b", value=footer, inline=False)
    try:
        if dashboard_msg: await dashboard_msg.edit(embed=embed)
        else:
            async for m in ch.history(limit=10):
                if m.author==bot.user and m.embeds:
                    try: await m.delete()
                    except: pass
            dashboard_msg=await ch.send(embed=embed)
    except: pass

# هذا اللي يخليه ما ينام في Render
@tasks.loop(minutes=10)
async def keep_alive():
    try:
        # يصحي نفسه كل 10 دقايق
        import requests
        url = os.getenv("RENDER_EXTERNAL_URL")
        if url:
            requests.get(url, timeout=5)
    except: pass

bot.run(TOKEN)

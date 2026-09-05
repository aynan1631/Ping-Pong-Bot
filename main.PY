import os, discord, requests, threading, random, time
from discord.ext import tasks
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "SAME BOARD FAST ✅"
def run_web(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981
CAPITAL = 250.0
MAX = 5
dashboard_msg, trades = None, {}
total_realized = 0.0
COINS = ["DOGEUSDT","SOLUSDT","AVAXUSDT","XRPUSDT","BNBUSDT","ADAUSDT","TRXUSDT","LTCUSDT","SHIBUSDT","PEPEUSDT"]

price_cache = {}
trend_cache = {}

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def price_thread():
    while True:
        try:
            r=requests.get("https://www.okx.com/api/v5/market/tickers?instType=SPOT",timeout=2).json()
            for x in r['data']:
                sym=x['instId'].replace('-','')
                if sym in COINS:
                    price_cache[sym]=float(x['last'])
        except: pass
        time.sleep(0.5)

def trend_thread():
    while True:
        for c in COINS:
            try:
                r=requests.get(f"https://www.okx.com/api/v5/market/candles?instId={c.replace('USDT','-USDT')}&bar=5m&limit=101",timeout=2).json()
                closes=[float(v[4]) for v in r['data']][::-1]
                ema=closes[0]
                for p in closes[1:]: ema=p*0.0198+ema*0.9802
                trend_cache[c]=closes[-1]-ema
            except: pass
        time.sleep(30)

@bot.event
async def on_ready():
    threading.Thread(target=price_thread, daemon=True).start()
    threading.Thread(target=trend_thread, daemon=True).start()
    if not fast_close.is_running(): fast_close.start()
    if not live_board.is_running(): live_board.start()
    if not auto_entry.is_running(): auto_entry.start()

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
        await msg.channel.send("✅ تم التصفير")

@tasks.loop(seconds=2.5)
async def auto_entry():
    if len(trades)>=MAX: return
    up=[c for c in COINS if c not in trades and trend_cache.get(c,0)>=0]
    down=[c for c in COINS if c not in trades and trend_cache.get(c,0)<0]
    longs=sum(1 for v in trades.values() if v['side']=='LONG')
    if up and down:
        if longs<=1: sym=random.choice(up); side="LONG"
        else: sym=random.choice(down); side="SHORT"
    elif up: sym=random.choice(up); side="LONG"
    elif down: sym=random.choice(down); side="SHORT"
    else: return
    cur=price_cache.get(sym,0)
    if cur==0: return
    trades[sym]={"entry":cur,"side":side,"qty":CAPITAL/cur}

# هذا هو اللي يقفل بسرعة البرق - نفس لوحتك
@tasks.loop(seconds=0.5)
async def fast_close():
    global trades, total_realized
    if not trades: return
    ch=bot.get_channel(CHANNEL_ID)
    sp=0; sl=0; pnls=[]
    for sym,d in list(trades.items()):
        cur=price_cache.get(sym,0)
        if cur==0: continue
        pnl=(cur-d['entry'])*d['qty'] if d['side']=='LONG' else (d['entry']-cur)*d['qty']
        pnls.append(pnl)
        if pnl>=0: sp+=pnl
        else: sl+=abs(pnl)
    total_net=sp-sl

    if total_net>=1.0 and pnls:
        total_realized+=total_net
        trades.clear()
        if ch: await ch.send(f"💰 قفل جماعي صافي {total_net:.2f}$ | مقفلة {total_realized:.2f}$ ✅")
        return

    for sym in list(trades.keys()):
        cur=price_cache.get(sym,0)
        if cur==0: continue
        d=trades[sym]
        pnl=(cur-d['entry'])*d['qty'] if d['side']=='LONG' else (d['entry']-cur)*d['qty']
        if pnl>=5 or pnl<=-5:
            if pnl>0: total_realized+=pnl
            del trades[sym]
            if ch: await ch.send(f"🔒 قفل {sym} {pnl:.2f}$")

# اللوحة نفس اللي في صورتك - بطيئة شوي عشان ما تعلق
@tasks.loop(seconds=2)
async def live_board():
    global dashboard_msg
    ch=bot.get_channel(CHANNEL_ID)
    if not ch: return
    txt=""; sp=0; sl=0
    for sym,d in list(trades.items()):
        cur=price_cache.get(sym,0)
        if cur==0: continue
        pnl=(cur-d['entry'])*d['qty'] if d['side']=='LONG' else (d['entry']-cur)*d['qty']
        if pnl>=0: sp+=pnl
        else: sl+=abs(pnl)
        txt+=f"{sym} {d['side']} ${CAPITAL}\nدخول {d['entry']:.6f} | حالي {cur:.6f}\nربح ${pnl:.2f}\n\n"

    if not txt: txt="بانتظار فرص EMA100 5m..."
    total_net=sp-sl
    l=sum(1 for v in trades.values() if v['side']=='LONG')
    s=sum(1 for v in trades.values() if v['side']=='SHORT')

    # نفس تصميم صورتك
    footer=f"مقفلة= ${total_realized:.2f}\nأرباح= ${sp:.2f} | خساير= ${sl:.2f}\nالصافي= ${total_net:.2f}- | L:{l} S:{s} 5/5\n\nكل صفقة $250 | كلي $1000 | EMA100 5m | يقفل الكل $1\nToday at {datetime.now().strftime('%I:%M %p')}"

    embed=discord.Embed(title="📊 الصفقات المفتوحة", description=txt, color=0x2ecc71)
    embed.add_field(name="\u200b", value=footer, inline=False)

    try:
        if dashboard_msg: await dashboard_msg.edit(embed=embed)
        else:
            async for m in ch.history(limit=5):
                if m.author==bot.user and m.embeds:
                    try: await m.delete()
                    except: pass
            dashboard_msg=await ch.send(embed=embed)
    except: pass

bot.run(TOKEN)

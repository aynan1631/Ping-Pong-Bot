import os, discord, requests, threading, random, time
from discord.ext import tasks
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "FINAL HEDGE FAST ✅"
def run_web(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981
CAPITAL = 250.0
MAX = 5
TP, SL = 5.0, -5.0
dashboard_msg, trades = None, {}
total_realized = 0.0
COINS = ["DOGEUSDT","SOLUSDT","AVAXUSDT","XRPUSDT","BNBUSDT","ADAUSDT","TRXUSDT","LTCUSDT","SHIBUSDT","PEPEUSDT"]

price_cache = {c:0 for c in COINS}
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
                if len(closes)<100: continue
                ema=closes[0]
                for p in closes[1:]: ema=p*0.0198+ema*0.9802
                trend_cache[c]=closes[-1]-ema
            except: pass
            time.sleep(0.3)
        time.sleep(25)

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
        await msg.channel.send("✅ تم التصفير - معاكس حقيقي فقط")

# دخول ذكي - لا يدخل شورت على عملة صاعدة
@tasks.loop(seconds=2.5)
async def auto_entry():
    if len(trades)>=MAX: return

    up=[c for c in COINS if c not in trades and trend_cache.get(c,0) >= 0]
    down=[c for c in COINS if c not in trades and trend_cache.get(c,0) < 0]

    longs=sum(1 for v in trades.values() if v['side']=='LONG')
    shorts=sum(1 for v in trades.values() if v['side']=='SHORT')

    sym=None; side=None

    # لو عنده لونق كثير وعنده هابط حقيقي يأخذه فورا - هذا يجيب الربح أسرع
    if longs >= 2 and down:
        sym=random.choice(down); side="SHORT"
    elif shorts >= 2 and up:
        sym=random.choice(up); side="LONG"
    # موازنة
    elif longs > shorts and down:
        sym=random.choice(down); side="SHORT"
    elif shorts > longs and up:
        sym=random.choice(up); side="LONG"
    # لو السوق كله اتجاه واحد لا يجبر معاكس وهمي
    elif up and longs < 3:
        sym=random.choice(up); side="LONG"
    elif down and shorts < 3:
        sym=random.choice(down); side="SHORT"
    else:
        return # ينتظر لين تظهر عملة معاكسة حقيقية

    cur=price_cache.get(sym,0)
    if cur==0: return
    trades[sym]={"entry":cur,"side":side,"qty":CAPITAL/cur}
    ch=bot.get_channel(CHANNEL_ID)
    if ch: await ch.send(f"🤖 {sym} {side} | L:{longs} S:{shorts} -> {len(trades)}/{MAX} | EMA5m {trend_cache.get(sym,0):.6f}")

# قفل لحظي كل 0.5 ثانية
@tasks.loop(seconds=0.5)
async def fast_close():
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
        if ch: await ch.send(f"💰 قفل جماعي صافي {total_net:.2f}$ | مقفلة {total_realized:.2f}$ ✅")
        return

    for sym in list(trades.keys()):
        cur=price_cache.get(sym,0)
        if cur==0: continue
        d=trades[sym]
        pnl=(cur-d['entry'])*d['qty'] if d['side']=='LONG' else (d['entry']-cur)*d['qty']
        if pnl>=TP or pnl<=-5:
            if pnl>0: total_realized+=pnl
            del trades[sym]
            if ch: await ch.send(f"🔒 قفل {sym} {pnl:.2f}$")

# نفس لوحتك اللي في الصورة
@tasks.loop(seconds=2)
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
            txt+=f"{sym} {d['side']} ${CAPITAL}\nدخول {d['entry']:.8f} | حالي {cur:.8f}\nربح {pnl:.2f}$\n\n"
        else:
            txt+=f"{sym} {d['side']} ${CAPITAL}\nدخول {d['entry']:.5f} | حالي {cur:.5f}\nربح {pnl:.2f}$\n\n"

    if not txt:
        txt="✅ تم قفل الكل - بانتظار عملة معاكسة حقيقية...\n"

    total_net=sp-sl
    l=sum(1 for v in trades.values() if v['side']=='LONG')
    s=sum(1 for v in trades.values() if v['side']=='SHORT')

    footer=f"مقفلة= ${total_realized:.2f}\nأرباح= ${sp:.2f} | خساير= ${sl:.2f}\nالصافي= ${total_net:.2f} | L:{l} S:{s} {len(trades)}/{MAX}\n\nكل صفقة $250 | كلي $1000 | EMA100 5m | يقفل الكل $1\nToday at {datetime.now().strftime('%I:%M %p')}"

    embed=discord.Embed(title=f"📊 الصفقات المفتوحة {len(trades)}/{MAX}", description=txt, color=0x2ecc71 if total_net>=0 else 0xe74c3c)
    embed.add_field(name="\u200b", value=footer, inline=False)
    embed.timestamp=datetime.now()

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

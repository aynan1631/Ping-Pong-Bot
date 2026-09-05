import os, discord, requests, threading, random, time
from discord.ext import tasks
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "FAST FIX ✅"
def run_web(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981
CAPITAL_PER_TRADE = 250.0
MAX_TRADES = 5
TP, SL = 5.0, -5.0
dashboard_msg, trades = None, {}
total_realized = 0.0
COINS = ["DOGEUSDT","SOLUSDT","AVAXUSDT","XRPUSDT","BNBUSDT","ADAUSDT","TRXUSDT","LTCUSDT","SHIBUSDT","PEPEUSDT"]

# كاش عشان السرعة
price_cache = {}
ema4h_cache = {"ema":None,"btc":0,"time":0}

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def get_all_prices():
    try:
        # طلب واحد يجيب كل الأسعار مرة وحدة - سريع
        r=requests.get("https://www.okx.com/api/v5/market/tickers?instType=SPOT",timeout=2).json()
        d={x['instId'].replace('-',''): float(x['last']) for x in r['data']}
        for c in COINS:
            key=c.replace('USDT','-USDT')
            # نحاول نلقاه
            if c in d: price_cache[c]=d[c]
            elif key in r: pass
        return d
    except: return {}

def price_fast(sym):
    # يجيب من الكاش أولا
    return price_cache.get(sym, 0)

def refresh_prices():
    try:
        for coin in list(trades.keys()) + COINS:
            if coin not in trades and random.random()>0.3: continue # نحدث الموجودة فقط بسرعة
            try:
                r=requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={coin.replace('USDT','-USDT')}",timeout=0.8).json()
                price_cache[coin]=float(r['data'][0]['last'])
            except: pass
    except: pass

def get_trend(sym):
    try:
        r=requests.get(f"https://www.okx.com/api/v5/market/candles?instId={sym.replace('USDT','-USDT')}&bar=5m&limit=120",timeout=2).json()
        closes=[float(c[4]) for c in r['data']][::-1]
        if len(closes)<10: return 0
        ema=closes[0]
        for p in closes[1:]: ema=p*0.0198+ema*0.9802
        return closes[-1]-ema
    except: return 0

def get_ema100_4h_cached():
    if time.time() - ema4h_cache["time"] < 60:
        return ema4h_cache["ema"], ema4h_cache["btc"]
    try:
        d=requests.get("https://www.okx.com/api/v5/market/candles?instId=BTC-USDT&bar=4H&limit=100",timeout=2).json()['data']
        closes=[float(c[4]) for c in d][::-1]
        ema=closes[0]
        for p in closes[1:]: ema=p*0.0198+ema*0.9802
        ema4h_cache.update({"ema":ema,"btc":closes[-1],"time":time.time()})
        return ema, closes[-1]
    except: return ema4h_cache["ema"], ema4h_cache["btc"]

@bot.event
async def on_ready():
    if not live_board.is_running(): live_board.start()
    if not auto_entry.is_running(): auto_entry.start()
    if not price_loop.is_running(): price_loop.start()

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
        await msg.channel.send("✅ تم التصفير - النسخة السريعة")

@tasks.loop(seconds=0.7)
async def price_loop():
    # يحدث الأسعار بالخلفية كل 0.7 ثانية
    threading.Thread(target=refresh_prices, daemon=True).start()

@tasks.loop(seconds=3)
async def auto_entry():
    if len(trades)>=MAX_TRADES: return
    longs = sum(1 for v in trades.values() if v['side']=='LONG')
    shorts = sum(1 for v in trades.values() if v['side']=='SHORT')
    up=[]; down=[]
    for coin in COINS:
        if coin in trades: continue
        t=get_trend(coin)
        if t>=0: up.append(coin)
        else: down.append(coin)
    sym=None; side=None
    if up and down:
        if longs <= shorts: sym=random.choice(up); side="LONG"
        else: sym=random.choice(down); side="SHORT"
    elif up: sym=random.choice(up); side="LONG"
    elif down: sym=random.choice(down); side="SHORT"
    else: return
    cur=price_fast(sym)
    if cur==0: return
    trades[sym]={"entry":cur,"side":side,"qty":CAPITAL_PER_TRADE/cur}
    ch=bot.get_channel(CHANNEL_ID)
    if ch: await ch.send(f"🤖 دخول {sym} {side} | {len(trades)}/{MAX_TRADES}")

@tasks.loop(seconds=1)
async def live_board():
    global dashboard_msg, trades, total_realized
    ch=bot.get_channel(CHANNEL_ID)
    if not ch: return
    try:
        ema4h, btc = get_ema100_4h_cached()
        header=f"BTC {btc:.0f} | EMA4H {ema4h:.0f}\n" if ema4h else ""

        # حساب سريع من الكاش بدون انتظار
        all_pnls=[]
        sum_profit=0; sum_loss=0; txt=""
        to_close_all=False; to_close_single=[]

        for sym,d in list(trades.items()):
            cur=price_fast(sym)
            if cur==0: continue
            pnl=(cur-d["entry"])*d["qty"] if d["side"]=="LONG" else (d["entry"]-cur)*d["qty"]
            all_pnls.append((sym,pnl,cur))
            if pnl>=0: sum_profit+=pnl
            else: sum_loss+=abs(pnl)

            # فحص فوري للوقف
            if pnl>=TP or pnl<=SL:
                to_close_single.append((sym,pnl))

        total_net=sum_profit-sum_loss

        # 1- يقفل الكل اذا صافي 1$ - فوري
        if total_net>=1.0 and len(all_pnls)>=1:
            total_realized+=total_net
            trades.clear()
            await ch.send(f"💰 قفل جماعي صافي {total_net:.2f}$ | {len(all_pnls)} صفقات | مقفلة {total_realized:.2f}$")
            to_close_single.clear()
        else:
            # 2- يقفل الفردي اللي ضرب وقف
            for sym,pnl in to_close_single:
                if sym in trades:
                    if pnl>0: total_realized+=pnl
                    del trades[sym]
                    await ch.send(f"🔒 قفل {sym} {pnl:.2f}$ | SL/TP")

        # بناء النص بعد القفل
        txt=""
        if trades:
            for sym,pnl,cur in all_pnls:
                if sym not in trades: continue
                d=trades[sym]
                txt+=f"**{sym} {d['side']}** ${CAPITAL_PER_TRADE}\nدخول {d['entry']:.6f} | {cur:.6f}\nربح {pnl:.2f}$\n\n"
        else:
            txt="بانتظار فرص..."

        l=sum(1 for v in trades.values() if v['side']=='LONG')
        s=sum(1 for v in trades.values() if v['side']=='SHORT')
        footer=f"💰 مقفلة= {total_realized:.2f}$\nأرباح= {sum_profit:.2f}$ | خساير= {sum_loss:.2f}$\nالصافي= {total_net:.2f}$ | {len(trades)}/{MAX_TRADES} L:{l} S:{s}\n\n250$ لكل صفقة | يقفل الكل 1$ | SL {SL}$\nToday at {datetime.now().strftime('%I:%M %p')}"

        embed=discord.Embed(title=f"📊 {len(trades)}/{MAX_TRADES} | صافي {total_net:.2f}$", description=header+txt, color=0x2ecc71 if total_net>=0 else 0xe74c3c)
        embed.add_field(name="\u200b", value=footer, inline=False)
        embed.timestamp=datetime.now()

        if dashboard_msg:
            try: await dashboard_msg.edit(embed=embed)
            except:
                dashboard_msg=await ch.send(embed=embed)
        else:
            async for m in ch.history(limit=10):
                if m.author==bot.user and m.embeds:
                    try: await m.delete()
                    except: pass
            dashboard_msg=await ch.send(embed=embed)
    except Exception as e: print("board err",e)

bot.run(TOKEN)

import os, discord, requests, threading, random
from discord.ext import tasks
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "SMART HEDGE 5 ✅"
def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981
CAPITAL_PER_TRADE = 250.0
MAX_TRADES = 5
TP, SL = 5.0, -5.0
dashboard_msg, trades = None, {}
total_realized = 0.0
COINS = ["DOGEUSDT","SOLUSDT","AVAXUSDT","XRPUSDT","BNBUSDT","ADAUSDT","TRXUSDT","LTCUSDT","SHIBUSDT","PEPEUSDT"]

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def price(s):
    try:
        r=requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={s.replace('USDT','-USDT')}",timeout=1).json()
        return float(r['data'][0]['last'])
    except: return 0

def get_trend(sym):
    try:
        r=requests.get(f"https://www.okx.com/api/v5/market/candles?instId={sym.replace('USDT','-USDT')}&bar=5m&limit=120",timeout=3).json()
        closes=[float(c[4]) for c in r['data']][::-1]
        if len(closes)<10: return 0,0
        ema=closes[0]
        for p in closes[1:]: ema=p*0.0198+ema*0.9802
        return closes[-1] - ema, ema
    except: return 0,0

def get_ema100_4h():
    try:
        d=requests.get("https://www.okx.com/api/v5/market/candles?instId=BTC-USDT&bar=4H&limit=100",timeout=3).json()['data']
        closes=[float(c[4]) for c in d][::-1]
        ema=closes[0]
        for p in closes[1:]: ema=p*0.0198+ema*0.9802
        return ema, closes[-1]
    except: return None,0

@bot.event
async def on_ready():
    if not live_board.is_running(): live_board.start()
    if not auto_entry.is_running(): auto_entry.start()

@bot.event
async def on_message(msg):
    global trades, dashboard_msg, total_realized
    if msg.author==bot.user or msg.channel.id!=CHANNEL_ID: return
    if msg.content.strip().lower() in ["تصفير","reset"]:
        trades.clear()
        total_realized=0.0
        if dashboard_msg:
            try: await dashboard_msg.delete()
            except: pass
            dashboard_msg=None
        await msg.channel.send("✅ تم التصفير - يدخل متعاكس ولو وجد")

@tasks.loop(seconds=3)
async def auto_entry():
    if len(trades)>=MAX_TRADES: return
    ch=bot.get_channel(CHANNEL_ID)

    longs = [k for k,v in trades.items() if v['side']=='LONG']
    shorts = [k for k,v in trades.items() if v['side']=='SHORT']

    up=[]; down=[]
    ema_map={}
    for coin in COINS:
        if coin in trades: continue
        diff, ema = get_trend(coin)
        ema_map[coin]=ema
        if diff>=0: up.append(coin)
        else: down.append(coin)

    # منطق المتعاكس الذكي
    sym=None; side=None
    if up and down:
        # يوجد متعاكسة - ندخل الناقص
        if len(longs) <= len(shorts):
            sym=random.choice(up); side="LONG"
        else:
            sym=random.choice(down); side="SHORT"
    elif up:
        sym=random.choice(up); side="LONG"
    elif down:
        sym=random.choice(down); side="SHORT"
    else: return

    cur=price(sym)
    if cur==0: return
    trades[sym]={"entry":cur,"side":side,"qty":CAPITAL_PER_TRADE/cur}
    if ch: await ch.send(f"🤖 دخول {sym} {side} | EMA {ema_map.get(sym,0):.5f} | {len(trades)}/{MAX_TRADES}")

@tasks.loop(seconds=1)
async def live_board():
    global dashboard_msg, trades, total_realized
    ch=bot.get_channel(CHANNEL_ID)
    if not ch: return
    try:
        ema100_4h, btc_now = get_ema100_4h()
        header=f"BTC {btc_now:.0f} | EMA100 4H {ema100_4h:.0f}\n\n" if ema100_4h else ""
        txt=""; all_pnls=[]; sum_profit=0; sum_loss=0
        for sym,d in list(trades.items()):
            cur=price(sym)
            if cur==0: continue
            pnl=(cur-d["entry"])*d["qty"] if d["side"]=="LONG" else (d["entry"]-cur)*d["qty"]
            all_pnls.append((sym,pnl))
            if pnl>=0: sum_profit+=pnl
            else: sum_loss+=abs(pnl)
            txt+=f"**{sym} {d['side']}** ${CAPITAL_PER_TRADE}\nدخول {d['entry']:.5f} | حالي {cur:.5f}\nربح {pnl:.2f}$\n\n"
        total_net = sum_profit - sum_loss

        if len(all_pnls)>=1 and total_net>=1.0:
            total_realized+=total_net
            for sym,_ in all_pnls:
                if sym in trades: del trades[sym]
            await ch.send(f"💰 قفل جماعي {total_net:.2f}$ | {len(all_pnls)} صفقات | المجموع {total_realized:.2f}$")
            txt="جاري البحث عن فرص..."
            sum_profit=sum_loss=total_net=0
        else:
            for sym,pnl in all_pnls:
                if pnl>=TP or pnl<=SL:
                    if pnl>0: total_realized+=pnl
                    if sym in trades: del trades[sym]
                    await ch.send(f"🔒 قفل {sym} {pnl:.2f}$")

        if not txt: txt="بانتظار ترند EMA100 5m..."
        l=len([v for v in trades.values() if v['side']=='LONG'])
        s=len([v for v in trades.values() if v['side']=='SHORT'])
        footer=f"💰 مقفلة= {total_realized:.2f}$\nأرباح= {sum_profit:.2f}$ | خساير= {sum_loss:.2f}$\nالصافي= {total_net:.2f}$ | {len(trades)}/{MAX_TRADES} L:{l} S:{s}\n\nكل صفقة 250$ | كلي 1000$ | EMA100 5m | يقفل الكل 1$\nToday at {datetime.now().strftime('%I:%M %p')}"
        embed=discord.Embed(title=f"📊 الصفقات {len(trades)}/{MAX_TRADES}", description=header+txt, color=0x2ecc71)
        embed.add_field(name="\u200b", value=footer, inline=False)
        embed.timestamp=datetime.now()
        if dashboard_msg: await dashboard_msg.edit(embed=embed)
        else:
            async for m in ch.history(limit=20):
                if m.author==bot.user and m.embeds:
                    try: await m.delete()
                    except: pass
            dashboard_msg=await ch.send(embed=embed)
    except Exception as e: print(e)

bot.run(TOKEN)

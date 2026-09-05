import os, discord, requests, threading, random
from discord.ext import tasks
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "EMA100 + TREND ✅"
def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981
CAPITAL, TP, SL = 500.0, 5.0, -5.0
dashboard_msg, trades = None, {}
total_realized = 0.0
COINS = ["DOGEUSDT","SOLUSDT","AVAXUSDT","XRPUSDT","BNBUSDT"]

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def price(s):
    try:
        r=requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={s.replace('USDT','-USDT')}",timeout=1).json()
        return float(r['data'][0]['last'])
    except: return 0

def get_trend(sym, minutes=5):
    try:
        r=requests.get(f"https://www.okx.com/api/v5/market/candles?instId={sym.replace('USDT','-USDT')}&bar=1m&limit={minutes+2}",timeout=2).json()
        closes=[float(c[4]) for c in r['data']][::-1]
        return closes[-1] - closes[0]
    except: return 0

def get_ema100():
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
        await msg.channel.send("✅ تم التصفير - EMA100 + ترند صحيح")

@tasks.loop(seconds=5)
async def auto_entry():
    if len(trades)>=2: return
    ch=bot.get_channel(CHANNEL_ID)
    up=[]; down=[]
    for coin in COINS:
        t=get_trend(coin,5)
        if t>0: up.append(coin)
        elif t<0: down.append(coin)
    if not up or not down: return
    c_long=random.choice(up)
    c_short=random.choice([c for c in down if c!=c_long])
    if not c_short: return
    for sym, side in [(c_long,"LONG"), (c_short,"SHORT")]:
        if sym in trades or len(trades)>=2: continue
        cur=price(sym)
        if cur==0: continue
        trades[sym]={"entry":cur,"side":side,"qty":CAPITAL/cur}
        if ch: await ch.send(f"🤖 دخول {sym} {side} | ترند صحيح ✅")

@tasks.loop(seconds=1)
async def live_board():
    global dashboard_msg, trades, total_realized
    ch=bot.get_channel(CHANNEL_ID)
    if not ch: return
    try:
        ema100, btc_now = get_ema100()
        header=f"BTC {btc_now:.0f} | EMA100 {ema100:.0f} | {'🟢' if ema100 and btc_now>ema100 else '🔴'}\n\n" if ema100 else ""
        txt=""; all_pnls=[]; sum_profit=0; sum_loss=0
        for sym,d in list(trades.items()):
            cur=price(sym)
            if cur==0: continue
            pnl=(cur-d["entry"])*d["qty"] if d["side"]=="LONG" else (d["entry"]-cur)*d["qty"]
            all_pnls.append((sym,pnl))
            if pnl>=0: sum_profit+=pnl
            else: sum_loss+=abs(pnl)
            txt+=f"**{sym} {d['side']}**\nسعر الدخول: {d['entry']:.4f} | الحالي: {cur:.4f}\nالربح: {pnl:.2f}$\n\n"
        total_net = sum_profit - sum_loss
        if len(all_pnls)>=2 and total_net>=1.0:
            total_realized+=total_net
            for sym,_ in all_pnls:
                if sym in trades: del trades[sym]
            await ch.send(f"💰 قفل صافي {total_net:.2f}$ | المجموع {total_realized:.2f}$")
            txt="جاري البحث عن ترند..."
            sum_profit=sum_loss=total_net=0
        else:
            for sym,pnl in all_pnls:
                if pnl>=TP or pnl<=SL:
                    if pnl>0: total_realized+=pnl
                    if sym in trades: del trades[sym]
                    await ch.send(f"🔒 قفل {sym} {pnl:.2f}$")
        if not txt: txt="بانتظار ترند صاعد + هابط..."
        footer=f"💰 أرباح العمليات المقفلة= {total_realized:.2f}$\nمجموع الأرباح= {sum_profit:.2f}$\nمجموع الخساير= {sum_loss:.2f}$\nالصافي الحالي= {total_net:.2f}$\n\nرأس المال {CAPITAL}$ لكل عملة | EMA100 4H | ترند 5د | يقفل صافي 1$\nToday at {datetime.now().strftime('%I:%M %p')}"
        embed=discord.Embed(title="📊 الصفقات المفتوحة", description=header+txt, color=0x2ecc71)
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

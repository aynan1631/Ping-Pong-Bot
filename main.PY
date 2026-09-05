import os, discord, requests, threading, random, asyncio
from discord.ext import tasks
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "Total 1$ Close ✅"
def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981
CAPITAL, TP, SL = 500.0, 5.0, -5.0
dashboard_msg, trades = None, {}
COINS = ["BTCUSDT","ETHUSDT","DOGEUSDT","SOLUSDT","XRPUSDT","BNBUSDT","AVAXUSDT"]

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def price(s):
    try:
        r=requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={s.replace('USDT','-USDT')}",timeout=2).json()
        return float(r['data'][0]['last'])
    except: return 0

def get_fast_movers():
    # يختار عملتين جديدة عشوائية أسرع كل مرة
    a=random.choice(COINS)
    b=random.choice([c for c in COINS if c!=a])
    return a, b

def get_ema200():
    try:
        d=requests.get("https://www.okx.com/api/v5/market/candles?instId=BTC-USDT&bar=4H&limit=250",timeout=4).json()['data']
        closes=[float(c[4]) for c in d][::-1]
        ema=closes[0]
        for p in closes[1:]: ema=p*0.00995+ema*0.99005
        return ema, closes[-1]
    except: return None,0

@bot.event
async def on_ready():
    if not live_board.is_running(): live_board.start()
    if not auto_entry.is_running(): auto_entry.start()

@bot.event
async def on_message(msg):
    global trades, dashboard_msg
    if msg.author==bot.user or msg.channel.id!=CHANNEL_ID: return
    if msg.content.strip().lower() in ["تصفير","reset"]:
        trades.clear()
        if dashboard_msg:
            try: await dashboard_msg.delete()
            except: pass
            dashboard_msg=None
        await msg.channel.send("✅ تم التصفير - نظام مجموع 1$")

@tasks.loop(seconds=5)
async def auto_entry():
    if len(trades)>=2: return
    ch=bot.get_channel(CHANNEL_ID)
    c1,c2 = get_fast_movers()
    for sym, side in [(c1,"LONG"), (c2,"SHORT")]:
        if sym in trades or len(trades)>=2: continue
        cur=price(sym)
        if cur==0: continue
        trades[sym]={"entry":cur,"side":side,"qty":CAPITAL/cur}
        if ch: await ch.send(f"🤖 دخول {sym} {side} {cur:.4f}")

@tasks.loop(seconds=2)
async def live_board():
    global dashboard_msg, trades
    ch=bot.get_channel(CHANNEL_ID)
    if not ch: return
    try:
        profit=loss=0; win=lose=0; txt=""
        all_pnls=[]; total_pnl=0
        ema200, btc_now = get_ema200()
        header=f"BTC {btc_now:.0f} | EMA200 {ema200:.0f} | {'🟢 شراء' if btc_now>ema200 else '🔴 بيع'}\n\n" if ema200 else ""

        for sym,d in list(trades.items()):
            cur=price(sym)
            if cur==0: continue
            pnl=(cur-d["entry"])*d["qty"] if d["side"]=="LONG" else (d["entry"]-cur)*d["qty"]
            all_pnls.append((sym,pnl))
            total_pnl+=pnl
            if pnl>=0: profit+=pnl; win+=1
            else: loss+=abs(pnl); lose+=1
            txt+=f"**{sym} {d['side']}**\nسعر الدخول: {d['entry']:.4f} | الحالي: {cur:.4f}\nالربح: {pnl:.2f}$\n\n"

        # الشرط الجديد: مجموع الصفقتين = 1$
        if len(all_pnls)>=2 and total_pnl>=1.0:
            for sym,pnl in all_pnls:
                if sym in trades: del trades[sym]
            await ch.send(f"💰 مجموع الربح {total_pnl:.2f}$ >= 1$ → قفل الصفقتين ودخول عملات جديدة أسرع")
            txt="لا يوجد صفقات مفتوحة - بيختار عملات جديدة"

        # قفل فردي لو ضرب TP/SL
        else:
            for sym,pnl in all_pnls:
                if pnl>=TP or pnl<=SL:
                    if sym in trades: del trades[sym]
                    await ch.send(f"🔒 قفل {sym} {pnl:.2f}$")

        if not txt: txt="لا يوجد صفقات مفتوحة"
        embed=discord.Embed(title="📊 الصفقات المفتوحة", description=header+txt, color=0x2ecc71)
        embed.add_field(name="✅ صفقات رابحة", value=str(win), inline=False)
        embed.add_field(name="💰 الأرباح", value=f"{profit:.2f}$", inline=True)
        embed.add_field(name="📉 الخساير", value=f"{loss:.2f}$", inline=True)
        embed.add_field(name="❌ صفقات خاسرة", value=str(lose), inline=True)
        embed.add_field(name="\u200b", value=f"رأس المال {CAPITAL}$ | مجموع 1$ يقفل | TP {TP}$ | SL {SL}$ | فحص كل ثانيتين\nToday at {datetime.now().strftime('%I:%M %p')}", inline=False)
        embed.timestamp=datetime.now()

        if dashboard_msg: await dashboard_msg.edit(embed=embed)
        else:
            async for m in ch.history(limit=15):
                if m.author==bot.user and m.embeds:
                    try: await m.delete()
                    except: pass
            dashboard_msg=await ch.send(embed=embed)
    except Exception as e: print(e)

bot.run(TOKEN)

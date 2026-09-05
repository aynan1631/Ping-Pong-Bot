import os, discord, requests, threading, random
from discord.ext import tasks
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "TOTAL REALIZED ✅"
def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981
CAPITAL, TP, SL = 500.0, 5.0, -5.0
dashboard_msg, trades = None, {}
total_realized = 0.0 # << عداد مجموع ما تم تحقيقه
COINS = ["DOGEUSDT","SOLUSDT","AVAXUSDT","XRPUSDT","BNBUSDT"]

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def price(s):
    try:
        r=requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={s.replace('USDT','-USDT')}",timeout=1).json()
        return float(r['data'][0]['last'])
    except: return 0

def get_ema200():
    try:
        d=requests.get("https://www.okx.com/api/v5/market/candles?instId=BTC-USDT&bar=4H&limit=200",timeout=3).json()['data']
        closes=[float(c[4]) for c in d][::-1]
        ema=closes[0]
        for p in closes[1:]: ema=p*0.01+ema*0.99
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
    txt = msg.content.strip().lower()
    if txt in ["تصفير","reset"]:
        trades.clear()
        total_realized = 0.0
        if dashboard_msg:
            try: await dashboard_msg.delete()
            except: pass
            dashboard_msg=None
        await msg.channel.send("✅ تم التصفير - وضع صاروخي")
    if txt == "الارباح":
        await msg.channel.send(f"💰 مجموع أرباح العمليات المقفلة = {total_realized:.2f}$")

@tasks.loop(seconds=3)
async def auto_entry():
    if len(trades)>=2: return
    ch=bot.get_channel(CHANNEL_ID)
    c1=random.choice(COINS)
    c2=random.choice([c for c in COINS if c!=c1])
    for sym, side in [(c1,"LONG"), (c2,"SHORT")]:
        if sym in trades or len(trades)>=2: continue
        cur=price(sym)
        if cur==0: continue
        trades[sym]={"entry":cur,"side":side,"qty":CAPITAL/cur}
        if ch: await ch.send(f"🤖 دخول {sym} {side}")

@tasks.loop(seconds=1)
async def live_board():
    global dashboard_msg, trades, total_realized
    ch=bot.get_channel(CHANNEL_ID)
    if not ch: return
    try:
        ema200, btc_now = get_ema200()
        header=f"BTC {btc_now:.0f} | EMA200 {ema200:.0f} | {'🟢 شراء' if ema200 and btc_now>ema200 else '🔴 بيع'}\n\n" if ema200 else ""
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

        # قفل عند صافي 1$
        if len(all_pnls)>=2 and total_net>=1.0:
            total_realized += total_net
            for sym,_ in all_pnls:
                if sym in trades: del trades[sym]
            await ch.send(f"💰 قفل صافي {total_net:.2f}$ | 💰 مجموع المقفلة الآن {total_realized:.2f}$")
            txt="لا يوجد صفقات مفتوحة - جاري الدخول الجديد"
            sum_profit=sum_loss=total_net=0
        else:
            for sym,pnl in all_pnls:
                if pnl>=TP or pnl<=SL:
                    if pnl>0: total_realized+=pnl
                    if sym in trades: del trades[sym]
                    await ch.send(f"🔒 قفل {sym} {pnl:.2f}$ | المجموع {total_realized:.2f}$")

        if not txt: txt="لا يوجد صفقات مفتوحة"

        # اللوحة الجديدة
        footer = f"💰 أرباح العمليات المقفلة= {total_realized:.2f}$\n"
        footer+= f"مجموع الأرباح= {sum_profit:.2f}$\n"
        footer+= f"مجموع الخساير= {sum_loss:.2f}$\n"
        footer+= f"الصافي الحالي= {total_net:.2f}$\n\n"
        footer+= f"رأس المال {CAPITAL}$ لكل عملة | يقفل عند صافي 1$ | فحص كل ثانية\n"
        footer+= f"Today at {datetime.now().strftime('%I:%M %p')}"

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

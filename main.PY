import os, discord, requests, threading, asyncio
from discord.ext import tasks
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "2 Trades Hedge ✅"
def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981
CAPITAL = 500.0
TP, SL = 5.0, -5.0
dashboard_msg = None
COINS = ["BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BNBUSDT"]
trades = {}
cooldown = 0 # انتظار بعد القفل

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def price(s):
    try:
        r=requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={s.replace('USDT','-USDT')}",timeout=3).json()
        return float(r['data'][0]['last'])
    except: return 0

def get_ema200():
    try:
        d=requests.get("https://www.okx.com/api/v5/market/candles?instId=BTC-USDT&bar=4H&limit=250",timeout=5).json()['data']
        closes=[float(c[4]) for c in d][::-1]
        ema=closes[0]
        k=2/201
        for p in closes[1:]: ema=p*k+ema*(1-k)
        return ema, closes[-1]
    except: return None,0

@bot.event
async def on_ready():
    print("2 Hedge Bot Ready")
    if not live_board.is_running(): live_board.start()
    if not auto_entry.is_running(): auto_entry.start()

@bot.event
async def on_message(msg):
    global trades, dashboard_msg, cooldown
    if msg.author==bot.user or msg.channel.id!=CHANNEL_ID: return
    if msg.content.strip().lower() in ["تصفير","!تصفير","reset"]:
        trades.clear()
        cooldown=0
        if dashboard_msg:
            try: await dashboard_msg.delete()
            except: pass
            dashboard_msg=None
        await msg.channel.send("✅ تم التصفير - بيرجع نظام الصفقتين المتعاكسة")

@tasks.loop(seconds=15)
async def auto_entry():
    global trades, cooldown
    if cooldown>0:
        cooldown-=15
        return
    if len(trades)>=2: return # صفقتين فقط مثل اول
    ema200, btc_now = get_ema200()
    if not ema200: return
    side="LONG" if btc_now>ema200 else "SHORT"
    ch=bot.get_channel(CHANNEL_ID)

    # يختار عملتين متعاكسة في الحركة عشان تغطي بعض
    for sym in COINS:
        if sym in trades: continue
        if len(trades)>=2: break
        cur=price(sym)
        if cur==0: continue
        trades[sym]={"entry":cur,"side":side,"qty":CAPITAL/cur}
        if ch: await ch.send(f"🤖 دخول {sym} {side} {cur:.4f}")
        await asyncio.sleep(1) # فاصل بسيط بين الصفقتين

@tasks.loop(seconds=3)
async def live_board():
    global dashboard_msg, trades, cooldown
    ch=bot.get_channel(CHANNEL_ID)
    if not ch: return
    try:
        profit=loss=0; win=lose=0; to_close=[]; txt=""
        ema200, btc_now = get_ema200()
        if ema200:
            dot="🟢" if btc_now>ema200 else "🔴"
            word="شراء" if btc_now>ema200 else "بيع"
            header=f"BTC {btc_now:.0f} | EMA200 {ema200:.0f} | {dot} {word}\n\n"
        else: header=""

        for sym,d in list(trades.items()):
            cur=price(sym)
            if cur==0: continue
            pnl=(cur-d["entry"])*d["qty"] if d["side"]=="LONG" else (d["entry"]-cur)*d["qty"]
            if pnl>=TP or pnl<=SL:
                to_close.append((sym,pnl))
                continue
            if pnl>=0: profit+=pnl; win+=1
            else: loss+=abs(pnl); lose+=1
            txt+=f"**{sym} {d['side']}**\n"
            txt+=f"سعر الدخول: {d['entry']:.4f} | الحالي: {cur:.4f}\n"
            txt+=f"الربح: {pnl:.2f}$\n\n"

        for sym,pnl in to_close:
            del trades[sym]
            cooldown=30 # ينتظر 30 ثانية بعد القفل مثل ما قلت
            await ch.send(f"🔒 قفل {sym} {pnl:.2f}$ - انتظار 30 ثانية ويدخل جديد")

        if not txt: txt="لا يوجد صفقات مفتوحة"

        embed=discord.Embed(title="📊 الصفقات المفتوحة", description=header+txt, color=0x2ecc71)
        embed.add_field(name="✅ صفقات رابحة", value=str(win), inline=False)
        embed.add_field(name="💰 الأرباح", value=f"{profit:.2f}$", inline=True)
        embed.add_field(name="📉 الخساير", value=f"{loss:.2f}$", inline=True)
        embed.add_field(name="❌ صفقات خاسرة", value=str(lose), inline=True)
        embed.add_field(name="\u200b", value=f"رأس المال {CAPITAL}$ لكل صفقة | TP {TP}$ | SL {SL}$ | فحص كل 3 ثواني\nToday at {datetime.now().strftime('%I:%M %p')} • ثواني", inline=False)
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

import os, discord, requests, threading
from discord.ext import tasks
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "Final EMA200 Bot ✅"
def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981
CAPITAL = 500.0
TP, SL = 5.0, -3.0
dashboard_msg = None
STRONG_COINS = ["BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BNBUSDT"]

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
trades = {}

def price(s):
    try:
        m={"BTCUSDT":"bitcoin","ETHUSDT":"ethereum","SOLUSDT":"solana","XRPUSDT":"ripple","BNBUSDT":"binancecoin"}
        r=requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={m[s]}&vs_currencies=usd",timeout=3).json()
        return float(r[m[s]]['usd'])
    except:
        try:
            r=requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={s.replace('USDT','-USDT')}",timeout=3).json()
            return float(r['data'][0]['last'])
        except: return 0

def get_ema200_btc():
    try:
        url="https://www.okx.com/api/v5/market/candles?instId=BTC-USDT&bar=4H&limit=250"
        data=requests.get(url,timeout=5).json()['data']
        closes=[float(c[4]) for c in data][::-1]
        ema=closes[0]
        k=2/(200+1)
        for p in closes[1:]:
            ema = p*k + ema*(1-k)
        return ema, closes[-1]
    except:
        return None, price("BTCUSDT")

@bot.event
async def on_ready():
    print("Bot Ready - EMA200 4H")
    if not live_board.is_running(): live_board.start()
    if not auto_entry.is_running(): auto_entry.start()

@bot.event
async def on_message(msg):
    global trades, dashboard_msg
    if msg.author==bot.user or msg.channel.id!=CHANNEL_ID: return
    if msg.content.strip().lower() in ["تصفير","!تصفير","reset"]:
        trades.clear()
        if dashboard_msg:
            try: await dashboard_msg.delete()
            except: pass
            dashboard_msg=None
        await msg.channel.send("✅ تم التصفير - الصفقات صفر - بيدخل جديد خلال 60 ثانية")

@tasks.loop(seconds=60)
async def auto_entry():
    global trades
    if len(trades) >= 2: return
    ema200, btc_now = get_ema200_btc()
    if not ema200: return
    ch=bot.get_channel(CHANNEL_ID)
    side = "LONG" if btc_now > ema200 else "SHORT"
    trend = "فوق EMA200 🟢 شراء" if side=="LONG" else "تحت EMA200 🔴 بيع"
    for sym in STRONG_COINS:
        if sym in trades: continue
        cur=price(sym)
        if cur==0: continue
        trades[sym]={"entry":cur,"side":side,"qty":CAPITAL/cur}
        if ch:
            await ch.send(f"🤖 دخول تلقائي\nBTC {btc_now:.0f} | EMA200 {ema200:.0f} = {trend}\n**{sym} {side}** بسعر {cur:.4f}")
        break

@tasks.loop(seconds=3)
async def live_board():
    global dashboard_msg, trades
    ch=bot.get_channel(CHANNEL_ID)
    if not ch: return
    try:
        profit=loss=0; win=lose=0; to_close=[]; txt=""
        ema200, btc_now = get_ema200_btc()
        trend_txt = f"BTC {btc_now:.0f} | EMA200 {ema200:.0f} | {'🟢 شراء' if btc_now>ema200 else '🔴 بيع'}\n\n" if ema200 else ""

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
            await ch.send(f"🔒 قفل {sym} {pnl:.2f}$ - بياخذ الربح ويدخل جديد")

        if not txt:
            txt="لا يوجد صفقات مفتوحة"

        embed=discord.Embed(title="📊 الصفقات المفتوحة", description=trend_txt+txt, color=0x2ecc71, timestamp=datetime.now())
        embed.add_field(name="💰 الأرباح", value=f"{profit:.2f}$", inline=True)
        embed.add_field(name="📉 الخساير", value=f"{loss:.2f}$", inline=True)
        embed.add_field(name="✅ صفقات رابحة", value=str(win), inline=True)
        embed.add_field(name="❌ صفقات خاسرة", value=str(lose), inline=True)
        embed.set_footer(text=f"راس المال {CAPITAL}$ لكل صفقة | TP {TP}$ | SL {SL}$ | فحص كل 3 ثواني")

        if dashboard_msg:
            await dashboard_msg.edit(embed=embed)
        else:
            async for m in ch.history(limit=10):
                if m.author==bot.user and m.embeds:
                    try: await m.delete()
                    except: pass
            dashboard_msg=await ch.send(embed=embed)
    except Exception as e: print(e)

bot.run(TOKEN)

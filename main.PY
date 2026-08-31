import discord, os, requests
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime

app = Flask('')
@app.route('/')
def home(): return "V4 1h EMA50/200"
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run, daemon=True).start()

COINS=["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","AVAXUSDT","LINKUSDT","ADAUSDT","DOTUSDT"]
TIMEFRAME="1h"
data={}
def init(c):
    if c not in data: data[c]={"ema50":0,"ema200":0,"macd":0,"adx":0,"longs":[],"shorts":[],"pnl":0,"wins":0,"losses":0,"price":0}
for c in COINS: init(c)

def get_price(s):
    try: return float(requests.get(f"https://data-api.binance.vision/api/v3/ticker/price?symbol={s}",timeout=5).json()['price'])
    except: return None

def calc_ema(prices, period):
    k=2/(period+1); ema=sum(prices[:period])/period
    for p in prices[period:]: ema=p*k+ema*(1-k)
    return ema

def get_indicators(sym):
    try:
        klines=requests.get(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={TIMEFRAME}&limit=250",timeout=10).json()
        if not isinstance(klines,list) or len(klines)<210: return None
        closes=[float(k[4]) for k in klines]
        highs=[float(k[2]) for k in klines]; lows=[float(k[3]) for k in klines]
        ema50=calc_ema(closes,50); ema200=calc_ema(closes,200)
        prev50=calc_ema(closes[:-1],50); prev200=calc_ema(closes[:-1],200)
        macd=calc_ema(closes,12)-calc_ema(closes,26)
        trs=[]; pdm=[]; mdm=[]
        for i in range(1,len(closes)):
            tr=max(highs[i]-lows[i],abs(highs[i]-closes[i-1]),abs(lows[i]-closes[i-1])); trs.append(tr)
            up=highs[i]-highs[i-1]; down=lows[i-1]-lows[i]
            pdm.append(up if up>down and up>0 else 0); mdm.append(down if down>up and down>0 else 0)
        atr=sum(trs[-14:])/14 if trs else 1
        pdi=sum(pdm[-14:])/14/atr*100; mdi=sum(mdm[-14:])/14/atr*100
        adx=abs(pdi-mdi)/(pdi+mdi)*100 if (pdi+mdi) else 0
        return {"ema50":ema50,"ema200":ema200,"prev50":prev50,"prev200":prev200,"macd":macd,"adx":adx,"pdi":pdi,"mdi":mdi,"price":closes[-1]}
    except: return None

intents=discord.Intents.default(); intents.message_content=True
bot=commands.Bot(command_prefix="!",intents=intents)

@tasks.loop(minutes=10)
async def loop():
    ch=discord.utils.get(bot.get_all_channels(),name="العام") or next((c for c in bot.get_all_channels() if isinstance(c,discord.TextChannel)),None)
    if not ch: return
    for sym in COINS:
        ind=get_indicators(sym)
        price=get_price(sym) or (ind["price"] if ind else None)
        if not ind or not price: continue
        d=data[sym]; d.update({"ema50":ind["ema50"],"ema200":ind["ema200"],"macd":ind["macd"],"adx":ind["adx"],"price":price})

        for t in d["longs"][:]:
            pnl=(price-t["price"])/t["price"]*t["amount"]
            if pnl<=-3 or pnl>=8 or ind["ema50"]<ind["ema200"]:
                d["pnl"]+=pnl; d["wins"]+=1 if pnl>=0 else 0; d["losses"]+=1 if pnl<0 else 0
                await ch.send(f"{'💰' if pnl>0 else '🛑'} **قفل LONG 1h {sym} {pnl:+.2f}$**\nEMA50 {ind['ema50']:.2f} / 200 {ind['ema200']:.2f} ADX {ind['adx']:.0f}")
                d["longs"]=[]
        for t in d["shorts"][:]:
            pnl=(t["price"]-price)/t["price"]*t["amount"]
            if pnl<=-3 or pnl>=8 or ind["ema50"]>ind["ema200"]:
                d["pnl"]+=pnl; d["wins"]+=1 if pnl>=0 else 0; d["losses"]+=1 if pnl<0 else 0
                await ch.send(f"{'💰' if pnl>0 else '🛑'} **قفل SHORT 1h {sym} {pnl:+.2f}$**\nEMA50 {ind['ema50']:.2f} / 200 {ind['ema200']:.2f} ADX {ind['adx']:.0f}")
                d["shorts"]=[]

        if d["longs"] or d["shorts"]: continue
        if ind["adx"]<20: continue

        cross_up = ind["prev50"]<=ind["prev200"] and ind["ema50"]>ind["ema200"]
        cross_down = ind["prev50"]>=ind["prev200"] and ind["ema50"]<ind["ema200"]

        if cross_up and ind["macd"]>0 and ind["pdi"]>ind["mdi"]:
            d["longs"].append({"price":price,"amount":50})
            await ch.send(f"📥 **GOLDEN CROSS 1h {sym} شراء**\nEMA50 {ind['ema50']:.2f} فوق 200 {ind['ema200']:.2f} ✅\nMACD {ind['macd']:.4f}>0 ADX {ind['adx']:.0f} DI+{ind['pdi']:.0f}>DI-{ind['mdi']:.0f}\nسعر {price:.4f} هدف 8$")

        if cross_down and ind["macd"]<0 and ind["mdi"]>ind["pdi"]:
            d["shorts"].append({"price":price,"amount":50})
            await ch.send(f"📤 **DEATH CROSS 1h {sym} بيع**\nEMA50 {ind['ema50']:.2f} تحت 200 {ind['ema200']:.2f} ✅\nMACD {ind['macd']:.4f}<0 ADX {ind['adx']:.0f} DI-{ind['mdi']:.0f}>DI+{ind['pdi']:.0f}\nسعر {price:.4f} هدف 8$")

@bot.event
async def on_ready():
    print(f"Ready {bot.user}")
    if not loop.is_running(): loop.start()

@bot.event
async def on_message(m):
    if m.author==bot.user: return
    if "الرصيد" in m.content:
        embed=discord.Embed(title=f"📊 V4 1h EMA50/200 + MACD + ADX هدف 8$ وقف 3$",color=0xFFD700)
        total=0
        for sym in COINS:
            d=data.get(sym)
            if not d: continue
            pr=get_price(sym) or d["price"] or 0
            fl=sum((pr-t["price"])/t["price"]*t["amount"] for t in d["longs"])+sum((t["price"]-pr)/t["price"]*t["amount"] for t in d["shorts"]) if pr else 0
            total+=d["pnl"]+fl
            status = "🟢 صاعد قوي" if d["ema50"]>d["ema200"] and d["adx"]>20 else "🔴 هابط قوي" if d["ema50"]<d["ema200"] and d["adx"]>20 else "⚪ عرضي"
            embed.add_field(name=f"{sym} {status} ADX {d['adx']:.0f}",value=f"محقق {d['pnl']:+.2f}$ عائم {fl:+.2f}$ ✅{d['wins']}❌{d['losses']}",inline=True)
        embed.add_field(name="💰 صافي",value=f"{total:+.2f}$ | فريم {TIMEFRAME}",inline=False)
        embed.set_footer(text=f"EMA50/200 الساعة | {datetime.now().strftime('%H:%M')}")
        await m.channel.send(embed=embed); return
    if "تصفير" in m.content:
        for c in data: data[c]={"ema50":0,"ema200":0,"macd":0,"adx":0,"longs":[],"shorts":[],"pnl":0,"wins":0,"losses":0,"price":0}
        await m.channel.send("✅ تصفير V4 1h"); return
    await bot.process_commands(m)

bot.run(os.getenv("DISCORD_TOKEN"))

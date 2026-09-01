import discord, os, requests
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime

app = Flask('')
@app.route('/')
def home(): return "V5 1h Trend"
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run, daemon=True).start()

COINS=["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","AVAXUSDT","LINKUSDT","ADAUSDT","DOTUSDT"]
TF="1h"
data={}
def init(c):
    if c not in data: data[c]={"ema50":0,"ema200":0,"macd":0,"adx":0,"longs":[],"shorts":[],"pnl":0,"wins":0,"losses":0,"price":0}
for c in COINS: init(c)

def get_price(s):
    try: return float(requests.get(f"https://data-api.binance.vision/api/v3/ticker/price?symbol={s}",timeout=5).json()['price'])
    except: return None

def calc_ema(p, per):
    k=2/(per+1); e=sum(p[:per])/per
    for x in p[per:]: e=x*k+e*(1-k)
    return e

def get_ind(sym):
    try:
        k=requests.get(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={TF}&limit=250",timeout=10).json()
        if not isinstance(k,list) or len(k)<210: return None
        c=[float(x[4]) for x in k]; h=[float(x[2]) for x in k]; l=[float(x[3]) for x in k]
        ema50=calc_ema(c,50); ema200=calc_ema(c,200)
        macd=calc_ema(c,12)-calc_ema(c,26)
        trs=[]; pdm=[]; mdm=[]
        for i in range(1,len(c)):
            tr=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])); trs.append(tr)
            up=h[i]-h[i-1]; down=l[i-1]-l[i]
            pdm.append(up if up>down and up>0 else 0); mdm.append(down if down>up and down>0 else 0)
        atr=sum(trs[-14:])/14 if trs else 1
        pdi=sum(pdm[-14:])/14/atr*100; mdi=sum(mdm[-14:])/14/atr*100
        adx=abs(pdi-mdi)/(pdi+mdi)*100 if (pdi+mdi) else 0
        return {"ema50":ema50,"ema200":ema200,"macd":macd,"adx":adx,"pdi":pdi,"mdi":mdi,"price":c[-1]}
    except: return None

intents=discord.Intents.default(); intents.message_content=True
bot=commands.Bot(command_prefix="!",intents=intents)

@tasks.loop(minutes=5)
async def loop():
    ch=discord.utils.get(bot.get_all_channels(),name="العام") or next((c for c in bot.get_all_channels() if isinstance(c,discord.TextChannel)),None)
    if not ch: return
    for sym in COINS:
        ind=get_ind(sym)
        price=get_price(sym) or (ind["price"] if ind else None)
        if not ind or not price: continue
        d=data[sym]; d.update({"ema50":ind["ema50"],"ema200":ind["ema200"],"macd":ind["macd"],"adx":ind["adx"],"price":price})

        for t in d["longs"][:]:
            pnl=(price-t["price"])/t["price"]*t["amount"]
            if pnl<=-3 or pnl>=8 or ind["ema50"]<ind["ema200"] or ind["macd"]<0:
                d["pnl"]+=pnl; d["wins"]+=1 if pnl>=0 else 0; d["losses"]+=1 if pnl<0 else 0
                await ch.send(f"{'💰' if pnl>0 else '🛑'} **قفل LONG 1h {sym} {pnl:+.2f}$ ADX {ind['adx']:.0f}**")
                d["longs"]=[]
        for t in d["shorts"][:]:
            pnl=(t["price"]-price)/t["price"]*t["amount"]
            if pnl<=-3 or pnl>=8 or ind["ema50"]>ind["ema200"] or ind["macd"]>0:
                d["pnl"]+=pnl; d["wins"]+=1 if pnl>=0 else 0; d["losses"]+=1 if pnl<0 else 0
                await ch.send(f"{'💰' if pnl>0 else '🛑'} **قفل SHORT 1h {sym} {pnl:+.2f}$ ADX {ind['adx']:.0f}**")
                d["shorts"]=[]

        if d["longs"] or d["shorts"]: continue
        if ind["adx"]<12: continue # كنت حاط 20 عشان كذا ADX 17 ما دخل - نزلته 12

        long_cond = ind["ema50"]>ind["ema200"] and price>ind["ema50"] and ind["macd"]>0 and ind["pdi"]>ind["mdi"]
        short_cond = ind["ema50"]<ind["ema200"] and price<ind["ema50"] and ind["macd"]<0 and ind["mdi"]>ind["pdi"]

        if long_cond:
            d["longs"].append({"price":price,"amount":50})
            await ch.send(f"📥 **شراء ترند 1h {sym}**\nEMA50 {ind['ema50']:.2f}>EMA200 {ind['ema200']:.2f} MACD {ind['macd']:.4f}>0 ADX {ind['adx']:.0f} سعر {price:.3f}")
        if short_cond:
            d["shorts"].append({"price":price,"amount":50})
            await ch.send(f"📤 **بيع ترند 1h {sym}**\nEMA50 {ind['ema50']:.2f}<EMA200 {ind['ema200']:.2f} MACD {ind['macd']:.4f}<0 ADX {ind['adx']:.0f} سعر {price:.3f}")

@bot.event
async def on_ready():
    print(f"Ready {bot.user}")
    if not loop.is_running(): loop.start()

@bot.event
async def on_message(m):
    if m.author==bot.user: return
    if "الرصيد" in m.content:
        embed=discord.Embed(title=f"📊 V5 1h EMA50/200 + MACD + DI ADX>12 هدف 8$ وقف 3$",color=0x00ff00)
        total=0
        for sym in COINS:
            d=data.get(sym)
            if not d: continue
            pr=get_price(sym) or d["price"] or 0
            fl=sum((pr-t["price"])/t["price"]*t["amount"] for t in d["longs"])+sum((t["price"]-pr)/t["price"]*t["amount"] for t in d["shorts"]) if pr else 0
            total+=d["pnl"]+fl
            trend = "🟢 فوق 200" if d["ema50"]>d["ema200"] else "🔴 تحت 200"
            embed.add_field(name=f"{sym} {trend} ADX {d['adx']:.0f}",value=f"محقق {d['pnl']:+.2f}$ عائم {fl:+.2f}$ ✅{d['wins']}❌{d['losses']}",inline=True)
        embed.add_field(name="💰 صافي",value=f"{total:+.2f}$",inline=False)
        await m.channel.send(embed=embed); return
    if "تصفير" in m.content:
        for c in data: data[c]={"ema50":0,"ema200":0,"macd":0,"adx":0,"longs":[],"shorts":[],"pnl":0,"wins":0,"losses":0,"price":0}
        await m.channel.send("✅ تصفير V5 1h"); return
    await bot.process_commands(m)

bot.run(os.getenv("DISCORD_TOKEN"))

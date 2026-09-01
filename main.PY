import discord, os, requests
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime

app = Flask('')
@app.route('/')
def home(): return "V5 DCA 3x50"
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

        # حساب الربح الإجمالي لكل العملة
        total_long_pnl = sum((price-t["price"])/t["price"]*t["amount"] for t in d["longs"]) if d["longs"] else 0
        total_short_pnl = sum((t["price"]-price)/t["price"]*t["amount"] for t in d["shorts"]) if d["shorts"] else 0

        # قفل LONG
        if d["longs"]:
            if total_long_pnl>=24 or total_long_pnl<=-9 or ind["ema50"]<ind["ema200"] or ind["macd"]<0:
                d["pnl"]+=total_long_pnl; d["wins"]+=1 if total_long_pnl>=0 else 0; d["losses"]+=1 if total_long_pnl<0 else 0
                await ch.send(f"{'💰' if total_long_pnl>0 else '🛑'} **قفل LONG {sym} {len(d['longs'])} دفعات {total_long_pnl:+.2f}$**\nEMA50 {ind['ema50']:.2f} / 200 {ind['ema200']:.2f} ADX {ind['adx']:.0f}")
                d["longs"]=[]

        # قفل SHORT
        if d["shorts"]:
            if total_short_pnl>=24 or total_short_pnl<=-9 or ind["ema50"]>ind["ema200"] or ind["macd"]>0:
                d["pnl"]+=total_short_pnl; d["wins"]+=1 if total_short_pnl>=0 else 0; d["losses"]+=1 if total_short_pnl<0 else 0
                await ch.send(f"{'💰' if total_short_pnl>0 else '🛑'} **قفل SHORT {sym} {len(d['shorts'])} دفعات {total_short_pnl:+.2f}$**\nEMA50 {ind['ema50']:.2f} / 200 {ind['ema200']:.2f} ADX {ind['adx']:.0f}")
                d["shorts"]=[]

        if ind["adx"]<12: continue

        # شروط الترند
        long_trend = ind["ema50"]>ind["ema200"] and price>ind["ema50"] and ind["macd"]>0 and ind["pdi"]>ind["mdi"]
        short_trend = ind["ema50"]<ind["ema200"] and price<ind["ema50"] and ind["macd"]<0 and ind["mdi"]>ind["pdi"]

        # دخول LONG دفعات
        if long_trend:
            if len(d["longs"])==0:
                d["longs"].append({"price":price,"amount":50})
                await ch.send(f"📥 **شراء 1/3 ترند {sym} 50$** EMA50 {ind['ema50']:.2f}>200 {ind['ema200']:.2f} MACD {ind['macd']:.4f}>0 ADX {ind['adx']:.0f} سعر {price:.2f}")
            elif len(d["longs"])==1 and price >= d["longs"][-1]["price"]*1.01:
                d["longs"].append({"price":price,"amount":50})
                await ch.send(f"📥 **شراء 2/3 ترند {sym} 50$** متوسط {sum(t['price'] for t in d['longs'])/2:.2f} ADX {ind['adx']:.0f}")
            elif len(d["longs"])==2 and price >= d["longs"][-1]["price"]*1.01 and ind["adx"]>25:
                d["longs"].append({"price":price,"amount":50})
                await ch.send(f"📥 **شراء 3/3 ترند {sym} 50$** إجمالي 150$ ADX قوي {ind['adx']:.0f}")

        # دخول SHORT دفعات (مثل صورتك)
        if short_trend:
            if len(d["shorts"])==0:
                d["shorts"].append({"price":price,"amount":50})
                await ch.send(f"📤 **بيع 1/3 ترند {sym} 50$** EMA50 {ind['ema50']:.2f}<200 {ind['ema200']:.2f} MACD {ind['macd']:.4f}<0 ADX {ind['adx']:.0f} سعر {price:.2f}")
            elif len(d["shorts"])==1 and price <= d["shorts"][-1]["price"]*0.99:
                d["shorts"].append({"price":price,"amount":50})
                await ch.send(f"📤 **بيع 2/3 ترند {sym} 50$** متوسط {sum(t['price'] for t in d['shorts'])/2:.2f} ADX {ind['adx']:.0f}")
            elif len(d["shorts"])==2 and price <= d["shorts"][-1]["price"]*0.99 and ind["adx"]>25:
                d["shorts"].append({"price":price,"amount":50})
                await ch.send(f"📤 **بيع 3/3 ترند {sym} 50$** إجمالي 150$ ADX قوي {ind['adx']:.0f}")

@bot.event
async def on_ready():
    print(f"Ready {bot.user}")
    if not loop.is_running(): loop.start()

@bot.event
async def on_message(m):
    if m.author==bot.user: return
    if "الرصيد" in m.content:
        embed=discord.Embed(title=f"📊 V5 DCA 3x50$ | 1h هدف 24$ وقف 9$ | ADX>12",color=0xFF0000)
        total=0
        for sym in COINS:
            d=data.get(sym)
            if not d: continue
            pr=get_price(sym) or d["price"] or 0
            fl_long=sum((pr-t["price"])/t["price"]*t["amount"] for t in d["longs"]) if pr else 0
            fl_short=sum((t["price"]-pr)/t["price"]*t["amount"] for t in d["shorts"]) if pr else 0
            fl=fl_long+fl_short
            total+=d["pnl"]+fl
            count = len(d["longs"])+len(d["shorts"])
            avg = f" متوسط {(sum(t['price'] for t in d['longs']+d['shorts'])/count):.2f}" if count>0 else ""
            embed.add_field(name=f"{sym} {count}/3 ADX {d['adx']:.0f}{avg}",value=f"محقق {d['pnl']:+.2f}$ عائم {fl:+.2f}$ ✅{d['wins']}❌{d['losses']}",inline=True)
        embed.add_field(name="💰 صافي",value=f"{total:+.2f}$ | فريم {TF}",inline=False)
        await m.channel.send(embed=embed); return
    if "تصفير" in m.content:
        for c in data: data[c]={"ema50":0,"ema200":0,"macd":0,"adx":0,"longs":[],"shorts":[],"pnl":0,"wins":0,"losses":0,"price":0}
        await m.channel.send("✅ تصفير V5 DCA"); return
    await bot.process_commands(m)

bot.run(os.getenv("DISCORD_TOKEN"))

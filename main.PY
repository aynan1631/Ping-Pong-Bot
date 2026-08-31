import discord, os, requests
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime

app = Flask('')
@app.route('/')
def home(): return "V3 1m 3$"
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run, daemon=True).start()

COINS=["BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","PEPEUSDT","WIFUSDT","BONKUSDT","FLOKIUSDT","SHIBUSDT"]
data={}
def init_coin(c):
    if c not in data: data[c]={"macd":0,"ema7":0,"ema21":0,"adx":0,"open_longs":[],"open_shorts":[],"closed_pnl":0,"wins":0,"losses":0,"last_price":0}
for c in COINS: init_coin(c)

def get_price(s):
    try: return float(requests.get(f"https://data-api.binance.vision/api/v3/ticker/price?symbol={s}",timeout=5).json()['price'])
    except: return None

def calc_ema(p,s):
    k=2/(s+1); e=sum(p[:s])/s
    for x in p[s:]: e=x*k+e*(1-k)
    return e

def get_indicators(sym,interval="1m"):
    try:
        klines=requests.get(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={interval}&limit=100",timeout=8).json()
        if not isinstance(klines,list) or len(klines)<50: return None
        closes=[float(k[4]) for k in klines]
        highs=[float(k[2]) for k in klines]; lows=[float(k[3]) for k in klines]
        ema7=calc_ema(closes,7); ema21=calc_ema(closes,21)
        prev7=calc_ema(closes[:-1],7); prev21=calc_ema(closes[:-1],21)
        macd=calc_ema(closes,12)-calc_ema(closes,26)
        trs=[]; pdm=[]; mdm=[]
        for i in range(1,len(closes)):
            tr=max(highs[i]-lows[i],abs(highs[i]-closes[i-1]),abs(lows[i]-closes[i-1])); trs.append(tr)
            up=highs[i]-highs[i-1]; down=lows[i-1]-lows[i]
            pdm.append(up if up>down and up>0 else 0); mdm.append(down if down>up and down>0 else 0)
        atr=sum(trs[-14:])/14 if len(trs)>=14 else 1
        pdi=sum(pdm[-14:])/14/atr*100 if atr else 0; mdi=sum(mdm[-14:])/14/atr*100 if atr else 0
        adx=abs(pdi-mdi)/(pdi+mdi)*100 if (pdi+mdi) else 0
        dist=abs(ema7-ema21)/closes[-1]*100
        return {"ema7":ema7,"ema21":ema21,"prev7":prev7,"prev21":prev21,"macd":macd,"adx":adx,"dist":dist,"price":closes[-1]}
    except: return None

intents=discord.Intents.default(); intents.message_content=True
bot=commands.Bot(command_prefix="!",intents=intents)

@tasks.loop(seconds=20)
async def strategy_loop():
    ch=discord.utils.get(bot.get_all_channels(),name="العام") or next((c for c in bot.get_all_channels() if isinstance(c,discord.TextChannel)),None)
    if not ch: return
    for sym in COINS:
        ind=get_indicators(sym,"1m")
        price=get_price(sym) or (ind["price"] if ind else None)
        if not ind or not price: continue
        d=data[sym]; d.update({"ema7":ind["ema7"],"ema21":ind["ema21"],"macd":ind["macd"],"adx":ind["adx"],"last_price":price})
        for t in d["open_longs"][:]:
            pnl=(price-t["price"])/t["price"]*t["amount"]
            if pnl<=-1.5 or pnl>=3 or (ind["macd"]<0 and ind["ema7"]<ind["ema21"]):
                d["closed_pnl"]+=pnl; d["wins"]+=1 if pnl>=0 else 0; d["losses"]+=1 if pnl<0 else 0
                await ch.send(f"{'💰' if pnl>0 else '🛑'} **قفل LONG {sym} {pnl:+.2f}$ ADX {ind['adx']:.0f}** سعر {price:.5f}")
                d["open_longs"]=[]
        for t in d["open_shorts"][:]:
            pnl=(t["price"]-price)/t["price"]*t["amount"]
            if pnl<=-1.5 or pnl>=3 or (ind["macd"]>0 and ind["ema7"]>ind["ema21"]):
                d["closed_pnl"]+=pnl; d["wins"]+=1 if pnl>=0 else 0; d["losses"]+=1 if pnl<0 else 0
                await ch.send(f"{'💰' if pnl>0 else '🛑'} **قفل SHORT {sym} {pnl:+.2f}$ ADX {ind['adx']:.0f}** سعر {price:.5f}")
                d["open_shorts"]=[]
        if d["open_longs"] or d["open_shorts"]: continue
        if ind["adx"]<12: continue
        if ind["dist"]<0.03: continue
        cross_up=ind["prev7"]<=ind["prev21"] and ind["ema7"]>ind["ema21"]
        cross_down=ind["prev7"]>=ind["prev21"] and ind["ema7"]<ind["ema21"]
        if cross_up and ind["macd"]>0:
            d["open_longs"].append({"price":price,"amount":50})
            await ch.send(f"📥 **شراء {sym} هدف 3$** MACD {ind['macd']:.4f}>0 ADX {ind['adx']:.0f} سعر {price:.5f}")
        if cross_down and ind["macd"]<0:
            d["open_shorts"].append({"price":price,"amount":50})
            await ch.send(f"📤 **بيع {sym} هدف 3$** MACD {ind['macd']:.4f}<0 ADX {ind['adx']:.0f} سعر {price:.5f}")

@bot.event
async def on_ready():
    print(f"Ready {bot.user}")
    if not strategy_loop.is_running(): strategy_loop.start()

@bot.event
async def on_message(m):
    if m.author==bot.user: return
    if "الرصيد" in m.content:
        embed=discord.Embed(title=f"📊 V3 1m هدف 3$ وقف 1.5$ ADX>12",color=0x00ff00)
        total=0
        for sym in COINS:
            d=data.get(sym);
            if not d: continue
            pr=get_price(sym) or d["last_price"] or 0
            fl=sum((pr-t["price"])/t["price"]*t["amount"] for t in d["open_longs"])+sum((t["price"]-pr)/t["price"]*t["amount"] for t in d["open_shorts"]) if pr else 0
            total+=d["closed_pnl"]+fl
            embed.add_field(name=f"{sym} ADX {d['adx']:.0f}",value=f"محقق {d['closed_pnl']:+.2f}$ عائم {fl:+.2f}$ ✅{d['wins']}❌{d['losses']}",inline=True)
        embed.add_field(name="💰 صافي",value=f"{total:+.2f}$",inline=False)
        embed.set_footer(text=f"هدف 3$ | {datetime.now().strftime('%H:%M')}")
        await m.channel.send(embed=embed); return
    if "تصفير" in m.content:
        for c in data: data[c]={"macd":0,"ema7":0,"ema21":0,"adx":0,"open_longs":[],"open_shorts":[],"closed_pnl":0,"wins":0,"losses":0,"last_price":0}
        await m.channel.send("✅ تصفير V3 هدف 3$"); return
    await bot.process_commands(m)

bot.run(os.getenv("DISCORD_TOKEN"))

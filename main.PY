import discord, os, requests
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime

app = Flask('')
@app.route('/')
def home(): return "1m V2 5$"
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run, daemon=True).start()

TIMEFRAME="1m"; HTF="5m"
COINS=["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","PEPEUSDT","WIFUSDT","TNSRUSDT","PUMPUSDT"]
data={}
def init_coin(c):
    if c not in data: data[c]={"macd":0,"ema7":0,"ema21":0,"ema50":0,"adx":0,"open_longs":[],"open_shorts":[],"closed_pnl":0,"wins":0,"losses":0,"last_price":0}
for c in COINS: init_coin(c)

def get_price(s):
    try: return float(requests.get(f"https://data-api.binance.vision/api/v3/ticker/price?symbol={s}",timeout=5).json()['price'])
    except: return None

def calc_ema(prices,period):
    k=2/(period+1); ema=sum(prices[:period])/period
    for p in prices[period:]: ema=p*k+ema*(1-k)
    return ema

def get_indicators(symbol,interval="1m"):
    try:
        klines=requests.get(f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit=150",timeout=10).json()
        if not isinstance(klines,list) or len(klines)<60: return None
        closes=[float(k[4]) for k in klines]; highs=[float(k[2]) for k in klines]; lows=[float(k[3]) for k in klines]
        ema7=calc_ema(closes,7); ema21=calc_ema(closes,21); ema50=calc_ema(closes,50)
        prev_ema7=calc_ema(closes[:-1],7); prev_ema21=calc_ema(closes[:-1],21)
        macd=calc_ema(closes,12)-calc_ema(closes,26)
        trs=[]; plus_dm=[]; minus_dm=[]
        for i in range(1,len(closes)):
            tr=max(highs[i]-lows[i],abs(highs[i]-closes[i-1]),abs(lows[i]-closes[i-1])); trs.append(tr)
            up=highs[i]-highs[i-1]; down=lows[i-1]-lows[i]
            plus_dm.append(up if up>down and up>0 else 0); minus_dm.append(down if down>up and down>0 else 0)
        atr=sum(trs[-14:])/14 if len(trs)>=14 else 1
        plus_di=sum(plus_dm[-14:])/14/atr*100 if atr else 0; minus_di=sum(minus_dm[-14:])/14/atr*100 if atr else 0
        dx=abs(plus_di-minus_di)/(plus_di+minus_di)*100 if (plus_di+minus_di) else 0
        dist=abs(ema7-ema21)/closes[-1]*100
        return {"ema7":ema7,"ema21":ema21,"ema50":ema50,"prev_ema7":prev_ema7,"prev_ema21":prev_ema21,"macd":macd,"plus_di":plus_di,"minus_di":minus_di,"adx":dx,"dist":dist,"price":closes[-1]}
    except: return None

def get_htf_macd(symbol):
    ind=get_indicators(symbol,HTF); return ind["macd"] if ind else 0

def get_most_volatile(limit=10):
    try:
        r=requests.get("https://data-api.binance.vision/api/v3/ticker/24hr",timeout=12).json()
        filt=[x for x in r if x['symbol'].endswith('USDT') and float(x['quoteVolume'])>8000000 and 'USDC' not in x['symbol']]
        s=sorted(filt,key=lambda x: abs(float(x['priceChangePercent'])),reverse=True)
        return [x['symbol'] for x in s[:limit]]
    except: return COINS

intents=discord.Intents.default(); intents.message_content=True
bot=commands.Bot(command_prefix="!",intents=intents)

@tasks.loop(minutes=30)
async def update_volatile():
    global COINS
    new=get_most_volatile(10)
    if new:
        COINS=new
        for c in COINS: init_coin(c)

@tasks.loop(seconds=30)
async def strategy_loop():
    ch=discord.utils.get(bot.get_all_channels(),name="العام") or next((c for c in bot.get_all_channels() if isinstance(c,discord.TextChannel)),None)
    if not ch: return
    all_to_check=list(set(COINS+[c for c in data if data[c]["open_longs"] or data[c]["open_shorts"]]))
    for sym in all_to_check:
        ind=get_indicators(sym,TIMEFRAME)
        price=get_price(sym) or (ind["price"] if ind else None)
        if not ind or not price: continue
        d=data[sym]; d.update({"ema7":ind["ema7"],"ema21":ind["ema21"],"ema50":ind["ema50"],"macd":ind["macd"],"adx":ind["adx"],"last_price":price})
        htf_macd=get_htf_macd(sym)
        for t in d["open_longs"][:]:
            pnl=(price-t["price"])/t["price"]*t["amount"]
            if pnl<=-1.5 or pnl>=5 or (ind["macd"]<0 and ind["ema7"]<ind["ema21"]):
                d["closed_pnl"]+=pnl
                d["wins"]+=1 if pnl>=0 else 0; d["losses"]+=1 if pnl<0 else 0
                await ch.send(f"{'💰' if pnl>0 else '🛑'} **قفل LONG {sym} {pnl:+.2f}$**\nMACD {ind['macd']:.4f} ADX {ind['adx']:.1f} سعر {price:.6f}")
                d["open_longs"]=[]
        for t in d["open_shorts"][:]:
            pnl=(t["price"]-price)/t["price"]*t["amount"]
            if pnl<=-1.5 or pnl>=5 or (ind["macd"]>0 and ind["ema7"]>ind["ema21"]):
                d["closed_pnl"]+=pnl
                d["wins"]+=1 if pnl>=0 else 0; d["losses"]+=1 if pnl<0 else 0
                await ch.send(f"{'💰' if pnl>0 else '🛑'} **قفل SHORT {sym} {pnl:+.2f}$**\nMACD {ind['macd']:.4f} ADX {ind['adx']:.1f} سعر {price:.6f}")
                d["open_shorts"]=[]
        if d["open_longs"] or d["open_shorts"]: continue
        if ind["adx"]<18 or ind["dist"]<0.10: continue
        cross_up=ind["prev_ema7"]<=ind["prev_ema21"] and ind["ema7"]>ind["ema21"]
        cross_down=ind["prev_ema7"]>=ind["prev_ema21"] and ind["ema7"]<ind["ema21"]
        if cross_up and price>ind["ema50"] and ind["macd"]>0 and htf_macd>0 and ind["plus_di"]>ind["minus_di"]:
            d["open_longs"].append({"price":price,"amount":50})
            await ch.send(f"📥 **شراء {sym} V2 5$**\nMACD {ind['macd']:.4f}>0 5m {htf_macd:.4f}>0 ADX {ind['adx']:.1f} ✅\nEMA7>EMA21 فوق 50 سعر {price:.6f}")
        if cross_down and price<ind["ema50"] and ind["macd"]<0 and htf_macd<0 and ind["minus_di"]>ind["plus_di"]:
            d["open_shorts"].append({"price":price,"amount":50})
            await ch.send(f"📤 **بيع {sym} V2 5$**\nMACD {ind['macd']:.4f}<0 5m {htf_macd:.4f}<0 ADX {ind['adx']:.1f} ✅\nEMA7<EMA21 تحت 50 سعر {price:.6f}")

@bot.event
async def on_ready():
    print(f"Ready {bot.user}")
    if not strategy_loop.is_running(): strategy_loop.start()
    if not update_volatile.is_running(): update_volatile.start()

@bot.event
async def on_message(m):
    if m.author==bot.user: return
    txt=m.content.strip()
    if "الرصيد" in txt:
        embed=discord.Embed(title=f"📊 V2 1m | هدف 5$ وقف 1.5$ | EMA50+ADX+5m",color=0x00ff00)
        embed.add_field(name="🎯",value=f"`{', '.join(COINS)}`",inline=False)
        total=0; show=list(set(COINS+[c for c in data if data[c]["closed_pnl"]!=0 or data[c]["open_longs"] or data[c]["open_shorts"]]))
        for sym in show[:12]:
            d=data.get(sym)
            if not d: continue
            pr=get_price(sym) or d["last_price"] or 0
            fl=sum((pr-t["price"])/t["price"]*t["amount"] for t in d["open_longs"])+sum((t["price"]-pr)/t["price"]*t["amount"] for t in d["open_shorts"]) if pr else 0
            total+=d["closed_pnl"]+fl
            embed.add_field(name=f"{sym} ADX {d['adx']:.0f}",value=f"محقق {d['closed_pnl']:+.2f}$ عائم {fl:+.2f}$ ✅{d['wins']}❌{d['losses']}",inline=True)
        embed.add_field(name="💰 صافي",value=f"{total:+.2f}$",inline=False)
        embed.set_footer(text=f"هدف 5$ وقف 1.5$ | {datetime.now().strftime('%H:%M')}")
        await m.channel.send(embed=embed); return
    if "تصفير" in txt:
        for c in list(data.keys()): data[c]={"macd":0,"ema7":0,"ema21":0,"ema50":0,"adx":0,"open_longs":[],"open_shorts":[],"closed_pnl":0,"wins":0,"losses":0,"last_price":0}
        await m.channel.send("✅ تصفير V2 هدف 5$"); return
    await bot.process_commands(m)

bot.run(os.getenv("DISCORD_TOKEN"))

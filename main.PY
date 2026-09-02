import discord, os, requests, math
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home():
    html = "<html><head><meta charset='utf-8'><style>body{font-family:Arial;background:#0f0f0f;color:#fff;padding:20px}.row{border:1px solid #333;padding:12px;margin:10px 0;border-radius:10px;background:#1a1a1a}.trade{font-size:18px;padding:8px 16px;border-radius:8px;font-weight:bold;display:inline-block;margin-left:10px}.total{font-size:18px;padding:8px 16px;border-radius:8px;font-weight:bold;display:inline-block;margin-left:10px}.win{background:#006400;color:#E0FFE0;border:1px solid #00AA00}.loss{background:#8B0000;color:#FFCCCC;border:1px solid #FF0000}</style></head><body><h2>V8.2 Bollinger + EMA200 15m - صعود شراء فقط هبوط بيع فقط</h2>"
    total_all=0
    for sym in COINS:
        d=data.get(sym,{}); total_all+=d.get("pnl",0)
        html+=f"<div class='row'><b style='font-size:18px'>{sym} | {'🔼 صاعد' if d.get('trend')=='up' else '🔽 هابط' if d.get('trend')=='down' else 'انتظار'} | سعر {d.get('price',0):.4f} وسط {d.get('middle',0):.4f} EMA200 {d.get('ema200',0):.4f}</b><br><br><span class='trade {'win' if d.get('last_pnl',0)>=0 else 'loss'}'>ربح الصفقة: {d.get('last_pnl',0):+.2f}$</span><span class='total {'win' if d.get('pnl',0)>=0 else 'loss'}'>مجموع المحقق: {d.get('pnl',0):+.2f}$</span><span style='font-size:18px;margin-right:15px'> | العائم {d.get('floating',0):+.2f}$ | {d.get('status','لا يوجد')}</span></div>"
    html+=f"<hr><div class='total {'win' if total_all>=0 else 'loss'}' style='font-size:22px'>الصافي الكلي: {total_all:+.2f}$</div></body></html>"
    return html
def run(): app.run(host='0.0.0.0',port=10000)
Thread(target=run,daemon=True).start()

COINS=["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","AVAXUSDT","LINKUSDT","ADAUSDT","DOTUSDT"]
TF="60m"
data={}
for c in COINS: data[c]={"middle":0,"ema200":0,"price":0,"longs":[],"shorts":[],"pnl":0,"last_pnl":0,"floating":0,"status":"لا يوجد","trend":""}

def get_price(s):
    try: return float(requests.get(f"https://data-api.binance.vision/api/v3/ticker/price?symbol={s}",timeout=5).json()['price'])
    except: return None

def get_bb_ema(sym):
    try:
        k=requests.get(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={TF}&limit=250",timeout=10).json()
        if not isinstance(k,list) or len(k)<210: return None
        closes=[float(x[4]) for x in k]; highs=[float(x[2]) for x in k]; lows=[float(x[3]) for x in k]
        sma20=sum(closes[-20:])/20; std=math.sqrt(sum((x-sma20)**2 for x in closes[-20:])/20); ema200=sum(closes[-200:])/200
        trs=[]; pdm=[]; mdm=[]
        for i in range(1,len(closes)):
            tr=max(highs[i]-lows[i],abs(highs[i]-closes[i-1]),abs(lows[i]-closes[i-1])); trs.append(tr)
            up=highs[i]-highs[i-1]; down=lows[i-1]-lows[i]
            pdm.append(up if up>down and up>0 else 0); mdm.append(down if down>up and down>0 else 0)
        atr=sum(trs[-14:])/14 if trs else 1; pdi=sum(pdm[-14:])/14/atr*100 if atr else 0; mdi=sum(mdm[-14:])/14/atr*100 if atr else 0
        adx=abs(pdi-mdi)/(pdi+mdi)*100 if (pdi+mdi) else 0
        return {"middle":sma20,"upper":sma20+2*std,"lower":sma20-2*std,"ema200":ema200,"adx":adx,"pdi":pdi,"mdi":mdi,"last":closes[-1],"prev":closes[-2]}
    except: return None

intents=discord.Intents.default(); intents.message_content=True
bot=commands.Bot(command_prefix="!",intents=intents)

@tasks.loop(minutes=2)
async def loop():
    ch=discord.utils.get(bot.get_all_channels(),name="العام") or next((c for c in bot.get_all_channels() if isinstance(c,discord.TextChannel)),None)
    if not ch: return
    for sym in COINS:
        bb=get_bb_ema(sym)
        if not bb: continue
        d=data[sym]; d["middle"]=bb["middle"]; d["ema200"]=bb["ema200"]; d["price"]=bb["last"]; d["trend"]="up" if bb["last"]>bb["ema200"] else "down"
        price=bb["last"]
        fl=0
        if d["longs"]: fl+=sum((price-t["price"])/t["price"]*t["amount"] for t in d["longs"])
        if d["shorts"]: fl+=sum((t["price"]-price)/t["price"]*t["amount"] for t in d["shorts"])
        d["floating"]=fl; d["status"]=f"LONG {len(d['longs'])} {fl:+.2f}$" if d["longs"] else f"SHORT {len(d['shorts'])} {fl:+.2f}$" if d["shorts"] else "انتظار"
        if bb["adx"]<20: continue
        close_above = bb["prev"]<=bb["middle"] and bb["last"]>bb["middle"] and bb["last"]>bb["ema200"] and bb["pdi"]>bb["mdi"] and bb["last"]>bb["lower"]
        close_below = bb["prev"]>=bb["middle"] and bb["last"]<bb["middle"] and bb["last"]<bb["ema200"] and bb["mdi"]>bb["pdi"] and bb["last"]<bb["upper"]
        if close_above:
            if d["shorts"]:
                pr=get_price(sym) or price; pnl=sum((t["price"]-pr)/t["price"]*t["amount"] for t in d["shorts"])
                d["pnl"]+=pnl; d["last_pnl"]=pnl; await ch.send(f"✅ قفل SHORT {sym} {pnl:+.2f}$ `ربح الصفقة {pnl:+.2f}$ | مجموع {d['pnl']:+.2f}$`"); d["shorts"]=[]
            if not d["longs"]:
                d["longs"].append({"price":price,"amount":150}); await ch.send(f"📥 شراء V8.2 {sym} صاعد فوق EMA200 {bb['ema200']:.4f} ADX {bb['adx']:.0f}")
        if close_below:
            if d["longs"]:
                pr=get_price(sym) or price; pnl=sum((pr-t["price"])/t["price"]*t["amount"] for t in d["longs"])
                d["pnl"]+=pnl; d["last_pnl"]=pnl; await ch.send(f"✅ قفل LONG {sym} {pnl:+.2f}$ `ربح الصفقة {pnl:+.2f}$ | مجموع {d['pnl']:+.2f}$`"); d["longs"]=[]
            if not d["shorts"]:
                d["shorts"].append({"price":price,"amount":150}); await ch.send(f"📤 بيع V8.2 {sym} هابط تحت EMA200 {bb['ema200']:.4f} ADX {bb['adx']:.0f}")

@bot.event
async def on_ready():
    print(f"Ready V8.2 {bot.user}")
    if not loop.is_running(): loop.start()

@bot.event
async def on_message(m):
    if m.author==bot.user: return
    if "الرصيد" in m.content:
        embed=discord.Embed(title="V8.2 بولنجر + EMA200 15m - صعود شراء فقط هبوط بيع فقط",color=0x00FF00)
        total=0
        for sym in COINS:
            d=data[sym]; total+=d["pnl"]+d["floating"]
            embed.add_field(name=f"{sym} {d['trend']} {d['status']} محقق {d['pnl']:+.2f}$ اخر {d['last_pnl']:+.2f}$",value=f"Price {d['price']:.4f} Mid {d['middle']:.4f} EMA200 {d['ema200']:.4f} Float {d['floating']:+.2f}$",inline=False)
        embed.add_field(name="الصافي",value=f"{total:+.2f}$",inline=False)
        await m.channel.send(embed=embed); return
    if "تصفير" in m.content:
        for c in COINS: data[c]={"middle":0,"ema200":0,"price":0,"longs":[],"shorts":[],"pnl":0,"last_pnl":0,"floating":0,"status":"لا يوجد","trend":""}
        await m.channel.send("✅ تصفير V8.2"); return
    await bot.process_commands(m)

bot.run(os.getenv("DISCORD_TOKEN"))

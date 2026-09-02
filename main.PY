import discord, os, requests, math
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread

app = Flask('')

# الصفحة المطلوبة: حقلين على خط واحد ملونين مقاس 18
@app.route('/')
def home():
    html = """
    <html><head><meta charset='utf-8'><style>
    body{font-family:Arial;background:#0f0f0f;color:#fff;padding:20px}
   .row{border:1px solid #333;padding:12px;margin:10px 0;border-radius:10px;background:#1a1a1a}
   .trade{font-size:18px;padding:8px 16px;border-radius:8px;font-weight:bold;display:inline-block;margin-left:10px}
   .total{font-size:18px;padding:8px 16px;border-radius:8px;font-weight:bold;display:inline-block;margin-left:10px}
   .win{background:#006400;color:#E0FFE0;border:1px solid #00AA00}
   .loss{background:#8B0000;color:#FFCCCC;border:1px solid #FF0000}
    </style></head><body><h2>📊 V7 Bollinger 15m - بولنجر باند فقط</h2>
    """
    total_all=0
    for sym in COINS:
        d=data.get(sym, {})
        total_all+=d.get("pnl",0)
        last=d.get("last_pnl",0)
        html+=f"""
        <div class='row'>
            <b style='font-size:18px'>{sym} / 15m | السعر {d.get('price',0):.4f} | وسط {d.get('middle',0):.4f}</b><br><br>
            <span class='trade {"win" if last>=0 else "loss"}'>ربح الصفقة: {last:+.2f}$</span>
            <span class='total {"win" if d.get("pnl",0)>=0 else "loss"}'>مجموع المحقق: {d.get("pnl",0):+.2f}$</span>
            <span style='font-size:18px;margin-right:15px'> | العائم: {d.get("floating",0):+.2f}$ | {d.get("status","لا يوجد")}</span>
        </div>
        """
    html+=f"<hr><div class='total {"win" if total_all>=0 else "loss"}' style='font-size:22px'>💰 الصافي الكلي: {total_all:+.2f}$</div></body></html>"
    return html

def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run, daemon=True).start()

COINS=["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","AVAXUSDT","LINKUSDT","ADAUSDT","DOTUSDT"]
TF="15m"
data={}
for c in COINS: data[c]={"middle":0,"price":0,"longs":[],"shorts":[],"pnl":0,"last_pnl":0,"floating":0,"status":"لا يوجد"}

def get_price(s):
    try: return float(requests.get(f"https://data-api.binance.vision/api/v3/ticker/price?symbol={s}",timeout=5).json()['price'])
    except: return None

def get_bb(sym):
    try:
        k=requests.get(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={TF}&limit=100",timeout=10).json()
        if not isinstance(k,list) or len(k)<25: return None
        closes=[float(x[4]) for x in k]
        sma=sum(closes[-20:])/20
        std=math.sqrt(sum((x-sma)**2 for x in closes[-20:])/20)
        return {"middle":sma,"upper":sma+2*std,"lower":sma-2*std,"last":closes[-1],"prev":closes[-2]}
    except: return None

intents=discord.Intents.default(); intents.message_content=True
bot=commands.Bot(command_prefix="!",intents=intents)

@tasks.loop(minutes=2)
async def loop():
    ch=discord.utils.get(bot.get_all_channels(),name="العام") or next((c for c in bot.get_all_channels() if isinstance(c,discord.TextChannel)),None)
    if not ch: return
    for sym in COINS:
        bb=get_bb(sym)
        if not bb: continue
        d=data[sym]
        d["middle"]=bb["middle"]; d["price"]=bb["last"]
        price=bb["last"]

        # حساب العائم الحالي
        fl=0
        if d["longs"]: fl+=sum((price-t["price"])/t["price"]*t["amount"] for t in d["longs"])
        if d["shorts"]: fl+=sum((t["price"]-price)/t["price"]*t["amount"] for t in d["shorts"])
        d["floating"]=fl
        d["status"]=f"LONG {len(d['longs'])} عائم {fl:+.2f}$" if d["longs"] else f"SHORT {len(d['shorts'])} عائم {fl:+.2f}$" if d["shorts"] else "لا يوجد"

        close_above = bb["prev"] <= bb["middle"] and bb["last"] > bb["middle"]
        close_below = bb["prev"] >= bb["middle"] and bb["last"] < bb["middle"]

        if close_above:
            if d["shorts"]:
                pr=get_price(sym) or price
                pnl=sum((t["price"]-pr)/t["price"]*t["amount"] for t in d["shorts"])
                d["pnl"]+=pnl; d["last_pnl"]=pnl
                await ch.send(f"📤 **قفل SHORT {sym} 15m {pnl:+.2f}$**\n`ربح الصفقة: {pnl:+.2f}$` | `مجموع المحقق: {d['pnl']:+.2f}$`")
                d["shorts"]=[]

            if not d["longs"]:
                d["longs"].append({"price":price,"amount":50})
                await ch.send(f"📥 **شراء بولنجر {sym} 15m**\nفوق الوسط {bb['middle']:.4f} سعر {price:.4f}")

        if close_below:
            if d["longs"]:
                pr=get_price(sym) or price
                pnl=sum((pr-t["price"])/t["price"]*t["amount"] for t in d["longs"])
                d["pnl"]+=pnl; d["last_pnl"]=pnl
                await ch.send(f"💰 **قفل LONG {sym} 15m {pnl:+.2f}$**\n`ربح الصفقة: {pnl:+.2f}$` | `مجموع المحقق: {d['pnl']:+.2f}$`")
                d["longs"]=[]

            if not d["shorts"]:
                d["shorts"].append({"price":price,"amount":50})
                await ch.send(f"📤 **بيع بولنجر {sym} 15m**\nتحت الوسط {bb['middle']:.4f} سعر {price:.4f}")

@bot.event
async def on_ready():
    print(f"Ready V7 Bollinger 15m {bot.user}")
    if not loop.is_running(): loop.start()

@bot.event
async def on_message(m):
    if m.author==bot.user: return
    if "الرصيد" in m.content:
        embed=discord.Embed(title="📊 V7 بولنجر 15m - وسط الباند فقط",color=0x00FF00)
        total=0
        for sym in COINS:
            d=data[sym]
            total+=d["pnl"]+d["floating"]
            embed.add_field(name=f"{sym} | {d['status']} | محقق {d['pnl']:+.2f}$ آخر صفقة {d['last_pnl']:+.2f}$",
                            value=f"سعر {d['price']:.4f} وسط {d['middle']:.4f} عائم {d['floating']:+.2f}$",inline=False)
        embed.add_field(name="💰 الصافي",value=f"{total:+.2f}$ | افتح رابط البوت للالوان مقاس 18",inline=False)
        await m.channel.send(embed=embed); return

    if "اقفل" in m.content:
        txt=m.content.upper()
        to_close=COINS if "الكل" in m.content else [c for c in COINS if c.replace("USDT","") in txt]
        for sym in to_close:
            d=data[sym]; pr=get_price(sym) or d["price"]
            if not pr or (not d["longs"] and not d["shorts"]): continue
            fl=sum((pr-t["price"])/t["price"]*t["amount"] for t in d["longs"])+sum((t["price"]-pr)/t["price"]*t["amount"] for t in d["shorts"])
            d["pnl"]+=fl; d["last_pnl"]=fl
            await m.channel.send(f"🛑 **إقفال يدوي {sym} {fl:+.2f}$**")
            d["longs"]=[]; d["shorts"]=[]; d["floating"]=0; d["status"]="لا يوجد"
        return

    if "تصفير" in m.content:
        for c in COINS: data[c]={"middle":0,"price":0,"longs":[],"shorts":[],"pnl":0,"last_pnl":0,"floating":0,"status":"لا يوجد"}
        await m.channel.send("✅ تصفير V7 بولنجر 15m"); return
    await bot.process_commands(m)

bot.run(os.getenv("DISCORD_TOKEN"))

import discord, os, requests
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime

app = Flask('')
@app.route('/')
def home(): return "Scalping TP 5% SL 5%"
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run, daemon=True).start()

COINS = ["FLOKIUSDT", "WIFUSDT", "PEPEUSDT"]
BUY_BUDGET = 100.0
SELL_BUDGET = 100.0
TP = 5.0
SL = 5.0

data = {}
for c in COINS:
    data[c] = {
        "high": 0, "low": 999999, "last_price": 0,
        "buy_spent": 0, "sell_spent": 0,
        "buy_stage": 0, "sell_stage": 0,
        "open_longs": [], "open_shorts": [],
        "closed_pnl": 0, "wins": 0, "losses": 0
    }

def get_price(s):
    try: return float(requests.get(f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={s}", timeout=5).json()['price'])
    except: return None

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@tasks.loop(seconds=60)
async def loop():
    channel = discord.utils.get(bot.get_all_channels(), name="العام") or next((c for c in bot.get_all_channels() if isinstance(c, discord.TextChannel)), None)
    if not channel: return

    for sym in COINS:
        price = get_price(sym)
        if not price: continue
        d = data[sym]
        if d["last_price"]==0:
            d["high"]=d["low"]=d["last_price"]=price; continue

        if price>d["high"]: d["high"]=price
        if price<d["low"]: d["low"]=price

        # === فحص الربح والخسارة ===
        for t in d["open_longs"][:]:
            pnl_pct = (price - t["price"]) / t["price"] * 100
            if pnl_pct >= TP: # ربح
                profit = t["amount"] * TP/100
                d["closed_pnl"]+=profit; d["wins"]+=1
                d["buy_spent"]-=t["amount"]; d["open_longs"].remove(t)
                d["buy_stage"]=0; d["high"]=d["low"]=price
                await channel.send(f"✅ **قفل ربح LONG {sym} +{TP}%**\nدخول `{t['price']}` خروج `{price}`\nربح `+{profit:.2f}$`")
            elif pnl_pct <= -SL: # خسارة
                loss = t["amount"] * SL/100
                d["closed_pnl"]-=loss; d["losses"]+=1
                d["buy_spent"]-=t["amount"]; d["open_longs"].remove(t)
                d["buy_stage"]=0; d["high"]=d["low"]=price
                await channel.send(f"❌ **وقف خسارة LONG {sym} -{SL}%**\nدخول `{t['price']}` خروج `{price}`\nخسارة `-{loss:.2f}$` - تم إرجاع الرصيد")

        for t in d["open_shorts"][:]:
            pnl_pct = (t["price"] - price) / t["price"] * 100
            if pnl_pct >= TP:
                profit = t["amount"] * TP/100
                d["closed_pnl"]+=profit; d["wins"]+=1
                d["sell_spent"]-=t["amount"]; d["open_shorts"].remove(t)
                d["sell_stage"]=0; d["high"]=d["low"]=price
                await channel.send(f"✅ **قفل ربح SHORT {sym} +{TP}%**\nدخول `{t['price']}` خروج `{price}`\nربح `+{profit:.2f}$`")
            elif pnl_pct <= -SL:
                loss = t["amount"] * SL/100
                d["closed_pnl"]-=loss; d["losses"]+=1
                d["sell_spent"]-=t["amount"]; d["open_shorts"].remove(t)
                d["sell_stage"]=0; d["high"]=d["low"]=price
                await channel.send(f"❌ **وقف خسارة SHORT {sym} -{SL}%**\nدخول `{t['price']}` خروج `{price}`\nخسارة `-{loss:.2f}$` - تم إرجاع الرصيد")

        # === دخول جديد ===
        drop_pct = (d["high"]-price)/d["high"]*100 if d["high"]>0 else 0
        rise_pct = (price-d["low"])/d["low"]*100 if d["low"]>0 else 0

        buy_amt=0
        if drop_pct>=1 and d["buy_stage"]==0: buy_amt=BUY_BUDGET*0.15; d["buy_stage"]=1
        elif drop_pct>=3 and d["buy_stage"]==1: buy_amt=BUY_BUDGET*0.30; d["buy_stage"]=2
        elif drop_pct>=5 and d["buy_stage"]==2: buy_amt=BUY_BUDGET*0.55; d["buy_stage"]=3
        if buy_amt>0 and d["buy_spent"]+buy_amt<=BUY_BUDGET:
            d["buy_spent"]+=buy_amt; d["open_longs"].append({"price":price,"amount":buy_amt}); d["low"]=price
            await channel.send(f"📥 **شراء {sym} م{ d['buy_stage']}/3** نزول {drop_pct:.2f}% سعر `{price}`")

        sell_amt=0
        if rise_pct>=1 and d["sell_stage"]==0: sell_amt=SELL_BUDGET*0.15; d["sell_stage"]=1
        elif rise_pct>=3 and d["sell_stage"]==1: sell_amt=SELL_BUDGET*0.30; d["sell_stage"]=2
        elif rise_pct>=5 and d["sell_stage"]==2: sell_amt=SELL_BUDGET*0.55; d["sell_stage"]=3
        if sell_amt>0 and d["sell_spent"]+sell_amt<=SELL_BUDGET:
            d["sell_spent"]+=sell_amt; d["open_shorts"].append({"price":price,"amount":sell_amt}); d["high"]=price
            await channel.send(f"📤 **بيع {sym} م{ d['sell_stage']}/3** صعود {rise_pct:.2f}% سعر `{price}`")

        d["last_price"]=price

@bot.event
async def on_ready():
    print(f"TP SL شغال {bot.user}")
    if not loop.is_running(): loop.start()

@bot.command(name="الرصيد")
async def bal(ctx):
    embed = discord.Embed(title="📊 سكالبينغ TP 5% / SL 5%", color=0x00ff00)
    total=0
    for sym in COINS:
        d=data[sym]; price=get_price(sym) or d["last_price"]
        floating=0
        for t in d["open_longs"]: floating+=(price-t["price"])/t["price"]*t["amount"]
        for t in d["open_shorts"]: floating+=(t["price"]-price)/t["price"]*t["amount"]
        total+=d["closed_pnl"]+floating
        embed.add_field(name=f"🔹 {sym} | ربح:{d['wins']} خسارة:{d['losses']}",
            value=f"سعر `{price}`\nمحقق {d['closed_pnl']:+.2f}$ عائم {floating:+.2f}$\nمفتوح {len(d['open_longs']+d['open_shorts'])} صفقة", inline=False)
    embed.add_field(name="💰 صافي الربح", value=f"{total:+.2f}$", inline=False)
    embed.set_footer(text=f"TP 5% SL 5% | {datetime.now().strftime('%H:%M')}")
    await ctx.channel.send(embed=embed)

@bot.event
async def on_message(m):
    if m.author==bot.user: return
    if "الرصيد" in m.content: await bal(m); return
    await bot.process_commands(m)

bot.run(os.getenv("DISCORD_TOKEN"))

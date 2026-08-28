import discord, os, requests
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime

app = Flask('')
@app.route('/')
def home(): return "Volatile Scalping Bot"
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run, daemon=True).start()

BUY_BUDGET = 100.0
SELL_BUDGET = 100.0
TP = 5.0
SL = 5.0

# يتغير تلقائياً
COINS = ["PEPEUSDT", "FLOKIUSDT", "WIFUSDT", "BONKUSDT", "DOGEUSDT"]
data = {}

def init_coin(c):
    if c not in data:
        data[c] = {"high":0,"low":999999,"last_price":0,"buy_spent":0,"sell_spent":0,"buy_stage":0,"sell_stage":0,"open_longs":[],"open_shorts":[],"closed_pnl":0,"wins":0,"losses":0}

for c in COINS: init_coin(c)

def get_price(s):
    try:
        r = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={s}", timeout=4).json()
        if 'price' in r: return float(r['price'])
    except: pass
    return None

def get_most_volatile(limit=10):
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=10).json()
        # فلترة: بس USDT ومش عملات مستقرة
        filtered = [x for x in r if x['symbol'].endswith('USDT') and not any(s in x['symbol'] for s in ['USDC','BUSD','TUSD','FDUSD']) and float(x['quoteVolume']) > 5000000]
        # ترتيب حسب الأكثر تقلباً (صعود+هبوط)
        sorted_coins = sorted(filtered, key=lambda x: abs(float(x['priceChangePercent'])), reverse=True)
        top = [x['symbol'] for x in sorted_coins[:limit]]
        return top
    except Exception as e:
        print(f"خطأ جلب المتقلبة: {e}")
        return COINS

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@tasks.loop(minutes=60)
async def update_volatile():
    global COINS
    new_coins = get_most_volatile(10)
    if new_coins:
        COINS = new_coins
        for c in COINS: init_coin(c)
        channel = discord.utils.get(bot.get_all_channels(), name="العام") or next((c for c in bot.get_all_channels() if isinstance(c, discord.TextChannel)), None)
        if channel:
            await channel.send(f"🔥 **تحديث العملات الأكثر تقلباً الآن:**\n`{', '.join(COINS)}`")

@tasks.loop(seconds=60)
async def loop():
    channel = discord.utils.get(bot.get_all_channels(), name="العام") or next((c for c in bot.get_all_channels() if isinstance(c, discord.TextChannel)), None)
    if not channel: return
    for sym in COINS:
        price = get_price(sym)
        if not price: continue
        d = data[sym]
        if d["last_price"]==0: d["high"]=d["low"]=d["last_price"]=price; continue
        if price>d["high"]: d["high"]=price
        if price<d["low"]: d["low"]=price

        for t in d["open_longs"][:]:
            pnl = (price - t["price"])/t["price"]*100
            if pnl >= TP:
                profit=t["amount"]*TP/100; d["closed_pnl"]+=profit; d["wins"]+=1; d["buy_spent"]-=t["amount"]; d["open_longs"].remove(t); d["buy_stage"]=0; d["high"]=d["low"]=price
                await channel.send(f"✅ ربح LONG {sym} +5% = +{profit:.2f}$")
            elif pnl <= -SL:
                loss=t["amount"]*SL/100; d["closed_pnl"]-=loss; d["losses"]+=1; d["buy_spent"]-=t["amount"]; d["open_longs"].remove(t); d["buy_stage"]=0; d["high"]=d["low"]=price
                await channel.send(f"❌ وقف LONG {sym} -5% = -{loss:.2f}$ رجع الرصيد")

        for t in d["open_shorts"][:]:
            pnl = (t["price"]-price)/t["price"]*100
            if pnl >= TP:
                profit=t["amount"]*TP/100; d["closed_pnl"]+=profit; d["wins"]+=1; d["sell_spent"]-=t["amount"]; d["open_shorts"].remove(t); d["sell_stage"]=0; d["high"]=d["low"]=price
                await channel.send(f"✅ ربح SHORT {sym} +5% = +{profit:.2f}$")
            elif pnl <= -SL:
                loss=t["amount"]*SL/100; d["closed_pnl"]-=loss; d["losses"]+=1; d["sell_spent"]-=t["amount"]; d["open_shorts"].remove(t); d["sell_stage"]=0; d["high"]=d["low"]=price
                await channel.send(f"❌ وقف SHORT {sym} -5% = -{loss:.2f}$ رجع الرصيد")

        drop_pct = (d["high"]-price)/d["high"]*100 if d["high"]>0 else 0
        rise_pct = (price-d["low"])/d["low"]*100 if d["low"]>0 else 0
        buy_amt=0
        if drop_pct>=1 and d["buy_stage"]==0: buy_amt=BUY_BUDGET*0.15; d["buy_stage"]=1
        elif drop_pct>=3 and d["buy_stage"]==1: buy_amt=BUY_BUDGET*0.30; d["buy_stage"]=2
        elif drop_pct>=5 and d["buy_stage"]==2: buy_amt=BUY_BUDGET*0.55; d["buy_stage"]=3
        if buy_amt>0 and d["buy_spent"]+buy_amt<=BUY_BUDGET:
            d["buy_spent"]+=buy_amt; d["open_longs"].append({"price":price,"amount":buy_amt}); d["low"]=price
            await channel.send(f"📥 شراء {sym} م{d['buy_stage']}/3 نزول {drop_pct:.1f}%")

        sell_amt=0
        if rise_pct>=1 and d["sell_stage"]==0: sell_amt=SELL_BUDGET*0.15; d["sell_stage"]=1
        elif rise_pct>=3 and d["sell_stage"]==1: sell_amt=SELL_BUDGET*0.30; d["sell_stage"]=2
        elif rise_pct>=5 and d["sell_stage"]==2: sell_amt=SELL_BUDGET*0.55; d["sell_stage"]=3
        if sell_amt>0 and d["sell_spent"]+sell_amt<=SELL_BUDGET:
            d["sell_spent"]+=sell_amt; d["open_shorts"].append({"price":price,"amount":sell_amt}); d["high"]=price
            await channel.send(f"📤 بيع {sym} م{d['sell_stage']}/3 صعود {rise_pct:.1f}%")
        d["last_price"]=price

@bot.event
async def on_ready():
    print(f"متقلبة شغال {bot.user}")
    # أول مرة يجيب المتقلبة
    global COINS
    vc = get_most_volatile(10)
    if vc: COINS=vc
    for c in COINS: init_coin(c)
    print(f"العملات: {COINS}")
    if not loop.is_running(): loop.start()
    if not update_volatile.is_running(): update_volatile.start()

@bot.command(name="الرصيد")
async def bal(ctx):
    embed = discord.Embed(title="📊 سكالبينغ - الأكثر تقلباً 🔥 TP 5% / SL 5%", color=0x00ff00)
    total=0
    embed.add_field(name="🎯 العملات الحالية", value=f"`{', '.join(COINS)}`", inline=False)
    for sym in COINS:
        d=data[sym]; price=get_price(sym) or d["last_price"]
        floating=0
        for t in d["open_longs"]: floating+=(price-t["price"])/t["price"]*t["amount"]
        for t in d["open_shorts"]: floating+=(t["price"]-price)/t["price"]*t["amount"]
        total+=d["closed_pnl"]+floating
        if len(d["open_longs"]+d["open_shorts"])>0 or d["closed_pnl"]!=0 or d["wins"]+d["losses"]>0:
            embed.add_field(name=f"🔹 {sym} ✅{d['wins']}❌{d['losses']}", value=f"محقق {d['closed_pnl']:+.2f}$ عائم {floating:+.2f}$ مفتوح {len(d['open_longs']+d['open_shorts'])}", inline=True)
    if len(embed.fields)==1:
        embed.description = "السوق هادي.. ننتظر أول حركة 1% في العملات المتقلبة"
    embed.add_field(name="💰 صافي الكل", value=f"{total:+.2f}$", inline=False)
    embed.set_footer(text=f"يتحدث كل ساعة | {datetime.now().strftime('%H:%M')}")
    await ctx.channel.send(embed=embed)

@bot.event
async def on_message(m):
    if m.author==bot.user: return
    if "الرصيد" in m.content: await bal(m); return
    if "المتقلبة" in m.content:
        vc = get_most_volatile(10)
        await m.channel.send(f"🔥 الأكثر تقلباً الآن:\n`{', '.join(vc)}`")
        return
    await bot.process_commands(m)

bot.run(os.getenv("DISCORD_TOKEN"))

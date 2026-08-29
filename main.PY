import discord, os, requests
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime

app = Flask('')
@app.route('/')
def home(): return "RSI Volatile Bot"
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run, daemon=True).start()

TIMEFRAME = "5m"
BUY_BUDGET = 100
SELL_BUDGET = 100

COINS = ["PEPEUSDT","FLOKIUSDT","WIFUSDT","BONKUSDT","DOGEUSDT","SHIBUSDT","SOLUSDT","BTCUSDT","ETHUSDT","1000PEPEUSDT"]
data = {}

def init_coin(c):
    if c not in data:
        data[c] = {"rsi":0,"open_longs":[],"open_shorts":[],"buy_spent":0,"sell_spent":0,"buy_levels_hit":[],"sell_levels_hit":[],"closed_pnl":0,"wins":0,"losses":0,"last_price":0}

for c in COINS: init_coin(c)

def get_price(s):
    try: return float(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={s}", timeout=4).json()['price'])
    except: return None

def get_most_volatile(limit=10):
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=10).json()
        filtered = [x for x in r if x['symbol'].endswith('USDT') and not any(s in x['symbol'] for s in ['USDC','BUSD','FDUSD','TUSD']) and float(x['quoteVolume']) > 5000000]
        sorted_coins = sorted(filtered, key=lambda x: abs(float(x['priceChangePercent'])), reverse=True)
        top = [x['symbol'] for x in sorted_coins[:limit]]
        return top
    except: return None

def get_rsi(symbol, interval="5m", period=14):
    try:
        klines = requests.get(f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100", timeout=6).json()
        closes = [float(k[4]) for k in klines]
        if len(closes) < period+1: return None
        gains, losses = [], []
        for i in range(1, len(closes)):
            diff = closes[i]-closes[i-1]
            if diff>=0: gains.append(diff); losses.append(0)
            else: gains.append(0); losses.append(-diff)
        avg_gain = sum(gains[:period])/period
        avg_loss = sum(losses[:period])/period
        for i in range(period, len(gains)):
            avg_gain = (avg_gain*(period-1)+gains[i])/period
            avg_loss = (avg_loss*(period-1)+losses[i])/period
        if avg_loss==0: return 100
        rs = avg_gain/avg_loss
        return round(100 - (100/(1+rs)),2)
    except: return None

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
            await channel.send(f"🔥 **تحديث تلقائي - الأكثر تقلباً الآن:**\n`{', '.join(COINS)}`")

@tasks.loop(seconds=60)
async def rsi_loop():
    channel = discord.utils.get(bot.get_all_channels(), name="العام") or next((c for c in bot.get_all_channels() if isinstance(c, discord.TextChannel)), None)
    if not channel: return
    for sym in COINS:
        price = get_price(sym)
        rsi = get_rsi(sym, TIMEFRAME)
        if not price or rsi is None: continue
        d = data[sym]; d["rsi"]=rsi; d["last_price"]=price

        if d["open_longs"] and rsi >= 95:
            total_amt = sum(t["amount"] for t in d["open_longs"])
            avg_entry = sum(t["price"]*t["amount"] for t in d["open_longs"])/total_amt
            pnl = (price-avg_entry)/avg_entry*total_amt
            d["closed_pnl"]+=pnl; d["wins" if pnl>=0 else "losses"]+=1
            await channel.send(f"💰 قفل LONG {sym} RSI {rsi} >=95 ربح {pnl:+.2f}$")
            d["open_longs"]=[]; d["buy_spent"]=0; d["buy_levels_hit"]=[]

        if d["open_shorts"] and rsi <= 15:
            total_amt = sum(t["amount"] for t in d["open_shorts"])
            avg_entry = sum(t["price"]*t["amount"] for t in d["open_shorts"])/total_amt
            pnl = (avg_entry-price)/avg_entry*total_amt
            d["closed_pnl"]+=pnl; d["wins" if pnl>=0 else "losses"]+=1
            await channel.send(f"💰 قفل SHORT {sym} RSI {rsi} <=15 ربح {pnl:+.2f}$")
            d["open_shorts"]=[]; d["sell_spent"]=0; d["sell_levels_hit"]=[]

        if d["open_longs"] or d["open_shorts"]:
            if d["open_longs"] and d["open_shorts"]: continue

        if not d["open_shorts"]:
            for level,pct in [(30,10),(20,10),(15,10),(10,20),(5,50)]:
                if rsi <= level and level not in d["buy_levels_hit"]:
                    amount = BUY_BUDGET*pct/100
                    if d["buy_spent"]+amount <= BUY_BUDGET+1:
                        d["open_longs"].append({"price":price,"amount":amount}); d["buy_spent"]+=amount; d["buy_levels_hit"].append(level)
                        await channel.send(f"📥 شراء {sym} RSI {rsi} لامس {level} | {amount}$ | فريم {TIMEFRAME}")
                        break

        if not d["open_longs"]:
            for level,pct in [(75,10),(80,10),(85,10),(90,20),(95,50)]:
                if rsi >= level and level not in d["sell_levels_hit"]:
                    amount = SELL_BUDGET*pct/100
                    if d["sell_spent"]+amount <= SELL_BUDGET+1:
                        d["open_shorts"].append({"price":price,"amount":amount}); d["sell_spent"]+=amount; d["sell_levels_hit"].append(level)
                        await channel.send(f"📤 بيع {sym} RSI {rsi} لامس {level} | {amount}$ | فريم {TIMEFRAME}")
                        break

@bot.event
async def on_ready():
    print(f"RSI Volatile شغال {bot.user}")
    vc = get_most_volatile(10)
    if vc:
        global COINS
        COINS=vc
        for c in COINS: init_coin(c)
        print(f"المتقلبة: {COINS}")
    if not rsi_loop.is_running(): rsi_loop.start()
    if not update_volatile.is_running(): update_volatile.start()

@bot.command(name="الرصيد")
async def bal(ctx):
    embed = discord.Embed(title=f"📊 RSI + الأكثر تقلباً | فريم {TIMEFRAME}", color=0x00ff00)
    total=0
    embed.add_field(name="🎯 العملات الحالية", value=f"`{', '.join(COINS)}`", inline=False)
    for sym in COINS:
        d=data[sym]; price=get_price(sym) or d["last_price"]
        floating=0
        for t in d["open_longs"]: floating+=(price-t["price"])/t["price"]*t["amount"]
        for t in d["open_shorts"]: floating+=(t["price"]-price)/t["price"]*t["amount"]
        total+=d["closed_pnl"]+floating
        if d["rsi"]!=0:
            embed.add_field(name=f"🔹 {sym} RSI {d['rsi']} ✅{d['wins']}❌{d['losses']}", value=f"محقق {d['closed_pnl']:+.2f}$ عائم {floating:+.2f}$", inline=True)
    embed.add_field(name="💰 صافي الكل", value=f"{total:+.2f}$", inline=False)
    embed.set_footer(text=f"قفل شراء 95 / بيع 15 | يتحدث كل ساعة")
    await ctx.channel.send(embed=embed)

@bot.event
async def on_message(m):
    if m.author==bot.user: return
    if "الرصيد" in m.content: await bal(m); return
    if "المتقلبة" in m.content:
        vc = get_most_volatile(10)
        if vc: await m.channel.send(f"🔥 الأكثر تقلباً الآن:\n`{', '.join(vc)}`")
        else: await m.channel.send(f"الحالية:\n`{', '.join(COINS)}`")
        return
    if "rsi" in m.content.lower():
        txt=""
        for sym in COINS[:5]:
            txt+=f"{sym}: RSI {get_rsi(sym, TIMEFRAME)}\n"
        await m.channel.send(f"📈 RSI فريم {TIMEFRAME}:\n{txt}")
        return
    await bot.process_commands(m)

bot.run(os.getenv("DISCORD_TOKEN"))

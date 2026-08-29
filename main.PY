import discord, os, requests
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime

app = Flask('')
@app.route('/')
def home(): return "RSI Volatile Fixed"
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

# === الدوال المصلحة - تستخدم binance.vision ===
def get_price(s):
    try:
        url = f"https://data-api.binance.vision/api/v3/ticker/price?symbol={s}"
        return float(requests.get(url, timeout=5).json()['price'])
    except:
        return None

def get_rsi(symbol, interval="5m"):
    try:
        url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
        r = requests.get(url, timeout=10)
        klines = r.json()
        if not isinstance(klines, list) or len(klines) < 20:
            print(f"klines error {symbol}: {klines}")
            return None
        closes = [float(k[4]) for k in klines]
        deltas = [closes[i]-closes[i-1] for i in range(1,len(closes))]
        gains = [d if d>0 else 0 for d in deltas]
        losses = [-d if d<0 else 0 for d in deltas]
        avg_gain = sum(gains[:14])/14
        avg_loss = sum(losses[:14])/14
        for i in range(14, len(gains)):
            avg_gain = (avg_gain*13 + gains[i])/14
            avg_loss = (avg_loss*13 + losses[i])/14
        if avg_loss == 0:
            return 100.0
        rs = avg_gain/avg_loss
        rsi = 100 - (100/(1+rs))
        return round(rsi,2)
    except Exception as e:
        print(f"RSI exception {symbol}: {e}")
        return None

def get_most_volatile(limit=10):
    try:
        url = "https://data-api.binance.vision/api/v3/ticker/24hr"
        r = requests.get(url, timeout=12).json()
        filt = [x for x in r if x['symbol'].endswith('USDT') and float(x['quoteVolume'])>5000000 and 'USDC' not in x['symbol'] and 'FDUSD' not in x['symbol']]
        sorted_coins = sorted(filt, key=lambda x: abs(float(x['priceChangePercent'])), reverse=True)
        return [x['symbol'] for x in sorted_coins[:limit]]
    except Exception as e:
        print(f"volatile error {e}")
        return None

# === البوت ===
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
        ch = discord.utils.get(bot.get_all_channels(), name="العام") or discord.utils.get(bot.get_all_channels(), name="general") or next((c for c in bot.get_all_channels() if isinstance(c, discord.TextChannel)), None)
        if ch:
            await ch.send(f"🔥 **تحديث تلقائي - الأكثر تقلباً الآن:**\n`{', '.join(COINS)}`")

@tasks.loop(seconds=60)
async def rsi_loop():
    ch = discord.utils.get(bot.get_all_channels(), name="العام") or discord.utils.get(bot.get_all_channels(), name="general") or next((c for c in bot.get_all_channels() if isinstance(c, discord.TextChannel)), None)
    if not ch: return

    for sym in COINS:
        price = get_price(sym)
        rsi = get_rsi(sym, TIMEFRAME)
        if price is None or rsi is None:
            print(f"skip {sym} price={price} rsi={rsi}")
            continue

        d = data[sym]
        d["rsi"] = rsi
        d["last_price"] = price
        print(f"{sym} RSI {rsi} @ {price}")

        # 1- إقفال شراء عند 95
        if d["open_longs"] and rsi >= 95:
            amt = sum(t["amount"] for t in d["open_longs"])
            avg = sum(t["price"]*t["amount"] for t in d["open_longs"])/amt if amt>0 else price
            pnl = (price-avg)/avg*amt
            d["closed_pnl"] += pnl
            if pnl >= 0: d["wins"]+=1
            else: d["losses"]+=1
            await ch.send(f"💰 **قفل LONG {sym}** RSI {rsi} لامس 95\nدخول {avg:.6f} خروج {price:.6f}\nربح {pnl:+.2f}$ | إجمالي {d['closed_pnl']:+.2f}$")
            d["open_longs"]=[]; d["buy_spent"]=0; d["buy_levels_hit"]=[]

        # 2- إقفال بيع عند 15
        if d["open_shorts"] and rsi <= 15:
            amt = sum(t["amount"] for t in d["open_shorts"])
            avg = sum(t["price"]*t["amount"] for t in d["open_shorts"])/amt if amt>0 else price
            pnl = (avg-price)/avg*amt
            d["closed_pnl"] += pnl
            if pnl >= 0: d["wins"]+=1
            else: d["losses"]+=1
            await ch.send(f"💰 **قفل SHORT {sym}** RSI {rsi} لامس 15\nدخول {avg:.6f} خروج {price:.6f}\nربح {pnl:+.2f}$ | إجمالي {d['closed_pnl']:+.2f}$")
            d["open_shorts"]=[]; d["sell_spent"]=0; d["sell_levels_hit"]=[]

        # 3- شراء (لا يفتح إذا فيه SHORT مفتوح)
        if not d["open_shorts"]:
            for level,pct in [(30,10),(20,10),(15,10),(10,20),(5,50)]:
                if rsi <= level and level not in d["buy_levels_hit"]:
                    amount = BUY_BUDGET * pct / 100
                    if d["buy_spent"] + amount <= BUY_BUDGET + 5:
                        d["open_longs"].append({"price":price,"amount":amount,"level":level})
                        d["buy_spent"]+=amount
                        d["buy_levels_hit"].append(level)
                        await ch.send(f"📥 **شراء {sym} RSI {rsi} لامس {level}**\nسعر {price} مبلغ {amount}$ فريم {TIMEFRAME} | مصروف {d['buy_spent']}/100$")
                        break

        # 4- بيع (لا يفتح إذا فيه LONG مفتوح)
        if not d["open_longs"]:
            for level,pct in [(75,10),(80,10),(85,10),(90,20),(95,50)]:
                if rsi >= level and level not in d["sell_levels_hit"]:
                    amount = SELL_BUDGET * pct / 100
                    if d["sell_spent"] + amount <= SELL_BUDGET + 5:
                        d["open_shorts"].append({"price":price,"amount":amount,"level":level})
                        d["sell_spent"]+=amount
                        d["sell_levels_hit"].append(level)
                        await ch.send(f"📤 **بيع {sym} RSI {rsi} لامس {level}**\nسعر {price} مبلغ {amount}$ فريم {TIMEFRAME} | مصروف {d['sell_spent']}/100$")
                        break

@bot.event
async def on_ready():
    print(f"Bot Ready {bot.user} فريم {TIMEFRAME}")
    vc = get_most_volatile(10)
    if vc:
        global COINS
        COINS = vc
        for c in COINS: init_coin(c)
        print(f"المتقلبة: {COINS}")
    if not rsi_loop.is_running(): rsi_loop.start()
    if not update_volatile.is_running(): update_volatile.start()

@bot.event
async def on_message(m):
    if m.author==bot.user: return
    txt = m.content.strip()
    if "الرصيد" in txt:
        embed = discord.Embed(title=f"📊 RSI Scalping فريم {TIMEFRAME}", color=0x00ff00)
        embed.add_field(name="🎯 العملات الحالية", value=f"`{', '.join(COINS)}`", inline=False)
        total=0
        for sym in COINS:
            d=data.get(sym)
            if not d: continue
            pr=get_price(sym) or d["last_price"]
            floating=0
            for t in d["open_longs"]: floating+=(pr-t["price"])/t["price"]*t["amount"]
            for t in d["open_shorts"]: floating+=(t["price"]-pr)/t["price"]*t["amount"]
            total+=d["closed_pnl"]+floating
            if d["rsi"]!=0:
                embed.add_field(name=f"🔹 {sym} RSI {d['rsi']} ✅{d['wins']}❌{d['losses']}", value=f"محقق {d['closed_pnl']:+.2f}$ عائم {floating:+.2f}$", inline=True)
        embed.add_field(name="💰 صافي الكل", value=f"{total:+.2f}$", inline=False)
        embed.set_footer(text=f"قفل شراء 95 / بيع 15 | {datetime.now().strftime('%H:%M')}")
        await m.channel.send(embed=embed)
        return
    if "المتقلبة" in txt:
        vc=get_most_volatile(10)
        await m.channel.send(f"🔥 **الأكثر تقلباً الآن:**\n`{', '.join(vc or COINS)}`")
        return
    if "rsi" in txt.lower():
        out=""
        for sym in COINS[:10]:
            r=get_rsi(sym, TIMEFRAME)
            out+=f"{sym}: RSI {r}\n"
        await m.channel.send(f"📈 **RSI فريم {TIMEFRAME}:**\n```\n{out}\n```")
        return
    await bot.process_commands(m)

bot.run(os.getenv("DISCORD_TOKEN"))

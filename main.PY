import discord, os, requests
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime

app = Flask('')
@app.route('/')
def home(): return "RSI 2-Level Strategy"
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run, daemon=True).start()

TIMEFRAME = "5m"
COINS = ["DEXEUSDT","BICOUSDT","MOVRUSDT","TUTUSDT","BMTUSDT","FETUSDT","HEMIUSDT","ZROUSDT","MSTRUSDT","HEIUSDT"]
data = {}

def init_coin(c):
    if c not in data:
        data[c] = {"rsi":0,"open_longs":[],"open_shorts":[],"buy_levels_hit":[],"sell_levels_hit":[],"closed_pnl":0,"wins":0,"losses":0,"last_price":0,"floating":0}
for c in COINS: init_coin(c)

def get_price(s):
    try:
        url = f"https://data-api.binance.vision/api/v3/ticker/price?symbol={s}"
        return float(requests.get(url, timeout=5).json()['price'])
    except: return None

def get_rsi(symbol, interval="5m"):
    try:
        url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
        klines = requests.get(url, timeout=10).json()
        if not isinstance(klines, list) or len(klines) < 20: return None
        closes = [float(k[4]) for k in klines]
        deltas = [closes[i]-closes[i-1] for i in range(1,len(closes))]
        gains = [d if d>0 else 0 for d in deltas]
        losses = [-d if d<0 else 0 for d in deltas]
        avg_gain = sum(gains[:14])/14
        avg_loss = sum(losses[:14])/14
        for i in range(14, len(gains)):
            avg_gain = (avg_gain*13 + gains[i])/14
            avg_loss = (avg_loss*13 + losses[i])/14
        if avg_loss == 0: return 100.0
        rs = avg_gain/avg_loss
        return round(100 - (100/(1+rs)),2)
    except: return None

def get_most_volatile(limit=10):
    try:
        r = requests.get("https://data-api.binance.vision/api/v3/ticker/24hr", timeout=12).json()
        filt = [x for x in r if x['symbol'].endswith('USDT') and float(x['quoteVolume'])>5000000 and 'USDC' not in x['symbol'] and 'FDUSD' not in x['symbol']]
        s = sorted(filt, key=lambda x: abs(float(x['priceChangePercent'])), reverse=True)
        return [x['symbol'] for x in s[:limit]]
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
        ch = discord.utils.get(bot.get_all_channels(), name="العام") or next((c for c in bot.get_all_channels() if isinstance(c, discord.TextChannel)), None)
        if ch: await ch.send(f"🔥 **تحديث المتقلبة:**\n`{', '.join(COINS)}`")

@tasks.loop(seconds=60)
async def rsi_loop():
    ch = discord.utils.get(bot.get_all_channels(), name="العام") or next((c for c in bot.get_all_channels() if isinstance(c, discord.TextChannel)), None)
    if not ch: return
    for sym in COINS:
        price = get_price(sym)
        rsi = get_rsi(sym, TIMEFRAME)
        if price is None or rsi is None: continue
        d = data[sym]; d["rsi"]=rsi; d["last_price"]=price
        print(f"{sym} RSI {rsi}")

        # === قفل الشراء عند 80 ===
        if d["open_longs"] and rsi >= 80:
            amt = sum(t["amount"] for t in d["open_longs"])
            avg = sum(t["price"]*t["amount"] for t in d["open_longs"])/amt
            pnl = (price-avg)/avg*amt
            d["closed_pnl"]+=pnl
            if pnl>=0: d["wins"]+=1
            else: d["losses"]+=1
            await ch.send(f"💰 **قفل LONG {sym} RSI {rsi} >=80**\nمتوسط {avg:.6f} خروج {price:.6f}\nربح {pnl:+.2f}$ | إجمالي {d['closed_pnl']:+.2f}$")
            d["open_longs"]=[]; d["buy_levels_hit"]=[]

        # === قفل البيع عند 30 ===
        if d["open_shorts"] and rsi <= 30:
            amt = sum(t["amount"] for t in d["open_shorts"])
            avg = sum(t["price"]*t["amount"] for t in d["open_shorts"])/amt
            pnl = (avg-price)/avg*amt
            d["closed_pnl"]+=pnl
            if pnl>=0: d["wins"]+=1
            else: d["losses"]+=1
            await ch.send(f"💰 **قفل SHORT {sym} RSI {rsi} <=30**\nمتوسط {avg:.6f} خروج {price:.6f}\nربح {pnl:+.2f}$ | إجمالي {d['closed_pnl']:+.2f}$")
            d["open_shorts"]=[]; d["sell_levels_hit"]=[]

        # === شراء مرحلتين ===
        if not d["open_shorts"]:
            # مرحلة 1: 30
            if rsi <= 30 and 30 not in d["buy_levels_hit"]:
                d["open_longs"].append({"price":price,"amount":50,"level":30})
                d["buy_levels_hit"].append(30)
                await ch.send(f"📥 **شراء 1 {sym} RSI {rsi} لامس 30**\nسعر {price} مبلغ 50$ | الهدف 80")
            # مرحلة 2: 5
            elif rsi <= 5 and 5 not in d["buy_levels_hit"]:
                d["open_longs"].append({"price":price,"amount":50,"level":5})
                d["buy_levels_hit"].append(5)
                await ch.send(f"📥📥 **شراء 2 {sym} RSI {rsi} لامس 5 تعزيز**\nسعر {price} مبلغ 50$ | الهدف 80")

        # === بيع مرحلتين ===
        if not d["open_longs"]:
            # مرحلة 1: 70
            if rsi >= 70 and 70 not in d["sell_levels_hit"]:
                d["open_shorts"].append({"price":price,"amount":50,"level":70})
                d["sell_levels_hit"].append(70)
                await ch.send(f"📤 **بيع 1 {sym} RSI {rsi} لامس 70**\nسعر {price} مبلغ 50$ | الهدف 30")
            # مرحلة 2: 90
            elif rsi >= 90 and 90 not in d["sell_levels_hit"]:
                d["open_shorts"].append({"price":price,"amount":50,"level":90})
                d["sell_levels_hit"].append(90)
                await ch.send(f"📤📤 **بيع 2 {sym} RSI {rsi} لامس 90 تعزيز**\nسعر {price} مبلغ 50$ | الهدف 30")

@bot.event
async def on_ready():
    print(f"Ready {bot.user}")
    vc = get_most_volatile(10)
    if vc:
        global COINS; COINS=vc
        for c in COINS: init_coin(c)
    if not rsi_loop.is_running(): rsi_loop.start()
    if not update_volatile.is_running(): update_volatile.start()

@bot.event
async def on_message(m):
    if m.author==bot.user: return
    txt=m.content.strip()
    if "الرصيد" in txt:
        embed=discord.Embed(title=f"📊 استراتيجية مرحلتين فريم {TIMEFRAME}", description="شراء 30+5=قفل80 | بيع 70+90=قفل30", color=0x00ff00)
        embed.add_field(name="🎯 العملات", value=f"`{', '.join(COINS)}`", inline=False)
        total=0
        for sym in COINS:
            d=data.get(sym)
            if not d: continue
            pr=get_price(sym) or d["last_price"]
            fl=0
            for t in d["open_longs"]: fl+=(pr-t["price"])/t["price"]*t["amount"]
            for t in d["open_shorts"]: fl+=(t["price"]-pr)/t["price"]*t["amount"]
            d["floating"]=fl
            total+=d["closed_pnl"]+fl
            status = f"محقق {d['closed_pnl']:+.2f}$ عائم {fl:+.2f}$ ✅{d['wins']}❌{d['losses']}"
            if d["open_longs"]: status+=f" | LONG {len(d['open_longs'])}"
            if d["open_shorts"]: status+=f" | SHORT {len(d['open_shorts'])}"
            embed.add_field(name=f"{sym} RSI {d['rsi']}", value=status, inline=True)
        embed.add_field(name="💰 صافي الكل", value=f"{total:+.2f}$", inline=False)
        embed.set_footer(text=f"قفل LONG 80 | قفل SHORT 30 | {datetime.now().strftime('%H:%M')}")
        await m.channel.send(embed=embed)
        return
    if "المتقلبة" in txt:
        vc=get_most_volatile(10)
        await m.channel.send(f"🔥 `{','.join(vc or COINS)}`")
        return
    if "rsi" in txt.lower():
        out="\n".join([f"{s}: {get_rsi(s, TIMEFRAME)}" for s in COINS[:10]])
        await m.channel.send(f"```\n{out}\n```")
        return
    await bot.process_commands(m)

bot.run(os.getenv("DISCORD_TOKEN"))

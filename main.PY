import discord, os, requests
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime

app = Flask('')
@app.route('/')
def home(): return "MACD EMA Strategy"
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run, daemon=True).start()

TIMEFRAME = "15m"
COINS = ["PROMUSDT","ZKUSDT","DEXEUSDT","TUTUSDT","PUMPUSDT","UNIUSDT","NILUSDT","CHIPUSDT","GIGGLEUSDT","DASHUSDT"]
data = {}

def init_coin(c):
    if c not in data:
        data[c] = {"rsi":0,"ema7":0,"ema21":0,"macd":0,"open_longs":[],"open_shorts":[],"closed_pnl":0,"wins":0,"losses":0,"last_price":0}

for c in COINS: init_coin(c)

def get_price(s):
    try: return float(requests.get(f"https://data-api.binance.vision/api/v3/ticker/price?symbol={s}", timeout=5).json()['price'])
    except: return None

def calc_ema(prices, period):
    k = 2/(period+1)
    ema = sum(prices[:period])/period
    for p in prices[period:]:
        ema = p*k + ema*(1-k)
    return ema

def get_indicators(symbol, interval="15m"):
    try:
        klines = requests.get(f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit=100", timeout=10).json()
        if not isinstance(klines, list) or len(klines) < 50: return None
        closes = [float(k[4]) for k in klines]

        # EMA 7 / 21
        ema7 = calc_ema(closes, 7)
        ema21 = calc_ema(closes, 21)
        prev_ema7 = calc_ema(closes[:-1], 7)
        prev_ema21 = calc_ema(closes[:-1], 21)

        # MACD 12,26,9
        ema12 = calc_ema(closes, 12)
        ema26 = calc_ema(closes, 26)
        macd_line = ema12 - ema26

        # حساب MACD للشمعة السابقة للتأكد من التقاطع
        ema12_prev = calc_ema(closes[:-1], 12)
        ema26_prev = calc_ema(closes[:-1], 26)
        macd_prev = ema12_prev - ema26_prev

        # Signal line (EMA9 للـ MACD)
        # نحسبها تقريبي من آخر 20 قيمة MACD
        macds = []
        for i in range(20):
            slice_c = closes[:len(closes)-i] if i>0 else closes
            if len(slice_c) < 26: break
            macds.append(calc_ema(slice_c,12)-calc_ema(slice_c,26))
        macds.reverse()
        signal = calc_ema(macds, 9) if len(macds)>=9 else 0

        return {
            "ema7": round(ema7,6), "ema21": round(ema21,6),
            "prev_ema7": round(prev_ema7,6), "prev_ema21": round(prev_ema21,6),
            "macd": round(macd_line,6), "macd_prev": round(macd_prev,6),
            "signal": round(signal,6),
            "price": closes[-1]
        }
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
async def strategy_loop():
    ch = discord.utils.get(bot.get_all_channels(), name="العام") or next((c for c in bot.get_all_channels() if isinstance(c, discord.TextChannel)), None)
    if not ch: return
    all_to_check = list(set(COINS + [c for c in data if data[c]["open_longs"] or data[c]["open_shorts"]]))

    for sym in all_to_check:
        ind = get_indicators(sym, TIMEFRAME)
        price = get_price(sym) or (ind["price"] if ind else None)
        if not ind or price is None: continue
        d = data[sym]
        d["ema7"]=ind["ema7"]; d["ema21"]=ind["ema21"]; d["macd"]=ind["macd"]; d["last_price"]=price

        # === حساب الربح العائم ===
        floating_long = sum((price-t["price"])/t["price"]*t["amount"] for t in d["open_longs"]) if d["open_longs"] else 0
        floating_short = sum((t["price"]-price)/t["price"]*t["amount"] for t in d["open_shorts"]) if d["open_shorts"] else 0
        total_floating = floating_long + floating_short

        # === 1- قفل على ربح 10$ ===
        if total_floating >= 10:
            pnl = total_floating
            d["closed_pnl"]+=pnl; d["wins"]+=1
            side = "LONG" if d["open_longs"] else "SHORT"
            await ch.send(f"💰 **قفل {side} {sym} ربح 10$**\nسعر {price:.6f} ربح {pnl:+.2f}$ | إجمالي {d['closed_pnl']:+.2f}$\nMACD {ind['macd']} EMA7 {ind['ema7']} EMA21 {ind['ema21']}")
            d["open_longs"]=[]; d["open_shorts"]=[]
            continue

        # === 2- قفل عند انعكاس المؤشرين ===
        # كان LONG وصار MACD تحت الصفر + EMA7 تحت 21 = خروج
        if d["open_longs"]:
            if ind["macd"] < 0 and ind["ema7"] < ind["ema21"]:
                amt = sum(t["amount"] for t in d["open_longs"])
                avg = sum(t["price"]*t["amount"] for t in d["open_longs"])/amt if amt else price
                pnl = (price-avg)/avg*amt if amt else 0
                d["closed_pnl"]+=pnl
                if pnl>=0: d["wins"]+=1
                else: d["losses"]+=1
                await ch.send(f"💰 **قفل LONG {sym} انعكاس**\nMACD {ind['macd']}<0 و EMA7 {ind['ema7']} < EMA21 {ind['ema21']}\nربح {pnl:+.2f}$")
                d["open_longs"]=[]

        if d["open_shorts"]:
            if ind["macd"] > 0 and ind["ema7"] > ind["ema21"]:
                amt = sum(t["amount"] for t in d["open_shorts"])
                avg = sum(t["price"]*t["amount"] for t in d["open_shorts"])/amt if amt else price
                pnl = (avg-price)/avg*amt if amt else 0
                d["closed_pnl"]+=pnl
                if pnl>=0: d["wins"]+=1
                else: d["losses"]+=1
                await ch.send(f"💰 **قفل SHORT {sym} انعكاس**\nMACD {ind['macd']}>0 و EMA7 {ind['ema7']} > EMA21 {ind['ema21']}\nربح {pnl:+.2f}$")
                d["open_shorts"]=[]

        # === 3- دخول جديد ===
        # تقاطع صاعد
        cross_up = ind["prev_ema7"] <= ind["prev_ema21"] and ind["ema7"] > ind["ema21"]
        cross_down = ind["prev_ema7"] >= ind["prev_ema21"] and ind["ema7"] < ind["ema21"]

        # شراء: MACD فوق الصفر + تقاطع صاعد (أو EMA7 فوق 21)
        if not d["open_longs"] and not d["open_shorts"]:
            if ind["macd"] > 0 and (cross_up or ind["ema7"] > ind["ema21"]):
                if cross_up: # دخول قوي عند التقاطع
                    d["open_longs"].append({"price":price,"amount":50})
                    await ch.send(f"📥 **شراء {sym}**\nMACD {ind['macd']}>0 ✅ + تقاطع EMA7 {ind['ema7']} فوق EMA21 {ind['ema21']} ✅\nسعر {price:.6f} مبلغ 50$ | هدف 10$ أو انعكاس")

        # بيع: MACD تحت الصفر + تقاطع هابط
        if not d["open_longs"] and not d["open_shorts"]:
            if ind["macd"] < 0 and (cross_down or ind["ema7"] < ind["ema21"]):
                if cross_down:
                    d["open_shorts"].append({"price":price,"amount":50})
                    await ch.send(f"📤 **بيع {sym}**\nMACD {ind['macd']}<0 ✅ + تقاطع EMA7 {ind['ema7']} تحت EMA21 {ind['ema21']} ✅\nسعر {price:.6f} مبلغ 50$ | هدف 10$ أو انعكاس")

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
        embed=discord.Embed(title=f"📊 MACD + EMA7/21 | {TIMEFRAME} | هدف 10$", color=0x00ff00)
        embed.add_field(name="🎯 المتقلبة", value=f"`{', '.join(COINS)}`", inline=False)
        total=0
        show = list(set(COINS + [c for c in data if c in data and (data[c]["open_longs"] or data[c]["open_shorts"] or data[c]["closed_pnl"]!=0)]))
        for sym in show:
            d=data.get(sym)
            if not d: continue
            pr=get_price(sym) or d["last_price"] or 0
            fl=0
            for t in d["open_longs"]: fl+=(pr-t["price"])/t["price"]*t["amount"] if pr else 0
            for t in d["open_shorts"]: fl+=(t["price"]-pr)/t["price"]*t["amount"] if pr else 0
            total+=d["closed_pnl"]+fl
            side = "LONG" if d["open_longs"] else "SHORT" if d["open_shorts"] else "-"
            embed.add_field(name=f"{sym} {side} MACD {d['macd']}", value=f"محقق {d['closed_pnl']:+.2f}$ عائم {fl:+.2f}$ ✅{d['wins']}❌{d['losses']}\nEMA7 {d['ema7']} EMA21 {d['ema21']}", inline=True)
        embed.add_field(name="💰 صافي الكل", value=f"{total:+.2f}$", inline=False)
        embed.set_footer(text=f"قفل ربح 10$ أو انعكاس MACD+EMA | {datetime.now().strftime('%H:%M')}")
        await m.channel.send(embed=embed)
        return
    if "تصفير" in txt:
        for c in list(data.keys()):
            data[c]={"ema7":0,"ema21":0,"macd":0,"rsi":0,"open_longs":[],"open_shorts":[],"closed_pnl":0,"wins":0,"losses":0,"last_price":0}
        await m.channel.send("✅ تم التصفير - بداية استراتيجية MACD+EMA")
        return
    if "المتقلبة" in txt:
        vc=get_most_volatile(10)
        await m.channel.send(f"🔥 `{', '.join(vc or COINS)}`")
        return
    await bot.process_commands(m)

bot.run(os.getenv("DISCORD_TOKEN"))

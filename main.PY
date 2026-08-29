import discord, os, requests
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime

app = Flask('')
@app.route('/')
def home(): return "RSI Bot 5m"
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run, daemon=True).start()

TIMEFRAME = "5m" # تقدر تغيره لـ 1m / 15m / 1h بعدين
COINS = ["PEPEUSDT","FLOKIUSDT","WIFUSDT","BONKUSDT","DOGEUSDT","SHIBUSDT","SOLUSDT","BTCUSDT","ETHUSDT","1000PEPEUSDT"]

BUY_BUDGET = 100
SELL_BUDGET = 100

data = {}
for c in COINS:
    data[c] = {"rsi":0,"open_longs":[],"open_shorts":[],"buy_spent":0,"sell_spent":0,"buy_levels_hit":[],"sell_levels_hit":[],"closed_pnl":0,"wins":0,"losses":0,"last_price":0}

def get_price(s):
    try: return float(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={s}", timeout=4).json()['price'])
    except: return None

def get_rsi(symbol, interval="5m", period=14):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
        klines = requests.get(url, timeout=6).json()
        closes = [float(k[4]) for k in klines]
        if len(closes) < period+1: return None
        gains, losses = [], []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i-1]
            if diff >= 0: gains.append(diff); losses.append(0)
            else: gains.append(0); losses.append(-diff)
        avg_gain = sum(gains[:period])/period
        avg_loss = sum(losses[:period])/period
        for i in range(period, len(gains)):
            avg_gain = (avg_gain*(period-1)+gains[i])/period
            avg_loss = (avg_loss*(period-1)+losses[i])/period
        if avg_loss == 0: return 100
        rs = avg_gain/avg_loss
        rsi = 100 - (100/(1+rs))
        return round(rsi,2)
    except Exception as e:
        print(f"RSI error {symbol}: {e}")
        return None

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@tasks.loop(seconds=60)
async def rsi_loop():
    channel = discord.utils.get(bot.get_all_channels(), name="العام") or next((c for c in bot.get_all_channels() if isinstance(c, discord.TextChannel)), None)
    if not channel: return

    for sym in COINS:
        price = get_price(sym)
        rsi = get_rsi(sym, TIMEFRAME)
        if not price or rsi is None: continue
        d = data[sym]
        d["rsi"] = rsi
        d["last_price"] = price

        # === 1. جني الأرباح / إقفال ===
        if d["open_longs"] and rsi >= 95:
            total_amt = sum(t["amount"] for t in d["open_longs"])
            avg_entry = sum(t["price"]*t["amount"] for t in d["open_longs"])/total_amt if total_amt>0 else price
            pnl = (price - avg_entry)/avg_entry * total_amt
            d["closed_pnl"] += pnl
            if pnl>=0: d["wins"]+=1
            else: d["losses"]+=1
            await channel.send(f"💰 **قفل LONG {sym}** RSI {rsi} وصل 95\nدخول {avg_entry:.6f} خروج {price:.6f}\nربح {pnl:+.2f}$ | إجمالي {d['closed_pnl']:+.2f}$")
            d["open_longs"]=[]; d["buy_spent"]=0; d["buy_levels_hit"]=[]

        if d["open_shorts"] and rsi <= 15:
            total_amt = sum(t["amount"] for t in d["open_shorts"])
            avg_entry = sum(t["price"]*t["amount"] for t in d["open_shorts"])/total_amt if total_amt>0 else price
            pnl = (avg_entry - price)/avg_entry * total_amt
            d["closed_pnl"] += pnl
            if pnl>=0: d["wins"]+=1
            else: d["losses"]+=1
            await channel.send(f"💰 **قفل SHORT {sym}** RSI {rsi} وصل 15\nدخول {avg_entry:.6f} خروج {price:.6f}\nربح {pnl:+.2f}$ | إجمالي {d['closed_pnl']:+.2f}$")
            d["open_shorts"]=[]; d["sell_spent"]=0; d["sell_levels_hit"]=[]

        # شرط عدم فتح صفقة إضافية إذا فيه صفقة قائمة (شراء يمنع بيع والعكس)
        if d["open_longs"] and d["open_shorts"]:
            continue

        # === 2. الشراء ===
        if not d["open_shorts"]: # لا يشتري إذا فيه بيع مفتوح
            buy_map = [(30,10),(20,10),(15,10),(10,20),(5,50)] # (RSI level, % من الميزانية)
            for level, pct in buy_map:
                if rsi <= level and level not in d["buy_levels_hit"]:
                    amount = BUY_BUDGET * pct / 100
                    if d["buy_spent"] + amount <= BUY_BUDGET + 1:
                        d["open_longs"].append({"price":price,"amount":amount,"rsi":rsi,"level":level})
                        d["buy_spent"]+=amount
                        d["buy_levels_hit"].append(level)
                        await channel.send(f"📥 **شراء {sym} RSI {rsi}** لامس {level}\nسعر {price} | مبلغ {amount}$ | فريم {TIMEFRAME}\nالمصروف {d['buy_spent']}/100$")
                        break # دخول واحد كل دقيقة

        # === 3. البيع ===
        if not d["open_longs"]:
            sell_map = [(75,10),(80,10),(85,10),(90,20),(95,50)]
            for level, pct in sell_map:
                if rsi >= level and level not in d["sell_levels_hit"]:
                    amount = SELL_BUDGET * pct / 100
                    if d["sell_spent"] + amount <= SELL_BUDGET + 1:
                        d["open_shorts"].append({"price":price,"amount":amount,"rsi":rsi,"level":level})
                        d["sell_spent"]+=amount
                        d["sell_levels_hit"].append(level)
                        await channel.send(f"📤 **بيع {sym} RSI {rsi}** لامس {level}\nسعر {price} | مبلغ {amount}$ | فريم {TIMEFRAME}\nالمصروف {d['sell_spent']}/100$")
                        break

@bot.event
async def on_ready():
    print(f"RSI Bot شغال {bot.user} فريم {TIMEFRAME}")
    if not rsi_loop.is_running(): rsi_loop.start()

@bot.command(name="الرصيد")
async def bal(ctx):
    embed = discord.Embed(title=f"📊 RSI Scalping فريم {TIMEFRAME}", color=0x00ff00)
    total=0
    for sym in COINS:
        d=data[sym]
        price = get_price(sym) or d["last_price"]
        floating=0
        for t in d["open_longs"]: floating+=(price-t["price"])/t["price"]*t["amount"]
        for t in d["open_shorts"]: floating+=(t["price"]-price)/t["price"]*t["amount"]
        total+=d["closed_pnl"]+floating
        if d["rsi"]!=0:
            status = f"RSI {d['rsi']}"
            if d["open_longs"]: status+=f" | LONG {len(d['open_longs'])}"
            if d["open_shorts"]: status+=f" | SHORT {len(d['open_shorts'])}"
            embed.add_field(name=f"🔹 {sym} | {status}", value=f"سعر {price}\nمحقق {d['closed_pnl']:+.2f}$ عائم {floating:+.2f}$ ✅{d['wins']}❌{d['losses']}", inline=True)
    embed.add_field(name="💰 صافي الكل", value=f"{total:+.2f}$", inline=False)
    embed.set_footer(text=f"فريم {TIMEFRAME} | قفل شراء 95 / بيع 15 | {datetime.now().strftime('%H:%M')}")
    await ctx.channel.send(embed=embed)

@bot.event
async def on_message(m):
    if m.author==bot.user: return
    if "الرصيد" in m.content: await bal(m); return
    if "rsi" in m.content.lower():
        txt = ""
        for sym in COINS[:5]:
            r = get_rsi(sym, TIMEFRAME)
            txt+=f"{sym}: RSI {r}\n"
        await m.channel.send(f"📈 RSI فريم {TIMEFRAME}:\n{txt}")
        return
    await bot.process_commands(m)

bot.run(os.getenv("DISCORD_TOKEN"))

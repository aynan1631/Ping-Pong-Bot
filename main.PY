import os, discord, requests, threading
from discord.ext import tasks
from flask import Flask

TOKEN = os.environ.get("DISCORD_TOKEN")

app = Flask('')
@app.route('/')
def home(): return "RSI Gradual Bot Live"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

USDT_BALANCE = 100.0
BTC_BALANCE = 0.0
avg_entry = 0.0
total_profit = 0.0
total_loss = 0.0
trades = []

bought_30 = False
bought_20 = False
bought_10 = False
sold_70 = False
sold_85 = False
sold_95 = False
position_side = None

def calc_rsi(prices, period=14):
    gains = []
    losses = []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        if diff >= 0: gains.append(diff); losses.append(0)
        else: gains.append(0); losses.append(abs(diff))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1+rs))

@tasks.loop(minutes=1)
async def check_market():
    global USDT_BALANCE, BTC_BALANCE, avg_entry, total_profit, total_loss
    global bought_30, bought_20, bought_10, sold_70, sold_85, sold_95, position_side
    try:
        price_r = requests.get("https://data-api.binance.vision/api/v3/ticker/price?symbol=BTCUSDT", timeout=10)
        curr = float(price_r.json()['price'])
        r = requests.get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=50", timeout=15)
        closes = [float(c[4]) for c in r.json()]
        rsi = calc_rsi(closes, 14)

        channel = None
        for guild in client.guilds:
            for c in guild.text_channels:
                if c.permissions_for(guild.me).send_messages:
                    channel = c; break
            if channel: break

        if rsi <= 30 and rsi > 20 and not bought_30 and USDT_BALANCE > 1:
            amount_usdt = USDT_BALANCE * 0.15
            btc_qty = amount_usdt / curr
            total_cost = (avg_entry * BTC_BALANCE) + amount_usdt
            BTC_BALANCE += btc_qty
            avg_entry = total_cost / BTC_BALANCE if BTC_BALANCE>0 else curr
            USDT_BALANCE -= amount_usdt
            bought_30 = True
            position_side = "LONG"
            if channel: await channel.send(f"🟢 **شراء 1 (RSI {rsi:.1f})** @ {curr:.2f}\n15% = ${amount_usdt:.2f}")

        if rsi <= 20 and rsi > 10 and not bought_20 and USDT_BALANCE > 1:
            amount_usdt = USDT_BALANCE * 0.30
            btc_qty = amount_usdt / curr
            total_cost = (avg_entry * BTC_BALANCE) + amount_usdt
            BTC_BALANCE += btc_qty
            avg_entry = total_cost / BTC_BALANCE
            USDT_BALANCE -= amount_usdt
            bought_20 = True
            position_side = "LONG"
            if channel: await channel.send(f"🟢🟢 **شراء 2 (RSI {rsi:.1f})** @ {curr:.2f}\n30% = ${amount_usdt:.2f}")

        if rsi <= 10 and not bought_10 and USDT_BALANCE > 1:
            amount_usdt = USDT_BALANCE
            btc_qty = amount_usdt / curr
            total_cost = (avg_entry * BTC_BALANCE) + amount_usdt
            BTC_BALANCE += btc_qty
            avg_entry = total_cost / BTC_BALANCE
            USDT_BALANCE -= amount_usdt
            bought_10 = True
            position_side = "LONG"
            if channel: await channel.send(f"🟢🟢🟢 **شراء 3 أخير (RSI {rsi:.1f})** @ {curr:.2f}")

        if position_side == "LONG" and BTC_BALANCE > 0 and rsi >= 60:
            if curr > avg_entry:
                sell_value = BTC_BALANCE * curr
                profit = (curr - avg_entry) * BTC_BALANCE
                USDT_BALANCE += sell_value
                total_profit += profit
                if channel: await channel.send(f"✅ **بيع LONG @ {curr:.2f} RSI {rsi:.1f} ربح ${profit:.4f}**")
                BTC_BALANCE = 0; avg_entry = 0
                bought_30 = bought_20 = bought_10 = False
                sold_70 = sold_85 = sold_95 = False
                position_side = None

        if rsi >= 70 and rsi < 85 and not sold_70 and position_side!= "LONG":
            sold_70 = True; position_side = "SHORT"
            if channel: await channel.send(f"🔴 **شورت 1 RSI {rsi:.1f}** @ {curr:.2f}")

        if rsi >= 85 and rsi < 95 and not sold_85:
            sold_85 = True; position_side = "SHORT"
            if channel: await channel.send(f"🔴🔴 **شورت 2 RSI {rsi:.1f}** @ {curr:.2f}")

        if rsi >= 95 and not sold_95:
            sold_95 = True; position_side = "SHORT"
            if channel: await channel.send(f"🔴🔴🔴 **شورت 3 RSI {rsi:.1f}** @ {curr:.2f}")

        if position_side == "SHORT" and rsi <= 30:
            if channel: await channel.send(f"⚪ **قفل SHORT @ {curr:.2f} RSI {rsi:.1f}**")
            bought_30 = bought_20 = bought_10 = False
            sold_70 = sold_85 = sold_95 = False
            position_side = None

    except Exception as e:
        print(f"ERR {e}")

@client.event
async def on_ready():
    print(f"Ready {client.user}")
    check_market.start()

@client.event
async def on_message(m):
    global USDT_BALANCE, BTC_BALANCE, avg_entry, bought_30, bought_20, bought_10, sold_70, sold_85, sold_95, position_side
    if m.author == client.user: return
    txt = m.content.strip()
    if txt == "الرصيد":
        await m.channel.send(f"💵 USDT: ${USDT_BALANCE:.2f}\n₿ BTC: {BTC_BALANCE:.6f}\n📍 دخول: {avg_entry:.2f}\n📊 حالة: {position_side}")
    elif txt == "تصفير":
        USDT_BALANCE = 100.0; BTC_BALANCE = 0; avg_entry = 0
        bought_30 = bought_20 = bought_10 = False
        sold_70 = sold_85 = sold_95 = False
        position_side = None
        await m.channel.send("تم تصفير المحفظة 100$")

client.run(TOKEN)

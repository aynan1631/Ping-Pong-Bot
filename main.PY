import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta
import random

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='', intents=intents)

# --- الاعدادات ---
BALANCE_START = 1000.0
balance = BALANCE_START
holdings = {} # {symbol: {qty, avg_price}}
BUY_PCT = 0.10 # 10%
RSI_MIN = 8
RSI_MAX = 30
BUY_INTERVAL_SEC = 300 # كل 5 دقايق
TAKE_PROFIT_PCT = 0.05 # يبيع على 0.05% ربح

last_any_buy = datetime.now() - timedelta(seconds=BUY_INTERVAL_SEC + 10)

COINS = ["WIFUSDT", "SHIBUSDT", "PEPEUSDT", "BONKUSDT", "FLOKIUSDT", "DOGEUSDT"]

def get_mock_price_and_rsi(symbol):
    # هنا سعر وهمي - انت لو رابط Binance خله نفس كودك القديم
    price = random.uniform(0.00001, 1.0)
    if "WIF" in symbol:
        price = random.uniform(0.19, 0.21)
    rsi = random.uniform(5, 45)
    return price, rsi

@bot.event
async def on_ready():
    print(f"Bot ready {bot.user}")
    trading_loop.start()

@bot.command(name="تصفير")
async def reset(ctx):
    global balance, holdings, last_any_buy
    balance = BALANCE_START
    holdings = {}
    last_any_buy = datetime.now() - timedelta(seconds=BUY_INTERVAL_SEC + 10)
    await ctx.send(f"✅ تم التصفير ${BALANCE_START} - يشتري عملة كل 5 دقايق فقط\nRSI فقط بين {RSI_MIN}-{RSI_MAX}")

@bot.command(name="رصيد")
async def show_balance(ctx):
    msg = f"الرصيد: {balance:.2f}$\n"
    for s, data in holdings.items():
        msg += f"{s}: {data['qty']} متوسط {data['avg_price']}\n"
    if not holdings:
        msg += "لا يوجد صفقات مفتوحة"
    await ctx.send(msg)

@tasks.loop(seconds=10)
async def trading_loop():
    global balance, last_any_buy
    now = datetime.now()

    # شرط 5 دقايق - يشتري عملة وحدة فقط
    if (now - last_any_buy).total_seconds() < BUY_INTERVAL_SEC:
        return

    if balance < 50:
        return

    # بيع أولاً
    for symbol in list(holdings.keys()):
        price, rsi = get_mock_price_and_rsi(symbol)
        buy_price = holdings[symbol]['avg_price']
        profit_pct = ((price - buy_price) / buy_price) * 100

        if profit_pct >= TAKE_PROFIT_PCT or rsi > 65:
            qty = holdings[symbol]['qty']
            profit_usd = (price - buy_price) * qty
            balance += price * qty
            del holdings[symbol]
            channel = discord.utils.get(bot.get_all_channels(), name='general')
            if channel:
                await channel.send(f"✅ قفل {symbol} @ {price:.8f} RSI\nربح {profit_pct:.1f} {profit_usd:.2f}$+ \nالرصيد {balance:.2f}$ 💵")
            return

    # شراء عملة وحدة فقط
    for symbol in COINS:
        if symbol in holdings:
            continue
        price, rsi = get_mock_price_and_rsi(symbol)
        if RSI_MIN <= rsi <= RSI_MAX:
            qty = (balance * BUY_PCT) / price
            cost = qty * price
            if balance >= cost:
                holdings[symbol] = {"qty": qty, "avg_price": price}
                balance -= cost
                last_any_buy = now
                channel = discord.utils.get(bot.get_all_channels(), name='general')
                if channel:
                    await channel.send(f"🟢 {symbol} شراء 1 RSI {rsi:.1f} @ {price:.8f}\nمتوسط {price:.8f} رصيد {BUY_PCT*100:.0f}%=${cost:.2f}\n{balance:.2f}$")
                break # مهم جداً - يوقف بعد أول عملة

bot.run("YOUR_TOKEN_HERE")

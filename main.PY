import os, time, threading, random
from flask import Flask
import discord
from discord.ext import commands

# --- موقع Render ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Ping-Pong-Bot V8.5 Demo - Live"

# --- اعدادات ---
AMOUNT_PER_TRADE = 500
TP_DOLLAR = 5
SL_DOLLAR = -5
open_positions = []

def get_movers():
    # تجريبي - يختار عملتين عشوائية
    coins = ["BTCUSDT", "ETHUSDT", "DOGEUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT"]
    up = random.choice(coins)
    down = random.choice([c for c in coins if c != up])
    return [(up, 3.2), (down, -4.1)]

def get_data(symbol):
    return 100.5, 98.0

def check_pnl(pos):
    # تجريبي - ربح وخسارة عشوائية بين -2 و +3
    pnl = round(random.uniform(-2, 4), 2)
    return pnl, 101.2

def create_position(symbol, usd):
    print(f"[DEMO] فتح {symbol} بـ {usd}$")
    return {'symbol': symbol, 'buy_price': round(random.uniform(90, 110), 2), 'usd': usd, 'time': time.strftime("%H:%M")}

def trading_loop():
    global open_positions
    while True:
        try:
            if len(open_positions) < 2:
                movers = get_movers()
                coin_up = movers[0]
                coin_down = movers[1]
                open_positions.append(create_position(coin_up[0], AMOUNT_PER_TRADE))
                open_positions.append(create_position(coin_down[0], AMOUNT_PER_TRADE))
                print(f">>> فتح صفقتين: {coin_up[0]} و {coin_down[0]} | المجموع: {len(open_positions)}")

            for pos in open_positions.copy():
                pnl, _ = check_pnl(pos)
                if pnl >= TP_DOLLAR or pnl <= SL_DOLLAR:
                    print(f">>> اغلق {pos['symbol']} PnL {pnl}$")
                    open_positions.remove(pos)

            time.sleep(90)
        except Exception as e:
            print(f"خطأ: {e}")
            time.sleep(60)

# --- ديسكورد ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f">>> Discord Online: {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send(f"✅ **البوت شغال!**\nالصفقات المفتوحة: **{len(open_positions)}**\nالوضع: **تجريبي DEMO**")

@bot.command()
async def status(ctx):
    if not open_positions:
        await ctx.send("📭 لا يوجد صفقات مفتوحة حالياً - البوت يبحث عن فرصة...")
    else:
        msg = f"📊 **الصفقات المفتوحة: {len(open_positions)}**\n\n"
        for i, p in enumerate(open_positions, 1):
            msg += f"**{i}. {p['symbol']}**\n   شراء: `{p['buy_price']}` | مبلغ: `{p['usd']}$` | وقت: `{p['time']}`\n"
        await ctx.send(msg)

@bot.command()
async def pnl(ctx):
    if not open_positions:
        await ctx.send("📭 لا يوجد صفقات لحساب الربح")
    else:
        msg = "💰 **الارباح الحالية (تجريبي):**\n\n"
        total = 0
        for p in open_positions:
            profit, curr = check_pnl(p)
            total += profit
            emoji = "🟢" if profit >= 0 else "🔴"
            msg += f"{emoji} {p['symbol']}: `{profit}$` (سعر حالي: {curr})\n"
        msg += f"\n**الاجمالي: {round(total, 2)}$**"
        await ctx.send(msg)

@bot.command()
async def close(ctx):
    global open_positions
    count = len(open_positions)
    open_positions.clear()
    await ctx.send(f"✅ تم اغلاق {count} صفقات يدوياً")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if "تصغير" in message.content.lower():
        await message.channel.send("تم ✅ تبي تصغير ماذا؟ اكتب `!status` لرؤية الصفقات")
    await bot.process_commands(message)

# --- التشغيل ---
if __name__ == "__main__":
    threading.Thread(target=trading_loop, daemon=True).start()
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()
    bot.run(os.getenv("DISCORD_TOKEN"))

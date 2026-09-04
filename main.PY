import os
import time
import threading
import random
import asyncio
import json
from flask import Flask
import discord
from discord.ext import commands

# ================== الإعدادات ==================
app = Flask(__name__)
@app.route('/')
def home():
    return "V9 - Bot Working - Persistent PnL"

AMOUNT_PER_TRADE = 500
TP_DOLLAR = 5.0
SL_DOLLAR = -5.0

open_positions = []
DISCORD_CHANNEL_ID = None
FILE = "trades.json"

# ================== حفظ الأرباح في ملف ==================
def load_closed():
    if os.path.exists(FILE):
        try:
            with open(FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_closed(trades):
    with open(FILE, "w") as f:
        json.dump(trades, f)

closed_trades = load_closed()

def get_movers():
    coins = ["BTCUSDT", "ETHUSDT", "DOGEUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT", "AVAXUSDT"]
    up = random.choice(coins)
    down = random.choice([c for c in coins if c!= up])
    return [(up, 3.2), (down, -4.1)]

def check_pnl(pos):
    # ربح يزيد تدريجياً مثل السوق الحقيقي
    if 'pnl' not in pos:
        pos['pnl'] = round(random.uniform(1.0, 4.5), 2)
    else:
        pos['pnl'] += round(random.uniform(-0.2, 0.7), 2)
    pos['pnl'] = round(pos['pnl'], 2)
    curr = round(pos['buy_price'] + pos['pnl'], 2)
    return pos['pnl'], curr

def create_position(symbol, usd):
    return {
        'symbol': symbol,
        'buy_price': round(random.uniform(90, 110), 2),
        'usd': usd,
        'pnl': round(random.uniform(1.0, 4.0), 2),
        'time': time.strftime("%H:%M:%S")
    }

def get_profit_text():
    closed = load_closed()
    if not closed:
        return "📊 **لم يتم إقفال أي صفقة بعد**\n\nاكتب `اقفال الكل` عشان تجرب الحساب"

    total_profit = sum([t['pnl'] for t in closed if t['pnl'] > 0])
    total_loss = sum([t['pnl'] for t in closed if t['pnl'] < 0])
    total_all = sum([t['pnl'] for t in closed])

    msg = f"💰 **ملخص الأرباح الكلي**\n\n"
    msg += f"✅ **مجموع الأرباح:** `+{round(total_profit, 2)}$`\n"
    msg += f"❌ **مجموع الخسائر:** `{round(total_loss, 2)}$`\n"
    msg += f"━━━━━━━━━━━━━━━\n"
    msg += f"📈 **الصافي النهائي:** `{round(total_all, 2)}$`\n"
    msg += f"🔢 **عدد الصفقات المقفلة:** {len(closed)}"
    return msg

def get_status_text():
    if not open_positions:
        return "📭 **لا يوجد صفقات مفتوحة حالياً - سيفتح صفقات جديدة تلقائياً**"

    msg = f"📊 **الصفقات المفتوحة: {len(open_positions)}**\n\n"
    for p in open_positions:
        pnl, curr = check_pnl(p)
        emoji = "🟢" if pnl >= 0 else "🔴"
        msg += f"{emoji} **{p['symbol']}** | الربح الآن: `{pnl}$`\n"
    return msg

# ================== إعداد بوت الديسكورد ==================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def send_auto_message(text):
    if DISCORD_CHANNEL_ID:
        try:
            channel = bot.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                asyncio.run_coroutine_threadsafe(channel.send(text), bot.loop)
        except Exception as e:
            print(f"فشل الارسال: {e}")

def trading_loop():
    global open_positions
    while True:
        try:
            if len(open_positions) < 2:
                movers = get_movers()
                open_positions.append(create_position(movers[0][0], AMOUNT_PER_TRADE))
                open_positions.append(create_position(movers[1][0], AMOUNT_PER_TRADE))
                send_auto_message(f"📈 **تم فتح صفقتين جديدتين**\n• {movers[0][0]}\n• {movers[1][0]}\n\nاكتب `الحالة` للمشاهدة")

            for pos in open_positions.copy():
                pnl, _ = check_pnl(pos)
                if pnl >= TP_DOLLAR or pnl <= SL_DOLLAR:
                    closed = load_closed()
                    closed.append(pos)
                    save_closed(closed)
                    open_positions.remove(pos)
                    emoji = "🟢" if pnl >= 0 else "🔴"
                    reason = "وصل للهدف +5$" if pnl > 0 else "وقف خسارة -5$"
                    send_auto_message(
                        f"{emoji} **تم إقفال تلقائي**\n\n"
                        f"**العملة:** {pos['symbol']}\n"
                        f"**الربح:** `{pnl}$`\n"
                        f"**السبب:** {reason}\n\n"
                        f"{get_profit_text()}"
                    )
            time.sleep(60)
        except Exception as e:
            print(f"Error loop: {e}")
            time.sleep(60)

@bot.event
async def on_ready():
    print(f">>> Bot Online {bot.user}")
    print(f">>> Closed trades loaded: {len(load_closed())}")

@bot.event
async def on_message(message):
    global DISCORD_CHANNEL_ID, open_positions
    if message.author == bot.user:
        return

    if DISCORD_CHANNEL_ID is None:
        DISCORD_CHANNEL_ID = message.channel.id
        print(f">>> Channel saved: {DISCORD_CHANNEL_ID}")

    text = message.content.strip()

    if text in ["الارباح", "الأرباح", "ارباح", "الملخص", "الربح"]:
        await message.channel.send(get_profit_text())
        return

    if text in ["الحالة", "الصفقات", "المفتوحة", "حالة"]:
        await message.channel.send(get_status_text())
        return

    if text in ["اقفال الكل", "إقفال الكل", "اقفل الكل", "قفل الكل", "اقفال", "تصفية"]:
        if not open_positions:
            await message.channel.send("📭 **لا يوجد صفقات مفتوحة**")
            return

        total_pnl = 0
        details = ""
        closed = load_closed()
        for pos in open_positions.copy():
            pnl, _ = check_pnl(pos)
            pos['pnl'] = pnl
            total_pnl += pnl
            closed.append(pos)
            details += f"• {pos['symbol']}: `{pnl}$`\n"
            open_positions.remove(pos)

        save_closed(closed)
        emoji = "🟢" if total_pnl >= 0 else "🔴"
        await message.channel.send(f"✅ **تم إقفال الكل**\n\n{details}\n{emoji} **صافي العملية: {round(total_pnl, 2)}$**\n\n{get_profit_text()}")
        return

    # اقفال عملة محددة
    if text.startswith("اقفال ") or text.startswith("اقفل "):
        try:
            symbol_input = text.split(" ", 1)[1].upper().strip()
            found = next((p for p in open_positions if symbol_input in p['symbol']), None)
            if not found:
                await message.channel.send(f"❌ **ما لقيت {symbol_input}**\n{get_status_text()}")
                return
            pnl, _ = check_pnl(found)
            found['pnl'] = pnl
            closed = load_closed()
            closed.append(found)
            save_closed(closed)
            open_positions.remove(found)
            await message.channel.send(f"✅ **تم إقفال {found['symbol']} بربح {pnl}$**\n\n{get_profit_text()}")
        except:
            await message.channel.send("❌ **استخدم:** `اقفال BTC`")
        return

    if text.lower() in ["reset", "تصفير", "مسح الارباح"]:
        save_closed([])
        await message.channel.send("🗑️ **تم تصفير سجل الأرباح**")
        return

    await bot.process_commands(message)

@bot.command()
async def ping(ctx):
    await ctx.send(f"✅ **شغال** | المفتوحة: {len(open_positions)} | المقفلة: {len(load_closed())}")

@bot.command()
async def status(ctx):
    await ctx.send(get_status_text())

@bot.command()
async def profit(ctx):
    await ctx.send(get_profit_text())

if __name__ == "__main__":
    threading.Thread(target=trading_loop, daemon=True).start()
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()
    bot.run(os.getenv("DISCORD_TOKEN"))

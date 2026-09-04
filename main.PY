import os, time, threading, random
from flask import Flask
import discord
from discord.ext import commands

app = Flask(__name__)
@app.route('/')
def home(): return "V8.7 Arabic Commands"

AMOUNT_PER_TRADE = 500
TP_DOLLAR = 5
SL_DOLLAR = -5
open_positions = []
closed_trades = []

def get_movers():
    coins = ["BTCUSDT", "ETHUSDT", "DOGEUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT"]
    up = random.choice(coins)
    down = random.choice([c for c in coins if c!= up])
    return [(up, 3.2), (down, -4.1)]

def check_pnl(pos):
    pnl = round(random.uniform(-2.5, 5.5), 2)
    curr = round(pos['buy_price'] + pnl, 2)
    return pnl, curr

def create_position(symbol, usd):
    return {'symbol': symbol, 'buy_price': round(random.uniform(90, 110), 2), 'usd': usd, 'time': time.strftime("%H:%M:%S")}

def trading_loop():
    global open_positions
    while True:
        try:
            if len(open_positions) < 2:
                movers = get_movers()
                open_positions.append(create_position(movers[0][0], AMOUNT_PER_TRADE))
                open_positions.append(create_position(movers[1][0], AMOUNT_PER_TRADE))
            for pos in open_positions.copy():
                pnl, _ = check_pnl(pos)
                if pnl >= TP_DOLLAR or pnl <= SL_DOLLAR:
                    pos['pnl'] = pnl
                    closed_trades.append(pos)
                    open_positions.remove(pos)
            time.sleep(90)
        except: time.sleep(60)

# دالة تجيب ملخص الارباح
def get_profit_text():
    if not closed_trades:
        return "📊 **لم يتم إقفال أي صفقة بعد**"
    total_profit = sum([t['pnl'] for t in closed_trades if t['pnl'] > 0])
    total_loss = sum([t['pnl'] for t in closed_trades if t['pnl'] < 0])
    total_all = sum([t['pnl'] for t in closed_trades])
    msg = f"💰 **ملخص الأرباح الكلي**\n\n"
    msg += f"✅ **مجموع الأرباح:** `+{round(total_profit, 2)}$`\n"
    msg += f"❌ **مجموع الخسائر:** `{round(total_loss, 2)}$`\n"
    msg += f"━━━━━━━━━━━━━━━\n"
    msg += f"📈 **الصافي النهائي:** `{round(total_all, 2)}$`\n"
    msg += f"🔢 **عدد الصفقات المقفلة:** {len(closed_trades)} صفقة"
    return msg

def get_status_text():
    if not open_positions:
        return "📭 **لا يوجد صفقات مفتوحة حالياً**"
    msg = f"📊 **الصفقات المفتوحة: {len(open_positions)}**\n\n"
    for p in open_positions:
        pnl, curr = check_pnl(p)
        emoji = "🟢" if pnl >=0 else "🔴"
        msg += f"{emoji} **{p['symbol']}**\n سعر الشراء: {p['buy_price']} | الحالي: {curr} | الربح الآن: `{pnl}$`\n\n"
    return msg

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f">>> Online {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user: return

    text = message.content.strip()
    text_low = text.lower()

    # --- اوامر عربية ---
    if text in ["الارباح", "الأرباح", "ارباح", "أرباح", "مجموع الارباح", "الملخص"]:
        await message.channel.send(get_profit_text())
        return

    if text in ["الحالة", "الصفقات", "المفتوحة", "status_ar"]:
        await message.channel.send(get_status_text())
        return

    if text in ["اقفال الكل", "إقفال الكل", "اقفل الكل", "قفل الكل", "close all"]:
        if not open_positions:
            await message.channel.send("📭 **لا يوجد صفقات لإقفالها**")
            return
        total_pnl = 0
        details = ""
        for pos in open_positions.copy():
            pnl, _ = check_pnl(pos)
            pos['pnl'] = pnl
            total_pnl += pnl
            closed_trades.append(pos)
            details += f"• {pos['symbol']}: `{pnl}$`\n"
            open_positions.remove(pos)
        emoji = "🟢" if total_pnl >=0 else "🔴"
        await message.channel.send(f"✅ **تم إقفال جميع الصفقات**\n\n{details}\n{emoji} **صافي ربح هذه العملية: {round(total_pnl, 2)}$**\n\nاكتب `الارباح` لتشوف المجموع الكلي")
        return

    # اقفال عملة محددة بالعربي: مثال "اقفال SOLUSDT" او "اقفل BTC"
    if text_low.startswith("اقفال ") or text_low.startswith("اقفل ") or text_low.startswith("إقفال "):
        symbol_input = text.split(" ", 1)[1].upper().strip()
        found = None
        for pos in open_positions:
            if symbol_input in pos['symbol']:
                found = pos
                break
        if not found:
            await message.channel.send(f"❌ **ما لقيت {symbol_input}**")
            return
        pnl, _ = check_pnl(found)
        found['pnl'] = pnl
        closed_trades.append(found)
        open_positions.remove(found)
        emoji = "🟢" if pnl >=0 else "🔴"
        await message.channel.send(f"✅ **تم إقفال {found['symbol']}**\n{emoji} **الربح: {pnl}$**\n\nاكتب `الارباح` عشان تشوف المجموع")
        return

    await bot.process_commands(message)

# اوامر انجليزية تبقى شغالة
@bot.command()
async def status(ctx): await ctx.send(get_status_text())
@bot.command()
async def profit(ctx): await ctx.send(get_profit_text())
@bot.command()
async def ping(ctx): await ctx.send(f"✅ **البوت شغال**\nالصفقات: {len(open_positions)}")

if __name__ == "__main__":
    threading.Thread(target=trading_loop, daemon=True).start()
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()
    bot.run(os.getenv("DISCORD_TOKEN"))

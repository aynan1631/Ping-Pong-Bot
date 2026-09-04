import os, time, threading, random, asyncio
from flask import Flask
import discord
from discord.ext import commands

app = Flask(__name__)
@app.route('/')
def home(): return "V8.8 Auto Notify"

AMOUNT_PER_TRADE = 500
TP_DOLLAR = 5
SL_DOLLAR = -5
open_positions = []
closed_trades = []
DISCORD_CHANNEL_ID = None # سيتم حفظه تلقائي

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

def get_profit_text():
    if not closed_trades:
        return "📊 **لم يتم إقفال أي صفقة بعد**"
    total_profit = sum([t['pnl'] for t in closed_trades if t['pnl'] > 0])
    total_loss = sum([t['pnl'] for t in closed_trades if t['pnl'] < 0])
    total_all = sum([t['pnl'] for t in closed_trades])
    msg = f"💰 **ملخص الأرباح الكلي**\n\n✅ **مجموع الأرباح:** `+{round(total_profit, 2)}$`\n❌ **مجموع الخسائر:** `{round(total_loss, 2)}$`\n━━━━━━━━━━━━━━━\n📈 **الصافي النهائي:** `{round(total_all, 2)}$`\n🔢 **عدد الصفقات المقفلة:** {len(closed_trades)}"
    return msg

def get_status_text():
    if not open_positions:
        return "📭 **لا يوجد صفقات مفتوحة حالياً**"
    msg = f"📊 **الصفقات المفتوحة: {len(open_positions)}**\n\n"
    for p in open_positions:
        pnl, curr = check_pnl(p)
        emoji = "🟢" if pnl >=0 else "🔴"
        msg += f"{emoji} **{p['symbol']}** | الربح الآن: `{pnl}$`\n"
    return msg

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# دالة ترسل اشعار تلقائي
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
                # اشعار فتح
                send_auto_message(f"📈 **تم فتح صفقتين جديدتين**\n• {movers[0][0]}\n• {movers[1][0]}\n\nاكتب `الحالة` للمشاهدة")

            for pos in open_positions.copy():
                pnl, _ = check_pnl(pos)
                if pnl >= TP_DOLLAR or pnl <= SL_DOLLAR:
                    pos['pnl'] = pnl
                    closed_trades.append(pos)
                    open_positions.remove(pos)
                    emoji = "🟢" if pnl >=0 else "🔴"
                    # اشعار اقفال تلقائي
                    send_auto_message(f"{emoji} **تم إقفال تلقائي**\n\n**العملة:** {pos['symbol']}\n**الربح:** `{pnl}$`\n**السبب:** {'وصل للهدف +5$' if pnl>0 else 'وقف خسارة -5$'}\n\n{get_profit_text()}")

            time.sleep(90)
        except Exception as e:
            print(e)
            time.sleep(60)

@bot.event
async def on_ready():
    print(f">>> Online {bot.user}")

@bot.event
async def on_message(message):
    global DISCORD_CHANNEL_ID
    if message.author == bot.user: return

    # حفظ اول قناة يكتب فيها عشان نرسل عليها التلقائي
    if DISCORD_CHANNEL_ID is None:
        DISCORD_CHANNEL_ID = message.channel.id
        print(f">>> تم حفظ القناة: {DISCORD_CHANNEL_ID}")

    text = message.content.strip()
    text_low = text.lower()

    if text in ["الارباح", "الأرباح", "ارباح", "الملخص"]:
        await message.channel.send(get_profit_text())
        return
    if text in ["الحالة", "الصفقات", "المفتوحة"]:
        await message.channel.send(get_status_text())
        return
    if text in ["اقفال الكل", "إقفال الكل", "اقفل الكل", "قفل الكل"]:
        if not open_positions:
            await message.channel.send("📭 **لا يوجد صفقات**")
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
        await message.channel.send(f"✅ **تم إقفال الكل**\n\n{details}\n{emoji} **صافي العملية: {round(total_pnl, 2)}$**\n\n{get_profit_text()}")
        return

    if text_low.startswith("اقفال ") or text_low.startswith("اقفل "):
        symbol_input = text.split(" ", 1)[1].upper().strip()
        found = next((p for p in open_positions if symbol_input in p['symbol']), None)
        if not found:
            await message.channel.send(f"❌ **ما لقيت {symbol_input}**")
            return
        pnl, _ = check_pnl(found)
        found['pnl'] = pnl
        closed_trades.append(found)
        open_positions.remove(found)
        await message.channel.send(f"✅ **تم إقفال {found['symbol']} ربح {pnl}$**\n\n{get_profit_text()}")
        return

    await bot.process_commands(message)

@bot.command()
async def ping(ctx): await ctx.send(f"✅ **شغال** | المفتوحة: {len(open_positions)}")

if __name__ == "__main__":
    threading.Thread(target=trading_loop, daemon=True).start()
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()
    bot.run(os.getenv("DISCORD_TOKEN"))

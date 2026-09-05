import os
import discord
from discord.ext import tasks, commands
import ccxt
import asyncio
from datetime import datetime
from flask import Flask
import threading

# --- حل مشكلة Render : فتح بورت ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Ping Pong Bot is Live! Dashboard is working."

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()
# ------------------------------------

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981 # روم general حقك

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

exchange = ccxt.binance()
dashboard_message = None

def get_price(symbol="BTC/USDT"):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except:
        return 0

def check_protection():
    # الحماية: بيتكوين فوق متوسط 200
    try:
        ohlcv = exchange.fetch_ohlcv("BTC/USDT", '1h', limit=200)
        closes = [x[4] for x in ohlcv]
        sma200 = sum(closes) / len(closes)
        price = closes[-1]
        return price > sma200, price, sma200
    except:
        return True, 0, 0

@bot.event
async def on_ready():
    print(f"Bot ready: {bot.user}")
    if not update_dashboard.is_running():
        update_dashboard.start()

@tasks.loop(seconds=30)
async def update_dashboard():
    global dashboard_message
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    is_safe, btc_price, sma = check_protection()
    xrp_price = get_price("XRP/USDT")
    ada_price = get_price("ADA/USDT")

    status = "✅ السوق آمن - بانتظار إشارة" if is_safe else "🛡️ الحماية شغالة - السوق هابط"

    embed = discord.Embed(
        title="📈 لوحة التحكم الحية",
        description=f"**{status}**\nتتحدث كل 30 ثانية تلقائياً",
        color=0x00ff00 if is_safe else 0xff0000,
        timestamp=datetime.now()
    )
    embed.add_field(name="BTC", value=f"${btc_price:.2f}\nSMA200: ${sma:.2f}", inline=True)
    embed.add_field(name="XRP", value=f"${xrp_price:.4f}", inline=True)
    embed.add_field(name="ADA", value=f"${ada_price:.4f}", inline=True)
    embed.add_field(name="الصفقات", value="لا يوجد صفقات - بانتظار إشارة...", inline=False)
    embed.set_footer(text="Ping-Pong-Bot • Render + UptimeRobot")

    try:
        if dashboard_message:
            await dashboard_message.edit(embed=embed)
        else:
            # إذا نسى الرسالة القديمة، يرسل واحدة جديدة
            async for msg in channel.history(limit=10):
                if msg.author == bot.user and msg.embeds:
                    if "لوحة التحكم الحية" in str(msg.embeds[0].title):
                        dashboard_message = msg
                        await msg.edit(embed=embed)
                        return
            dashboard_message = await channel.send(embed=embed)
    except Exception as e:
        print(f"Dashboard error: {e}")
        dashboard_message = None # يخليه يرسل جديد المرة الجاية

bot.run(TOKEN)

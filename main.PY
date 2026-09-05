import os, discord
from discord.ext import tasks, commands
import ccxt
from datetime import datetime
from flask import Flask
import threading

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Live"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955401536733327  # هذا الـ ID حق روم general عندك من الرابط

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

exchange = ccxt.binance()
dashboard_msg = None
open_trades = {"XRPUSDT": 1.42, "ETHUSDT": 2.04} # نفس صفقاتك اللي في الصورة

@bot.event
async def on_ready():
    print(f"Bot Ready {bot.user}")
    if not live_board.is_running():
        live_board.start()

@tasks.loop(seconds=30)
async def live_board():
    global dashboard_msg
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return
    try:
        price_xrp = exchange.fetch_ticker("XRP/USDT")['last']
        price_eth = exchange.fetch_ticker("ETH/USDT")['last']
        embed = discord.Embed(title="📊 الصفقات المفتوحة:", color=0x00ff00, timestamp=datetime.now())
        embed.add_field(name="", value=f"• XRPUSDT: {price_xrp:.2f}$\n• ETHUSDT: {price_eth:.2f}$", inline=False)
        embed.set_footer(text="تتحدث كل 30 ثانية تلقائياً")
        
        if dashboard_msg:
            await dashboard_msg.edit(embed=embed)
        else:
            # يدور على رسالته القديمة حقت 2:58 ويحدثها
            async for m in channel.history(limit=20):
                if m.author == bot.user and m.embeds:
                    dashboard_msg = m
                    await m.edit(embed=embed)
                    return
            dashboard_msg = await channel.send(embed=embed)
    except Exception as e:
        print(f"Board Error: {e}")

@bot.event
async def on_message(message):
    if message.author.bot: return
    msg = message.content.strip()
    
    if msg == "الالة":
        await message.channel.send("الآلة شغالة ✅ Live على Render")
    elif msg == "الحالة":
        await message.channel.send(f"الحالة: يوجد {len(open_trades)} صفقات مفتوحة")
    elif msg == "الارباح":
        await message.channel.send("الأرباح: XRP: 1.42$ | ETH: 2.04$")
    elif msg == "تصفير":
        open_trades.clear()
        await message.channel.send("تم تصفير الأرباح ✅")
    
    await bot.process_commands(message)

bot.run(TOKEN)

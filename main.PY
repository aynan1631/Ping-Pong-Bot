import os
import discord
from discord.ext import tasks
from datetime import datetime
from flask import Flask
import threading

# --- حل مشكلة Render - لازم بورت ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Ping-Pong-Bot Live ✅"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
threading.Thread(target=run_web, daemon=True).start()
# ----------------------------------

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981  # روم general حقك

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# الصفقات اللي ظاهرة عندك في الصورة
open_trades = {
    "XRPUSDT": 1.42,
    "ETHUSDT": 2.04
}

dashboard_msg = None

@bot.event
async def on_ready():
    print(f"Bot Ready: {bot.user}")
    if not live_board.is_running():
        live_board.start()

@tasks.loop(seconds=30)
async def live_board():
    global dashboard_msg
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        # لو ما لقى الروم بالـ ID يحاول يدور general
        for ch in bot.get_all_channels():
            if str(ch.name) == "general":
                channel = ch
                break
    if not channel:
        print("Channel not found")
        return

    try:
        embed = discord.Embed(
            title="📊 الصفقات المفتوحة:",
            description=f"• XRPUSDT: {open_trades.get('XRPUSDT', 0)}$\n• ETHUSDT: {open_trades.get('ETHUSDT', 0)}$" if open_trades else "لا يوجد صفقات مفتوحة",
            color=0x00ff00 if open_trades else 0xff0000,
            timestamp=datetime.now()
        )
        embed.add_field(name="الحالة", value=f"يوجد {len(open_trades)} صفقات مفتوحة", inline=True)
        embed.add_field(name="التحديث", value="كل 30 ثانية تلقائياً", inline=True)
        embed.set_footer(text="Ping-Pong-Bot Live • Render + UptimeRobot")

        if dashboard_msg:
            await dashboard_msg.edit(embed=embed)
            print(f"Dashboard updated: {datetime.now()}")
        else:
            dashboard_msg = await channel.send(embed=embed)
            print(f"Dashboard sent new: {dashboard_msg.id}")

    except Exception as e:
        print(f"Board Error: {e}")
        dashboard_msg = None

@bot.event
async def on_message(message):
    global open_trades, dashboard_msg
    if message.author.bot:
        return

    content = message.content.strip()

    if content == "الالة":
        await message.channel.send("الآلة شغالة ✅ Live على Render")
    
    elif content == "الحالة" or "الحالة" in content:
        await message.channel.send(f"الحالة: يوجد {len(open_trades)} صفقات مفتوحة")
    
    elif content == "الارباح" or "الارباح" in content:
        if open_trades:
            txt = " | ".join([f"{k.replace('USDT','')}: {v}$" for k,v in open_trades.items()])
            await message.channel.send(f"الأرباح: {txt}")
        else:
            await message.channel.send("الأرباح: لا يوجد صفقات")
    
    elif content == "تصفير":
        open_trades.clear()
        await message.channel.send("تم تصفير الأرباح ✅")
        # يحدث اللوحة فوراً بعد التصفير
        if dashboard_msg:
            try:
                await dashboard_msg.edit(embed=discord.Embed(title="📊 الصفقات المفتوحة:", description="تم التصفير - لا يوجد صفقات", color=0xff0000, timestamp=datetime.now()))
            except:
                pass

bot.run(TOKEN)

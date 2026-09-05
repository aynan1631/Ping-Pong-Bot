import discord
from discord.ext import commands, tasks
import os
import asyncio
import aiohttp
from flask import Flask
from threading import Thread
import time

# ========== إعدادات البوت ==========
TOKEN = os.getenv("DISCORD_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")  # اللي ضفته انت الحين
PORT = int(os.getenv("PORT", 10000))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="", intents=intents)

# ========== سيرفر يخلي ريندر ما ينام ==========
app = Flask('')

@app.route('/')
def home():
    return "CRAZY NO-SLEEP NO-429 ✅ Bot is Alive!"

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ========== حلقة تصحي نفسها كل 4 دقايق ==========
async def self_ping():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            if RENDER_URL:
                async with aiohttp.ClientSession() as session:
                    async with session.get(RENDER_URL) as r:
                        print(f"[SELF-PING] {r.status} - صحيت نفسي")
        except Exception as e:
            print(f"[SELF-PING ERROR] {e}")
        await asyncio.sleep(240)  # كل 4 دقايق

# ========== متغيرات اللعبة ==========
scores = {}
is_crazy = False

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print("CRAZY NO-SLEEP NO-429 ✅")
    bot.loop.create_task(self_ping())

@bot.event
async def on_message(message):
    global is_crazy
    if message.author.bot:
        return

    content = message.content.strip().lower()

    # حماية من سبام 429
    try:
        if content == "تصفير":
            scores[message.channel.id] = 0
            is_crazy = True
            await message.channel.send("🔥 تم التصفير! المجنون بدأ يضرب 💰")
            return

        if content in ["بينق", "بونق", "ping", "pong"]:
            # تأخير بسيط عشان ما ننبلوك
            await asyncio.sleep(0.5)
            
            count = scores.get(message.channel.id, 0) + 1
            scores[message.channel.id] = count

            # كل 10 ضربات يعطي 1$
            if count % 10 == 0:
                await message.channel.send(f"💰 **هروب مجنون!** جبنا 1$ | الضربات: {count}")
            else:
                await message.channel.send(f"🏓 {content} | {count}")

    except discord.errors.HTTPException as e:
        if e.status == 429:
            print(f"⚠️ بلوك 429 - بننتظر {e.retry_after} ثانية")
            await asyncio.sleep(e.retry_after)
        else:
            print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

# ========== التشغيل ==========
keep_alive()
bot.run(TOKEN)

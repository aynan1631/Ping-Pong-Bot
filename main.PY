import os, discord, requests
from discord.ext import tasks
from flask import Flask
import threading

TOKEN = os.environ.get("DISCORD_TOKEN")
app = Flask('')
@app.route('/')
def home(): return "OK"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
pos = None
trades = []

@client.event
async def on_ready():
    print(f"Ready {client.user}")

@client.event
async def on_message(m):
    global pos
    if m.author == client.user: return
    if m.content == "صفقات":
        await m.channel.send("\n".join(trades[-5:]) if trades else "لا يوجد صفقات")
    if m.content == "الرصيد":
        await m.channel.send(f"داخل {pos}" if pos else "ما في صفقة")

client.run(TOKEN)

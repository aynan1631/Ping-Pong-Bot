from flask import Flask
import threading, os, json, requests, asyncio, discord
from datetime import datetime
app=Flask(__name__)
@app.route('/')
def home(): return "Bot is alive"
threading.Thread(target=lambda: app.run(host='0.0.0.0',port=8080),daemon=True).start()
TOKEN=os.getenv("DISCORD_TOKEN")
intents=discord.Intents.default()
intents.message_content=True
FILE="paper_trades.json"
def load():
    try:
        with open(FILE,"r") as f: return json.load(f)
    except: return {"balance":1000.0,"open":None}
def save(d):
    with open(FILE,"w") as f: json.dump(d,f)
class MyBot(discord.Client):
    async def setup_hook(self):
        print(">>> Bot ready <<<")
    async def on_message(self,m):
        if m.author.bot: return
        if m.content.strip()=="ايدي":
            await m.channel.send(f"ايدي القناة: `{m.channel.id}` انسخه")
        if m.content.strip()=="صفقات":
            await m.channel.send("البوت شغال ✅")
bot=MyBot(intents=intents)
bot.run(TOKEN)

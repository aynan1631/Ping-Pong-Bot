import discord
from discord.ext import commands
import requests
from datetime import datetime
import os
from flask import Flask
from threading import Thread

# سيرفر وهمي عشان Render ما يزعجنا
app = Flask('')
@app.route('/')
def home(): return "البوت شغال ✅"
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

positions = [
    {"symbol": "FLOKIUSDT", "side": "SHORT", "entry": 0.00002575, "current": 0.00002523, "pnl": 0.91, "time": "2026-05-13 17:22:03", "executed": True},
    {"symbol": "WIFUSDT", "side": "LONG", "entry": 0.22623, "current": 0.2196, "pnl": -4.08, "time": "2026-05-13 09:17:27", "executed": False},
    {"symbol": "PEPEUSDT", "side": "SHORT", "entry": 0.00000372, "current": 0.00000363, "pnl": 0.93, "time": "2026-05-13 17:17:03", "executed": True},
]
BALANCE_START = 1200

@bot.event
async def on_ready():
    print(f"البوت شغال ✅ {bot.user}")

@bot.command(name="سعر")
async def price(ctx, coin="bitcoin"):
    try:
        r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd", timeout=10).json()
        await ctx.send(f"💰 سعر {coin}: ${r[coin]['usd']}")
    except:
        await ctx.send("جرب: !سعر bitcoin")

@bot.command(name="الرصيد")
async def balance_report(ctx):
    total_realized = sum(p['pnl'] for p in positions if p['executed'])
    total_unrealized = sum(p['pnl'] for p in positions if not p['executed'])
    current_balance = BALANCE_START + total_realized + total_unrealized

    lines = []
    lines.append(f"{'العملة':<10} {'النوع':<12} {'دخول':<12} {'هدف':<12} {'ربح':<8} {'الحالة'}")
    lines.append("-"*85)
    for p in positions:
        target = p['entry']*0.98 if p['side']=="SHORT" else p['entry']*1.02
        side_text = "بيع SHORT" if p['side']=="SHORT" else "شراء LONG"
        status = "✅ منفذ" if p['executed'] else "⏳ مفتوح"
        lines.append(f"{p['symbol']:<10} {side_text:<12} {p['entry']:<12.8f} {target:<12.8f} {p['pnl']:+.2f}$ {status}")

    table = "\n".join(lines)
    embed = discord.Embed(title=f"📊 التقرير الشامل", description=f"```\n{table}\n```", color=0x00ff00)
    embed.add_field(name="💰 الابتدائي", value=f"{BALANCE_START}$", inline=True)
    embed.add_field(name="💵 الحالي", value=f"{current_balance:.2f}$", inline=True)
    await ctx.send(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))

import discord
from discord.ext import commands
import requests
from datetime import datetime
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# بيانات صفقاتك - تقدر تربطها لاحقا بملفك الحقيقي
positions = [
    {"symbol": "FLOKIUSDT", "side": "SHORT", "entry": 0.00002575, "current": 0.00002523, "pnl": 0.91, "time": "2026-05-13 17:22:03", "executed": True},
    {"symbol": "WIFUSDT", "side": "LONG", "entry": 0.22623706, "current": 0.2196, "pnl": -4.08, "time": "2026-05-13 09:17:27", "executed": False},
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
    lines.append(f"{'العملة':<10} {'النوع':<12} {'دخول':<12} {'خروج مستهدف':<12} {'ربح/خسارة':<10} {'التاريخ':<19} {'الحالة'}")
    lines.append("-"*95)
    for p in positions:
        target = p['entry']*0.98 if p['side']=="SHORT" else p['entry']*1.02
        side_text = "بيع SHORT" if p['side']=="SHORT" else "شراء LONG"
        status = "✅ منفذ" if p['executed'] else "⏳ غير منفذ"
        lines.append(f"{p['symbol']:<10} {side_text:<12} {p['entry']:<12.8f} {target:<12.8f} {p['pnl']:+.2f}$ {p['time']:<19} {status}")

    table = "\n".join(lines)
    embed = discord.Embed(title=f"📊 التقرير الشامل - {datetime.now().strftime('%Y-%m-%d %H:%M')}", description=f"```\n{table}\n```", color=0x00ff00)
    embed.add_field(name="💰 الابتدائي", value=f"{BALANCE_START}$", inline=True)
    embed.add_field(name="💵 الحالي", value=f"{current_balance:.2f}$", inline=True)
    embed.add_field(name="📈 منفذ", value=f"{total_realized:+.2f}$", inline=True)
    embed.add_field(name="📉 مفتوح", value=f"{total_unrealized:+.2f}$", inline=True)
    await ctx.send(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))

import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread
from datetime import datetime

app = Flask('')
@app.route('/')
def home(): return "Bot Demo 100% - وهمي"
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run, daemon=True).start()

# ===== هنا تعدل صفقاتك الوهمية =====
BALANCE_START = 1200.0

positions = [
    {"symbol": "FLOKIUSDT", "side": "SHORT", "entry": 0.00002575, "tp": 0.00002523, "pnl": 0.91, "time": "2026-05-13 17:22", "status": "مغلقة ✅ رابحة"},
    {"symbol": "WIFUSDT", "side": "LONG", "entry": 0.22623, "tp": 0.23075, "pnl": -4.08, "time": "2026-05-13 09:17", "status": "مفتوحة ⏳"},
    {"symbol": "PEPEUSDT", "side": "SHORT", "entry": 0.00000372, "tp": 0.00000365, "pnl": 0.93, "time": "2026-05-13 17:17", "status": "مغلقة ✅ رابحة"},
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"البوت الوهمي شغال ✅ {bot.user}")

async def send_report(ctx):
    realized = sum(p['pnl'] for p in positions if "مغلقة" in p['status'])
    unrealized = sum(p['pnl'] for p in positions if "مفتوحة" in p['status'])
    current = BALANCE_START + realized + unrealized
    
    wins = len([p for p in positions if p['pnl'] > 0 and "مغلقة" in p['status']])
    losses = len([p for p in positions if p['pnl'] < 0 and "مغلقة" in p['status']])
    closed_count = wins + losses
    winrate = (wins / closed_count * 100) if closed_count > 0 else 0

    # جدول مرتب بالإنجليزي عشان ما يتلخبط
    table = "```\n"
    table += f"{'SYMBOL':<12} {'SIDE':<10} {'ENTRY':<14} {'PNL':<10} STATUS\n"
    table += "-"*60 + "\n"
    for p in positions:
        table += f"{p['symbol']:<12} {p['side']:<10} {p['entry']:<14} {p['pnl']:+.2f}$   {p['status']}\n"
    table += "```"

    embed = discord.Embed(title="📊 تقرير الأداء الوهمي - اختبار 100%", description=table, color=0x00ff00)
    embed.add_field(name="💰 ابتدائي", value=f"{BALANCE_START}$", inline=True)
    embed.add_field(name="💵 الحالي", value=f"{current:.2f}$", inline=True)
    embed.add_field(name="📈 محقق", value=f"{realized:+.2f}$", inline=True)
    embed.add_field(name="📉 عائم", value=f"{unrealized:+.2f}$", inline=True)
    embed.add_field(name="🏆 نسبة النجاح", value=f"{winrate:.1f}% ({wins} ربح / {losses} خسارة)", inline=True)
    embed.add_field(name="📊 الإجمالي", value=f"{realized+unrealized:+.2f}$", inline=True)
    
    embed.set_footer(text=f"النظام وهمي للاختبار - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    await ctx.channel.send(embed=embed)

@bot.command(name="الرصيد")
async def bal(ctx): await send_report(ctx)

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    if "الرصيد" in message.content or "التقرير" in message.content:
        await send_report(message)
        return
    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))

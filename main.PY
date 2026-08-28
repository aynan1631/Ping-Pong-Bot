import discord
from discord.ext import commands
import requests
from datetime import datetime
import os
import pandas as pd

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== بيانات تجريبية - اربطها ببوتك الحقيقي =====
# هنا تخزن صفقاتك المفتوحة
positions = {
    "FLOKIUSDT": {"side": "SHORT", "entry": 0.00002575, "qty": 3883495, "current": 0.00002523, "pnl": 0.91, "pnl_pct": 2.03, "time": "2026-05-13 17:22:03", "executed": True},
    "WIFUSDT": {"side": "LONG", "entry": 0.22623706, "qty": 441, "current": 0.2196, "pnl": -4.08, "pnl_pct": -1.80, "time": "2026-05-13 09:17:27", "executed": False},
    "PEPEUSDT": {"side": "SHORT", "entry": 0.00000372, "qty": 26881, "current": 0.00000363, "pnl": 0.93, "pnl_pct": 2.07, "time": "2026-05-13 17:17:03", "executed": True},
}
INITIAL_BALANCE = 1200
# ===============================================

@bot.event
async def on_ready():
    print(f"البوت شغال ✅ {bot.user}")

@bot.command(name="سعر")
async def price(ctx, coin="bitcoin"):
    r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd").json()
    try:
        await ctx.send(f"💰 سعر {coin}: ${r[coin]['usd']}")
    except:
        await ctx.send("جرب: !سعر bitcoin")

@bot.command(name="الرصيد")
async def balance_report(ctx):
    rows = []
    total_pnl_realized = 0
    total_pnl_unrealized = 0

    for symbol, p in positions.items():
        entry = p['entry']
        # سعر الخروج المستهدف 2%
        target = entry * 0.98 if p['side'] == 'SHORT' else entry * 1.02
        exit_real = p['current'] if p['executed'] else 0

        # نوع الصفقة
        buy_sell = "بيع SHORT" if p['side'] == 'SHORT' else "شراء LONG"
        status = "✅ منفذ" if p['executed'] else "⏳ غير منفذ - مفتوحة"

        # حساب
        loss = p['pnl'] if p['pnl'] < 0 else 0
        profit = p['pnl'] if p['pnl'] > 0 else 0

        if p['executed']:
            total_pnl_realized += p['pnl']
        else:
            total_pnl_unrealized += p['pnl']

        rows.append([
            symbol,
            buy_sell,
            f"{entry:.8f}",
            f"{target:.8f}",
            f"{exit_real:.8f}" if p['executed'] else "-",
            f"{loss:.2f}" if loss != 0 else "-",
            f"{profit:+.2f}",
            p['time'],
            status
        ])

    current_balance = INITIAL_BALANCE + total_pnl_realized + total_pnl_unrealized

    # نكون الجدول
    headers = ["العملة", "النوع", "دخول", "خروج مستهدف", "خروج فعلي", "خسارة", "ربح", "التاريخ", "الحالة"]
    df = pd.DataFrame(rows, columns=headers)

    table_str = f"```\n{df.to_string(index=False)}\n```"

    embed = discord.Embed(
        title=f"📊 التقرير الشامل - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        description=table_str,
        color=0x00ff00
    )
    embed.add_field(name="💰 الرصيد الابتدائي", value=f"{INITIAL_BALANCE}$", inline=True)
    embed.add_field(name="💵 الرصيد الحالي", value=f"{current_balance:.2f}$", inline=True)
    embed.add_field(name="📈 إجمالي منفذ", value=f"{total_pnl_realized:+.2f}$", inline=True)
    embed.add_field(name="📉 إجمالي غير منفذ", value=f"{total_pnl_unrealized:+.2f}$", inline=True)
    embed.set_footer(text="الربح/الخسارة محسوبة على 100$ لكل صفقة")

    await ctx.send(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))

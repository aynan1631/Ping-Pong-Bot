import discord
from discord.ext import tasks, commands
import ccxt
import asyncio
from datetime import datetime
import os

# ============ إعداداتك الجاهزة - لا تغير شي ============
CHANNEL_ID = 1538955402513747981
TOKEN = os.getenv("DISCORD_TOKEN") or "حط توكنك هنا اذا ما تستخدم ENV"

SYMBOLS = ['XRP/USDT', 'ADA/USDT']
TP_SL = 5.0

exchange = ccxt.binance({
    'apiKey': os.getenv("BINANCE_API"),
    'secret': os.getenv("BINANCE_SECRET"),
    'enableRateLimit': True
})

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

positions = []
trade_history = []
dashboard_message = None

def is_bull_market():
    try:
        btc = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=200)
        closes = [c[4] for c in btc]
        ma200 = sum(closes) / len(closes)
        return closes[-1] > ma200
    except:
        return True

def get_current_price(symbol):
    try:
        return exchange.fetch_ticker(symbol)['last']
    except:
        return 0

def build_dashboard_embed():
    total_pnl = sum(t['pnl'] for t in trade_history)
    wins = len([t for t in trade_history if t['win']])
    losses = len([t for t in trade_history if not t['win']])
    floating_pnl = 0
    desc = ""
    for pos in positions:
        current = get_current_price(pos['symbol'])
        pnl = (current - pos['entry']) * pos['qty']
        floating_pnl += pnl
        emoji = "🟢" if pnl >= 0 else "🔴"
        desc += f"{emoji} **{pos['symbol']}**\n`دخول:` {pos['entry']:.4f} | `حالي:` {current:.4f} | `ربح:` {pnl:+.2f}$\n\n"
    if not desc:
        desc = "⏸️ السوق هابط - متوقف" if not is_bull_market() else "لا يوجد صفقات - بانتظار إشارة..."

    embed = discord.Embed(title="📈 لوحة التحكم الحية", description=desc, color=0x2ecc71 if floating_pnl >=0 else 0xe74c3c, timestamp=datetime.now())
    embed.add_field(name="💰 الأرباح المحققة", value=f"**{total_pnl:.2f}$**", inline=True)
    embed.add_field(name="📊 العائمة", value=f"**{floating_pnl:.2f}$**", inline=True)
    embed.add_field(name="💵 الصافي الكلي", value=f"**{total_pnl + floating_pnl:.2f}$**", inline=True)
    embed.add_field(name="✅ الرابحة", value=f"**{wins}**", inline=True)
    embed.add_field(name="❌ الخاسرة", value=f"**{losses}**", inline=True)
    embed.add_field(name="📦 الإجمالي", value=f"**{len(trade_history)}**", inline=True)
    embed.set_footer(text="تتحدث كل 30 ثانية تلقائياً")
    return embed

@tasks.loop(seconds=30)
async def update_dashboard():
    global dashboard_message
    try:
        channel = bot.get_channel(CHANNEL_ID)
        if not channel: return
        embed = build_dashboard_embed()
        if dashboard_message is None:
            async for msg in channel.history(limit=20):
                if msg.author == bot.user and msg.embeds and "لوحة التحكم" in msg.embeds[0].title:
                    dashboard_message = msg
                    break
            if dashboard_message is None:
                dashboard_message = await channel.send(embed=embed)
            else:
                await dashboard_message.edit(embed=embed)
        else:
            await dashboard_message.edit(embed=embed)
    except Exception as e:
        print(e)

@tasks.loop(seconds=15)
async def trading_loop():
    global positions
    for pos in positions[:]:
        current = get_current_price(pos['symbol'])
        pnl = (current - pos['entry']) * pos['qty']
        if pnl >= TP_SL or pnl <= -TP_SL:
            trade_history.append({'pnl': pnl, 'win': pnl > 0})
            positions.remove(pos)
            ch = bot.get_channel(CHANNEL_ID)
            if ch: await ch.send(f"{'🟢' if pnl>0 else '🔴'} تقفلت {pos['symbol']} بـ {pnl:.2f}$")

    if len(positions) < 2 and is_bull_market():
        for sym in SYMBOLS:
            if len(positions) >= 2: break
            if any(p['symbol'] == sym for p in positions): continue
            price = get_current_price(sym)
            if price == 0: continue
            positions.append({'symbol': sym, 'entry': price, 'qty': 20/price})

@bot.event
async def on_ready():
    print(f"✅ شغال: {bot.user}")
    update_dashboard.start()
    trading_loop.start()

bot.run(TOKEN)

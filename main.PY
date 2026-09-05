import os, discord, requests, threading
from discord.ext import tasks
from datetime import datetime
from flask import Flask

# --- سيرفر Render ---
app = Flask(__name__)
@app.route('/')
def home(): return "Demo Live ✅"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# --- الصفقات المفتوحة (تجريبي - عدل هنا فقط) ---
trades = {
    "XRPUSDT": {"entry": 1.35, "qty": 100},
    "ETHUSDT": {"entry": 2400.00, "qty": 0.5}
}

dashboard_msg = None

def get_live_price(symbol):
    mapping = {"XRPUSDT": "ripple", "ETHUSDT": "ethereum", "BTCUSDT": "bitcoin"}
    try:
        cid = mapping.get(symbol)
        if cid:
            r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={cid}&vs_currencies=usd", timeout=5).json()
            return float(r[cid]['usd'])
    except:
        pass
    try:
        okx_sym = symbol.replace("USDT", "-USDT")
        r = requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={okx_sym}", timeout=5).json()
        return float(r['data'][0]['last'])
    except:
        return 0

@bot.event
async def on_ready():
    print(f"Bot Ready: {bot.user}")
    if not live_board.is_running():
        live_board.start()

@tasks.loop(seconds=15)
async def live_board():
    global dashboard_msg
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return
    try:
        txt_open = ""
        total_profit = 0.0
        total_loss = 0.0
        count_win = 0
        count_lose = 0

        for sym, data in trades.items():
            entry = data['entry']
            current = get_live_price(sym)
            if current == 0: continue

            pnl = (current - entry) * data['qty']

            if pnl >= 0:
                total_profit += pnl
                count_win += 1
                emoji = "🟢"
            else:
                total_loss += abs(pnl)
                count_lose += 1
                emoji = "🔴"

            txt_open += f"{emoji} **{sym}**\n"
            txt_open += f"سعر الدخول: {entry}\n"
            txt_open += f"السعر الحالي: {current:.4f}\n"
            txt_open += f"ربح/خسارة الصفقة: {pnl:.2f}$\n\n"

        net = total_profit - total_loss

        embed = discord.Embed(
            title="📊 الصفقات المفتوحة",
            description=txt_open if txt_open else "لا يوجد صفقات",
            color=0x00ff00 if net >= 0 else 0xff0000,
            timestamp=datetime.now()
        )
        embed.add_field(name="💰 الأرباح", value=f"+{total_profit:.2f}$", inline=True)
        embed.add_field(name="📉 الخساير", value=f"-{total_loss:.2f}$", inline=True)
        embed.add_field(name="💵 صافي الأرباح", value=f"**{net:.2f}$**", inline=True)
        embed.add_field(name="✅ عدد الصفقات الرابحة", value=str(count_win), inline=True)
        embed.add_field(name="❌ عدد الصفقات الخاسرة", value=str(count_lose), inline=True)
        embed.add_field(name="📈 إجمالي المفتوح", value=f"{len(trades)} صفقات", inline=True)
        embed.set_footer(text="تجريبي - تحديث حي كل 15 ثانية • بدون أوامر")

        if dashboard_msg:
            await dashboard_msg.edit(embed=embed)
        else:
            async for m in channel.history(limit=15):
                if m.author == bot.user and m.embeds:
                    try: await m.delete()
                    except: pass
            dashboard_msg = await channel.send(embed=embed)

    except Exception as e:
        print(f"Error: {e}")

bot.run(TOKEN)

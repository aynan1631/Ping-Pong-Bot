import os
import discord
import requests
import threading
from discord.ext import tasks
from datetime import datetime
from flask import Flask

# --- سيرفر Render ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Full Board - Hedge + Protection ✅"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()

# --- إعدادات البوت ---
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# ========= الصفقات + الحماية =========
trades = {
    "XRPUSDT": {"entry": 1.35, "qty": 100, "side": "LONG"},
    "ETHUSDT": {"entry": 2400.00, "qty": 0.5, "side": "SHORT"}
}
TAKE_PROFIT = 5.0 # يقفل اذا ربح 5$
STOP_LOSS = -3.0 # حماية اذا خسر -3$
# =====================================

dashboard_msg = None

def get_live_price(symbol):
    mapping = {"XRPUSDT": "ripple", "ETHUSDT": "ethereum", "BTCUSDT": "bitcoin", "SOLUSDT": "solana"}
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
    global dashboard_msg, trades
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return
    try:
        txt_trades = ""
        total_profit = 0.0
        total_loss = 0.0
        count_win = 0
        count_lose = 0
        to_close = []

        for sym, data in list(trades.items()):
            entry = data['entry']
            side = data.get('side', 'LONG')
            qty = data['qty']
            current = get_live_price(sym)
            if current == 0:
                continue

            # حساب الربح حسب LONG / SHORT
            if side == "LONG":
                pnl = (current - entry) * qty
            else:
                pnl = (entry - current) * qty

            # الحماية
            if pnl >= TAKE_PROFIT:
                to_close.append((sym, pnl, "ربح ✅"))
                continue
            if pnl <= STOP_LOSS:
                to_close.append((sym, pnl, "حماية خسارة 🛡️"))
                continue

            if pnl >= 0:
                total_profit += pnl
                count_win += 1
            else:
                total_loss += abs(pnl)
                count_lose += 1

            # ظهور الصفقات باللوحة
            tag = "📈 LONG" if side == "LONG" else "📉 SHORT"
            txt_trades += f"{tag} **{sym}**\n"
            txt_trades += f"سعر الدخول: {entry} | الحالي: {current:.4f}\n"
            txt_trades += f"الكمية: {qty} | الربح: {pnl:.2f}$\n\n"

        # إقفال الصفقات اللي حققت الحماية
        for sym, pnl, reason in to_close:
            del trades[sym]
            await channel.send(f"🔒 **قفل {sym}** - {reason} ({pnl:.2f}$)")

        embed = discord.Embed(
            title="📊 الصفقات المفتوحة - تحوط متعاكس + حماية",
            description=txt_trades if txt_trades else "✅ لا يوجد صفقات مفتوحة - تم الإقفال بالحماية",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.add_field(name="💰 الأرباح", value=f"+{total_profit:.2f}$", inline=True)
        embed.add_field(name="📉 الخساير", value=f"-{total_loss:.2f}$", inline=True)
        embed.add_field(name="✅ صفقات رابحة", value=str(count_win), inline=True)
        embed.add_field(name="❌ صفقات خاسرة", value=str(count_lose), inline=True)
        embed.add_field(name="📈 إجمالي المفتوح", value=f"{len(trades)} صفقات", inline=True)
        embed.set_footer(text=f"TP: +{TAKE_PROFIT}$ | SL: {STOP_LOSS}$ | تحديث حي كل 15 ثانية")

        if dashboard_msg:
            await dashboard_msg.edit(embed=embed)
        else:
            async for m in channel.history(limit=20):
                if m.author == bot.user and m.embeds:
                    try:
                        await m.delete()
                    except:
                        pass
            dashboard_msg = await channel.send(embed=embed)

    except Exception as e:
        print(f"Error: {e}")

bot.run(TOKEN)

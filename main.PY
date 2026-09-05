import os, discord, requests, threading
from discord.ext import tasks
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "Fixed SL 3$ ✅"
def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981
CAPITAL = 500.0
TP, SL = 5.0, -3.0
dashboard_msg = None

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# الكمية محسوبة صح 500$ لكل صفقة
trades = {
    "XRPUSDT": {"entry": 1.35, "side": "LONG", "qty": CAPITAL/1.35, "capital": CAPITAL},
    "ETHUSDT": {"entry": 2400, "side": "SHORT", "qty": CAPITAL/2400, "capital": CAPITAL}
}

def price(s):
    try:
        m={"XRPUSDT":"ripple","ETHUSDT":"ethereum","BTCUSDT":"bitcoin","SOLUSDT":"solana"}
        if s in m:
            r=requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={m[s]}&vs_currencies=usd",timeout=3).json()
            return float(r[m[s]]['usd'])
    except: pass
    try:
        r=requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={s.replace('USDT','-USDT')}",timeout=3).json()
        return float(r['data'][0]['last'])
    except: return 0

@bot.event
async def on_ready():
    print(f"Ready {bot.user}")
    if not live_board.is_running(): live_board.start()

@bot.event
async def on_message(msg):
    global trades, dashboard_msg
    if msg.author==bot.user or msg.channel.id!=CHANNEL_ID: return
    if msg.content.strip().lower() in ["تصفير","!تصفير","reset"]:
        trades.clear()
        if dashboard_msg:
            try: await dashboard_msg.delete()
            except: pass
            dashboard_msg=None
        await msg.channel.send("✅ تم التصفير - الصفقات صفر")

@tasks.loop(seconds=3) # فحص كل 3 ثواني عشان ما يصير انزلاق -11$
async def live_board():
    global dashboard_msg, trades
    ch=bot.get_channel(CHANNEL_ID)
    if not ch: return
    try:
        profit=loss=0; win=lose=0; txt=""; to_close=[]

        for sym,d in list(trades.items()):
            cur=price(sym)
            if cur==0: continue
            qty=d["qty"]
            pnl=(cur-d["entry"])*qty if d["side"]=="LONG" else (d["entry"]-cur)*qty

            # حماية صارمة
            if pnl >= TP or pnl <= SL:
                to_close.append((sym,pnl,cur))
                continue

            if pnl>=0: profit+=pnl; win+=1
            else: loss+=abs(pnl); lose+=1

            txt+=f"**{sym} {d['side']}**\n"
            txt+=f"سعر الدخول: {d['entry']} | الحالي: {cur:.4f}\n"
            txt+=f"الربح: {pnl:.2f}$\n\n"

        for sym,pnl,cur in to_close:
            del trades[sym]
            if pnl>0:
                await ch.send(f"🔒 قفل **{sym}** ✅ ربح {pnl:.2f}$ | السعر {cur:.4f}")
            else:
                await ch.send(f"🔒 قفل **{sym}** 🛡️ وقف خسارة {pnl:.2f}$ | السعر {cur:.4f} | المفروض {SL}$")

        if not txt:
            txt="لا يوجد صفقات مفتوحة"

        total = profit - loss
        color = 0x2ecc71 if total>=0 else 0xe74c3c

        embed=discord.Embed(title="📊 الصفقات المفتوحة", description=txt, color=color, timestamp=datetime.now())
        embed.add_field(name="💰 الأرباح", value=f"{profit:.2f}$", inline=True)
        embed.add_field(name="📉 الخساير", value=f"{loss:.2f}$", inline=True)
        embed.add_field(name="✅ صفقات رابحة", value=str(win), inline=True)
        embed.add_field(name="❌ صفقات خاسرة", value=str(lose), inline=True)
        embed.set_footer(text=f"راس المال {CAPITAL}$ لكل صفقة | TP {TP}$ | SL {SL}$ | فحص كل 3 ثواني")

        if dashboard_msg:
            await dashboard_msg.edit(embed=embed)
        else:
            async for m in ch.history(limit=15):
                if m.author==bot.user and m.embeds:
                    try: await m.delete()
                    except: pass
            dashboard_msg=await ch.send(embed=embed)

    except Exception as e:
        print(f"Error: {e}")

bot.run(TOKEN)

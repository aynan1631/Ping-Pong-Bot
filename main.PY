import os, discord, requests, threading
from discord.ext import tasks
from flask import Flask

TOKEN = os.environ.get("DISCORD_TOKEN")

app = Flask('')
@app.route('/')
def home(): return "RSI Bot Fixed"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

USDT_BALANCE = 100.0
BTC_BALANCE = 0.0
avg_entry = 0.0
total_profit = 0.0
short_entry = 0.0
short_qty = 0.0

bought_30 = bought_20 = bought_10 = False
sold_70 = sold_85 = sold_95 = False
position_side = None

def calc_rsi(prices, period=14):
    gains=[]; losses=[]
    for i in range(1, len(prices)):
        d=prices[i]-prices[i-1]
        gains.append(d if d>0 else 0)
        losses.append(abs(d) if d<0 else 0)
    ag=sum(gains[-period:])/period
    al=sum(losses[-period:])/period
    if al==0: return 100
    return 100-(100/(1+ag/al))

@tasks.loop(minutes=1)
async def check_market():
    global USDT_BALANCE,BTC_BALANCE,avg_entry,total_profit,short_entry,short_qty
    global bought_30,bought_20,bought_10,sold_70,sold_85,sold_95,position_side
    try:
        curr=float(requests.get("https://data-api.binance.vision/api/v3/ticker/price?symbol=BTCUSDT",timeout=10).json()['price'])
        closes=[float(c[4]) for c in requests.get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=50",timeout=15).json()]
        rsi=calc_rsi(closes,14)

        ch=None
        for g in client.guilds:
            for c in g.text_channels:
                if c.permissions_for(g.me).send_messages: ch=c; break
            if ch: break

        # === 1 - اقفال أول ===
        if position_side=="SHORT" and rsi<=30:
            profit=(short_entry-curr)*short_qty if short_entry else 0
            USDT_BALANCE+=profit
            total_profit+=profit
            if ch: await ch.send(f"⚪ **قفل SHORT @ {curr:.2f} RSI {rsi:.1f} ربح ${profit:.2f}**")
            sold_70=sold_85=sold_95=False
            short_entry=short_qty=0
            position_side=None
            return

        if position_side=="LONG" and BTC_BALANCE>0 and rsi>=60 and curr>avg_entry:
            profit=(curr-avg_entry)*BTC_BALANCE
            USDT_BALANCE+=BTC_BALANCE*curr
            total_profit+=profit
            if ch: await ch.send(f"✅ **قفل LONG @ {curr:.2f} RSI {rsi:.1f} ربح ${profit:.2f}**")
            BTC_BALANCE=0; avg_entry=0
            bought_30=bought_20=bought_10=False
            position_side=None
            return

        # === 2 - فتح جديد فقط اذا فاضي ===
        if position_side is None:
            if rsi<=30 and rsi>20 and not bought_30 and USDT_BALANCE>1:
                amt=USDT_BALANCE*0.15
                qty=amt/curr
                tc=(avg_entry*BTC_BALANCE)+amt
                BTC_BALANCE+=qty; avg_entry=tc/BTC_BALANCE; USDT_BALANCE-=amt
                bought_30=True; position_side="LONG"
                if ch: await ch.send(f"🟢 **شراء 1 (RSI {rsi:.1f})** @ {curr:.2f}\n15% = ${amt:.2f}")

            elif rsi>=70 and rsi<85 and not sold_70:
                sold_70=True; position_side="SHORT"
                short_entry=curr; short_qty=(USDT_BALANCE*0.15)/curr
                if ch: await ch.send(f"🔴 **شورت 1 RSI {rsi:.1f} @ {curr:.2f}**")

    except Exception as e: print(e)

@client.event
async def on_ready():
    print(f"Ready {client.user}")
    check_market.start()

@client.event
async def on_message(m):
    global USDT_BALANCE,BTC_BALANCE,avg_entry,position_side,bought_30,bought_20,bought_10,sold_70,sold_85,sold_95,short_entry,short_qty
    if m.author==client.user: return
    if m.content.strip()=="الرصيد":
        await m.channel.send(f"💵 USDT: ${USDT_BALANCE:.2f}\n₿ BTC: {BTC_BALANCE:.6f}\n📍 دخول: {avg_entry:.2f}\n📊 حالة: {position_side}\nRSI SHORT: {short_entry}")
    if m.content.strip()=="تصفير":
        USDT_BALANCE=100.0; BTC_BALANCE=0; avg_entry=0; short_entry=0; short_qty=0
        bought_30=bought_20=bought_10=False; sold_70=sold_85=sold_95=False; position_side=None
        await m.channel.send("تم التصفير 100$")

client.run(TOKEN)

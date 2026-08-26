import os, discord, requests, threading, json
from discord.ext import tasks
from flask import Flask

TOKEN = os.environ.get("DISCORD_TOKEN")
STATE_FILE = "state.json"

app = Flask('')
@app.route('/')
def home(): return "RSI6 Fixed"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def load_state():
    global USDT_BALANCE, BTC_BALANCE, avg_entry, bought_30, bought_20, bought_10, position_side
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                s=json.load(f)
                USDT_BALANCE=s.get('usdt',100); BTC_BALANCE=s.get('btc',0); avg_entry=s.get('entry',0)
                bought_30=s.get('b30',False); bought_20=s.get('b20',False); bought_10=s.get('b10',False)
                position_side=s.get('side',None)
                return
    except: pass
    USDT_BALANCE=100.0; BTC_BALANCE=0.0; avg_entry=0.0
    bought_30=bought_20=bought_10=False
    position_side=None

def save_state():
    try:
        with open(STATE_FILE,'w') as f:
            json.dump({'usdt':USDT_BALANCE,'btc':BTC_BALANCE,'entry':avg_entry,'b30':bought_30,'b20':bought_20,'b10':bought_10,'side':position_side},f)
    except: pass

load_state()

def calc_rsi(prices, period=6): # نفس بينانس RSI(6)
    gains=[]; losses=[]
    for i in range(1,len(prices)):
        d=prices[i]-prices[i-1]
        gains.append(d if d>0 else 0)
        losses.append(abs(d) if d<0 else 0)
    ag=sum(gains[-period:])/period
    al=sum(losses[-period:])/period
    if al==0: return 100
    return 100-(100/(1+ag/al))

@tasks.loop(minutes=1)
async def check_market():
    global USDT_BALANCE,BTC_BALANCE,avg_entry,bought_30,bought_20,bought_10,position_side
    try:
        curr=float(requests.get("https://data-api.binance.vision/api/v3/ticker/price?symbol=BTCUSDT",timeout=10).json()['price'])
        closes=[float(c[4]) for c in requests.get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=50",timeout=15).json()]
        rsi=calc_rsi(closes,6)

        ch=None
        for g in client.guilds:
            for c in g.text_channels:
                if c.permissions_for(g.me).send_messages: ch=c; break
            if ch: break

        # قفل
        if position_side=="LONG" and BTC_BALANCE>0 and rsi>=60 and curr>avg_entry:
            profit=(curr-avg_entry)*BTC_BALANCE
            USDT_BALANCE+=BTC_BALANCE*curr
            BTC_BALANCE=0; avg_entry=0
            bought_30=bought_20=bought_10=False
            position_side=None
            save_state()
            if ch: await ch.send(f"✅ **قفل LONG @ {curr:.2f} RSI {rsi:.1f} ربح ${profit:.2f}**")
            return

        # شراء - كل مستوى مرة وحدة بس
        if rsi <= 30 and not bought_30 and USDT_BALANCE>1:
            amt=USDT_BALANCE*0.15
            BTC_BALANCE+=amt/curr
            avg_entry=curr if avg_entry==0 else (avg_entry+curr)/2
            USDT_BALANCE-=amt
            bought_30=True; position_side="LONG"
            save_state()
            if ch: await ch.send(f"🟢 **شراء 1 (RSI {rsi:.1f})** @ {curr:.2f} 15%=${amt:.2f}")

        if rsi <= 20 and not bought_20 and USDT_BALANCE>1:
            amt=USDT_BALANCE*0.30
            BTC_BALANCE+=amt/curr
            USDT_BALANCE-=amt
            bought_20=True; position_side="LONG"
            save_state()
            if ch: await ch.send(f"🟢🟢 **شراء 2 (RSI {rsi:.1f})** @ {curr:.2f} 30%=${amt:.2f}")

        if rsi <= 10 and not bought_10 and USDT_BALANCE>1:
            amt=USDT_BALANCE
            BTC_BALANCE+=amt/curr
            USDT_BALANCE-=amt
            bought_10=True; position_side="LONG"
            save_state()
            if ch: await ch.send(f"🟢🟢🟢 **شراء 3 (RSI {rsi:.1f})** @ {curr:.2f} باقي المحفظة")

    except Exception as e: print(e)

@client.event
async def on_ready():
    print(f"Ready {client.user}")
    check_market.start()

@client.event
async def on_message(m):
    global USDT_BALANCE,BTC_BALANCE,avg_entry,bought_30,bought_20,bought_10,position_side
    if m.author==client.user: return
    if m.content.strip()=="الرصيد":
        await m.channel.send(f"💵 USDT: ${USDT_BALANCE:.2f}\n₿ BTC: {BTC_BALANCE:.6f}\n📍 دخول: {avg_entry:.2f}\n📊 {position_side} B30:{bought_30} B20:{bought_20} B10:{bought_10}")
    if m.content.strip()=="تصفير":
        USDT_BALANCE=100.0; BTC_BALANCE=0; avg_entry=0; bought_30=bought_20=bought_10=False; position_side=None
        save_state()
        await m.channel.send("تم التصفير 100$")

client.run(TOKEN)

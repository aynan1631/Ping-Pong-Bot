import os, discord, requests, threading, json
from discord.ext import tasks
from flask import Flask

TOKEN = os.environ.get("DISCORD_TOKEN")
STATE_FILE = "state.json"

app = Flask('')
@app.route('/')
def home(): return "RSI6 Both Sides"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def load_state():
    global USDT_BALANCE, BTC_BALANCE, avg_entry, short_entry, short_qty
    global b30,b20,b10,s70,s80,s85, side
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE,'r') as f:
                s=json.load(f)
                USDT_BALANCE=s.get('usdt',100); BTC_BALANCE=s.get('btc',0)
                avg_entry=s.get('entry',0); short_entry=s.get('s_entry',0); short_qty=s.get('s_qty',0)
                b30=s.get('b30',False); b20=s.get('b20',False); b10=s.get('b10',False)
                s70=s.get('s70',False); s80=s.get('s80',False); s85=s.get('s85',False)
                side=s.get('side',None); return
    except: pass
    USDT_BALANCE=100; BTC_BALANCE=0; avg_entry=0; short_entry=0; short_qty=0
    b30=b20=b10=False; s70=s80=s85=False; side=None

def save_state():
    try:
        with open(STATE_FILE,'w') as f:
            json.dump({'usdt':USDT_BALANCE,'btc':BTC_BALANCE,'entry':avg_entry,'s_entry':short_entry,'s_qty':short_qty,'b30':b30,'b20':b20,'b10':b10,'s70':s70,'s80':s80,'s85':s85,'side':side},f)
    except: pass

load_state()

def calc_rsi(prices, period=6):
    gains=[]; losses=[]
    for i in range(1,len(prices)):
        d=prices[i]-prices[i-1]
        gains.append(d if d>0 else 0)
        losses.append(abs(d) if d<0 else 0)
    if len(gains)<period: return 50
    ag=sum(gains[-period:])/period; al=sum(losses[-period:])/period
    if al==0: return 100
    return 100-(100/(1+ag/al))

@tasks.loop(minutes=1)
async def check_market():
    global USDT_BALANCE,BTC_BALANCE,avg_entry,short_entry,short_qty,b30,b20,b10,s70,s80,s85,side
    try:
        curr=float(requests.get("https://data-api.binance.vision/api/v3/ticker/price?symbol=BTCUSDT",timeout=10).json()['price'])
        closes=[float(c[4]) for c in requests.get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=50",timeout=15).json()]
        rsi=calc_rsi(closes,6)

        ch=None
        for g in client.guilds:
            for c in g.text_channels:
                if c.permissions_for(g.me).send_messages: ch=c; break
            if ch: break
        if not ch: return

        # 1 - قفل LONG على 60 بشرط ربح
        if side=="LONG" and BTC_BALANCE>0 and rsi>=60 and curr>avg_entry:
            profit=(curr-avg_entry)*BTC_BALANCE
            USDT_BALANCE+=BTC_BALANCE*curr
            BTC_BALANCE=0; avg_entry=0; b30=b20=b10=False; side=None
            save_state()
            await ch.send(f"✅ **قفل LONG @ {curr:.2f} RSI {rsi:.1f} ربح +${profit:.2f}**")
            return

        # 2 - قفل SHORT على 40 بشرط ربح (نزل السعر)
        if side=="SHORT" and short_qty>0 and rsi<=40 and curr<short_entry:
            profit=(short_entry-curr)*short_qty
            USDT_BALANCE+=profit
            short_entry=0; short_qty=0; s70=s80=s85=False; side=None
            save_state()
            await ch.send(f"⚪ **قفل SHORT @ {curr:.2f} RSI {rsi:.1f} ربح +${profit:.2f}**")
            return

        # 3 - صفقات شراء
        if side is None or side=="LONG":
            if rsi<=30 and not b30 and USDT_BALANCE>1:
                amt=USDT_BALANCE*0.15; qty=amt/curr
                new=BTC_BALANCE+qty
                avg_entry=((avg_entry*BTC_BALANCE)+(curr*qty))/new if new else curr
                BTC_BALANCE=new; USDT_BALANCE-=amt; b30=True; side="LONG"; save_state()
                await ch.send(f"🟢 **شراء 1 RSI {rsi:.1f} @ {curr:.2f}**")
            if rsi<=20 and not b20 and USDT_BALANCE>1:
                amt=USDT_BALANCE*0.30; qty=amt/curr
                new=BTC_BALANCE+qty
                avg_entry=((avg_entry*BTC_BALANCE)+(curr*qty))/new
                BTC_BALANCE=new; USDT_BALANCE-=amt; b20=True; side="LONG"; save_state()
                await ch.send(f"🟢🟢 **شراء 2 RSI {rsi:.1f} @ {curr:.2f} متوسط {avg_entry:.2f}**")
            if rsi<=10 and not b10 and USDT_BALANCE>1:
                amt=USDT_BALANCE; qty=amt/curr
                new=BTC_BALANCE+qty
                avg_entry=((avg_entry*BTC_BALANCE)+(curr*qty))/new
                BTC_BALANCE=new; USDT_BALANCE=0; b10=True; side="LONG"; save_state()
                await ch.send(f"🟢🟢🟢 **شراء 3 RSI {rsi:.1f} @ {curr:.2f}**")

        # 4 - صفقات بيع شورت
        if side is None or side=="SHORT":
            if rsi>=70 and rsi<80 and not s70:
                short_entry=curr if short_entry==0 else short_entry
                short_qty+=(USDT_BALANCE*0.15)/curr
                s70=True; side="SHORT"; save_state()
                await ch.send(f"🔴 **بيع شورت 1 RSI {rsi:.1f} @ {curr:.2f}**")
            if rsi>=80 and rsi<85 and not s80:
                short_qty+=(USDT_BALANCE*0.30)/curr
                if short_entry==0: short_entry=curr
                s80=True; side="SHORT"; save_state()
                await ch.send(f"🔴🔴 **بيع شورت 2 RSI {rsi:.1f} @ {curr:.2f}**")
            if rsi>=85 and not s85:
                short_qty+=(USDT_BALANCE*0.55)/curr
                if short_entry==0: short_entry=curr
                s85=True; side="SHORT"; save_state()
                await ch.send(f"🔴🔴🔴 **بيع شورت 3 RSI {rsi:.1f} @ {curr:.2f}**")

    except Exception as e: print(e)

@client.event
async def on_ready():
    print(f"Ready {client.user}"); check_market.start()

@client.event
async def on_message(m):
    global USDT_BALANCE,BTC_BALANCE,avg_entry,b30,b20,b10,s70,s80,s85,side,short_entry,short_qty
    if m.author==client.user: return
    if m.content.strip()=="الرصيد":
        await m.channel.send(f"💵 {USDT_BALANCE:.2f} ₿ {BTC_BALANCE:.6f} دخول LONG {avg_entry:.2f} SHORT {short_entry:.2f} qty {short_qty:.6f}\nside {side} B:{b30}{b20}{b10} S:{s70}{s80}{s85}")
    if m.content.strip()=="تصفير":
        USDT_BALANCE=100; BTC_BALANCE=0; avg_entry=0; short_entry=0; short_qty=0; b30=b20=b10=False; s70=s80=s85=False; side=None; save_state()
        await m.channel.send("تم التصفير 100$")

client.run(TOKEN)

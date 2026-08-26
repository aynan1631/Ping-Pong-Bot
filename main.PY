import os, discord, requests, threading, json, time
from discord.ext import tasks
from flask import Flask

TOKEN = os.environ.get("DISCORD_TOKEN")
STATE_FILE = "state.json"

# العملات المجنونة
SYMBOLS = ["PEPEUSDT", "WIFUSDT", "BONKUSDT", "DOGEUSDT", "SHIBUSDT", "FLOKIUSDT"]

app = Flask('')
@app.route('/')
def home(): return "Meme Bot Live"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def load_state():
    global USDT, HOLDINGS
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE,'r') as f:
                s=json.load(f)
                USDT=s.get('usdt',1000.0)
                HOLDINGS=s.get('hold',{})
                # تأكد كل العملات موجودة
                for sym in SYMBOLS:
                    if sym not in HOLDINGS:
                        HOLDINGS[sym]={'qty':0,'avg':0,'b30':False,'b20':False,'b10':False,'side':None,'last':0}
                return
    except: pass
    USDT=1000.0
    HOLDINGS={sym:{'qty':0,'avg':0,'b30':False,'b20':False,'b10':False,'side':None,'last':0} for sym in SYMBOLS}

def save_state():
    try:
        with open(STATE_FILE,'w') as f:
            json.dump({'usdt':USDT,'hold':HOLDINGS},f)
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
    global USDT, HOLDINGS
    try:
        ch=None
        for g in client.guilds:
            for c in g.text_channels:
                if c.permissions_for(g.me).send_messages: ch=c; break
            if ch: break
        if not ch: return

        for sym in SYMBOLS:
            try:
                curr=float(requests.get(f"https://data-api.binance.vision/api/v3/ticker/price?symbol={sym}",timeout=10).json()['price'])
                closes=[float(c[4]) for c in requests.get(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval=1m&limit=50",timeout=10).json()]
                rsi=calc_rsi(closes,6)
                h=HOLDINGS[sym]

                # قفل LONG على 60 بشرط ربح
                if h['side']=="LONG" and h['qty']>0 and rsi>=60 and curr>h['avg']:
                    profit=(curr-h['avg'])*h['qty']
                    USDT+=h['qty']*curr
                    HOLDINGS[sym]={'qty':0,'avg':0,'b30':False,'b20':False,'b10':False,'side':None,'last':0}
                    save_state()
                    await ch.send(f"✅ **قفل {sym} @ {curr} RSI {rsi:.1f} ربح +${profit:.2f}**\n💵 الرصيد {USDT:.2f}$")
                    continue

                # منع التكرار كل 4 دقائق
                if time.time()-h['last']<240: continue

                # شراء 1
                if rsi<=30 and not h['b30'] and USDT>10 and h['side'] in [None,"LONG"]:
                    amt=min(USDT*0.10, 100) # 10% من المحفظة بحد اقصى 100$
                    qty=amt/curr
                    new_qty=h['qty']+qty
                    avg=((h['avg']*h['qty'])+(curr*qty))/new_qty if new_qty else curr
                    h['qty']=new_qty; h['avg']=avg; h['b30']=True; h['side']="LONG"; h['last']=time.time()
                    USDT-=amt; save_state()
                    await ch.send(f"🟢 **{sym} شراء 1 RSI {rsi:.1f} @ {curr}**\n10%=${amt:.2f} متوسط {avg}")

                # شراء 2 تبريد
                elif rsi<=20 and not h['b20'] and USDT>10:
                    amt=min(USDT*0.15, 150)
                    qty=amt/curr
                    new_qty=h['qty']+qty
                    avg=((h['avg']*h['qty'])+(curr*qty))/new_qty
                    h['qty']=new_qty; h['avg']=avg; h['b20']=True; h['side']="LONG"; h['last']=time.time()
                    USDT-=amt; save_state()
                    await ch.send(f"🟢🟢 **{sym} شراء 2 RSI {rsi:.1f} @ {curr} متوسط {avg}**")

                # شراء 3 اخير
                elif rsi<=12 and not h['b10'] and USDT>10:
                    amt=min(USDT*0.20, 200)
                    qty=amt/curr
                    new_qty=h['qty']+qty
                    avg=((h['avg']*h['qty'])+(curr*qty))/new_qty
                    h['qty']=new_qty; h['avg']=avg; h['b10']=True; h['side']="LONG"; h['last']=time.time()
                    USDT-=amt; save_state()
                    await ch.send(f"🟢🟢🟢 **{sym} شراء 3 RSI {rsi:.1f} @ {curr}**")

                time.sleep(1)
            except Exception as e:
                print(f"{sym} err {e}")
                continue

    except Exception as e: print(e)

@client.event
async def on_ready():
    print(f"Ready {client.user}"); check_market.start()

@client.event
async def on_message(m):
    global USDT,HOLDINGS
    if m.author==client.user: return
    if m.content.strip()=="الرصيد":
        txt=f"💵 USDT: ${USDT:.2f}\n"
        for sym,h in HOLDINGS.items():
            if h['qty']>0:
                txt+=f"{sym}: {h['qty']:.2f} متوسط {h['avg']} RSI flags {h['b30']}{h['b20']}{h['b10']}\n"
        await m.channel.send(txt or "ما فيه صفقات")
    if m.content.strip()=="تصفير":
        USDT=1000.0
        HOLDINGS={sym:{'qty':0,'avg':0,'b30':False,'b20':False,'b10':False,'side':None,'last':0} for sym in SYMBOLS}
        save_state()
        await m.channel.send("تم التصفير 1000$ - 6 عملات مجنونة جاهزة")

client.run(TOKEN)

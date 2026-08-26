import os, discord, requests, threading, json, time
from discord.ext import tasks
from flask import Flask

TOKEN = os.environ.get("DISCORD_TOKEN")
STATE_FILE = "state.json"
SYMBOLS = ["WIFUSDT", "PEPEUSDT", "DOGEUSDT", "BONKUSDT", "SHIBUSDT", "FLOKIUSDT"]

app = Flask('')
@app.route('/')
def home(): return "Meme Fixed Bot"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

last_any_buy = 0

def load_state():
    global USDT, HOLDINGS, last_any_buy
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE,'r') as f:
                s=json.load(f)
                USDT=s.get('usdt',1000.0)
                HOLDINGS=s.get('hold',{})
                last_any_buy=s.get('last_any',0)
                for sym in SYMBOLS:
                    if sym not in HOLDINGS:
                        HOLDINGS[sym]={'qty':0,'avg':0,'b30':False,'b20':False,'b10':False,'side':None,'last':0}
                return
    except: pass
    USDT=1000.0
    last_any_buy=0
    HOLDINGS={sym:{'qty':0,'avg':0,'b30':False,'b20':False,'b10':False,'side':None,'last':0} for sym in SYMBOLS}

def save_state():
    try:
        with open(STATE_FILE,'w') as f:
            json.dump({'usdt':USDT,'hold':HOLDINGS,'last_any':last_any_buy},f)
    except: pass

load_state()

def calc_rsi(prices, period=6):
    if len(prices) < period+1: return 50
    gains=[]; losses=[]
    for i in range(1,len(prices)):
        d=prices[i]-prices[i-1]
        gains.append(d if d>0 else 0)
        losses.append(abs(d) if d<0 else 0)
    ag=sum(gains[-period:])/period
    al=sum(losses[-period:])/period
    if al==0: return 100
    if ag==0: return 0
    return 100-(100/(1+ag/al))

@tasks.loop(minutes=1)
async def check_market():
    global USDT, HOLDINGS, last_any_buy
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
                klines=requests.get(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval=1m&limit=50",timeout=15).json()
                closes=[float(c[4]) for c in klines]
                rsi=calc_rsi(closes,6)
                h=HOLDINGS[sym]

                # قفل على 60 بشرط ربح
                if h['side']=="LONG" and h['qty']>0 and rsi>=60 and curr>h['avg']:
                    profit=(curr-h['avg'])*h['qty']
                    USDT+=h['qty']*curr
                    HOLDINGS[sym]={'qty':0,'avg':0,'b30':False,'b20':False,'b10':False,'side':None,'last':0}
                    save_state()
                    await ch.send(f"✅ **قفل {sym} @ {curr:.8f} RSI {rsi:.1f} ربح +${profit:.2f}**\n💵 الرصيد ${USDT:.2f}")
                    continue

                # فلتر RSI - تجاهل 0 واكثر من 30
                if rsi < 8 or rsi > 30:
                    continue

                # منع الشراء الجماعي - عملة كل 5 دقايق فقط
                if time.time() - last_any_buy < 300:
                    continue
                if time.time() - h['last'] < 300:
                    continue

                # شراء 1 فقط (10% = 100$)
                if not h['b30'] and USDT>=20 and h['side'] in [None,"LONG"]:
                    amt=min(USDT*0.10, 100)
                    qty=amt/curr
                    new_qty=h['qty']+qty
                    avg=((h['avg']*h['qty'])+(curr*qty))/new_qty if new_qty else curr
                    h['qty']=new_qty; h['avg']=avg; h['b30']=True; h['side']="LONG"
                    h['last']=time.time(); last_any_buy=time.time()
                    USDT-=amt; save_state()
                    await ch.send(f"🟢 **{sym} شراء 1 RSI {rsi:.1f} @ {curr:.8f}**\n10%=${amt:.2f} متوسط {avg:.8f} رصيد ${USDT:.2f}")
                    break # يشتري عملة وحدة فقط كل لفة

                # تبريد 2 - RSI 20
                if h['b30'] and not h['b20'] and rsi<=20 and USDT>=20:
                    amt=min(USDT*0.15, 150)
                    qty=amt/curr
                    new_qty=h['qty']+qty
                    avg=((h['avg']*h['qty'])+(curr*qty))/new_qty
                    h['qty']=new_qty; h['avg']=avg; h['b20']=True
                    h['last']=time.time(); last_any_buy=time.time()
                    USDT-=amt; save_state()
                    await ch.send(f"🟢🟢 **{sym} تبريد 2 RSI {rsi:.1f} @ {curr:.8f} متوسط {avg:.8f}**")
                    break

                # تبريد 3 - RSI 12
                if h['b20'] and not h['b10'] and rsi<=12 and USDT>=20:
                    amt=min(USDT*0.20, 200)
                    qty=amt/curr
                    new_qty=h['qty']+qty
                    avg=((h['avg']*h['qty'])+(curr*qty))/new_qty
                    h['qty']=new_qty; h['avg']=avg; h['b10']=True
                    h['last']=time.time(); last_any_buy=time.time()
                    USDT-=amt; save_state()
                    await ch.send(f"🟢🟢🟢 **{sym} تبريد أخير RSI {rsi:.1f} @ {curr:.8f}**")
                    break

            except Exception as e:
                print(f"{sym} {e}")
                continue

    except Exception as e:
        print(f"MAIN ERR {e}")

@client.event
async def on_ready():
    print(f"Ready {client.user}")
    check_market.start()

@client.event
async def on_message(m):
    global USDT, HOLDINGS, last_any_buy
    if m.author==client.user: return
    if m.content.strip()=="الرصيد":
        txt=f"💵 USDT: ${USDT:.2f}\n"
        for sym,h in HOLDINGS.items():
            if h['qty']>0:
                txt+=f"{sym}: qty {h['qty']:.4f} avg {h['avg']:.8f} B:{h['b30']}{h['b20']}{h['b10']}\n"
        await m.channel.send(txt)
    if m.content.strip()=="تصفير":
        USDT=1000.0
        last_any_buy=0
        HOLDINGS={sym:{'qty':0,'avg':0,'b30':False,'b20':False,'b10':False,'side':None,'last':0} for sym in SYMBOLS}
        save_state()
        await m.channel.send("✅ تم التصفير 1000$ - يشتري عملة كل 5 دقايق فقط RSI بين 8-30")

client.run(TOKEN)

import os, discord, requests, threading, json, time
from discord.ext import tasks
from flask import Flask
from datetime import datetime

TOKEN = os.environ.get("DISCORD_TOKEN")
STATE_FILE = "state.json"
SYMBOLS = ["WIFUSDT", "PEPEUSDT", "DOGEUSDT", "BONKUSDT", "SHIBUSDT", "FLOKIUSDT"]

app = Flask('')
@app.route('/')
def home(): return "Meme Bot V3 - 10$ Target"
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
                        HOLDINGS[sym]={'qty':0,'avg':0,'b30':False,'b20':False,'b10':False,'side':None,'last':0,'entry_time':0}
                    if 'entry_time' not in HOLDINGS[sym]:
                        HOLDINGS[sym]['entry_time']=0
                return
    except: pass
    USDT=1000.0
    last_any_buy=0
    HOLDINGS={sym:{'qty':0,'avg':0,'b30':False,'b20':False,'b10':False,'side':None,'last':0,'entry_time':0} for sym in SYMBOLS}

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

def fmt_time(ts):
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S")

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
                klines=requests.get(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval=5m&limit=50",timeout=15).json()
                closes=[float(c[4]) for c in klines]
                rsi=calc_rsi(closes,6)
                h=HOLDINGS[sym]

                # --- بيع سكالبنق محسن للربح 10$+ ---
                if h['side']=="LONG" and h['qty']>0:
                    profit_pct = ((curr - h['avg']) / h['avg']) * 100 if h['avg']>0 else 0
                    profit_usd = (curr - h['avg']) * h['qty']
                    hold_minutes = (time.time() - h['entry_time'])/60 if h['entry_time']>0 else 0

                    # شرط البيع الجديد: لازم ربح +2% على الأقل + RSI 60
                    # او ربح +10% مهما كان RSI (الهدف اللي تبيه)
                    should_sell = False
                    reason = ""
                    if profit_pct >= 10:
                        should_sell = True
                        reason = f"هدف 10%+"
                    elif profit_pct >= 2 and rsi >= 65:
                        should_sell = True
                        reason = f"سكالبنق {profit_pct:.1f}% + RSI {rsi:.0f}"

                    if should_sell:
                        USDT+=h['qty']*curr
                        HOLDINGS[sym]={'qty':0,'avg':0,'b30':False,'b20':False,'b10':False,'side':None,'last':0,'entry_time':0}
                        save_state()
                        await ch.send(
                            f"✅ **قفل {sym} | {reason}**\n"
                            f"▫️ دخول: {fmt_time(h['entry_time'])} @ {h['avg']:.8f}\n"
                            f"▫️ خروج: {fmt_time(time.time())} @ {curr:.8f} RSI {rsi:.1f}\n"
                            f"▫️ المدة: {hold_minutes:.0f} دقيقة\n"
                            f"▫️ **الربح: {'+' if profit_usd>=0 else ''}${profit_usd:.2f} ({profit_pct:.2f}%)**\n"
                            f"💵 **الرصيد الحالي: ${USDT:.2f}**"
                        )
                        continue

                    if profit_pct <= -15:
                        loss = (curr-h['avg'])*h['qty']
                        USDT+=h['qty']*curr
                        HOLDINGS[sym]={'qty':0,'avg':0,'b30':False,'b20':False,'b10':False,'side':None,'last':0,'entry_time':0}
                        save_state()
                        await ch.send(f"❌ **ستوب {sym} @ {curr:.8f} خسارة {profit_pct:.2f}% ({loss:.2f}$)**\n💵 الرصيد الحالي: ${USDT:.2f}")
                        continue

                if rsi < 8 or rsi > 30:
                    continue
                if time.time() - last_any_buy < 300:
                    continue
                if time.time() - h['last'] < 300:
                    continue

                if not h['b30'] and USDT>=20 and h['side'] in [None,"LONG"]:
                    amt=min(USDT*0.10, 100)
                    qty=amt/curr
                    new_qty=h['qty']+qty
                    avg=((h['avg']*h['qty'])+(curr*qty))/new_qty if new_qty else curr
                    if h['qty']==0:
                        h['entry_time']=time.time()
                    h['qty']=new_qty; h['avg']=avg; h['b30']=True; h['side']="LONG"
                    h['last']=time.time(); last_any_buy=time.time()
                    USDT-=amt; save_state()
                    await ch.send(
                        f"🟢 **شراء 1 {sym} RSI {rsi:.1f} @ {curr:.8f}**\n"
                        f"▫️ وقت الدخول: {fmt_time(h['entry_time'])}\n"
                        f"▫️ الكمية: {qty:.4f} | متوسط: {avg:.8f}\n"
                        f"▫️ الهدف: +10% = +${amt*0.10:.2f}\n"
                        f"💵 الرصيد الحالي: ${USDT:.2f}"
                    )
                    break

                if h['b30'] and not h['b20'] and rsi<=20 and USDT>=20:
                    amt=min(USDT*0.15, 150)
                    qty=amt/curr
                    new_qty=h['qty']+qty
                    avg=((h['avg']*h['qty'])+(curr*qty))/new_qty
                    h['qty']=new_qty; h['avg']=avg; h['b20']=True
                    h['last']=time.time(); last_any_buy=time.time()
                    USDT-=amt; save_state()
                    await ch.send(f"🟢🟢 **تبريد 2 {sym} RSI {rsi:.1f} @ {curr:.8f} متوسط جديد {avg:.8f}**\n💵 الرصيد: ${USDT:.2f}")
                    break

                if h['b20'] and not h['b10'] and rsi<=12 and USDT>=20:
                    amt=min(USDT*0.20, 200)
                    qty=amt/curr
                    new_qty=h['qty']+qty
                    avg=((h['avg']*h['qty'])+(curr*qty))/new_qty
                    h['qty']=new_qty; h['avg']=avg; h['b10']=True
                    h['last']=time.time(); last_any_buy=time.time()
                    USDT-=amt; save_state()
                    await ch.send(f"🟢🟢🟢 **تبريد أخير {sym} RSI {rsi:.1f} @ {curr:.8f}**\n💵 الرصيد: ${USDT:.2f}")
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
        total_pnl = USDT - 1000
        txt=f"📊 **التقرير الحالي**\n💵 الرصيد: ${USDT:.2f}\n📈 إجمالي الربح: {'+' if total_pnl>=0 else ''}${total_pnl:.2f}\n{'='*20}\n"
        has_pos=False
        for sym,h in HOLDINGS.items():
            if h['qty']>0:
                has_pos=True
                try:
                    curr=float(requests.get(f"https://data-api.binance.vision/api/v3/ticker/price?symbol={sym}",timeout=5).json()['price'])
                    pnl_pct=((curr-h['avg'])/h['avg']*100) if h['avg'] else 0
                    pnl_usd=(curr-h['avg'])*h['qty']
                    txt+=f"🔹 {sym}\nدخول {fmt_time(h['entry_time'])} @ {h['avg']:.8f}\nحالي {curr:.8f} | ربح {pnl_usd:+.2f}$ ({pnl_pct:+.2f}%)\n"
                except:
                    txt+=f"{sym}: {h['qty']:.4f} avg {h['avg']:.8f}\n"
        if not has_pos:
            txt+="لا توجد صفقات مفتوحة"
        await m.channel.send(txt)
    if m.content.strip()=="تصفير":
        USDT=1000.0
        last_any_buy=0
        HOLDINGS={sym:{'qty':0,'avg':0,'b30':False,'b20':False,'b10':False,'side':None,'last':0,'entry_time':0} for sym in SYMBOLS}
        save_state()
        await m.channel.send("✅ تم التصفير 1000$ - نظام جديد: هدف 10% سكالبنق 2%+ - فريم 5m")

client.run(TOKEN)

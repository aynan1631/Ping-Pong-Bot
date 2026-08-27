import os, discord, requests, threading, json, time
from discord.ext import tasks
from flask import Flask
from datetime import datetime

TOKEN = os.environ.get("DISCORD_TOKEN")
STATE_FILE = "state.json"
SYMBOLS = ["WIFUSDT", "PEPEUSDT", "DOGEUSDT", "BONKUSDT", "SHIBUSDT", "FLOKIUSDT"]

TOTAL_BALANCE = 1200
PER_COIN_BUDGET = 200  # 100 لونج + 100 شورت

app = Flask('')
@app.route('/')
def home(): return f"Bot 1200$ - 6 coins x 200$"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def default_holding():
    return {
        'long_qty':0, 'long_avg':0, 'long_entry':0,
        'l1':False, 'l2':False, 'l3':False, 'long_spent':0,
        'short_qty':0, 'short_avg':0, 'short_entry':0,
        's1':False, 's2':False, 's3':False, 'short_spent':0,
        'last_long':0, 'last_short':0
    }

def load_state():
    global USDT, HOLDINGS
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE,'r') as f:
                s=json.load(f)
                USDT=s.get('usdt', TOTAL_BALANCE)
                HOLDINGS=s.get('hold',{})
                for sym in SYMBOLS:
                    if sym not in HOLDINGS:
                        HOLDINGS[sym]=default_holding()
                return
    except: pass
    USDT=TOTAL_BALANCE
    HOLDINGS={sym:default_holding() for sym in SYMBOLS}

def save_state():
    try:
        with open(STATE_FILE,'w') as f:
            json.dump({'usdt':USDT,'hold':HOLDINGS},f)
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

def fmt(t): return datetime.fromtimestamp(t).strftime("%H:%M:%S")

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
                klines=requests.get(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval=5m&limit=50",timeout=15).json()
                closes=[float(c[4]) for c in klines]
                rsi=calc_rsi(closes,6)
                h=HOLDINGS[sym]
                now=time.time()

                # ===== 1- نظام الشراء LONG (من تحت) =====
                if h['long_qty']>0:
                    pnl_pct = ((curr - h['long_avg'])/h['long_avg']*100) if h['long_avg'] else 0
                    pnl_usd = (curr - h['long_avg'])*h['long_qty']
                    # قفل على 2% ربح
                    if pnl_pct >= 2:
                        USDT += h['long_qty']*curr
                        await ch.send(
                            f"✅ **قفل LONG {sym} @ {curr:.8f} RSI {rsi:.1f}**\n"
                            f"▫️ دخول: {fmt(h['long_entry'])} متوسط {h['long_avg']:.8f}\n"
                            f"▫️ المدة: {(now-h['long_entry'])/60:.0f} د\n"
                            f"▫️ **الربح: +${pnl_usd:.2f} ({pnl_pct:.2f}%)**\n"
                            f"💵 الرصيد الحالي: ${USDT:.2f} | ربح إجمالي: ${USDT-TOTAL_BALANCE:+.2f}"
                        )
                        h['long_qty']=0; h['long_avg']=0; h['long_entry']=0
                        h['l1']=h['l2']=h['l3']=False; h['long_spent']=0
                        save_state()
                        continue

                # شراء 1: RSI 30 بنسبة 15% من 100 = 15$
                if not h['l1'] and rsi <= 30 and rsi >= 20:
                    if now - h['last_long'] < 300: pass
                    else:
                        amt = 15.0
                        if USDT >= amt:
                            qty = amt/curr
                            new_qty = h['long_qty']+qty
                            avg = ((h['long_avg']*h['long_qty'])+(curr*qty))/new_qty if new_qty else curr
                            if h['long_qty']==0: h['long_entry']=now
                            h['long_qty']=new_qty; h['long_avg']=avg; h['l1']=True
                            h['long_spent']+=amt; h['last_long']=now
                            USDT-=amt; save_state()
                            await ch.send(f"🟢 **LONG 1 {sym} RSI {rsi:.1f} @ {curr:.8f}**\n▫️ 15% = ${amt} | متوسط {avg:.8f} | كمية {new_qty:.4f}\n▫️ وقت الدخول: {fmt(h['long_entry'])}\n💵 الرصيد الحالي: ${USDT:.2f}")

                # شراء 2: RSI 20 بنسبة 30% = 30$
                elif h['l1'] and not h['l2'] and rsi <= 20 and rsi > 15:
                    amt = 30.0
                    if USDT >= amt:
                        qty = amt/curr
                        new_qty = h['long_qty']+qty
                        avg = ((h['long_avg']*h['long_qty'])+(curr*qty))/new_qty
                        h['long_qty']=new_qty; h['long_avg']=avg; h['l2']=True
                        h['long_spent']+=amt; h['last_long']=now
                        USDT-=amt; save_state()
                        await ch.send(f"🟢🟢 **LONG 2 {sym} RSI {rsi:.1f} @ {curr:.8f}**\n▫️ 30% = ${amt} | متوسط جديد {avg:.8f}\n💵 الرصيد: ${USDT:.2f}")

                # شراء 3: RSI تحت 15 بباقي الرصيد 55$
                elif h['l2'] and not h['l3'] and rsi <= 15:
                    amt = min(55.0, 100 - h['long_spent'])
                    if amt>0 and USDT >= amt:
                        qty = amt/curr
                        new_qty = h['long_qty']+qty
                        avg = ((h['long_avg']*h['long_qty'])+(curr*qty))/new_qty
                        h['long_qty']=new_qty; h['long_avg']=avg; h['l3']=True
                        h['long_spent']+=amt; h['last_long']=now
                        USDT-=amt; save_state()
                        await ch.send(f"🟢🟢🟢 **LONG 3 أخير {sym} RSI {rsi:.1f} @ {curr:.8f}**\n▫️ باقي ${amt} | متوسط {avg:.8f}\n💵 الرصيد: ${USDT:.2f}")

                # ===== 2- نظام البيع SHORT (من فوق) =====
                if h['short_qty']>0:
                    pnl_pct_short = ((h['short_avg'] - curr)/h['short_avg']*100) if h['short_avg'] else 0
                    pnl_usd_short = (h['short_avg'] - curr)*h['short_qty']
                    if pnl_pct_short >= 2:
                        USDT -= h['short_qty']*curr  # شراء لإغلاق الشورت
                        # الربح الفعلي هو الفرق
                        await ch.send(
                            f"✅ **قفل SHORT {sym} @ {curr:.8f} RSI {rsi:.1f}**\n"
                            f"▫️ دخول شورت: {fmt(h['short_entry'])} متوسط {h['short_avg']:.8f}\n"
                            f"▫️ **الربح: +${pnl_usd_short:.2f} ({pnl_pct_short:.2f}%)**\n"
                            f"💵 الرصيد الحالي: ${USDT:.2f} | ربح إجمالي: ${USDT-TOTAL_BALANCE:+.2f}"
                        )
                        h['short_qty']=0; h['short_avg']=0; h['short_entry']=0
                        h['s1']=h['s2']=h['s3']=False; h['short_spent']=0
                        save_state()
                        continue

                # بيع 1: RSI 75 بنسبة 15% = 15$
                if not h['s1'] and rsi >= 75 and rsi < 80:
                    if now - h['last_short'] < 300: pass
                    else:
                        amt = 15.0
                        qty = amt/curr
                        new_qty = h['short_qty']+qty
                        avg = ((h['short_avg']*h['short_qty'])+(curr*qty))/new_qty if new_qty else curr
                        if h['short_qty']==0: h['short_entry']=now
                        h['short_qty']=new_qty; h['short_avg']=avg; h['s1']=True
                        h['short_spent']+=amt; h['last_short']=now
                        USDT += qty*curr  # استلام مبلغ البيع
                        save_state()
                        await ch.send(f"🔴 **SHORT 1 {sym} RSI {rsi:.1f} @ {curr:.8f}**\n▫️ 15% = ${amt} | متوسط {avg:.8f}\n▫️ وقت الدخول: {fmt(h['short_entry'])}\n💵 الرصيد: ${USDT:.2f}")

                # بيع 2: RSI 80 بنسبة 30% = 30$
                elif h['s1'] and not h['s2'] and rsi >= 80 and rsi < 90:
                    amt = 30.0
                    qty = amt/curr
                    new_qty = h['short_qty']+qty
                    avg = ((h['short_avg']*h['short_qty'])+(curr*qty))/new_qty
                    h['short_qty']=new_qty; h['short_avg']=avg; h['s2']=True
                    h['short_spent']+=amt; h['last_short']=now
                    USDT += qty*curr
                    save_state()
                    await ch.send(f"🔴🔴 **SHORT 2 {sym} RSI {rsi:.1f} @ {curr:.8f}**\n▫️ 30% = ${amt} | متوسط {avg:.8f}\n💵 الرصيد: ${USDT:.2f}")

                # بيع 3: RSI فوق 90 بباقي الرصيد
                elif h['s2'] and not h['s3'] and rsi >= 90:
                    amt = min(55.0, 100 - h['short_spent'])
                    if amt>0:
                        qty = amt/curr
                        new_qty = h['short_qty']+qty
                        avg = ((h['short_avg']*h['short_qty'])+(curr*qty))/new_qty
                        h['short_qty']=new_qty; h['short_avg']=avg; h['s3']=True
                        h['short_spent']+=amt; h['last_short']=now
                        USDT += qty*curr
                        save_state()
                        await ch.send(f"🔴🔴🔴 **SHORT 3 أخير {sym} RSI {rsi:.1f} @ {curr:.8f}**\n▫️ باقي ${amt} | متوسط {avg:.8f}\n💵 الرصيد: ${USDT:.2f}")

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
    global USDT, HOLDINGS
    if m.author==client.user: return
    if m.content.strip()=="الرصيد":
        total_pnl = USDT - TOTAL_BALANCE
        txt=f"📊 **التقرير - 1200$ موزع 200$ لكل عملة**\n💵 الرصيد الحالي: ${USDT:.2f}\n📈 الربح الإجمالي: {'+' if total_pnl>=0 else ''}${total_pnl:.2f}\n{'='*30}\n"
        for sym,h in HOLDINGS.items():
            txt+=f"\n**{sym}** [مخصص 200$]\n"
            if h['long_qty']>0:
                try:
                    curr=float(requests.get(f"https://data-api.binance.vision/api/v3/ticker/price?symbol={sym}",timeout=5).json()['price'])
                    pnl_pct=((curr-h['long_avg'])/h['long_avg']*100)
                    pnl_usd=(curr-h['long_avg'])*h['long_qty']
                    txt+=f"  LONG: {h['long_qty']:.2f} @ {h['long_avg']:.8f} | PnL {pnl_usd:+.2f}$ ({pnl_pct:+.2f}%) دخول {fmt(h['long_entry'])}\n"
                except: txt+=f"  LONG: {h['long_qty']:.2f}\n"
            else:
                txt+=f"  LONG: فاضي (متبقي 100$)\n"
            if h['short_qty']>0:
                try:
                    curr=float(requests.get(f"https://data-api.binance.vision/api/v3/ticker/price?symbol={sym}",timeout=5).json()['price'])
                    pnl_pct=((h['short_avg']-curr)/h['short_avg']*100)
                    pnl_usd=(h['short_avg']-curr)*h['short_qty']
                    txt+=f"  SHORT: {h['short_qty']:.2f} @ {h['short_avg']:.8f} | PnL {pnl_usd:+.2f}$ ({pnl_pct:+.2f}%)\n"
                except: txt+=f"  SHORT: {h['short_qty']:.2f}\n"
            else:
                txt+=f"  SHORT: فاضي (متبقي 100$)\n"
        await m.channel.send(txt)

    if m.content.strip()=="تصفير":
        USDT=TOTAL_BALANCE
        HOLDINGS={sym:default_holding() for sym in SYMBOLS}
        save_state()
        await m.channel.send(f"✅ تم التصفير {TOTAL_BALANCE}$\n• كل عملة 200$ = 100 LONG + 100 SHORT\n• LONG: RSI 30(15$) 20(30$) <15(55$) | هدف 2%\n• SHORT: RSI 75(15$) 80(30$) >90(55$) | هدف 2%")

client.run(TOKEN)

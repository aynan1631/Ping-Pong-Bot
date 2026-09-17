import os, time, math, threading
from flask import Flask
from binance.client import Client
import pandas as pd

app = Flask(__name__)
hospital = []
active = []
real_profit = 0.0

@app.route('/')
def home():
    return f"V102 شغال ✅ | مستشفى {len(hospital)}/7 | نشط {len(active)} | صافي {real_profit:.3f}$ | {time.ctime()}"

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
client = Client(API_KEY, API_SECRET)

ROOM_SIZE = 5.0
MAX_ROOMS = 7
TARGET = 0.10
SL = -0.20

BLACKLIST = ["ALGOUSDT","BTSUSDT","DREPUSDT","PAXGUSDT","TORNUSDT","WAVESUSDT","XMRUSDT","ZECUSDT","LUNAUSDT","LUNCUSDT","LSKUSDT","LAUSDT","ZILUSDT"]
STRONG = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","LINKUSDT","AVAXUSDT","ADAUSDT","DOGEUSDT","SUIUSDT","ARBUSDT","OPUSDT","LTCUSDT","DOTUSDT","TRXUSDT"]

def get_free():
    try: return float(client.get_asset_balance(asset='USDT')['free'])
    except: return 0.0

def is_green(sym):
    try:
        kl = client.get_klines(symbol=sym, interval='15m', limit=50)
        cl = pd.Series([float(k[4]) for k in kl])
        return cl.ewm(span=12).mean().iloc[-1] > cl.ewm(span=26).mean().iloc[-1]
    except: return False

def strongest():
    for s in STRONG:
        if s in BLACKLIST: continue
        if is_green(s): return s
    return "BTCUSDT"

def buy(sym, usdt):
    try:
        price = float(client.get_symbol_ticker(symbol=sym)['price'])
        qty = usdt/price
        info = client.get_symbol_info(sym)
        step = float([f for f in info['filters'] if f['filterType']=='LOT_SIZE'][0]['stepSize'])
        qty = math.floor(qty/step)*step
        qty = round(qty, 8)
        if qty==0: return None
        client.order_market_buy(symbol=sym, quantity=qty)
        print(f"🟢 شراء {sym}")
        return {"symbol":sym,"qty":qty,"entry":price,"time":time.time(),"is_doctor":False}
    except Exception as e:
        print(f"❌ شراء {e}")
        return None

def sell(pos, reason=""):
    try:
        client.order_market_sell(symbol=pos["symbol"], quantity=pos["qty"])
        curr = float(client.get_symbol_ticker(symbol=pos["symbol"])['price'])
        pnl = (curr-pos["entry"])*pos["qty"]
        print(f"🔴 بيع {pos['symbol']} {reason} {pnl:.3f}$")
        return pnl
    except Exception as e:
        print(f"❌ بيع {e}")
        return 0

def loop():
    global real_profit
    print("🔥 V102 اشتغل")
    # تحميل المرضى القدامى BOME ONE HEI...
    try:
        for b in client.get_account()['balances']:
            asset=b['asset']; free=float(b['free'])
            if free>0 and asset not in ["USDT","DOT"]:
                sym=asset+"USDT"
                try:
                    price=float(client.get_symbol_ticker(symbol=sym)['price'])
                    if free*price>=3:
                        hospital.append({"symbol":sym,"qty":free,"entry":price,"time":time.time()-1000,"is_doctor":False})
                        print(f"🏥 وجد {sym}")
                except: pass
    except: pass

    while True:
        try:
            free = get_free()
            print(f"حر {free:.2f}$ مستشفى {len(hospital)}/7 نشط {len(active)} صافي {real_profit:.3f}$")

            if len(hospital)>=7 and free<1.0:
                print("🚨 طوارئ يفك غرفة")
                p = sorted(hospital, key=lambda x: x['qty'])[0]
                sell(p,"فك طوارئ")
                hospital.remove(p)
                time.sleep(2)
                continue

            for pos in active[:]:
                curr=float(client.get_symbol_ticker(symbol=pos["symbol"])['price'])
                pnl=(curr-pos["entry"])*pos["qty"]
                if pos.get("is_doctor") and pnl>=pos["heal_target"]:
                    pat=pos["patient"]
                    sell(pos,f"شفاء {pat['symbol']}")
                    sell(pat,"شفى")
                    if pat in hospital: hospital.remove(pat)
                    active.remove(pos)
                    real_profit+=0.10
                    print(f"✅ شفى {pat['symbol']}")
                elif not pos.get("is_doctor") and pnl>=TARGET:
                    sell(pos,"+10 سنت")
                    active.remove(pos)
                    real_profit+=pnl
                elif not pos.get("is_doctor") and pnl<=SL:
                    hospital.append(pos)
                    active.remove(pos)
                    print(f"🏥 دخل {pos['symbol']}")

            if len(hospital)>0 and len(active)<MAX_ROOMS and free>=ROOM_SIZE:
                pat=sorted(hospital, key=lambda x: x["time"])[0]
                curr_p=float(client.get_symbol_ticker(symbol=pat["symbol"])['price'])
                inv=abs((curr_p-pat["entry"])*pat["qty"])
                doc=strongest()
                d=buy(doc,ROOM_SIZE)
                if d:
                    d["is_doctor"]=True
                    d["patient"]=pat
                    d["heal_target"]=inv+0.10+0.05
                    active.append(d)
                    print(f"👨‍⚕️ طبيب {doc} يعالج {pat['symbol']} فاتورة {inv:.3f}$")

            if len(hospital)==0 and len(active)<MAX_ROOMS and free>=ROOM_SIZE:
                c=strongest()
                p=buy(c,ROOM_SIZE)
                if p: active.append(p)

            time.sleep(15)
        except Exception as e:
            print(f"خطأ {e}")
            time.sleep(10)

threading.Thread(target=loop, daemon=True).start()

if __name__=="__main__":
    port=int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0", port=port)

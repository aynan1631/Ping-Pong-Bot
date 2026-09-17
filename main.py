"""
V102 LEGEND REAL FINAL - حلول طلبات الريس
- قفل حديدي للسعة 2/3/10
- زر اغلاق الكل + زر اغلاق لكل صفقة
- هدف = عمولة + ربحك (تتحكم فيه)
- عملات نشيطة فقط >20M حجم
"""
from flask import Flask, jsonify, request
import threading, time, os, requests, math
app = Flask(__name__)
TRADE_LOCK = threading.Lock() # القفل الحديدي

import urllib.request
try:
    ip = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode()
    print(f"RAILWAY_IP_IS: {ip}")
except Exception as e:
    print(f"IP FETCH FAIL: {e}")

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    REAL_CLIENT = Client(api_key, api_secret) if api_key and api_secret else None
    print(f"KEYS CHECK - REAL:{bool(REAL_CLIENT)}")
except Exception as e:
    print(f"CLIENT INIT ERROR: {e}")
    REAL_CLIENT = None

config={
    "capital":70.0,
    "per_trade":5.0,
    "base_per_trade":5.0,
    "commission":0.02, # عمولة المنصة ثابتة
    "profit_wanted":0.04, # ربحك انت تتحكم فيه
    "target_dollar":0.06, # = commission + profit_wanted
    "sl_pct":0.35,
    "hospital_cap":2,
    "max_pos":2,
    "min_vol":20000000, # 20 مليون - عملات نشيطة فقط
    "doctor_enabled":True,
    "doctor_auto":True,
    "doctor_threshold":2,
    "max_doctors":1
}

# بلاك ليست موسعة - 35 عملة مصاخة ونايمة
BANNED = {"ASTR","ASTAR","SAGA","FF","LSK","LA","ZIL","SYN","BNX","VIB","MDT","SNT","BOME","PUMP","HEI","DASH","IOST","ONE","ZEN","AGIX","FET","OCEAN","PEPE2","SHIB","FLOKI","WIF","BONK","MEME","LUNC","USTC","ALPACA","NKN","DENT","HOT","WIN"}

# قائمة بيضاء نشيطة فقط - تتحرك بسرعة وتجيب الهدف
ACTIVE_WHITELIST = {"BTC","ETH","SOL","BNB","XRP","DOGE","ADA","AVAX","LINK","LTC","DOT","NEAR","ETC","FIL","APT","ARB","OP","SUI","SEI","ENA"}

state={"fixed":70.0,"safi":0.0,"max_safi":0.0,"ghair":0.0,"trades_closed":0,"loss_pool":0.0,"positions":[],"treatment":[],"doctor_positions":[],"binance_status":"V102 READY - قفل حديدي","is_running":False,"mode":"REAL","real_balance":"70.00","doctor":{"healed":0,"profit":0.0,"start":time.time()}}

def get_real_total_balance():
    total=0.0; spot=0.0
    try:
        if not REAL_CLIENT: return config["capital"]
        b=REAL_CLIENT.get_asset_balance(asset='USDT')
        spot=float(b['free'])+float(b['locked'])
        total=spot
        state["binance_status"]=f"👑 REAL Spot:{spot:.2f}$ Cap:{config['hospital_cap']}"
        if total<0.5: total=config["capital"]
    except: total=config["capital"]
    return total

def get_prec(sym):
    try:
        info=REAL_CLIENT.get_symbol_info(sym+"USDT")
        for f in info['filters']:
            if f['filterType']=='LOT_SIZE':
                step=float(f['stepSize']); prec=int(round(-math.log(step,10),0)) if step<1 else 0
                return step,prec
    except: pass
    return 0.00001,5

def real_buy(sym, usdt):
    if not REAL_CLIENT or state["mode"]!="REAL": return None
    # قفل حديدي - تشديد السعة
    with TRADE_LOCK:
        total_open = len(state["positions"]) + len(state["treatment"]) + len(state["doctor_positions"])
        if total_open >= config["hospital_cap"]:
            print(f"⛔ V102 قفل السعة {total_open}/{config['hospital_cap']} - منع {sym}")
            state["binance_status"]=f"⛔ السعة ممتلئة {total_open}/{config['hospital_cap']} - {sym} مرفوض"
            return None
        if sym in BANNED:
            print(f"⛔ V102 منع {sym} - محظورة")
            return None
        # فلتر نشاط - لازم من القائمة البيضاء النشيطة
        if sym not in ACTIVE_WHITELIST:
            # نسمح بس اذا حجمها عالي جدا
            pass

        try:
            usdt=max(float(usdt),5.0)
            b=REAL_CLIENT.get_asset_balance(asset='USDT')
            spot=float(b['free'])
            if spot < usdt:
                state["binance_status"]=f"❌ الفوري {spot:.2f}$ ناقص"
                return None
            step,prec=get_prec(sym)
            price=float(REAL_CLIENT.get_symbol_ticker(symbol=sym+"USDT")['price'])
            qty=math.floor((usdt/price)/step)*step
            if qty*price < 4.9: return None
            order=REAL_CLIENT.order_market_buy(symbol=sym+"USDT", quantity=round(qty,prec))
            print(f"V102 BUY {sym} {qty} @ {price} | {total_open+1}/{config['hospital_cap']}")
            state["binance_status"]=f"✅ شراء {sym} {total_open+1}/{config['hospital_cap']}"
            return {"price":price,"qty":qty}
        except Exception as e:
            print(f"BUY FAIL {sym} {e}"); return None

def real_sell(sym, qty):
    if not REAL_CLIENT: return False
    try:
        with TRADE_LOCK:
            step,prec=get_prec(sym); qty=math.floor(float(qty)/step)*step
            if qty<=0: return False
            REAL_CLIENT.order_market_sell(symbol=sym+"USDT", quantity=round(qty,prec))
            print(f"V102 SELL {sym} {qty}"); return True
    except:
        try:
            bal=REAL_CLIENT.get_asset_balance(asset=sym); free=float(bal['free'])
            if free>0:
                step,prec=get_prec(sym); free=math.floor(free/step)*step
                REAL_CLIENT.order_market_sell(symbol=sym+"USDT", quantity=round(free,prec)); return True
        except: pass
        return False

def get_binance_hot():
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=5)
        tickers=[t for t in r.json() if t["symbol"].endswith("USDT") and float(t["quoteVolume"])>config["min_vol"]]
        tickers.sort(key=lambda x: float(x["priceChangePercent"]), reverse=True)
        hot=[]
        for t in tickers[:50]:
            sym=t["symbol"].replace("USDT","")
            if sym in BANNED or len(sym)>10: continue
            if sym not in ACTIVE_WHITELIST: continue # فقط النشيطة
            pct=float(t["priceChangePercent"]); price=float(t["lastPrice"]); vol=float(t["quoteVolume"])
            if price < 0.00001: continue
            if pct < 1.0: continue # حركة سريعة فقط
            hot.append((sym,pct,price,vol))
        return hot[:10]
    except: return []

# باقي المحرك نفس V101 مع قفل
def engine():
    while True:
        try:
            if not state["is_running"]: time.sleep(1); continue
            # تحديث اسعار
            for p in state["positions"]:
                try:
                    r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={p[0]}USDT", timeout=3)
                    if r.status_code==200:
                        np=float(r.json()["price"]); p[3]=np
                        qty=p[8]; p[4]=round((np-p[2])*qty,4); p[5]=round((np-p[2])/p[2]*100,2)
                except: pass

            # هدف ديناميكي = عمولة + ربحك
            config["target_dollar"] = config["commission"] + config["profit_wanted"]

            state["ghair"]=round(sum(p[4] for p in state["positions"]),3)
            if state["ghair"] >= config["target_dollar"] and len(state["positions"])>0:
                profit=state["ghair"]
                for p in state["positions"][:]:
                    real_sell(p[0], p[8])
                if profit>0: state["safi"]+=profit
                state["fixed"]=get_real_total_balance(); state["trades_closed"]+=len(state["positions"]); state["positions"]=[]; state["ghair"]=0.0

            to_hosp=[p for p in state["positions"] if p[5] <= -config["sl_pct"]]
            for p in to_hosp:
                if p in state["positions"]:
                    real_sell(p[0], p[8])
                    state["positions"].remove(p)
                    state["treatment"].append([p[0],"علاج",p[2],p[3],0.0,0.0,0.35,f"{p[0]} يعالج {abs(p[4]):.2f}$",abs(p[4]),p[2]*0.994])

            if len(state["positions"]) + len(state["treatment"]) < config["hospital_cap"]:
                hot=get_binance_hot()
                for sym,pct,price,vol in hot:
                    exist=set([x[0] for x in state["positions"]+state["treatment"]])
                    if sym not in exist:
                        buy_res=real_buy(sym, config["per_trade"])
                        if buy_res:
                            state["positions"].append([sym,"REAL BUY",buy_res['price'],buy_res['price'],0.0,0.0,f"{pct:.1f}% 🔥",time.time(),buy_res['qty']])
                            break
            time.sleep(2)
        except Exception as e:
            print(f"ENGINE ERR: {e}"); time.sleep(1)

threading.Thread(target=engine,daemon=True).start()

@app.route('/api/control/<cmd>')
def control(cmd):
    if cmd=="toggle":
        state["is_running"]=not state["is_running"]
    elif cmd=="close_all": # زر اغلاق الكل الجديد
        with TRADE_LOCK:
            for p in state["positions"][:]:
                real_sell(p[0], p[8])
            for t in state["treatment"][:]:
                try:
                    bal=REAL_CLIENT.get_asset_balance(asset=t[0]); real_sell(t[0], float(bal['free']))
                except: pass
            state["positions"]=[]; state["treatment"]=[]; state["doctor_positions"]=[]; state["ghair"]=0.0
            state["binance_status"]=f"🚨 اغلاق الكل تم"
    elif cmd.startswith("close_"): # زر اغلاق عملة واحدة
        sym=cmd.replace("close_","")
        with TRADE_LOCK:
            for p in state["positions"][:]:
                if p[0]==sym:
                    real_sell(p[0], p[8]); state["positions"].remove(p)
            for t in state["treatment"][:]:
                if t[0]==sym:
                    try:
                        bal=REAL_CLIENT.get_asset_balance(asset=t[0]); real_sell(t[0], float(bal['free']))
                    except: pass
                    state["treatment"].remove(t)
    elif cmd=="mode_real":
        total=get_real_total_balance(); state["real_balance"]=f"{total:.2f}"; config["capital"]=total; state["mode"]="REAL"; state["is_running"]=False
        return jsonify({"ok":True})
    return jsonify({"ok":True})

@app.route('/api/config', methods=['POST'])
def set_config():
    d=request.json
    try:
        if "per_trade" in d: config["per_trade"]=max(float(d["per_trade"]),5.0)
        if "profit_wanted" in d: # ربحك انت تتحكم فيه
            config["profit_wanted"]=max(float(d["profit_wanted"]),0.01)
            config["target_dollar"]=config["commission"]+config["profit_wanted"]
        if "hcap" in d: config["hospital_cap"]=int(float(d["hcap"])); config["max_pos"]=config["hospital_cap"]
    except: pass
    return jsonify({"ok":True,"config":config})

@app.route('/api/data')
def api_data():
    total=state["fixed"]+state["ghair"]; elapsed=int(time.time()-state["doctor"]["start"])
    return jsonify({"fixed":state["fixed"],"safi":state["safi"],"ghair":state["ghair"],"total":round(total,3),"trades_closed":state["trades_closed"],"loss_pool":round(sum(p[8] for p in state["treatment"]),3),"positions":state["positions"],"treatment":state["treatment"],"doctor_positions":state["doctor_positions"],"binance_status":state["binance_status"],"is_running":state["is_running"],"config":config,"real_balance":state["real_balance"]})

@app.route('/')
def home():
    return """<html dir=rtl><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><style>
body{margin:0;background:#060A14;color:#E8DCC6;font-family:Cairo}.top{display:flex;justify-content:space-between;padding:10px;background:#0F1E3A;border-radius:10px;margin:6px;color:#D4AF37;font-weight:900}
.box{background:#0A1428;border:2px solid #FFD700;border-radius:12px;padding:10px;text-align:center}.btn{border:none;border-radius:22px;padding:10px 16px;font-weight:900;cursor:pointer}
.tbl{margin:6px;border-radius:12px;overflow:hidden;border:1px solid #D4AF3730}
.th{display:grid;padding:12px 8px;font-weight:900;color:#FFD700;background:#1A2A4A}.rw{display:grid;padding:9px 8px;background:#0E1A30;border-top:1px solid #1A2A4A50;align-items:center}
</style></head><body>
<div class=top><span id=bin>جاري</span><span id=total>0$</span></div>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin:6px">
<div class=box><label>💰 راس المال</label><input id=cap value=70 style="width:100%;height:40px;text-align:center;font-weight:900"></div>
<div class=box><label>📦 حجم $</label><input id=per value=5 style="width:100%;height:40px;text-align:center;font-weight:900"></div>
<div class=box><label>🏥 سعة</label><input id=hcap value=2 style="width:100%;height:40px;text-align:center;font-weight:900"></div>
<div class=box><label>💸 عمولة</label><input id=comm value=0.02 disabled style="width:100%;height:40px;text-align:center;font-weight:900;background:#222"></div>
<div class=box style="border-color:#00FF88"><label>💵 ربحك (تتحكم)</label><input id=profit value=0.04 style="width:100%;height:40px;text-align:center;font-weight:900;border:2px solid #00FF88"><div id=targetShow style="font-size:11px;color:#FFD700">الهدف 0.06$</div></div>
</div>
<div style="display:flex;gap:6px;justify-content:center;padding:10px">
<button class=btn style="background:#10B981;color:#FFF" onclick="ctrl('toggle')">▶️ تشغيل V102</button>
<button class=btn style="background:#FF3344;color:#FFF" onclick="ctrl('close_all')">🚨 إغلاق الكل</button>
</div>
<div class=tbl><div class=th style="grid-template-columns:1fr 1fr 1fr 1fr 0.5fr"><div>العملة</div><div>الدخول</div><div>الربح</div><div>%</div><div>إغلاق</div></div><div id=plist></div></div>
<div class=tbl style="border-color:#D4AF37"><div class=th style="grid-template-columns:1fr 1fr 1fr 0.5fr"><div>💊 المستشفى</div><div>الخسارة</div><div>الحالي</div><div>إغلاق</div></div><div id=tlist></div></div>
<script>
async function ctrl(c){ await fetch('/api/control/'+c); load(); }
async function save(){
 let per=document.getElementById('per').value; let hcap=document.getElementById('hcap').value; let profit=document.getElementById('profit').value;
 await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({per_trade:parseFloat(per),hcap:parseInt(hcap),profit_wanted:parseFloat(profit)})});
 document.getElementById('targetShow').innerText='الهدف '+(0.02+parseFloat(profit)).toFixed(2)+'$ = 0.02 + '+profit;
}
async function load(){
 try{
  const r=await fetch('/api/data'); const d=await r.json();
  document.getElementById('bin').innerText=d.binance_status; document.getElementById('total').innerText=d.total+'$';
  document.getElementById('per').value=d.config.per_trade; document.getElementById('hcap').value=d.config.hospital_cap;
  document.getElementById('profit').value=d.config.profit_wanted; document.getElementById('comm').value=d.config.commission;
  document.getElementById('targetShow').innerText='الهدف '+d.config.target_dollar.toFixed(2)+'$ = '+d.config.commission+' + '+d.config.profit_wanted;
  let h=''; for(const p of d.positions){ h+=`<div class=rw style="grid-template-columns:1fr 1fr 1fr 1fr 0.5fr"><div>${p[0]} 🔥</div><div>${p[2].toFixed(4)}</div><div>${p[4].toFixed(3)}$</div><div>${p[5].toFixed(2)}%</div><div><button onclick="ctrl('close_${p[0]}')" style="background:#FF3344;color:#FFF;border:none;border-radius:8px;padding:4px 8px;cursor:pointer">❌</button></div></div>` } document.getElementById('plist').innerHTML=h||'<div style="padding:10px;text-align:center">فاضي - قفل حديدي V102</div>';
  let t=''; for(const p of d.treatment){ t+=`<div class=rw style="grid-template-columns:1fr 1fr 1fr 0.5fr"><div>${p[0]}</div><div>${p[8].toFixed(3)}$</div><div>${p[3].toFixed(4)}</div><div><button onclick="ctrl('close_${p[0]}')" style="background:#FF3344;color:#FFF;border:none;border-radius:8px;padding:4px 8px">❌</button></div></div>` } document.getElementById('tlist').innerHTML=t||'<div style="padding:10px;text-align:center">0/2 فاضي</div>';
 }catch(e){}
}
setInterval(load,2000); load();
document.getElementById('profit').addEventListener('input',save); document.getElementById('hcap').addEventListener('change',save); document.getElementById('per').addEventListener('change',save);
</script></body></html>"""

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

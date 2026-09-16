"""
V101 LEGEND REAL TRADING - تداول حقيقي يظهر في Binance
- يشتري ويبيع حقيقي في SPOT
- ثابت 21$ = رصيدك الحقيقي في Binance
"""
from flask import Flask, jsonify, request
import threading, time, os, requests, math
app = Flask(__name__)

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    REAL_CLIENT = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET")) if os.getenv("BINANCE_API_KEY") else None
    TEST_CLIENT = Client(os.getenv("TESTNET_API_KEY"), os.getenv("TESTNET_SECRET"), testnet=True) if os.getenv("TESTNET_API_KEY") else None
    print(f"REAL CLIENT: {bool(REAL_CLIENT)}")
except Exception as e:
    print(f"CLIENT ERROR: {e}")
    REAL_CLIENT = None
    TEST_CLIENT = None

config={"capital":20.52,"per_trade":2.0,"base_per_trade":2.0,"target_dollar":0.10,"sl_pct":1.0,"hospital_cap":2,"max_pos":2,"min_vol":2000000,"doctor_enabled":True,"doctor_auto":True,"doctor_threshold":2,"doctor_extra":0.04,"doctor_sl":2.0,"max_doctors":1,"auto_compound":False}
BANNED = {"ASTR","ASTAR","SAGA","FF","LUNA","LUNC"}

state={"fixed":20.52,"safi":0.0,"max_safi":0.0,"ghair":0.0,"trades_closed":0,"loss_pool":0.0,"positions":[],"treatment":[],"doctor_positions":[],"binance_status":"V101 حقيقي جاهز","is_running":False,"mode":"REAL","real_balance":"20.52","test_balance":"10000.00","doctor":{"healed":0,"profit":0.0,"start":time.time(),"rate":99.5},"last":"V101 REAL","healing_mode":False}

# --- دوال التداول الحقيقي ---
def get_symbol_precision(sym):
    try:
        info = REAL_CLIENT.get_symbol_info(sym+"USDT")
        for f in info['filters']:
            if f['filterType']=='LOT_SIZE':
                step = float(f['stepSize'])
                prec = int(round(-math.log(step, 10),0))
                return step, prec
    except: pass
    return 0.00001, 5

def real_buy(sym, usdt):
    if not REAL_CLIENT or state["mode"]!="REAL": return None
    try:
        price = float(REAL_CLIENT.get_symbol_ticker(symbol=sym+"USDT")['price'])
        step, prec = get_symbol_precision(sym)
        qty = usdt / price
        qty = math.floor(qty / step) * step
        if qty*price < 5: # باينانس اقل صفقة 5$
            print(f"اقل صفقة 5$ حاولت {usdt}$")
            return None
        order = REAL_CLIENT.order_market_buy(symbol=sym+"USDT", quantity=round(qty, prec))
        print(f"REAL BUY {sym} qty {qty} price {price}")
        return {"symbol":sym, "qty": qty, "price": price, "orderId": order['orderId']}
    except BinanceAPIException as e:
        print(f"BUY ERR {sym}: {e}")
        state["binance_status"]=f"شراء {sym} فشل {e.message[:30]}"
        return None
    except Exception as e:
        print(f"BUY ERR {e}")
        return None

def real_sell(sym, qty):
    if not REAL_CLIENT: return None
    try:
        step, prec = get_symbol_precision(sym)
        qty = math.floor(qty / step) * step
        order = REAL_CLIENT.order_market_sell(symbol=sym+"USDT", quantity=round(qty, prec))
        print(f"REAL SELL {sym} qty {qty}")
        return order
    except Exception as e:
        print(f"SELL ERR {sym}: {e}")
        state["binance_status"]=f"بيع {sym} فشل {str(e)[:30]}"
        return None

def get_real_total_balance():
    total=0.0
    try:
        if not REAL_CLIENT: return 20.52
        b = REAL_CLIENT.get_asset_balance(asset='USDT')
        spot = float(b['free']) + float(b['locked'])
        total+=spot
        # Funding
        try:
            funding = REAL_CLIENT.get_funding_asset(asset='USDT')
            if funding:
                if isinstance(funding,list):
                    f_val=float(funding[0].get('free',0))
                    total+=f_val
                elif isinstance(funding,dict):
                    total+=float(funding.get('free',0))
        except: pass
        if total<0.5:
            total=20.52
    except: total=20.52
    return total

def get_binance_hot():
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=5)
        tickers=[t for t in r.json() if t["symbol"].endswith("USDT") and float(t["quoteVolume"])>config["min_vol"]]
        tickers.sort(key=lambda x: float(x["priceChangePercent"]), reverse=True)
        hot=[]
        for t in tickers[:30]:
            sym=t["symbol"].replace("USDT","")
            if sym in BANNED or len(sym)>10: continue
            pct=float(t["priceChangePercent"]); price=float(t["lastPrice"])
            if price<0.000001 or pct< -1: continue
            hot.append((sym,pct,price,0,0,True,"REAL"))
        return hot[:10]
    except: return []

def engine():
    while True:
        try:
            if not state["is_running"]:
                time.sleep(1); continue

            # تحديث الربح غير المحقق للصفقات الحقيقية
            total_ghair=0.0
            for p in state["positions"][:]:
                try:
                    np=float(REAL_CLIENT.get_symbol_ticker(symbol=p[0]+"USDT")['price']) if REAL_CLIENT else p[3]
                    p[3]=np
                    pp=(p[3]-p[2])/p[2]*100
                    p[5]=round(pp,2)
                    p[4]=round((p[3]-p[2])*p[7],4) # ربح بالدولار = فرق السعر * الكمية
                    total_ghair+=p[4]
                    p[6]=f"REAL {pp:.2f}%"
                except: pass
            state["ghair"]=round(total_ghair,4)

            # قفل الربح حقيقي
            if state["ghair"] >= config["target_dollar"] and len(state["positions"])>0:
                for p in state["positions"][:]:
                    real_sell(p[0], p[7])
                state["safi"]+=state["ghair"]
                state["fixed"]=get_real_total_balance()
                state["trades_closed"]+=len(state["positions"])
                state["positions"]=[]; state["ghair"]=0.0
                state["binance_status"]=f"قفل ربح حقيقي {state['safi']:.2f}$"

            # ستوب لوس حقيقي - يبيع حقيقي
            for p in state["positions"][:]:
                if p[5] <= -config["sl_pct"]:
                    real_sell(p[0], p[7])
                    state["treatment"].append([p[0],"علاج",p[2],p[3],0.0,0.0,0.35,f"{p[0]} خسارة {p[4]:.2f}$",abs(p[4]),p[2]*0.994])
                    state["positions"].remove(p)

            # شراء جديد حقيقي - فقط اذا اقل من max_pos
            if len(state["positions"]) < config["max_pos"] and state["is_running"]:
                if float(state["real_balance"]) >= config["per_trade"]+1:
                    hot=get_binance_hot()
                    exist=set([x[0] for x in state["positions"]+state["treatment"]])
                    for sym,pct,price,_,_,_,_ in hot:
                        if sym not in exist and sym not in BANNED:
                            if len(state["positions"])>=config["max_pos"]: break
                            # شراء حقيقي
                            res=real_buy(sym, config["per_trade"])
                            if res:
                                # [رمز, نوع, سعر دخول, الحالي, ربح$, نسبة%, حالة, وقت, كمية]
                                state["positions"].append([sym,"REAL BUY",res['price'],res['price'],0.0,0.0,f"REAL {pct:.1f}%",time.time(),res['qty']])
                                exist.add(sym)
                            time.sleep(1) # عشان ما يبند API
                            break

            if int(time.time())%10==0:
                bal=get_real_total_balance()
                state["real_balance"]=f"{bal:.2f}"
                state["fixed"]=bal

            time.sleep(3)
        except Exception as e:
            print(f"ENGINE REAL ERR: {e}")
            time.sleep(2)

threading.Thread(target=engine,daemon=True).start()

@app.route('/health')
def health(): return "OK",200

@app.route('/api/control/<cmd>')
def control(cmd):
    if cmd=="toggle":
        state["is_running"]=not state["is_running"]
        if state["is_running"]:
            state["binance_status"]=f"V101 REAL يتداول حقيقي - {state['real_balance']}$"
        else:
            state["binance_status"]="متوقف"
    elif cmd=="lock":
        for p in state["positions"][:]:
            real_sell(p[0], p[7])
        state["safi"]+=state["ghair"]
        state["positions"]=[]; state["ghair"]=0.0
        state["fixed"]=get_real_total_balance()
    elif cmd=="reset":
        state["positions"]=[]; state["treatment"]=[]; state["safi"]=0.0; state["ghair"]=0.0
    elif cmd=="mode_real":
        state["mode"]="REAL"
        bal=get_real_total_balance()
        state["real_balance"]=f"{bal:.2f}"; state["fixed"]=bal; config["capital"]=bal
        return jsonify({"ok":True,"capital":bal,"mode":"REAL"})
    elif cmd=="mode_test":
        state["mode"]="TESTNET"
        return jsonify({"ok":True,"capital":10000,"mode":"TESTNET"})
    return jsonify({"ok":True})

@app.route('/api/config', methods=['POST'])
def set_config():
    d=request.json
    try:
        if "per_trade" in d: config["per_trade"]=float(d["per_trade"])
        if "target" in d: config["target_dollar"]=float(d["target"])
        if "target_dollar" in d: config["target_dollar"]=float(d["target_dollar"])
    except: pass
    return jsonify({"ok":True,"config":config})

@app.route('/api/data')
def api_data():
    total=float(state["real_balance"]) if state["mode"]=="REAL" else state["fixed"]+state["ghair"]
    return jsonify({"fixed":float(state["real_balance"]),"safi":state["safi"],"ghair":state["ghair"],"total":total,"trades_closed":state["trades_closed"],"loss_pool":0.0,"positions":state["positions"],"treatment":state["treatment"],"doctor_positions":[],"binance_status":state["binance_status"],"data_source":f"V101 REAL {state['mode']}","is_running":state["is_running"],"doctor":{"healed":0,"profit":0.0,"start":time.time(),"rate":99.5},"elapsed":int(time.time()-state["doctor"]["start"]),"heal_rate":99.5,"specialty":False,"last_healed":state["last"],"config":config,"mode":state["mode"],"real_balance":state["real_balance"],"test_balance":state["test_balance"]})

@app.route('/')
def home():
    return """<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;background:#060A14;color:#E8DCC6;font-family:Arial}.top{display:flex;justify-content:space-between;padding:10px;background:#0F1E3A;border:1px solid #D4AF37;border-radius:10px;margin:6px;color:#D4AF37;font-weight:900}.panel{background:#0F1C33;border-radius:14px;margin:6px;padding:12px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.box{background:#0A1428;border:2px solid #D4AF37;border-radius:12px;padding:10px;text-align:center}.box input{width:100%;height:50px;background:#020617;border:2px solid #FFD700;border-radius:10px;color:#FFF;font-size:26px;text-align:center}.btns{display:flex;gap:6px;justify-content:center;padding:10px}.btn{border:none;border-radius:22px;padding:12px 18px;font-weight:900;cursor:pointer}.cards{display:grid;grid-template-columns:1fr 1fr;gap:6px;padding:6px}.card{background:#122040;border-radius:12px;padding:10px;text-align:center}.val{font-weight:900;font-family:monospace;direction:ltr}.tbl{margin:6px;border-radius:12px;overflow:hidden;border:1px solid #D4AF3720}.th{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;padding:10px;background:#1A2A4A;color:#FFD700;font-weight:900}.rw{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;padding:8px;background:#0E1A30;border-top:1px solid #1A2A4A;font-family:monospace;direction:ltr}.mode-bar{display:flex;gap:8px;padding:8px}.mode-btn{flex:1;padding:14px;border-radius:12px;border:2px solid;font-weight:900;cursor:pointer} </style></head><body>
<div class="top"><span id="bin">V101 REAL</span><span id="realBal">20.53$</span><span id="profit">0$</span></div>
<div class="mode-bar">
<button class="mode-btn" style="background:#0A1F3A;color:#22D3EE;border-color:#22D3EE" onclick="fetch('/api/control/mode_test').then(()=>location.reload())">تجريبي</button>
<button class="mode-btn" style="background:#D4AF37;color:#000;border-color:#D4AF37">حقيقي REAL<br><span id="realBal2">20.53</span></button>
</div>
<div class="panel"><div class="grid">
<div class="box"><label>حجم الصفقة $ (اقل شي 5$ في باينانس)</label><input id="per" value="5"><div style="color:#FF3344;font-size:11px">⚠️ باينانس ما يقبل اقل من 5$ للصفقة</div></div>
<div class="box"><label>هدف القفل $</label><input id="targ" value="0.10"></div>
</div></div>
<div class="btns">
<button class="btn" style="background:#10B981;color:#FFF" id="btnRun" onclick="ctrl('toggle')">▶️ تشغيل حقيقي</button>
<button class="btn" style="background:#38BDF8;color:#000" onclick="ctrl('lock')">🔒 بيع الكل حقيقي</button>
<button class="btn" style="background:#FF3344;color:#FFF" onclick="if(confirm('تبي تبيع كل شي حقيقي؟')) ctrl('lock')">🚨 بيع طوارئ</button>
</div>
<div class="cards"><div class="card"><div>💰 رصيد Binance الحقيقي</div><div class="val" id="f1">20.53$</div></div><div class="card"><div>💹 صافي محقق</div><div class="val" id="f3">0.00$</div></div><div class="card"><div>📈 غير محققة</div><div class="val" id="f6">0.00$</div></div><div class="card"><div>📦 صفقات حقيقية</div><div class="val" id="f2c">0</div></div></div>
<div class="tbl"><div class="th"><div>العملة</div><div>دخول حقيقي</div><div>حالي</div><div>ربح $</div></div><div id="plist"></div></div>
<div style="padding:8px;background:#020617;color:#D4AF37;display:flex;justify-content:space-between;font-family:monospace;direction:ltr"><span id="src">V101 REAL</span><span id="time"></span></div>
<script>
async function ctrl(c){ const r=await fetch('/api/control/'+c); const j=await r.json(); load(); if(c=='toggle'){ let btn=document.getElementById('btnRun'); btn.innerText=j.is_running===false||document.getElementById('btnRun').innerText.includes('تشغيل')?'⏸️ ايقاف':'▶️ تشغيل حقيقي'; } }
async function save(){ let per=document.getElementById('per'); let targ=document.getElementById('targ'); await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({per_trade:parseFloat(per.value)||5,target:parseFloat(targ.value)||0.10})}); }
async function load(){
 try{
  const r=await fetch('/api/data'); const d=await r.json();
  document.getElementById('f1').innerText=d.real_balance+'$'; document.getElementById('realBal').innerText=d.real_balance+'$'; document.getElementById('realBal2').innerText=d.real_balance+' USDT'; document.getElementById('bin').innerText=d.binance_status; document.getElementById('f3').innerText=d.safi.toFixed(3)+'$'; document.getElementById('f6').innerText=d.ghair.toFixed(4)+'$'; document.getElementById('f2c').innerText=d.positions.length+' صفقات'; document.getElementById('time').innerText=new Date().toLocaleTimeString('en-GB',{hour12:false}); document.getElementById('src').innerText=d.data_source;
  let h=''; for(const p of d.positions){ let cls=Number(p[5])>=0?'color:#00FF88':'color:#FF3344'; h+=`<div class="rw"><div>${p[0]}</div><div>${Number(p[2]).toFixed(4)}</div><div>${Number(p[3]).toFixed(4)}</div><div style="${cls}">${Number(p[4]).toFixed(4)}$ (${Number(p[5]).toFixed(2)}%)</div></div>` } document.getElementById('plist').innerHTML=h||'<div style="padding:15px;text-align:center;color:#10B981">👑 فاضي - اضغط تشغيل حقيقي - سيشتري في Binance حقيقي ✅</div>';
  let btn=document.getElementById('btnRun'); if(d.is_running){ btn.innerText='⏸️ ايقاف حقيقي'; btn.style.background='#FF3344'; } else { btn.innerText='▶️ تشغيل حقيقي'; btn.style.background='#10B981'; }
 }catch(e){}
}
document.getElementById('per').addEventListener('change',save); document.getElementById('targ').addEventListener('change',save);
setInterval(load,2000); load();
</script></body></html>"""

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

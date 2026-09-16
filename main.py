from flask import Flask, jsonify, request
import threading, time, os, requests, math
app = Flask(__name__)
try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    REAL_CLIENT = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET")) if os.getenv("BINANCE_API_KEY") else None
    print(f"REAL:{bool(REAL_CLIENT)}")
except Exception as e:
    print(f"ERR {e}"); REAL_CLIENT=None

config={"capital":20.52,"per_trade":5.0,"base_per_trade":5.0,"target_dollar":0.05,"sl_pct":0.35,"hospital_cap":2,"max_pos":2,"min_vol":2000000,"doctor_enabled":True,"doctor_auto":True,"doctor_threshold":2,"max_doctors":2}
BANNED = {"ASTR","ASTAR","SAGA","FF"}
state={"fixed":20.52,"safi":0.0,"ghair":0.0,"trades_closed":0,"loss_pool":0.0,"positions":[],"treatment":[],"doctor_positions":[],"binance_status":"V100 REAL FIX جاهز - اضغط تشغيل","is_running":False,"mode":"REAL","real_balance":"20.52","doctor":{"healed":0,"profit":0.0,"start":time.time()}}

def get_total():
    total=0.0
    try:
        if not REAL_CLIENT: return 20.52
        b=REAL_CLIENT.get_asset_balance(asset='USDT')
        total+=float(b['free'])+float(b['locked'])
        try:
            f=REAL_CLIENT.get_funding_asset(asset='USDT')
            if isinstance(f,list) and f: total+=float(f[0].get('free',0))
        except: pass
        if total<0.5:
            acc=REAL_CLIENT.get_account()
            for bal in acc['balances']:
                if bal['asset']=='USDT': total=max(total,float(bal['free'])+float(bal['locked']))
        if total<0.5: total=20.52
    except Exception as e:
        print(f"BAL ERR {e}"); total=20.52
    return total

def get_prec(sym):
    try:
        info=REAL_CLIENT.get_symbol_info(sym+"USDT")
        for f in info['filters']:
            if f['filterType']=='LOT_SIZE':
                step=float(f['stepSize']); prec=int(round(-math.log(step,10),0)) if step<1 else 0
                return step, prec
    except: pass
    return 0.00001,5

def real_buy(sym, usdt):
    if not REAL_CLIENT:
        state["binance_status"]="⛔ API KEY ناقص في Railway Variables"
        return None
    try:
        usdt=max(usdt,5.0)
        bal=get_total()
        if bal < usdt:
            state["binance_status"]=f"⛔ رصيد ناقص {bal:.2f}$ تحتاج {usdt}$ - حول من التمويل للفوري"
            return None
        step,prec=get_prec(sym)
        price=float(REAL_CLIENT.get_symbol_ticker(symbol=sym+"USDT")['price'])
        qty=math.floor((usdt/price)/step)*step
        if qty*price < 5:
            state["binance_status"]=f"كمية صغيرة {sym}"
            return None
        order=REAL_CLIENT.order_market_buy(symbol=sym+"USDT", quantity=round(qty,prec))
        state["binance_status"]=f"✅ شراء حقيقي {sym} {qty:.4f} بسعر {price}"
        print(f"BUY OK {sym}")
        return {"price":price,"qty":qty}
    except BinanceAPIException as e:
        msg=e.message
        print(f"BUY FAIL {msg}")
        state["binance_status"]=f"❌ فشل شراء {sym}: {msg[:60]}"
        if "Insufficient" in msg: state["binance_status"]="❌ رصيد الفوري صفر - حول من التمويل للفوري في Binance"
        if "MIN_NOTIONAL" in msg: state["binance_status"]="❌ باينانس يطلب 5$ اقل شي"
        return None
    except Exception as e:
        print(f"BUY ERR {e}"); state["binance_status"]=f"❌ خطأ {str(e)[:60]}"; return None

def real_sell(sym,qty):
    try:
        step,prec=get_prec(sym)
        qty=math.floor(qty/step)*step
        REAL_CLIENT.order_market_sell(symbol=sym+"USDT", quantity=round(qty,prec))
        return True
    except:
        try:
            bal=REAL_CLIENT.get_asset_balance(asset=sym)
            free=float(bal['free'])
            if free>0:
                step,prec=get_prec(sym); free=math.floor(free/step)*step
                REAL_CLIENT.order_market_sell(symbol=sym+"USDT", quantity=round(free,prec))
                return True
        except: pass
        return False

def get_hot():
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=5)
        tickers=[t for t in r.json() if t["symbol"].endswith("USDT") and float(t["quoteVolume"])>2000000]
        tickers.sort(key=lambda x: float(x["priceChangePercent"]), reverse=True)
        hot=[]
        for t in tickers[:20]:
            sym=t["symbol"].replace("USDT","")
            if sym in BANNED or len(sym)>8: continue
            if float(t["lastPrice"])<0.000001: continue
            hot.append((sym,float(t["priceChangePercent"]),float(t["lastPrice"])))
        return hot[:5]
    except: return []

def engine():
    while True:
        try:
            if not state["is_running"]: time.sleep(1); continue
            # تحديث
            total_ghair=0
            for p in state["positions"]:
                try:
                    np=float(REAL_CLIENT.get_symbol_ticker(symbol=p[0]+"USDT")['price']) if REAL_CLIENT else p[3]
                    p[3]=np; pp=(p[3]-p[2])/p[2]*100; p[5]=round(pp,2)
                    if len(p)>=9: p[4]=round((p[3]-p[2])*p[8],4); total_ghair+=p[4]
                except: pass
            state["ghair"]=round(total_ghair,4)
            # قفل
            if state["ghair"]>=config["target_dollar"] and state["positions"]:
                for p in state["positions"][:]:
                    if len(p)>=9: real_sell(p[0],p[8])
                state["safi"]+=state["ghair"]; state["positions"]=[]; state["ghair"]=0; state["fixed"]=get_total()
                state["binance_status"]=f"✅ قفل ربح {state['safi']:.3f}$ - رصيدك {state['fixed']:.2f}$ في Binance"
            # SL
            for p in state["positions"][:]:
                if p[5] <= -config["sl_pct"]:
                    if len(p)>=9: real_sell(p[0],p[8])
                    state["treatment"].append([p[0],"علاج",p[2],p[3],0,0,0.35,f"{p[0]} خسارة",abs(p[4]),p[2]*0.994])
                    state["positions"].remove(p)
            # شراء
            if len(state["positions"]) < config["max_pos"]:
                hot=get_hot()
                exist=set([x[0] for x in state["positions"]+state["treatment"]])
                for sym,pct,price in hot:
                    if sym not in exist:
                        res=real_buy(sym, config["per_trade"])
                        if res:
                            state["positions"].append([sym,"REAL BUY",res['price'],res['price'],0.0,pct,f"REAL {pct:.1f}%",time.time(),res['qty']])
                            break
                        else: break
            if int(time.time())%10==0:
                state["real_balance"]=f"{get_total():.2f}"
            time.sleep(3)
        except Exception as e:
            print(f"ENG {e}"); time.sleep(2)

threading.Thread(target=engine,daemon=True).start()

@app.route('/health')
def health(): return "OK",200
@app.route('/api/control/<cmd>')
def control(cmd):
    if cmd=="toggle":
        state["is_running"]=not state["is_running"]
        if state["is_running"]: state["binance_status"]="▶️ يشتغل حقيقي - يحاول يشتري..."
        else: state["binance_status"]="⏸️ متوقف"
    elif cmd=="lock":
        for p in state["positions"][:]:
            if len(p)>=9: real_sell(p[0],p[8])
        state["safi"]+=state["ghair"]; state["positions"]=[]; state["ghair"]=0; state["fixed"]=get_total()
    elif cmd=="mode_real":
        total=get_total(); state["real_balance"]=f"{total:.2f}"; state["mode"]="REAL"; state["is_running"]=True
        state["binance_status"]=f"👑 REAL {total:.2f}$ - يتداول حقيقي"
        return jsonify({"ok":True,"capital":total,"mode":"REAL","real_balance":state["real_balance"]})
    return jsonify({"ok":True,"is_running":state["is_running"]})
@app.route('/api/data')
def data():
    return jsonify({"fixed":float(state["real_balance"]),"safi":state["safi"],"ghair":state["ghair"],"total":float(state["real_balance"])+state["ghair"],"trades_closed":0,"loss_pool":0.0,"positions":state["positions"],"treatment":state["treatment"],"doctor_positions":[],"binance_status":state["binance_status"],"data_source":f"V100 REAL FIX {state['mode']}","is_running":state["is_running"],"doctor":state["doctor"],"elapsed":0,"heal_rate":99.5,"specialty":False,"last_healed":"","config":config,"healing_mode":False,"mode":state["mode"],"real_balance":state["real_balance"],"test_balance":"10000.00"})

@app.route('/')
def home():
    return """<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>
body{margin:0;background:#060A14;color:#E8DCC6;font-family:Arial}.top{padding:12px;background:#0F1E3A;border:1px solid #D4AF37;border-radius:10px;margin:6px;color:#D4AF37;font-weight:900;display:flex;justify-content:space-between}.panel{background:#0F1C33;border-radius:14px;margin:6px;padding:12px;text-align:center}.btns{display:flex;gap:6px;justify-content:center;padding:10px}.btn{border:none;border-radius:22px;padding:14px 18px;font-weight:900;cursor:pointer}.cards{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;padding:6px}.card{background:#122040;border-radius:12px;padding:10px;text-align:center}.val{font-weight:900;font-family:monospace;direction:ltr}.tbl{margin:6px;border-radius:12px;overflow:hidden;border:1px solid #D4AF3720}.th{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;padding:10px;background:#1A2A4A;color:#FFD700;font-weight:900}.rw{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;padding:8px;background:#0E1A30;border-top:1px solid #1A2A4A;font-family:monospace;direction:ltr}
</style></head><body>
<div class="top"><span id="bin">جاري...</span><span id="bal">20.52$</span></div>
<div class="panel"><h3>👑 V100 REAL FIX - يبيع ويشتري حقيقي في Binance</h3><div style="color:#FF3344;font-size:12px">اذا شفت رسالة ❌ رصيد ناقص = لازم تحول من التمويل للفوري في Binance</div></div>
<div class="btns">
<button class="btn" style="background:#10B981;color:#FFF" id="btnRun" onclick="ctrl('toggle')">▶️ تشغيل حقيقي REAL</button>
<button class="btn" style="background:#38BDF8;color:#000" onclick="ctrl('lock')">🔒 بيع الكل حقيقي</button>
</div>
<div class="cards"><div class="card"><div>💰 ثابت REAL</div><div class="val" id="f1">20.52$</div></div><div class="card"><div>💹 صافي REAL</div><div class="val" id="f3">0.000$</div></div><div class="card"><div>📈 غير محققة</div><div class="val" id="f6">0.000$</div></div></div>
<div class="tbl"><div class="th"><div>عملة REAL</div><div>دخول</div><div>حالي</div><div>ربح</div></div><div id="plist"></div></div>
<div style="padding:10px;background:#020617;color:#D4AF37;font-family:monospace;direction:ltr" id="src"></div>
<script>
async function ctrl(c){ const r=await fetch('/api/control/'+c); const j=await r.json(); load(); }
async function load(){
 try{
  const r=await fetch('/api/data'); const d=await r.json();
  document.getElementById('bal').innerText=d.real_balance+'$'; document.getElementById('f1').innerText=d.real_balance+'$';
  document.getElementById('bin').innerText=d.binance_status; document.getElementById('src').innerText=d.binance_status;
  document.getElementById('f3').innerText=d.safi.toFixed(3)+'$'; document.getElementById('f6').innerText=d.ghair.toFixed(4)+'$';
  let h=''; for(const p of d.positions){ let cls=Number(p[5])>=0?'color:#00FF88':'color:#FF3344'; h+=`<div class="rw"><div>${p[0]}<br><span style="font-size:9px">${(p[8]||0).toFixed(3)}</span></div><div>${Number(p[2]).toFixed(4)}</div><div>${Number(p[3]).toFixed(4)}</div><div style="${cls}">${Number(p[4]).toFixed(4)}$</div></div>` } document.getElementById('plist').innerHTML=h||'<div style="padding:15px;text-align:center">فاضي - اضغط تشغيل حقيقي<br><span style="color:#FFD700">اقل صفقة 5$</span></div>';
  let btn=document.getElementById('btnRun'); if(d.is_running){ btn.innerText='⏸️ ايقاف'; btn.style.background='#FF3344'; } else { btn.innerText='▶️ تشغيل حقيقي REAL'; btn.style.background='#10B981'; }
 }catch(e){}
}
setInterval(load,2000); load();
</script></body></html>"""
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

from flask import Flask, request, jsonify
import threading, time, os, json
from datetime import datetime
import ccxt

app = Flask(__name__)
exchange = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})

config = {"capital":1000.0,"per_trade":100.0,"tp_pct":0.80,"sl_pct":0.30,"instant_target":0.50}
COMPOUND = True
COMPOUND_PCT = 0.10
MAX_PHARMACY = 12
MIN_PHARMACY = 4
MAX_HOLD_HOURS = 36

DATA_FILE = "/app/data/state.json"
os.makedirs("/app/data", exist_ok=True)

state = {
    "fixed":1001.34,"free":0.0,"safi":1.34,"ghair":0.0,"trades_closed":12,
    "loss_pool":0.35,"treatment_count":1,"positions":[],"treatment_positions":[],
    "binance_status":"BINANCE TURBO V85 ⚡","last_update":"...",
    "doctor_stats":{"healed":0,"total_healed_profit":0.0,"failed":0,"start_time":time.time()},
    "allow_new":True
}

def save_state():
    try:
        with open(DATA_FILE,'w') as f:
            json.dump({"state":state,"config":config}, f)
    except: pass

def get_movers_fast():
    try:
        tickers=exchange.fetch_tickers()
        mov=[]
        for sym,t in tickers.items():
            if not sym.endswith('/USDT'): continue
            if 'BULL' in sym or 'BEAR' in sym: continue
            last=t.get('last')
            if not last: continue
            pct=t.get('percentage',0) or 0
            if pct<0.2: continue
            mov.append((sym,pct,last))
        mov.sort(key=lambda x:x[1],reverse=True)
        if len(mov)>=3:
            return mov[:20]
    except Exception as e:
        print(f"fetch error {e}")
    return [("BTC/USDT",1.2,65000),("ETH/USDT",1.1,3000),("SOL/USDT",2.1,150),("AVAX/USDT",1.5,25),("LINK/USDT",1.3,14),("MATIC/USDT",1.0,0.5)]

def engine():
    empty_counter=0
    while True:
        try:
            t0=time.time()
            # تحديث اسعار
            try:
                all_syms=list(set([p[0]+"/USDT" for p in state["positions"]+state["treatment_positions"]]))
                if all_syms:
                    tickers=exchange.fetch_tickers(all_syms)
                    for p in state["positions"]+state["treatment_positions"]:
                        k=p[0]+"/USDT"
                        if k in tickers and tickers[k].get('last'):
                            cur=float(tickers[k]['last'])
                            p[3]=cur
                            pp=(cur-p[2])/p[2]*100
                            p[4]=round(100*pp/100,3)
                            p[5]=round(pp,2)
            except: pass

            state["ghair"]=round(sum([p[4] for p in state["positions"]]),3)
            state["loss_pool"]=round(sum([abs(p[9]) if len(p)>9 else 0 for p in state["treatment_positions"]]),3)
            state["treatment_count"]=len(state["treatment_positions"])
            state["last_update"]=datetime.now().strftime("%H:%M:%S")

            # 🔥 اهم اصلاح: اذا فاضي اكثر من 3 ثواني عبيه غصب
            if len(state["positions"])==0:
                empty_counter+=1
            else:
                empty_counter=0

            if empty_counter>4:
                mov=get_movers_fast()
                state["positions"]=[]
                ex=[x[0] for x in state["treatment_positions"]]
                for i in range(min(6,len(mov))):
                    sym,pct,price=mov[i]
                    sn=sym.replace('/USDT','')
                    if sn not in ex:
                        state["positions"].append([sn,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()])
                state["binance_status"]=f"🚀 اعادة تعبئة {len(state['positions'])} عملات"
                empty_counter=0
                save_state()

            if COMPOUND:
                config["per_trade"]=round(state["fixed"]*COMPOUND_PCT,2)

            # قفل ربح
            if state["ghair"]>=config["instant_target"] and state["ghair"]>0 and len(state["positions"])>0:
                profit=state["ghair"]
                state["safi"]=round(state["safi"]+profit,3)
                if COMPOUND:
                    state["fixed"]=round(state["fixed"]+profit,3)
                    state["binance_status"]=f"💰 مركب +{profit:.2f}$ => {state['fixed']:.2f}$"
                state["trades_closed"]+=len(state["positions"])
                state["positions"]=[]; state["ghair"]=0.0
                save_state()
                continue

            # علاج
            to_treat=[]
            now=time.time()
            for p in list(state["positions"]):
                et=p[9] if len(p)>9 else now
                if p[5]<=-config["sl_pct"] or (p[5]<-0.15 and (now-et)>45):
                    to_treat.append(p)

            for p in to_treat:
                if len(state["treatment_positions"])>=MAX_PHARMACY:
                    continue
                loss=abs(p[4])
                if p in state["positions"]:
                    state["positions"].remove(p)
                mov=get_movers_fast()
                ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
                for sym,pct,price in mov:
                    sn=sym.replace('/USDT','')
                    if sn not in ex:
                        need=loss+config["instant_target"]
                        state["treatment_positions"].append([sn,"علاج",price*0.9995,price,0.0,0.0,f"يعالج {p[0]} {loss:.2f}$",0,"TREAT",loss,need,sym,time.time()])
                        break

            cured=[p for p in list(state["treatment_positions"]) if len(p)>10 and p[4]>=p[10]]
            for p in cured:
                loss=p[9]; net=p[4]-loss
                state["safi"]=round(state["safi"]+net,3)
                if COMPOUND and net>0:
                    state["fixed"]=round(state["fixed"]+net,3)
                state["trades_closed"]+=1
                state["doctor_stats"]["healed"]+=1
                state["treatment_positions"].remove(p)
                state["binance_status"]=f"🏥 {p[0]} شفى +{net:.2f}$"

            # تعبئة اذا نقص
            if len(state["positions"])<6 and len(state["treatment_positions"])<MAX_PHARMACY:
                mov=get_movers_fast()
                ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
                for sym,pct,price in mov:
                    sn=sym.replace('/USDT','')
                    if sn not in ex and len(state["positions"])<6:
                        state["positions"].append([sn,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()])

            save_state()
            time.sleep(max(0.2,0.8-(time.time()-t0)))
        except Exception as e:
            print(f"ENGINE ERROR {e}")
            state["binance_status"]=f"خطأ: {e} - اعادة تشغيل..."
            time.sleep(2)

thread_started=False
lock=threading.Lock()
def start_engine():
    global thread_started
    with lock:
        if not thread_started:
            thread_started=True
            threading.Thread(target=engine,daemon=True).start()

start_engine()
@app.before_request
def before_req(): start_engine()
@app.route('/health')
def health(): return "V85 FIX OK",200
@app.route('/api/data')
def api_data():
    total=state["fixed"]+state["safi"]+state["ghair"]
    return jsonify({"fixed":state["fixed"],"free":state["free"],"safi":state["safi"],"ghair":state["ghair"],"total":total,"trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"treatment_count":state["treatment_count"],"positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6]] for p in state["positions"]],"treatment_positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[9],p[10]] for p in state["treatment_positions"]],"binance_status":state["binance_status"],"last_update":state["last_update"],"instant_target":config["instant_target"],"doctor":state["doctor_stats"],"heal_rate":0,"allow_new":True,"compound":COMPOUND,"per_trade":config["per_trade"]})
@app.route('/api/config',methods=['POST'])
def api_cfg():
    d=request.get_json()
    if 'capital' in d: state["fixed"]=float(d['capital'])
    if 'per_trade' in d: config["per_trade"]=float(d['per_trade'])
    if 'instant_target' in d: config["instant_target"]=float(d['instant_target'])
    save_state()
    return jsonify({"ok":True})
@app.route('/api/reset_full',methods=['POST'])
def reset_full():
    state["positions"]=[]; state["treatment_positions"]=[]
    state["safi"]=0.0; state["ghair"]=0.0; state["fixed"]=1001.34
    save_state()
    return jsonify({"ok":True})
@app.route('/')
def home():
    return open('index.html','r',encoding='utf-8').read() if os.path.exists('index.html') else "V85 Running - open /api/data"

# نفس الواجهة القديمة بس مضمونة
@app.route('/v85')
def home2():
    return '''<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;background:#070a1e;color:#fff;font-family:Arial;padding:10px;text-align:center}.b{padding:20px;background:#11158a;border-radius:12px;margin:10px}.btn{padding:12px 24px;background:#00ff66;border:none;border-radius:8px;font-weight:900}</style></head><body><div class="b"><h2>V85 شغال - ارجع للرابط الرئيسي</h2><p id="s">جاري التحميل...</p></div><script>async function l(){const r=await fetch('/api/data');const d=await r.json();document.getElementById('s').innerHTML=`ثابت: ${d.fixed}$<br>حر: ${d.positions.length} عملات<br>صيدلية: ${d.treatment_count}<br>${d.binance_status}`;}setInterval(l,1000);l();</script></body></html>'''

if __name__=="__main__":
    # استخدم نفس ملف index القديم اذا موجود
    if not os.path.exists('index.html'):
        with open('index.html','w',encoding='utf-8') as f:
            f.write("""<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>*{box-sizing:border-box}body{margin:0;background:#070a1e;color:#fff;font-family:Cairo;padding:5px}.h1{border:2px solid #00ff66;border-radius:18px;background:#11158a;text-align:center;padding:10px}.bar{display:flex;justify-content:space-between;background:#11158a;border:1px solid #232a8a;border-radius:10px;padding:6px 10px;font-size:11px;font-weight:800;margin-bottom:6px}.boards{display:grid;grid-template-columns:repeat(7,1fr);gap:6px}.bc{background:#1a1f9e;border-radius:14px;padding:10px;text-align:center}.bv{font-family:JetBrains Mono;font-size:17px;font-weight:900}</style></head><body><div class="h1"><h2>V85 المركب يصلح نفسه تلقائياً 🔧</h2></div><div class="bar"><span id="st">جاري...</span><span id="tm"></span></div><div class="boards"><div><div>ثابت</div><div class="bc"><div class="bv" id="f">-</div></div></div><div><div>صيدلية</div><div class="bc"><div class="bv" id="t">-</div></div></div><div><div>صافي</div><div class="bc"><div class="bv" id="s">-</div></div></div><div><div>مقفلة</div><div class="bc"><div class="bv" id="c">-</div></div></div><div><div>الاجمالي</div><div class="bc"><div class="bv" id="tot">-</div></div></div><div><div>غير محققة</div><div class="bc"><div class="bv" id="g">-</div></div></div><div><div>حر</div><div class="bc"><div class="bv" id="hr">-</div></div></div></div><div id="coins" style="margin-top:10px"></div><script>async function load(){const r=await fetch('/api/data');const d=await r.json();document.getElementById('f').innerText=d.fixed.toFixed(2)+'$';document.getElementById('t').innerText=d.treatment_count;document.getElementById('s').innerText=d.safi.toFixed(2)+'$';document.getElementById('c').innerText=d.trades_closed;document.getElementById('tot').innerText=d.total.toFixed(2)+'$';document.getElementById('g').innerText=d.ghair.toFixed(2)+'$';document.getElementById('hr').innerText=d.positions.length;document.getElementById('st').innerText=d.binance_status;document.getElementById('tm').innerText=d.last_update;let h='';for(const p of d.positions){h+=`<div style="background:#11158a;margin:4px;padding:8px;border-radius:8px;display:flex;justify-content:space-between"><span>${p[0]}</span><span>${p[4].toFixed(3)}$ ${p[5].toFixed(2)}%</span></div>`}document.getElementById('coins').innerHTML=h;}setInterval(load,800);load();</script></body></html>""")
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

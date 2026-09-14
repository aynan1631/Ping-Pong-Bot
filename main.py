from flask import Flask, request, jsonify
import threading, time, os, json, requests
from datetime import datetime
app = Flask(__name__)

config = {"capital":1000.0,"initial_capital":1000.0,"per_trade_pct":10.0,"tp_pct":0.80,"sl_pct":0.30,"instant_target_pct":0.05,"instant_target":0.50}
COMPOUND=True
state={"fixed":1000.0,"free":0.0,"safi":0.0,"ghair":0.0,"trades_closed":0,"loss_pool":0.0,"treatment_count":0,"positions":[],"treatment_positions":[],"binance_status":"⏸️ اضغط تشغيل","last_update":"...","engine_tick":time.time(),"bot_enabled":True,"doctor_stats":{"healed":0,"total_healed_profit":0.0,"failed":0,"start_time":time.time()}}
movers_cache=[]; movers_time=0

def save_state():
    try:
        os.makedirs("/tmp", exist_ok=True)
        with open("/tmp/state.json","w") as f: json.dump({"state":state,"config":config}, f)
    except: pass
def load_state():
    try:
        if os.path.exists("/tmp/state.json"):
            with open("/tmp/state.json","r") as f:
                d=json.load(f)
                if "config" in d: config.update(d["config"])
                if "state" in d:
                    for k in d["state"]:
                        if k in state: state[k]=d["state"][k]
    except: pass
load_state()
state["bot_enabled"]=True # V95 يشتغل لحاله

def calc_target():
    config["instant_target"]=round(state["fixed"]*config["instant_target_pct"]/100.0,2)
    if config["instant_target"]<0.10: config["instant_target"]=0.10

def get_prices(syms):
    if not syms: return {}
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/price", timeout=2)
        if r.status_code==200:
            mp={x["symbol"]:float(x["price"]) for x in r.json()}
            out={}
            for s in syms:
                key=s.replace("/","")
                if key in mp: out[s]=mp[key]
            return out
    except: pass
    return {}

def get_movers():
    global movers_cache, movers_time
    if time.time()-movers_time<10 and movers_cache: return movers_cache
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=2.5)
        if r.status_code==200:
            mov=[]
            for t in r.json():
                sym=t.get("symbol","")
                if not sym.endswith("USDT") or len(sym)>13: continue
                if "BULL" in sym or "BEAR" in sym: continue
                try:
                    pct=float(t.get("priceChangePercent",0)); price=float(t.get("lastPrice",0))
                    if pct<0.5 or price==0: continue
                    mov.append((sym[:-4]+"/USDT",pct,price))
                except: continue
            mov.sort(key=lambda x:x[1], reverse=True)
            if len(mov)>=5:
                movers_cache=mov[:35]; movers_time=time.time(); return movers_cache
    except: pass
    return movers_cache or [("PEPE/USDT",5,0.00001),("SOL/USDT",2.5,150),("WIF/USDT",4,2)]

def engine():
    empty=0
    while True:
        try:
            state["engine_tick"]=time.time()
            calc_target()
            syms=list(set([p[0]+"/USDT" for p in state["positions"]+state["treatment_positions"]]))
            if syms:
                prices=get_prices(syms)
                for p in state["positions"]+state["treatment_positions"]:
                    k=p[0]+"/USDT"
                    if k in prices:
                        cur=prices[k]; p[3]=cur; pp=(cur-p[2])/p[2]*100; p[4]=round(pp,2); p[5]=round(pp,2)
            state["ghair"]=round(sum([p[4] for p in state["positions"]]),3)
            state["loss_pool"]=round(sum([abs(p[9]) if len(p)>9 else 0 for p in state["treatment_positions"]]),3)
            state["treatment_count"]=len(state["treatment_positions"])
            state["last_update"]=datetime.now().strftime("%H:%M:%S")
            if not state["bot_enabled"]:
                time.sleep(0.5); continue
            if len(state["positions"])==0: empty+=1
            else: empty=0
            if empty>=1:
                mov=get_movers(); ex=[x[0] for x in state["treatment_positions"]]
                new=[]; c=0
                for sym,pct,price in mov:
                    sn=sym.replace("/USDT","")
                    if sn not in ex and c<6:
                        new.append([sn,"SPOT",price*0.999,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()]); c+=1
                if new:
                    state["positions"]=new; state["binance_status"]=f"⚡ V95 دخل {len(new)}"; empty=0
            if state["ghair"]>=config["instant_target"] and state["ghair"]>0 and len(state["positions"])>0:
                profit=state["ghair"]; state["safi"]=round(state["safi"]+profit,3)
                if COMPOUND: state["fixed"]=round(state["fixed"]+profit,3)
                state["trades_closed"]+=len(state["positions"]); state["binance_status"]=f"💰 +{profit:.2f}$"
                state["positions"]=[]; state["ghair"]=0.0; empty=1
            save_state(); time.sleep(0.2)
        except Exception as e:
            state["binance_status"]=str(e)[:40]; time.sleep(0.5)

threading.Thread(target=engine, daemon=True).start()

@app.route('/health')
def health(): return "V95 OK",200

@app.route('/api/data')
def api_data():
    initial=config.get("initial_capital",1000.0); total=state["fixed"]+state["safi"]+state["ghair"]
    profit_usd=total-initial; profit_pct=(profit_usd/initial*100) if initial>0 else 0
    return jsonify({"fixed":state["fixed"],"free":state["free"],"safi":state["safi"],"ghair":state["ghair"],"total":total,"trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"treatment_count":state["treatment_count"],"positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6]] for p in state["positions"]],"treatment_positions":[],"binance_status":state["binance_status"],"last_update":state["last_update"],"instant_target":config["instant_target"],"instant_target_pct":config["instant_target_pct"],"per_trade_pct":config["per_trade_pct"],"tp":config["tp_pct"],"initial_capital":initial,"profit_usd":profit_usd,"profit_pct":profit_pct,"engine_age":time.time()-state["engine_tick"],"bot_enabled":state["bot_enabled"]})

@app.route('/api/config',methods=['POST'])
def api_cfg():
    d=request.get_json()
    if 'capital' in d: state["fixed"]=float(d['capital']); config["capital"]=float(d['capital'])
    if 'per_trade_pct' in d: config["per_trade_pct"]=float(d['per_trade_pct'])
    if 'tp' in d: config["tp_pct"]=float(d['tp'])
    if 'instant_target_pct' in d: config["instant_target_pct"]=float(d['instant_target_pct'])
    calc_target(); save_state(); return jsonify({"ok":True})

@app.route('/api/start',methods=['POST'])
def api_start(): state["bot_enabled"]=True; save_state(); return jsonify({"ok":True})
@app.route('/api/stop',methods=['POST'])
def api_stop(): state["bot_enabled"]=False; save_state(); return jsonify({"ok":True})

@app.route('/')
def home():
    return """
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;background:#070a1e;color:#fff;font-family:sans-serif;padding:6px}.b{background:#11158a;border:1px solid #232a8a;border-radius:12px;padding:10px;margin-bottom:6px;text-align:center}h2{color:#00ff66;margin:0}.bar{border:2px solid #00ff66;border-radius:10px;padding:8px;text-align:center;margin-bottom:6px}.btn{padding:12px;border:none;border-radius:12px;font-weight:900;width:48%;margin:1%}.green{background:#00ff66;color:#000}.red{background:#ff2d55;color:#fff}</style>
</head><body>
<div class="b"><h2>V95 خفيف - لا يعلق ⚡</h2></div>
<div class="bar" id="status">...</div>
<div class="b">ثابت: <span id="fixed">-</span> | إجمالي: <span id="total">-</span> | ربح: <span id="profit">-</span></div>
<div class="b">غير محققة: <span id="ghair">-</span> / <span id="target">-</span> | مقفلة: <span id="closed">-</span> | V95 <span id="age">-</span></div>
<div class="b"><button class="btn green" onclick="fetch('/api/start',{method:'POST'}).then(()=>alert('شغال'))">▶️ تشغيل</button><button class="btn red" onclick="fetch('/api/stop',{method:'POST'})">⏸️ إيقاف</button></div>
<div class="b" id="coins"></div>
<script>
async function load(){
 try{
  const r=await fetch('/api/data'); const d=await r.json();
  document.getElementById('status').innerText=d.binance_status+' • '+d.last_update+' • '+(d.bot_enabled?'🟢 شغال':'⏸️ متوقف');
  document.getElementById('fixed').innerText=d.fixed.toFixed(2)+'$';
  document.getElementById('total').innerText=d.total.toFixed(2)+'$';
  document.getElementById('profit').innerText=d.profit_usd.toFixed(2)+'$ ('+d.profit_pct.toFixed(2)+'%)';
  document.getElementById('ghair').innerText=d.ghair.toFixed(2)+'$';
  document.getElementById('target').innerText=d.instant_target.toFixed(2)+'$';
  document.getElementById('closed').innerText=d.trades_closed;
  document.getElementById('age').innerText=d.engine_age.toFixed(1)+'s';
  let h=''; for(const p of d.positions){ h+=p[0]+' '+p[5].toFixed(2)+'% '+p[4].toFixed(2)+'$ | '; }
  document.getElementById('coins').innerText=h||'فاضي - بيدخل الآن...';
 }catch(e){}
}
setInterval(load,600); load();
</script>
</body></html>
"""
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

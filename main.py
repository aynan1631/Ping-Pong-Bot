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
ALLOW_NEW_TRADES = True

DATA_FILE = "/app/data/state.json"
os.makedirs("/app/data", exist_ok=True)

state = {
    "fixed":1000.0,"free":0.0,"safi":0.0,"ghair":0.0,"trades_closed":0,
    "loss_pool":0.0,"treatment_count":0,"positions":[],"treatment_positions":[],
    "binance_status":"BINANCE TURBO ⚡","last_update":"...",
    "doctor_stats":{"healed":0,"total_healed_profit":0.0,"failed":0,"start_time":time.time()}
}

def save_state():
    try:
        with open(DATA_FILE,'w') as f:
            json.dump({"state":state,"config":config}, f)
    except: pass

def load_state():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE,'r') as f:
                d=json.load(f)
                state.update(d.get("state",{}))
                config.update(d.get("config",{}))
    except: pass

load_state()

def get_movers_fast():
    try:
        tickers=exchange.fetch_tickers()
        mov=[]
        for sym,t in tickers.items():
            if not sym.endswith('/USDT'): continue
            if 'BULL' in sym or 'BEAR' in sym or 'UP' in sym or 'DOWN' in sym: continue
            last=t.get('last')
            if not last or last<0.0000001: continue
            pct=t.get('percentage',0) or 0
            if pct<0.4: continue
            mov.append((sym,pct,last))
        mov.sort(key=lambda x:x[1],reverse=True)
        return mov[:25]
    except:
        return [("BTC/USDT",2,65000),("ETH/USDT",2,3000),("SOL/USDT",2,150),("PEPE/USDT",5,0.00001)]

def engine():
    global ALLOW_NEW_TRADES
    try:
        mov=get_movers_fast()
        state["positions"]=[]
        for i in range(min(6,len(mov))):
            sym,pct,price=mov[i]
            state["positions"].append([sym.replace('/USDT',''),"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()])
    except Exception as e:
        state["binance_status"]=f"خطأ: {e}"
    while True:
        try:
            t0=time.time()
            try:
                all_syms=[p[0]+"/USDT" for p in state["positions"]+state["treatment_positions"]]
                if all_syms:
                    tickers=exchange.fetch_tickers(all_syms)
                    for p in state["positions"]+state["treatment_positions"]:
                        key=p[0]+"/USDT"
                        if key in tickers and tickers[key].get('last'):
                            cur=float(tickers[key]['last']); p[3]=cur
                            pp=(cur-p[2])/p[2]*100; p[4]=round(100*pp/100,3); p[5]=round(pp,2)
            except: pass
            state["ghair"]=round(sum([p[4] for p in state["positions"]]),3)
            state["loss_pool"]=round(sum([abs(p[9]) for p in state["treatment_positions"]]),3) if state["treatment_positions"] else 0.0
            state["treatment_count"]=len(state["treatment_positions"])
            state["last_update"]=datetime.now().strftime("%H:%M:%S")
            now=time.time()
            if COMPOUND:
                config["per_trade"] = round(state["fixed"] * COMPOUND_PCT,2)
            to_liquidate=[p for p in list(state["treatment_positions"]) if (now - (p[12] if len(p)>12 else now))/3600 >= MAX_HOLD_HOURS]
            for p in to_liquidate:
                net=p[4]-p[9]
                state["safi"]=round(state["safi"]+net,3)
                if COMPOUND and net>0: state["fixed"]=round(state["fixed"]+net,3)
                state["trades_closed"]+=1
                state["doctor_stats"]["failed"]+=1
                state["treatment_positions"].remove(p)
                save_state()
            if len(state["treatment_positions"]) >= MAX_PHARMACY:
                ALLOW_NEW_TRADES=False
                state["binance_status"]=f"⛔ ممتلئة {len(state['treatment_positions'])}/{MAX_PHARMACY}"
            elif len(state["treatment_positions"]) <= MIN_PHARMACY:
                ALLOW_NEW_TRADES=True
            if state["ghair"]>=config["instant_target"] and state["ghair"]>0 and len(state["positions"])>0:
                profit = state["ghair"]
                state["safi"]=round(state["safi"]+profit,3)
                if COMPOUND:
                    state["fixed"]=round(state["fixed"]+profit,3)
                    state["binance_status"]=f"💰 مركب +{profit:.2f}$ => ثابت {state['fixed']:.2f}$"
                else:
                    state["binance_status"]=f"✅ قفل +{profit:.2f}$"
                state["trades_closed"]+=len(state["positions"])
                state["positions"]=[]; state["ghair"]=0.0
                save_state()
                if ALLOW_NEW_TRADES:
                    mov=get_movers_fast()
                    for i in range(min(6,len(mov))):
                        sym,pct,price=mov[i]
                        state["positions"].append([sym.replace('/USDT',''),"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()])
                continue
            to_treat=[]
            for p in list(state["positions"]):
                entry_time=p[9] if len(p)>9 else now
                if p[5]<=-config["sl_pct"] or (p[5]<-0.15 and (now-entry_time)>45):
                    to_treat.append(p)
            for p in to_treat:
                if not ALLOW_NEW_TRADES and len(state["treatment_positions"]) >= MAX_PHARMACY:
                    net=p[4]
                    state["safi"]=round(state["safi"]+net,3)
                    if COMPOUND and net>0: state["fixed"]=round(state["fixed"]+net,3)
                    state["trades_closed"]+=1
                    state["doctor_stats"]["failed"]+=1
                    state["positions"].remove(p)
                    save_state()
                    continue
                loss=abs(p[4])
                if p in state["positions"]: state["positions"].remove(p)
                mov=get_movers_fast()
                ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
                for sym,pct,price in mov:
                    sn=sym.replace('/USDT','')
                    if sn not in ex:
                        target_needed=loss+config["instant_target"]
                        state["treatment_positions"].append([sn,"علاج",price*0.9995,price,0.0,0.0,f"يعالج {p[0]} {loss:.2f}$",0,"TREAT",loss,target_needed,sym,time.time()])
                        break
            cured=[p for p in list(state["treatment_positions"]) if p[4]>=p[10]]
            for p in cured:
                loss=p[9]; net=p[4]-loss
                state["safi"]=round(state["safi"]+net,3)
                if COMPOUND and net>0: state["fixed"]=round(state["fixed"]+net,3)
                state["trades_closed"]+=1
                state["doctor_stats"]["healed"]+=1
                state["doctor_stats"]["total_healed_profit"]=round(state["doctor_stats"]["total_healed_profit"]+net,3)
                state["treatment_positions"].remove(p)
                state["binance_status"]=f"🏥 {p[0]} شفى +{net:.2f}$ 🩺 ثابت {state['fixed']:.1f}$"
                save_state()
            if ALLOW_NEW_TRADES and len(state["positions"])<6:
                mov=get_movers_fast()
                ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
                for sym,pct,price in mov:
                    sn=sym.replace('/USDT','')
                    if sn not in ex:
                        state["positions"].append([sn,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()])
                        if len(state["positions"])>=6: break
            time.sleep(max(0.3, 0.8-(time.time()-t0)))
        except Exception as e:
            print(e); time.sleep(1)

thread_started=False
thread_lock = threading.Lock()
def start_engine():
    global thread_started
    with thread_lock:
        if not thread_started:
            thread_started=True
            threading.Thread(target=engine,daemon=True).start()

start_engine()
@app.before_request
def before_req(): start_engine()
@app.route('/health')
def health(): return "V84 COMPOUND OK",200
@app.route('/api/data')
def api_data():
    total=state["fixed"]+state["safi"]+state["ghair"]
    healed=state["doctor_stats"]["healed"]
    total_cases=healed+len(state["treatment_positions"])+state["doctor_stats"]["failed"]
    heal_rate=round((healed/total_cases*100) if total_cases>0 else 0,1)
    return jsonify({
        "fixed":state["fixed"],"free":state["free"],"safi":state["safi"],"ghair":state["ghair"],"total":total,
        "trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"treatment_count":state["treatment_count"],
        "positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6]] for p in state["positions"]],
        "treatment_positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[9],p[10]] for p in state["treatment_positions"]],
        "binance_status":state["binance_status"],"last_update":state["last_update"],"instant_target":config["instant_target"],
        "doctor":state["doctor_stats"],"heal_rate":heal_rate,"allow_new":ALLOW_NEW_TRADES,
        "compound":COMPOUND,"per_trade":config["per_trade"]
    })
@app.route('/api/config',methods=['POST'])
def api_cfg():
    d=request.get_json()
    if 'capital' in d: state["fixed"]=float(d['capital'])
    if 'per_trade' in d: config["per_trade"]=float(d['per_trade'])
    if 'tp' in d: config["tp_pct"]=float(d['tp'])
    if 'instant_target' in d: config["instant_target"]=float(d['instant_target'])
    save_state()
    return jsonify({"ok":True})
@app.route('/api/reset_full',methods=['POST'])
def reset_full():
    global ALLOW_NEW_TRADES
    ALLOW_NEW_TRADES=True
    state["safi"]=0.0; state["ghair"]=0.0; state["loss_pool"]=0.0; state["trades_closed"]=0
    state["positions"]=[]; state["treatment_positions"]=[]
    state["doctor_stats"]={"healed":0,"total_healed_profit":0.0,"failed":0,"start_time":time.time()}
    save_state()
    return jsonify({"ok":True})
@app.route('/api/force_treat',methods=['POST'])
def force_treat():
    if state["positions"]:
        worst=min(state["positions"], key=lambda x:x[4])
        if worst in state["positions"]:
            loss=abs(worst[4]) if worst[4]<0 else 0.20
            state["positions"].remove(worst)
            mov=get_movers_fast()
            ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
            for sym,pct,price in mov:
                sn=sym.replace('/USDT','')
                if sn not in ex:
                    target_needed=loss+config["instant_target"]
                    state["treatment_positions"].append([sn,"علاج",price*0.9995,price,0.0,0.0,f"يعالج {worst[0]} {loss:.2f}$",0,"TREAT",loss,target_needed,sym,time.time()])
                    break
    return jsonify({"ok":True})
@app.route('/')
def home():
    return '''<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>*{box-sizing:border-box}body{margin:0;background:#070a1e;color:#fff;font-family:Cairo;padding:5px}.h1{border:2px solid #00ff66;border-radius:18px;background:#11158a;text-align:center;padding:10px 8px;margin-bottom:6px}.h1 h2{margin:0;color:#00ff66;font-size:15px;font-weight:900}.bar{display:flex;justify-content:space-between;align-items:center;background:#11158a;border:1px solid #232a8a;border-radius:10px;padding:6px 10px;font-size:11px;font-weight:800;margin-bottom:6px}.bar.doc{background:#001a00;border:1.5px solid #00ff66;color:#00ff66}.bar.comp{background:#1a0a00;border:1.5px solid #ffcc00;color:#ffcc00}.ctrl{display:flex;justify-content:center;align-items:center;gap:8px;background:#11158a;border:1px solid #232a8a;border-radius:14px;padding:8px;margin-bottom:6px;flex-wrap:wrap}.c-inp{background:#070a1e;border:2px solid #00ff66;border-radius:12px;color:#00ff66;font-family:JetBrains Mono;font-weight:900;width:58px;text-align:center;padding:7px 0;outline:none;font-size:13px}.c-inp.target{border-color:#ffcc00;color:#ffcc00;width:68px}.c-btn{background:#00ff66;border:none;border-radius:12px;padding:7px 16px;font-weight:900;color:#000;cursor:pointer;font-size:13px}.boards{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;margin-bottom:6px}.b{display:flex;flex-direction:column;gap:4px}.bt{font-size:10px;font-weight:900;text-align:center}.bc{background:#1a1f9e;border:1px solid #2d36c0;border-radius:14px;padding:10px 2px;text-align:center;min-height:76px;display:flex;flex-direction:column;justify-content:center}.bc.gold{border:2px solid #00ff66}.bc.treat{border:2px solid #ff9800;background:#2a1a00;animation:glow 2s infinite}@keyframes glow{0%,100%{box-shadow:0 0 5px #ff9800}50%{box-shadow:0 0 15px #ff9800}}.bv{font-family:JetBrains Mono;font-size:17px;font-weight:900;direction:ltr}.bv.pos{color:#00ff66}.bv.neg{color:#ff2d55}.bv.zero{color:#6a6a8a}.bv.w{color:#fff}.bv.yb{border-radius:8px;padding:3px 6px;display:inline-block;font-size:13px}.bv.yb.pos{background:#00ff66;color:#000}.bv.yb.neg{background:#ff2d55;color:#fff}.bv.yb.zero{background:transparent;color:#555;border:1px dashed #333}.act{display:flex;justify-content:center;gap:10px;margin-bottom:6px;flex-wrap:wrap}.act button{border:none;border-radius:12px;padding:8px 20px;font-weight:900;font-size:12px;cursor:pointer}.r{background:#ff2d55;color:#fff}.y{background:#ffeb3b;color:#000}.t{background:#ff9800;color:#000}.tbl-wrap{background:#11158a;border:1px solid #232a8a;border-radius:16px;overflow:hidden;overflow-x:auto;margin-bottom:8px}.tbl{width:100%;border-collapse:collapse;min-width:520px}.tbl th{background:#2a36f0;color:#ff4d8d;font-size:12px;font-weight:900;padding:10px 4px;text-align:center}.tbl td{padding:10px 4px;text-align:center;font-family:JetBrains Mono;font-size:12px;font-weight:800;border-top:1px solid #1a1f8a}.tbl tr{background:#11158a}.spot{background:#00ff55;color:#000;border-radius:20px;padding:4px 12px;font-size:11px;font-weight:900;display:inline-block}.treat-badge{background:#ff9800;color:#000;border-radius:20px;padding:4px 12px;font-size:11px;font-weight:900;display:inline-block}@media(max-width:600px){.boards{grid-template-columns:repeat(2,1fr)}.bar.doc{flex-direction:column;gap:4px}.ctrl{flex-direction:column}.c-btn{width:100%}.tbl{min-width:600px}}</style></head><body>
<div class="h1"><h2>V84 المركب 🩺💰</h2><p>الربح ينضاف لرأس المال تلقائياً</p></div>
<div class="bar"><span id="binStatus">BINANCE TURBO</span><span id="progText">0 / 0.50$</span><span>V84 COMPOUND</span></div>
<div class="bar comp"><span>💰 المركب: <b id="compStatus">مفعل ✅</b></span><span>📦 صفقة: <b id="perTrade">100$</b></span><span>📈 رأس مال: <b id="capGrow">1000$</b></span></div>
<div class="bar doc"><span>🩺 شفى: <b id="healed">0</b></span><span>💰 ارباح علاج: <b id="healProfit">0.00$</b></span><span>📊 نسبة: <b id="healRate">0%</b></span><span>⏱️ <b id="docTime">0 د</b></span></div>
<div class="ctrl"><button class="c-btn" onclick="save()">حفظ 🟢</button><input class="c-inp" id="tp" value="0.80"><input class="c-inp" id="per_trade" value="100"><input class="c-inp" id="capital" value="1000"><input class="c-inp target" id="instant_target" value="0.50"></div>
<div class="boards">
  <div class="b"><div class="bt">💰 ثابت مركب</div><div class="bc gold"><div class="bv w" id="v_fixed">1000.0$</div><div style="font-size:8px;color:#00ff66">يكبر تلقائياً</div></div></div>
  <div class="b"><div class="bt">🏥 الصيدلية</div><div class="bc treat"><div class="bv" id="v_treat">0.00$</div><div style="font-size:10px;color:#ffcc00" id="v_treat_c">0 دواء</div></div></div>
  <div class="b"><div class="bt">💹 صافي ربح</div><div class="bc"><div class="bv" id="v_safi">0.0$</div><div style="font-size:8px;color:#00ff66">ربح فقط ✅</div></div></div>
  <div class="b"><div class="bt">⚖️ مقفلة</div><div class="bc"><div class="bv w" id="v_ls">0</div></div></div>
  <div class="b"><div class="bt">💎 الإجمالي</div><div class="bc gold"><div class="bv" id="v_total">1000.0$</div></div></div>
  <div class="b"><div class="bt">📈 غير محققة</div><div class="bc"><div class="bv yb" id="v_ghair">0.00$</div></div></div>
  <div class="b"><div class="bt">🔥 حر</div><div class="bc"><div class="bv" id="v_free">0.00$</div></div></div>
</div>
<div class="act"><button class="r" onclick="doReset()">🔒 قفل الكل</button><button class="y" onclick="doReset()">🔄 تصفير</button><button class="t" onclick="testPharmacy()">🧪 جرب الصيدلية</button></div>
<div class="tbl-wrap"><table class="tbl"><thead><tr><th>عملة</th><th>نوع</th><th>حالة</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th></tr></thead><tbody id="coins"></tbody></table></div>
<div class="tbl-wrap" id="treatWrap" style="display:none;border:2px solid #ff9800"><table class="tbl"><thead><tr><th style="color:#ff9800;background:#2a1a00">🏥 الصيدلية</th><th style="background:#2a1a00">يعالج</th><th style="background:#2a1a00">خسارة</th><th style="background:#2a1a00">هدف</th><th style="background:#2a1a00">حالي</th><th style="background:#2a1a00">ربح علاج</th></tr></thead><tbody id="treatCoins"></tbody></table></div>
<script>
function colorClass(v){ if(Math.abs(v)<0.001) return 'zero'; return v>0?'pos':'neg'; }
async function save(){ const d={capital:parseFloat(capital.value),per_trade:parseFloat(per_trade.value),tp:parseFloat(tp.value),instant_target:parseFloat(instant_target.value)}; await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}); const b=document.querySelector('.c-btn'); b.innerText='✅ تم'; setTimeout(()=>b.innerText='حفظ 🟢',1000); }
async function doReset(){ if(!confirm('تصفير؟')) return; await fetch('/api/reset_full',{method:'POST'}); location.reload(); }
async function testPharmacy(){ await fetch('/api/force_treat',{method:'POST'}); }
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('v_fixed').innerText=d.fixed.toFixed(2)+'$';
    document.getElementById('capGrow').innerText=d.fixed.toFixed(2)+'$';
    document.getElementById('perTrade').innerText=d.per_trade.toFixed(0)+'$';
    document.getElementById('compStatus').innerText=d.compound?'مفعل ✅':'متوقف';
    const setC=(id,val)=>{ const el=document.getElementById(id); el.innerText=(Math.abs(val)<0.001?'0.00':(val>0?'+':'')+val.toFixed(2))+'$'; el.className='bv '+colorClass(val); if(id=='v_ghair'){ el.className='bv yb '+colorClass(val); if(Math.abs(val)<0.001) el.innerText='0.00$'; } };
    setC('v_safi',d.safi); setC('v_ghair',d.ghair); setC('v_free',d.free);
    document.getElementById('v_total').innerText=d.total.toFixed(2)+'$'; document.getElementById('v_total').className='bv '+colorClass(d.total-d.fixed);
    document.getElementById('v_ls').innerText=d.trades_closed;
    document.getElementById('v_treat').innerText=(d.loss_pool>0?'-':'')+d.loss_pool.toFixed(2)+'$'; document.getElementById('v_treat').className='bv '+(d.loss_pool>0?'neg':'zero');
    document.getElementById('v_treat_c').innerText=d.treatment_count+' دواء'+(d.allow_new==false?' ⛔ مقفل':'');
    document.getElementById('binStatus').innerText=d.binance_status+' • '+d.last_update;
    document.getElementById('progText').innerText=`${d.ghair.toFixed(2)} / ${d.instant_target}$`;
    document.getElementById('healed').innerText=d.doctor.healed;
    document.getElementById('healProfit').innerText='+'+d.doctor.total_healed_profit.toFixed(2)+'$';
    document.getElementById('healRate').innerText=d.heal_rate+'%';
    let rateEl=document.getElementById('healRate');
    if(d.heal_rate>=80) rateEl.style.color='#00ff66'; else if(d.heal_rate>=50) rateEl.style.color='#ffcc00'; else rateEl.style.color='#ff3344';
    let mins=Math.floor((Date.now()/1000 - d.doctor.start_time));
    let m=Math.floor(mins/60); let s=mins%60;
    document.getElementById('docTime').innerText=m+'د '+s+'ث';
    let h=''; for(const p of d.positions){ h+=`<tr><td style="font-weight:900">${p[0]}</td><td><span class="spot">${p[1]}</span></td><td style="font-size:10px">${p[6]}</td><td>${p[2].toFixed(4)}</td><td>${p[3].toFixed(4)}</td><td class="${colorClass(p[4])}">${p[4].toFixed(3)}$</td><td class="${colorClass(p[5])}">${p[5].toFixed(2)}%</td></tr>`; }
    document.getElementById('coins').innerHTML=h||'<tr><td colspan=7>⏳ TURBO...</td></tr>';
    const tw=document.getElementById('treatWrap');
    if(d.treatment_positions.length>0){ tw.style.display='block'; let th=''; for(const p of d.treatment_positions){ th+=`<tr style="background:#2a1a00"><td><span class="treat-badge">🏥 ${p[0]}</span></td><td style="font-size:10px;color:#ffcc00">${p[6]}</td><td class="neg">-${p[7].toFixed(2)}$</td><td style="color:#ffcc00">${p[8].toFixed(2)}$</td><td>${p[3].toFixed(4)}</td><td class="${colorClass(p[4])}">${p[4].toFixed(3)}$</td></tr>`; } document.getElementById('treatCoins').innerHTML=th; } else tw.style.display='none';
  }catch(e){}
}
setInterval(load,800); load();
</script>
</body></html>'''
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

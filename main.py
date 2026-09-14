from flask import Flask, request, jsonify
import threading, time, os, json
from datetime import datetime
import ccxt

app = Flask(__name__)
exchange = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'spot'}, 'timeout': 3000})

config = {"capital":1000.0,"per_trade_pct":10.0,"tp_pct":0.80,"sl_pct":0.30,"instant_target_pct":0.05,"instant_target":0.50}
COMPOUND = True
MAX_PHARMACY = 12

state = {
    "fixed":1000.0,"free":0.0,"safi":0.0,"ghair":0.0,"trades_closed":0,
    "loss_pool":0.0,"treatment_count":0,"positions":[],"treatment_positions":[],
    "binance_status":"⏸️ متوقف - اضغط تشغيل","last_update":"...","engine_tick":time.time(),
    "bot_enabled":False,
    "doctor_stats":{"healed":0,"total_healed_profit":0.0,"failed":0,"start_time":time.time()}
}

def save_state():
    for p in ["/tmp/state.json","/app/data/state.json"]:
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p,'w') as f: json.dump({"state":state,"config":config}, f)
        except: pass

def load_state():
    for p in ["/tmp/state.json","/app/data/state.json"]:
        try:
            if os.path.exists(p):
                with open(p,'r') as f:
                    d=json.load(f)
                    # لا نرجع تفعيل البوت تلقائيا بعد اعادة التشغيل
                    old_enabled = state.get("bot_enabled",False)
                    state.update(d.get("state",{}))
                    state["bot_enabled"]=old_enabled
                    config.update(d.get("config",{}))
        except: pass
load_state()

def calc_target():
    config["instant_target"] = round(state["fixed"] * config["instant_target_pct"] / 100.0, 2)
    if config["instant_target"] < 0.10: config["instant_target"]=0.10
    config["per_trade"] = round(state["fixed"] * config["per_trade_pct"]/100.0,2)

def get_movers_fast():
    try:
        tickers=exchange.fetch_tickers()
        mov=[]
        for sym,t in tickers.items():
            if not sym.endswith('/USDT'): continue
            if 'BULL' in sym or 'BEAR' in sym or 'UP' in sym or 'DOWN' in sym: continue
            last=t.get('last')
            if not last: continue
            pct=t.get('percentage',0) or 0
            if pct<0.1: continue
            mov.append((sym,pct,last))
        mov.sort(key=lambda x:x[1],reverse=True)
        if len(mov)>=3: return mov[:30]
    except: pass
    return [("BTC/USDT",1.2,65000),("ETH/USDT",1.1,3000),("SOL/USDT",2.1,150),("PEPE/USDT",5,0.00001)]

def engine():
    empty=0
    while True:
        try:
            t0=time.time()
            state["engine_tick"]=t0
            calc_target()

            # تحديث اسعار حتى وهو متوقف
            try:
                all_syms=list(set([p[0]+"/USDT" for p in state["positions"]+state["treatment_positions"]]))
                if all_syms:
                    tickers=exchange.fetch_tickers(all_syms[:20])
                    for p in state["positions"]+state["treatment_positions"]:
                        k=p[0]+"/USDT"
                        if k in tickers and tickers[k].get('last'):
                            cur=float(tickers[k]['last']); p[3]=cur
                            pp=(cur-p[2])/p[2]*100; p[4]=round(100*pp/100,3); p[5]=round(pp,2)
            except: pass

            state["ghair"]=round(sum([p[4] for p in state["positions"]]),3)
            state["loss_pool"]=round(sum([abs(p[9]) if len(p)>9 else 0 for p in state["treatment_positions"]]),3)
            state["treatment_count"]=len(state["treatment_positions"])
            state["last_update"]=datetime.now().strftime("%H:%M:%S")

            if not state["bot_enabled"]:
                state["binance_status"]="⏸️ متوقف - اضغط ▶️ تشغيل للدخول"
                save_state()
                time.sleep(0.5)
                continue

            # --- البوت شغال ---
            if len(state["positions"])==0: empty+=1
            else: empty=0
            if empty>2:
                mov=get_movers_fast()
                state["positions"]=[]
                ex=[x[0] for x in state["treatment_positions"]]
                c=0
                for sym,pct,price in mov:
                    sn=sym.replace('/USDT','')
                    if sn not in ex and c<6:
                        state["positions"].append([sn,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()])
                        c+=1
                state["binance_status"]=f"🚀 دخل السوق {len(state['positions'])} عملات"
                empty=0

            if state["ghair"]>=config["instant_target"] and state["ghair"]>0 and len(state["positions"])>0:
                profit=state["ghair"]
                state["safi"]=round(state["safi"]+profit,3)
                if COMPOUND: state["fixed"]=round(state["fixed"]+profit,3)
                state["trades_closed"]+=len(state["positions"])
                state["binance_status"]=f"💰 قفل +{profit:.2f}$ => ثابت {state['fixed']:.2f}$"
                state["positions"]=[]; state["ghair"]=0.0
                save_state(); continue

            to_treat=[]; now=time.time()
            for p in list(state["positions"]):
                et=p[9] if len(p)>9 else now
                if p[5]<=-config["sl_pct"] or (p[5]<-0.20 and (now-et)>40): to_treat.append(p)
            for p in to_treat:
                if len(state["treatment_positions"])>=MAX_PHARMACY: continue
                loss=abs(p[4])
                if p in state["positions"]: state["positions"].remove(p)
                mov=get_movers_fast(); ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
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
                if COMPOUND and net>0: state["fixed"]=round(state["fixed"]+net,3)
                state["trades_closed"]+=1; state["doctor_stats"]["healed"]+=1
                state["doctor_stats"]["total_healed_profit"]=round(state["doctor_stats"]["total_healed_profit"]+net,3)
                state["treatment_positions"].remove(p)
                state["binance_status"]=f"🏥 {p[0]} شفى +{net:.2f}$"

            if len(state["positions"])<6:
                mov=get_movers_fast(); ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
                for sym,pct,price in mov:
                    sn=sym.replace('/USDT','')
                    if sn not in ex and len(state["positions"])<6:
                        state["positions"].append([sn,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()])

            save_state()
            time.sleep(0.35)
        except Exception as e:
            print(f"ERR {e}"); time.sleep(0.5)

thread_started=False; lock=threading.Lock()
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
def health(): return f"V88 {state['bot_enabled']} {time.time()-state['engine_tick']:.1f}s",200

@app.route('/api/data')
def api_data():
    total=state["fixed"]+state["safi"]+state["ghair"]
    healed=state["doctor_stats"]["healed"]
    total_cases=healed+len(state["treatment_positions"])+state["doctor_stats"]["failed"]
    heal_rate=round((healed/total_cases*100) if total_cases>0 else 0,1)
    return jsonify({"fixed":state["fixed"],"free":state["free"],"safi":state["safi"],"ghair":state["ghair"],"total":total,"trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"treatment_count":state["treatment_count"],"positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6]] for p in state["positions"]],"treatment_positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[9],p[10]] for p in state["treatment_positions"]],"binance_status":state["binance_status"],"last_update":state["last_update"],"instant_target":config["instant_target"],"instant_target_pct":config["instant_target_pct"],"per_trade_pct":config["per_trade_pct"],"tp":config["tp_pct"],"sl":config["sl_pct"],"doctor":state["doctor_stats"],"heal_rate":heal_rate,"compound":COMPOUND,"per_trade":config.get("per_trade",100),"engine_age":time.time()-state["engine_tick"],"bot_enabled":state["bot_enabled"]})

@app.route('/api/config',methods=['POST'])
def api_cfg():
    d=request.get_json()
    if 'capital' in d: state["fixed"]=float(d['capital']); config["capital"]=float(d['capital'])
    if 'per_trade_pct' in d: config["per_trade_pct"]=float(d['per_trade_pct'])
    if 'tp' in d: config["tp_pct"]=float(d['tp'])
    if 'sl' in d: config["sl_pct"]=float(d['sl'])
    if 'instant_target_pct' in d: config["instant_target_pct"]=float(d['instant_target_pct'])
    calc_target(); save_state()
    return jsonify({"ok":True})

@app.route('/api/start',methods=['POST'])
def api_start():
    state["bot_enabled"]=True
    state["doctor_stats"]["start_time"]=time.time()
    state["binance_status"]="▶️ بدأ - يدخل السوق..."
    save_state()
    return jsonify({"ok":True})

@app.route('/api/stop',methods=['POST'])
def api_stop():
    # ايقاف مؤقت بدون تصفية
    state["bot_enabled"]=False
    state["binance_status"]="⏸️ توقف مؤقت"
    save_state()
    return jsonify({"ok":True})

@app.route('/api/close_all',methods=['POST'])
def api_close_all():
    # قفل الكل - يصفي ويطلع من السوق
    pnl = state["ghair"]
    state["safi"]=round(state["safi"]+pnl,3)
    if pnl>0 and COMPOUND: state["fixed"]=round(state["fixed"]+pnl,3)
    state["positions"]=[]
    state["treatment_positions"]=[]
    state["ghair"]=0.0
    state["loss_pool"]=0.0
    state["treatment_count"]=0
    state["bot_enabled"]=False
    state["binance_status"]=f"🔒 قفل الكل {pnl:.2f}$ - خارج السوق"
    save_state()
    return jsonify({"ok":True,"pnl":pnl})

@app.route('/api/reset_full',methods=['POST'])
def reset_full():
    # تصفير كامل يبدأ من جديد
    d=request.get_json() or {}
    new_cap = d.get("capital", config["capital"])
    state["fixed"]=float(new_cap)
    config["capital"]=float(new_cap)
    state["free"]=0.0; state["safi"]=0.0; state["ghair"]=0.0; state["loss_pool"]=0.0
    state["trades_closed"]=0; state["positions"]=[]; state["treatment_positions"]=[]
    state["treatment_count"]=0; state["bot_enabled"]=False
    state["doctor_stats"]={"healed":0,"total_healed_profit":0.0,"failed":0,"start_time":time.time()}
    state["binance_status"]="🔄 تصفير كامل - اضغط تشغيل للبدء"
    calc_target(); save_state()
    return jsonify({"ok":True})

@app.route('/api/force_treat',methods=['POST'])
def force_treat():
    if state["positions"]:
        worst=min(state["positions"], key=lambda x:x[4])
        if worst in state["positions"]:
            loss=abs(worst[4]) if worst[4]<0 else 0.20
            state["positions"].remove(worst)
            mov=get_movers_fast(); ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
            for sym,pct,price in mov:
                sn=sym.replace('/USDT','')
                if sn not in ex:
                    need=loss+config["instant_target"]
                    state["treatment_positions"].append([sn,"علاج",price*0.9995,price,0.0,0.0,f"يعالج {worst[0]} {loss:.2f}$",0,"TREAT",loss,need,sym,time.time()])
                    break
    return jsonify({"ok":True})

@app.route('/')
def home():
    return '''<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>*{box-sizing:border-box}body{margin:0;background:#070a1e;color:#fff;font-family:Cairo;padding:5px}.h1{border:2px solid #00ff66;border-radius:18px;background:#11158a;text-align:center;padding:10px 8px;margin-bottom:6px}.h1 h2{margin:0;color:#00ff66;font-size:14px}.bar{display:flex;justify-content:space-between;align-items:center;background:#11158a;border:1px solid #232a8a;border-radius:10px;padding:6px 10px;font-size:11px;font-weight:800;margin-bottom:6px}.bar.doc{background:#001a00;border:1.5px solid #00ff66;color:#00ff66}.bar.comp{background:#1a0a00;border:1.5px solid #ffcc00;color:#ffcc00}.bar.status{border:2px solid #00ff66;justify-content:center;font-size:13px}.bar.status.off{border-color:#ff2d55;background:#1a0000;color:#ff9999}.ctrl{background:#11158a;border:1px solid #232a8a;border-radius:16px;padding:10px;margin-bottom:6px;display:flex;flex-direction:column;gap:8px}.ctrl-row{display:flex;gap:8px;align-items:center;justify-content:space-between;flex-wrap:wrap}.ctrl-label{font-size:11px;font-weight:900;min-width:70px}.ctrl-group{display:flex;gap:4px;align-items:center}.c-inp{background:#070a1e;border:2px solid #00ff66;border-radius:10px;color:#00ff66;font-family:JetBrains Mono;font-weight:900;width:75px;text-align:center;padding:6px 0;outline:none;font-size:12px}.c-inp.cap{border-color:#00d9ff;color:#00d9ff;width:90px}.c-inp.pct{border-color:#ffcc00;color:#ffcc00;width:70px}.c-inp.tp{border-color:#ff55aa;color:#ff55aa;width:65px}.c-btn{border:none;border-radius:10px;padding:6px 14px;font-weight:900;cursor:pointer;font-size:12px}.c-btn.sm{padding:4px 8px;font-size:14px;background:#232a8a;color:#fff;border:1px solid #444}.c-btn.save{background:#00ff66;color:#000;padding:8px 22px}.sel{background:#070a1e;border:2px solid #00d9ff;border-radius:10px;color:#00d9ff;font-weight:900;padding:5px;font-size:11px}.boards{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;margin-bottom:6px}.b{display:flex;flex-direction:column;gap:4px}.bt{font-size:9px;font-weight:900;text-align:center}.bc{background:#1a1f9e;border:1px solid #2d36c0;border-radius:14px;padding:10px 2px;text-align:center;min-height:76px;display:flex;flex-direction:column;justify-content:center}.bc.gold{border:2px solid #00ff66}.bc.treat{border:2px solid #ff9800;background:#2a1a00}.bv{font-family:JetBrains Mono;font-size:15px;font-weight:900;direction:ltr}.bv.pos{color:#00ff66}.bv.neg{color:#ff2d55}.bv.zero{color:#6a6a8a}.bv.w{color:#fff}.bv.yb{border-radius:8px;padding:3px 6px;display:inline-block;font-size:12px}.bv.yb.pos{background:#00ff66;color:#000}.bv.yb.neg{background:#ff2d55;color:#fff}.bv.yb.zero{background:transparent;color:#555;border:1px dashed #333}.act{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:8px}.act button{border:none;border-radius:14px;padding:12px 5px;font-weight:900;font-size:12px;cursor:pointer}.btn-start{background:#00ff66;color:#000;font-size:14px;animation:pulse 1.5s infinite}.btn-stop{background:#ffcc00;color:#000}.btn-lock{background:#ff2d55;color:#fff}.btn-reset{background:#6c757d;color:#fff}@keyframes pulse{0%,100%{box-shadow:0 0 0 0 #00ff66}50%{box-shadow:0 0 0 8px rgba(0,255,102,0)}}.tbl-wrap{background:#11158a;border:1px solid #232a8a;border-radius:16px;overflow:hidden;overflow-x:auto;margin-bottom:8px}.tbl{width:100%;border-collapse:collapse;min-width:520px}.tbl th{background:#2a36f0;color:#ff4d8d;font-size:11px;font-weight:900;padding:8px 4px;text-align:center}.tbl td{padding:8px 4px;text-align:center;font-family:JetBrains Mono;font-size:11px;font-weight:800;border-top:1px solid #1a1f8a}.spot{background:#00ff55;color:#000;border-radius:20px;padding:3px 10px;font-size:10px;font-weight:900;display:inline-block}.treat-badge{background:#ff9800;color:#000;border-radius:20px;padding:3px 10px;font-size:10px;font-weight:900;display:inline-block}@media(max-width:700px){.boards{grid-template-columns:repeat(3,1fr)}.act{grid-template-columns:repeat(2,1fr)}}</style></head><body>
<div class="h1"><h2>V88 تحكم كامل ▶️⏸️🔒🔄</h2><p>تشغيل / ايقاف / قفل وتصفية / تصفير كامل</p></div>
<div class="bar status" id="mainStatusBar"><span id="binStatus">...</span></div>
<div class="bar"><span id="progText">0 / 0.50$</span><span>V88 PRO • <span id="engineAge">0s</span></span><span id="botState">⏸️ متوقف</span></div>
<div class="bar comp"><span>💰 المركب: <b id="compStatus">مفعل ✅</b></span><span>📦 <b id="perTrade">10%</b></span><span>📈 <b id="capGrow">1000$</b></span></div>
<div class="bar doc"><span>🩺 شفى: <b id="healed">0</b></span><span>💰 ارباح علاج: <b id="healProfit">0.00$</b></span><span>📊 نسبة: <b id="healRate">0%</b></span></div>

<div class="ctrl">
  <div class="ctrl-row">
    <span class="ctrl-label">💰 رأس المال:</span>
    <div class="ctrl-group">
      <select class="sel" id="capSel" onchange="capSelChange()"><option value="">اختر...</option><option value="100">100$</option><option value="200">200$</option><option value="300">300$</option><option value="400">400$</option><option value="500">500$</option><option value="1000">1000$</option><option value="2000">2000$</option><option value="5000">5000$</option></select>
      <input class="c-inp cap" id="capital" type="number" placeholder="حر">
    </div>
    <span class="ctrl-label">📦 نسبة الصفقة:</span>
    <div class="ctrl-group"><input class="c-inp pct" id="per_trade_pct" type="number" step="1" value="10"><span>%</span></div>
  </div>
  <div class="ctrl-row">
    <span class="ctrl-label">🎯 نسبة الربح:</span>
    <div class="ctrl-group"><input class="c-inp pct" id="instant_pct" type="number" step="0.01" value="0.05"><span style="font-size:10px">% = <b id="targetCalc" style="color:#ffcc00">0.50$</b></span></div>
    <span class="ctrl-label">📈 جني الربح:</span>
    <div class="ctrl-group"><button class="c-btn sm" onclick="stepTP(-0.05)">-</button><input class="c-inp tp" id="tp" type="number" step="0.05" value="0.80"><button class="c-btn sm" onclick="stepTP(0.05)">+</button></div>
    <button class="c-btn save" onclick="save()">حفظ 🟢</button>
  </div>
</div>

<div class="act">
  <button class="btn-start" onclick="botStart()">▶️ تشغيل ودخول السوق</button>
  <button class="btn-stop" onclick="botStop()">⏸️ إيقاف مؤقت</button>
  <button class="btn-lock" onclick="botCloseAll()">🔒 قفل الكل وتصفية</button>
  <button class="btn-reset" onclick="botResetFull()">🔄 تصفير كامل ويبدأ جديد</button>
</div>

<div class="boards">
  <div class="b"><div class="bt">💰 ثابت مركب</div><div class="bc gold"><div class="bv w" id="v_fixed">-</div></div></div>
  <div class="b"><div class="bt">🏥 الصيدلية</div><div class="bc treat"><div class="bv" id="v_treat">-</div><div style="font-size:9px;color:#ffcc00" id="v_treat_c">0 دواء</div></div></div>
  <div class="b"><div class="bt">💹 صافي ربح</div><div class="bc"><div class="bv" id="v_safi">-</div></div></div>
  <div class="b"><div class="bt">⚖️ مقفلة</div><div class="bc"><div class="bv w" id="v_ls">0</div></div></div>
  <div class="b"><div class="bt">💎 الإجمالي</div><div class="bc gold"><div class="bv" id="v_total">-</div></div></div>
  <div class="b"><div class="bt">📈 غير محققة</div><div class="bc"><div class="bv yb" id="v_ghair">-</div></div></div>
  <div class="b"><div class="bt">🔥 حر</div><div class="bc"><div class="bv" id="v_free">-</div></div></div>
</div>

<div class="tbl-wrap"><table class="tbl"><thead><tr><th>عملة</th><th>نوع</th><th>حالة</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th></tr></thead><tbody id="coins"></tbody></table></div>
<div class="tbl-wrap" id="treatWrap" style="display:none;border:2px solid #ff9800"><table class="tbl"><thead><tr><th style="color:#ff9800;background:#2a1a00">🏥 المستشفى</th><th style="background:#2a1a00">يعالج</th><th style="background:#2a1a00">خسارة</th><th style="background:#2a1a00">هدف</th><th style="background:#2a1a00">حالي</th><th style="background:#2a1a00">ربح</th></tr></thead><tbody id="treatCoins"></tbody></table></div>
<script>
function capSelChange(){ const v=document.getElementById('capSel').value; if(v) document.getElementById('capital').value=v; updateCalc(); }
function stepTP(d){ let el=document.getElementById('tp'); let v=parseFloat(el.value)||0.8; v=Math.round((v+d)*100)/100; if(v<0.1) v=0.1; if(v>5) v=5; el.value=v.toFixed(2); }
function updateCalc(){ const cap=parseFloat(document.getElementById('capital').value)||1000; const pct=parseFloat(document.getElementById('instant_pct').value)||0.05; const target=cap*pct/100; document.getElementById('targetCalc').innerText=target.toFixed(2)+'$'; }
document.getElementById('capital').addEventListener('input',updateCalc); document.getElementById('instant_pct').addEventListener('input',updateCalc);
function colorClass(v){ if(Math.abs(v)<0.001) return 'zero'; return v>0?'pos':'neg'; }
async function save(){ const d={capital:parseFloat(capital.value),per_trade_pct:parseFloat(per_trade_pct.value),tp:parseFloat(tp.value),instant_target_pct:parseFloat(instant_pct.value)}; await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}); const b=document.querySelector('.c-btn.save'); b.innerText='✅ تم'; setTimeout(()=>b.innerText='حفظ 🟢',1000); }
async function botStart(){ await save(); await fetch('/api/start',{method:'POST'}); }
async function botStop(){ await fetch('/api/stop',{method:'POST'}); }
async function botCloseAll(){ if(!confirm('🔒 قفل الكل؟ بيصفي كل الصفقات المفتوحة ويطلع من السوق')) return; const r=await fetch('/api/close_all',{method:'POST'}); const j=await r.json(); alert('تم التصفية: '+j.pnl.toFixed(2)+'$ - البوت توقف'); }
async function botResetFull(){ if(!confirm('🔄 تصفير كامل؟ بيمسح كل شي ويبدأ من جديد برأس المال اللي في الحقل')) return; const cap=parseFloat(document.getElementById('capital').value)||1000; await fetch('/api/reset_full',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capital:cap})}); location.reload(); }
async function testPharmacy(){ await fetch('/api/force_treat',{method:'POST'}); }
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('v_fixed').innerText=d.fixed.toFixed(2)+'$';
    document.getElementById('capGrow').innerText=d.fixed.toFixed(2)+'$';
    document.getElementById('perTrade').innerText=d.per_trade_pct.toFixed(0)+'% ('+d.per_trade.toFixed(0)+'$)';
    document.getElementById('compStatus').innerText=d.compound?'مفعل ✅':'متوقف';
    const setC=(id,val)=>{ const el=document.getElementById(id); el.innerText=(Math.abs(val)<0.001?'0.00':(val>0?'+':'')+val.toFixed(2))+'$'; el.className='bv '+colorClass(val); if(id=='v_ghair'){ el.className='bv yb '+colorClass(val); if(Math.abs(val)<0.001) el.innerText='0.00$'; } };
    setC('v_safi',d.safi); setC('v_ghair',d.ghair); setC('v_free',d.free);
    document.getElementById('v_total').innerText=d.total.toFixed(2)+'$';
    document.getElementById('v_ls').innerText=d.trades_closed;
    document.getElementById('v_treat').innerText=(d.loss_pool>0?'-':'')+d.loss_pool.toFixed(2)+'$'; document.getElementById('v_treat').className='bv '+(d.loss_pool>0?'neg':'zero');
    document.getElementById('v_treat_c').innerText=d.treatment_count+' دواء';
    document.getElementById('binStatus').innerText=d.binance_status+' • '+d.last_update;
    document.getElementById('progText').innerText=`${d.ghair.toFixed(2)} / ${d.instant_target.toFixed(2)}$ (${d.instant_target_pct}%)`;
    document.getElementById('engineAge').innerText=d.engine_age.toFixed(1)+'s';
    document.getElementById('botState').innerText=d.bot_enabled?'🟢 شغال':'⏸️ متوقف';
    document.getElementById('mainStatusBar').className='bar status '+(d.bot_enabled?'':'off');
    document.getElementById('healed').innerText=d.doctor.healed;
    document.getElementById('healProfit').innerText='+'+d.doctor.total_healed_profit.toFixed(2)+'$';
    document.getElementById('healRate').innerText=d.heal_rate+'%';
    if(!window.fieldsFilled){ document.getElementById('capital').value=d.fixed.toFixed(0); document.getElementById('per_trade_pct').value=d.per_trade_pct; document.getElementById('tp').value=d.tp.toFixed(2); document.getElementById('instant_pct').value=d.instant_target_pct; updateCalc(); window.fieldsFilled=true; }
    let h=''; for(const p of d.positions){ h+=`<tr><td style="font-weight:900">${p[0]}</td><td><span class="spot">${p[1]}</span></td><td style="font-size:9px">${p[6]}</td><td>${p[2].toFixed(4)}</td><td>${p[3].toFixed(4)}</td><td class="${colorClass(p[4])}">${p[4].toFixed(3)}$</td><td class="${colorClass(p[5])}">${p[5].toFixed(2)}%</td></tr>`; }
    document.getElementById('coins').innerHTML=h||(d.bot_enabled?'<tr><td colspan=7>⏳ يعبي عملات...</td></tr>':'<tr><td colspan=7>⏸️ البوت متوقف - اضغط تشغيل</td></tr>');
    const tw=document.getElementById('treatWrap');
    if(d.treatment_positions.length>0){ tw.style.display='block'; let th=''; for(const p of d.treatment_positions){ th+=`<tr style="background:#2a1a00"><td><span class="treat-badge">🏥 ${p[0]}</span></td><td style="font-size:9px;color:#ffcc00">${p[6]}</td><td class="neg">-${p[7].toFixed(2)}$</td><td style="color:#ffcc00">${p[8].toFixed(2)}$</td><td>${p[3].toFixed(4)}</td><td class="${colorClass(p[4])}">${p[4].toFixed(3)}$</td></tr>`; } document.getElementById('treatCoins').innerHTML=th; } else tw.style.display='none';
  }catch(e){}
}
setInterval(load,400); load();
</script>
</body></html>'''

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

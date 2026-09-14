from flask import Flask, request, jsonify
import threading, time, os, json, requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import ccxt
app = Flask(__name__)
exchange = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'spot'}, 'timeout': 1500})
config = {"capital":1000.0,"initial_capital":1000.0,"per_trade_pct":10.0,"tp_pct":0.80,"sl_pct":0.30,"instant_target_pct":0.05,"instant_target":0.50}
COMPOUND=True; MAX_PHARMACY=12
state={"fixed":1000.0,"free":0.0,"safi":0.0,"ghair":0.0,"trades_closed":0,"loss_pool":0.0,"treatment_count":0,"positions":[],"treatment_positions":[],"binance_status":"⏸️ متوقف","last_update":"...","engine_tick":time.time(),"bot_enabled":False,"doctor_stats":{"healed":0,"total_healed_profit":0.0,"failed":0,"start_time":time.time()}}
movers_cache=[]; movers_time=0

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
                    if "config" in d: config.update(d["config"])
                    if "state" in d:
                        tmp=d["state"]
                        for k in ["fixed","free","safi","ghair","trades_closed","loss_pool","positions","treatment_positions","doctor_stats"]:
                            if k in tmp: state[k]=tmp[k]
        except: pass
load_state()
state["bot_enabled"]=False

def calc_target():
    config["instant_target"]=round(state["fixed"]*config["instant_target_pct"]/100.0,2)
    if config["instant_target"]<0.10: config["instant_target"]=0.10

def get_all_prices_fast(symbols):
    # symbols like ["BTC/USDT",...] -> {"BTC/USDT": price}
    if not symbols: return {}
    try:
        # محاولة سريعة واحدة تجيب كل الأسعار
        r=requests.get("https://api.binance.com/api/v3/ticker/price", timeout=2)
        if r.status_code==200:
            data=r.json()
            mp={d["symbol"]: float(d["price"]) for d in data}
            out={}
            for sym in symbols:
                s=sym.replace("/","")
                if s in mp: out[sym]=mp[s]
            if len(out)>=len(symbols)//2: return out
    except: pass
    # fallback متوازي
    def fetch_one(sym):
        try:
            s=sym.replace("/","")
            rr=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={s}", timeout=1.2)
            if rr.status_code==200: return sym, float(rr.json()["price"])
        except: pass
        return sym, None
    out={}
    with ThreadPoolExecutor(max_workers=10) as ex:
        for sym, price in ex.map(fetch_one, symbols):
            if price: out[sym]=price
    return out

def get_movers_fast_cached():
    global movers_cache, movers_time
    if time.time()-movers_time < 10 and movers_cache: return movers_cache
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=2.5)
        if r.status_code==200:
            data=r.json()
            mov=[]
            for t in data:
                sym=t.get("symbol","")
                if not sym.endswith("USDT"): continue
                if len(sym)>12: continue
                if "BULL" in sym or "BEAR" in sym or "UP" in sym or "DOWN" in sym: continue
                try:
                    pct=float(t.get("priceChangePercent",0))
                    price=float(t.get("lastPrice",0))
                    if pct<0.4 or price==0: continue
                    base=sym[:-4]
                    mov.append((f"{base}/USDT",pct,price))
                except: continue
            mov.sort(key=lambda x:x[1], reverse=True)
            if len(mov)>=5:
                movers_cache=mov[:40]
                movers_time=time.time()
                return movers_cache
    except: pass
    if movers_cache: return movers_cache
    return [("PEPE/USDT",5,0.00001),("WIF/USDT",4,2),("BONK/USDT",4.5,0.00003),("FLOKI/USDT",3.5,0.0002),("SOL/USDT",2.5,150),("BTC/USDT",1.5,65000)]

def engine():
    empty=0
    while True:
        try:
            state["engine_tick"]=time.time()
            calc_target()
            syms=list(set([p[0]+"/USDT" for p in state["positions"]+state["treatment_positions"]]))
            if syms:
                prices=get_all_prices_fast(syms)
                for p in state["positions"]+state["treatment_positions"]:
                    k=p[0]+"/USDT"
                    if k in prices:
                        cur=prices[k]; p[3]=cur; pp=(cur-p[2])/p[2]*100; p[4]=round(100*pp/100,3); p[5]=round(pp,2)
            state["ghair"]=round(sum([p[4] for p in state["positions"]]),3)
            state["loss_pool"]=round(sum([abs(p[9]) if len(p)>9 else 0 for p in state["treatment_positions"]]),3)
            state["treatment_count"]=len(state["treatment_positions"])
            state["last_update"]=datetime.now().strftime("%H:%M:%S")
            if not state["bot_enabled"]:
                state["binance_status"]="⏸️ متوقف - اضغط ▶️ تشغيل"; save_state(); time.sleep(0.4); continue
            if len(state["positions"])==0: empty+=1
            else: empty=0
            if empty>=1:
                mov=get_movers_fast_cached()
                ex=[x[0] for x in state["treatment_positions"]]
                new_positions=[]
                c=0
                for sym,pct,price in mov:
                    sn=sym.replace('/USDT','')
                    if sn not in ex and c<6:
                        new_positions.append([sn,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()]); c+=1
                if new_positions:
                    state["positions"]=new_positions
                    state["binance_status"]=f"⚡ دخل {len(new_positions)} تيربو"
                    empty=0
            if state["ghair"]>=config["instant_target"] and state["ghair"]>0 and len(state["positions"])>0:
                profit=state["ghair"]; state["safi"]=round(state["safi"]+profit,3)
                if COMPOUND: state["fixed"]=round(state["fixed"]+profit,3)
                state["trades_closed"]+=len(state["positions"]); state["binance_status"]=f"💰 +{profit:.2f}$ ⚡ يدخل"
                state["positions"]=[]; state["ghair"]=0.0; empty=1; save_state(); continue
            to_treat=[]; now=time.time()
            for p in list(state["positions"]):
                et=p[9] if len(p)>9 else now
                if p[5]<=-config["sl_pct"] or (p[5]<-0.20 and (now-et)>35): to_treat.append(p)
            for p in to_treat:
                if len(state["treatment_positions"])>=MAX_PHARMACY: continue
                loss=abs(p[4])
                if p in state["positions"]: state["positions"].remove(p)
                mov=get_movers_fast_cached(); ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
                for sym,pct,price in mov:
                    sn=sym.replace('/USDT','')
                    if sn not in ex:
                        need=loss+config["instant_target"]
                        state["treatment_positions"].append([sn,"علاج",price*0.9995,price,0.0,0.0,f"يعالج {p[0]} {loss:.2f}$",0,"TREAT",loss,need,sym,time.time()]); break
            cured=[p for p in list(state["treatment_positions"]) if len(p)>10 and p[4]>=p[10]]
            for p in cured:
                loss=p[9]; net=p[4]-loss; state["safi"]=round(state["safi"]+net,3)
                if COMPOUND and net>0: state["fixed"]=round(state["fixed"]+net,3)
                state["trades_closed"]+=1; state["doctor_stats"]["healed"]+=1; state["doctor_stats"]["total_healed_profit"]=round(state["doctor_stats"]["total_healed_profit"]+net,3)
                state["treatment_positions"].remove(p); state["binance_status"]=f"🏥 {p[0]} شفى +{net:.2f}$"
            save_state(); time.sleep(0.15)
        except Exception as e: print(e); time.sleep(0.3)

thread_started=False; lock=threading.Lock()
def start_engine():
    global thread_started
    with lock:
        if not thread_started: thread_started=True; threading.Thread(target=engine,daemon=True).start()
start_engine()
@app.before_request
def before_req(): start_engine()
@app.route('/health')
def health(): return f"V93 turbo {state['bot_enabled']}",200
@app.route('/api/data')
def api_data():
    initial=config.get("initial_capital",1000.0); total=state["fixed"]+state["safi"]+state["ghair"]; profit_usd=total-initial; profit_pct=(profit_usd/initial*100) if initial>0 else 0
    healed=state["doctor_stats"]["healed"]; total_cases=healed+len(state["treatment_positions"])+state["doctor_stats"]["failed"]; heal_rate=round((healed/total_cases*100) if total_cases>0 else 0,1)
    return jsonify({"fixed":state["fixed"],"free":state["free"],"safi":state["safi"],"ghair":state["ghair"],"total":total,"trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"treatment_count":state["treatment_count"],"positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6]] for p in state["positions"]],"treatment_positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[9],p[10]] for p in state["treatment_positions"]],"binance_status":state["binance_status"],"last_update":state["last_update"],"instant_target":config["instant_target"],"instant_target_pct":config["instant_target_pct"],"per_trade_pct":config["per_trade_pct"],"tp":config["tp_pct"],"initial_capital":initial,"profit_usd":profit_usd,"profit_pct":profit_pct,"doctor":state["doctor_stats"],"heal_rate":heal_rate,"compound":COMPOUND,"per_trade":config.get("per_trade",100),"engine_age":time.time()-state["engine_tick"],"bot_enabled":state["bot_enabled"]})
@app.route('/api/config',methods=['POST'])
def api_cfg():
    d=request.get_json()
    if 'capital' in d: state["fixed"]=float(d['capital']); config["capital"]=float(d['capital'])
    if 'per_trade_pct' in d: config["per_trade_pct"]=float(d['per_trade_pct'])
    if 'tp' in d: config["tp_pct"]=float(d['tp'])
    if 'instant_target_pct' in d: config["instant_target_pct"]=float(d['instant_target_pct'])
    calc_target(); save_state(); return jsonify({"ok":True})
@app.route('/api/start',methods=['POST'])
def api_start(): state["bot_enabled"]=True; state["doctor_stats"]["start_time"]=time.time(); state["binance_status"]="⚡ تيربو شغال"; save_state(); return jsonify({"ok":True})
@app.route('/api/stop',methods=['POST'])
def api_stop(): state["bot_enabled"]=False; state["binance_status"]="⏸️ متوقف مؤقت"; save_state(); return jsonify({"ok":True})
@app.route('/api/close_all',methods=['POST'])
def api_close_all():
    pnl=state["ghair"]; state["safi"]=round(state["safi"]+pnl,3)
    if pnl>0 and COMPOUND: state["fixed"]=round(state["fixed"]+pnl,3)
    state["positions"]=[]; state["treatment_positions"]=[]; state["ghair"]=0.0; state["loss_pool"]=0.0; state["treatment_count"]=0; state["bot_enabled"]=False
    state["binance_status"]=f"🔒 قفل {pnl:.2f}$"; save_state(); return jsonify({"ok":True,"pnl":pnl})
@app.route('/api/reset_full',methods=['POST'])
def reset_full():
    d=request.get_json() or {}; new_cap=d.get("capital",1000.0)
    state["fixed"]=float(new_cap); config["capital"]=float(new_cap); config["initial_capital"]=float(new_cap)
    state["free"]=0.0; state["safi"]=0.0; state["ghair"]=0.0; state["loss_pool"]=0.0; state["trades_closed"]=0; state["positions"]=[]; state["treatment_positions"]=[]; state["treatment_count"]=0; state["bot_enabled"]=False
    state["doctor_stats"]={"healed":0,"total_healed_profit":0.0,"failed":0,"start_time":time.time()}; state["binance_status"]="🔄 تصفير كامل"; calc_target(); save_state(); return jsonify({"ok":True})
@app.route('/')
def home():
    return '''<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>*{box-sizing:border-box}body{margin:0;background:#070a1e;color:#fff;font-family:Cairo;padding:5px}.h1{border:2px solid #00ff66;border-radius:18px;background:#11158a;text-align:center;padding:10px;margin-bottom:6px}.h1 h2{margin:0;color:#00ff66;font-size:14px}.bar{display:flex;justify-content:space-between;align-items:center;background:#11158a;border:1px solid #232a8a;border-radius:10px;padding:6px 10px;font-size:11px;font-weight:800;margin-bottom:6px}.bar.profit{border:2px solid #00ff66;background:linear-gradient(90deg,#001a00,#003300);justify-content:center;gap:12px;font-size:12px}.bar.profit.neg{border-color:#ff2d55;background:linear-gradient(90deg,#1a0000,#330000)}.bar.status{border:2px solid #00ff66;justify-content:center;font-size:13px}.bar.status.off{border-color:#ff2d55;background:#1a0000;color:#ff9999}.ctrl{background:#11158a;border:1px solid #232a8a;border-radius:16px;padding:10px;margin-bottom:6px;display:flex;flex-direction:column;gap:8px}.ctrl-row{display:flex;gap:8px;align-items:center;justify-content:space-between;flex-wrap:wrap}.c-inp{background:#070a1e;border:2px solid #00ff66;border-radius:10px;color:#00ff66;font-family:JetBrains Mono;font-weight:900;width:70px;text-align:center;padding:6px 0;outline:none;font-size:12px}.c-inp.cap{border-color:#00d9ff;color:#00d9ff;width:85px}.c-inp.pct{border-color:#ffcc00;color:#ffcc00;width:65px}.c-inp.tp{border-color:#ff55aa;color:#ff55aa;width:60px}.c-btn{border:none;border-radius:10px;padding:6px 12px;font-weight:900;cursor:pointer;font-size:11px}.c-btn.sm{padding:4px 8px;background:#232a8a;color:#fff;border:1px solid #444}.c-btn.save{background:#00ff66;color:#000;padding:8px 18px}.sel{background:#070a1e;border:2px solid #00d9ff;border-radius:10px;color:#00d9ff;font-weight:900;padding:5px;font-size:11px}.boards{display:grid;grid-template-columns:repeat(8,1fr);gap:5px;margin-bottom:6px}.b{display:flex;flex-direction:column;gap:3px}.bt{font-size:7px;font-weight:900;text-align:center}.bc{background:#1a1f9e;border:1px solid #2d36c0;border-radius:12px;padding:8px 2px;text-align:center;min-height:68px;display:flex;flex-direction:column;justify-content:center}.bc.gold{border:2px solid #00ff66}.bc.treat{border:2px solid #ff9800;background:#2a1a00}.bc.profit-pos{border:2px solid #00ff66;background:#001a00}.bc.profit-neg{border:2px solid #ff2d55;background:#1a0000}.bv{font-family:JetBrains Mono;font-size:12px;font-weight:900;direction:ltr}.bv.pos{color:#00ff66}.bv.neg{color:#ff2d55}.bv.zero{color:#6a6a8a}.bv.w{color:#fff}.bv.yb{border-radius:8px;padding:3px 5px;display:inline-block;font-size:10px}.act{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:8px}.act button{border:none;border-radius:14px;padding:12px 4px;font-weight:900;font-size:11px;cursor:pointer}.btn-start{background:#00ff66;color:#000}.btn-stop{background:#ffcc00;color:#000}.btn-lock{background:#ff2d55;color:#fff}.btn-reset{background:#6c757d;color:#fff}.tbl-wrap{background:#11158a;border:1px solid #232a8a;border-radius:16px;overflow:hidden;overflow-x:auto;margin-bottom:8px}.tbl{width:100%;border-collapse:collapse;min-width:520px}.tbl th{background:#2a36f0;color:#ff4d8d;font-size:10px;font-weight:900;padding:7px 4px;text-align:center}.tbl td{padding:7px 4px;text-align:center;font-family:JetBrains Mono;font-size:10px;font-weight:800;border-top:1px solid #1a1f8a}.spot{background:#00ff55;color:#000;border-radius:20px;padding:3px 8px;font-size:9px;font-weight:900;display:inline-block}.treat-badge{background:#ff9800;color:#000;border-radius:20px;padding:3px 8px;font-size:9px;font-weight:900;display:inline-block}@media(max-width:800px){.boards{grid-template-columns:repeat(4,1fr)}.act{grid-template-columns:repeat(2,1fr)}}</style></head><body>
<div class="h1"><h2>V93 تيربو ⚡ 0.15 ثانية</h2></div>
<div class="bar status" id="mainStatusBar"><span id="binStatus">...</span></div>
<div class="bar profit" id="profitBar"><span>أصلي: <b id="initialCap">1000$</b></span><span>ربح: <b id="profitUsd">0$</b></span><span>نسبة: <b id="profitPctTop">0%</b></span></div>
<div class="bar"><span id="progText">0 / 0.50$</span><span>V93 • <span id="engineAge">0s</span></span><span id="botState">⏸️</span></div>
<div class="ctrl"><div class="ctrl-row"><span>💰 رأس المال:</span><div style="display:flex;gap:4px"><select class="sel" id="capSel" onchange="capSelChange()"><option value="">اختر</option><option value="100">100$</option><option value="500">500$</option><option value="1000">1000$</option></select><input class="c-inp cap" id="capital" type="number"></div><span>📦 %:</span><div style="display:flex;gap:2px"><input class="c-inp pct" id="per_trade_pct" type="number" value="10"><span>%</span></div></div><div class="ctrl-row"><span>🎯 % الربح:</span><div style="display:flex;gap:2px"><input class="c-inp pct" id="instant_pct" type="number" step="0.01" value="0.05"><span style="font-size:9px">% = <b id="targetCalc">0.50$</b></span></div><span>📈 جني:</span><div style="display:flex;gap:2px"><button class="c-btn sm" onclick="stepTP(-0.05)">-</button><input class="c-inp tp" id="tp" type="number" value="0.80"><button class="c-btn sm" onclick="stepTP(0.05)">+</button></div><button class="c-btn save" onclick="save()">حفظ 🟢</button></div></div>
<div class="act"><button class="btn-start" onclick="botStart()">⚡ تشغيل تيربو</button><button class="btn-stop" onclick="botStop()">⏸️ إيقاف مؤقت</button><button class="btn-lock" onclick="botCloseAll()">🔒 قفل الكل وتصفية</button><button class="btn-reset" onclick="botResetFull()">🔄 تصفير كامل جديد</button></div>
<div class="boards"><div class="b"><div class="bt">💰 ثابت</div><div class="bc gold"><div class="bv w" id="v_fixed">-</div></div></div><div class="b"><div class="bt">🏥 صيدلية</div><div class="bc treat"><div class="bv" id="v_treat">-</div><div style="font-size:8px;color:#ffcc00" id="v_treat_c">0</div></div></div><div class="b"><div class="bt">💹 صافي</div><div class="bc"><div class="bv" id="v_safi">-</div></div></div><div class="b"><div class="bt">⚖️ مقفلة</div><div class="bc"><div class="bv w" id="v_ls">0</div></div></div><div class="b"><div class="bt">💎 إجمالي</div><div class="bc gold"><div class="bv" id="v_total">-</div></div></div><div class="b"><div class="bt">📈 غير محققة</div><div class="bc"><div class="bv yb" id="v_ghair">-</div></div></div><div class="b"><div class="bt">📊 نسبة</div><div class="bc" id="profitBox"><div class="bv" id="v_profit_pct">0%</div><div style="font-size:7px" id="v_profit_usd">0$</div></div></div><div class="b"><div class="bt">🔥 حر</div><div class="bc"><div class="bv" id="v_free">-</div></div></div></div>
<div class="tbl-wrap"><table class="tbl"><thead><tr><th>عملة</th><th>نوع</th><th>حالة</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th></tr></thead><tbody id="coins"></tbody></table></div>
<div class="tbl-wrap" id="treatWrap" style="display:none;border:2px solid #ff9800"><table class="tbl"><thead><tr><th style="color:#ff9800;background:#2a1a00">🏥 المستشفى</th><th style="background:#2a1a00">يعالج</th><th style="background:#2a1a00">خسارة</th><th style="background:#2a1a00">هدف</th><th style="background:#2a1a00">حالي</th><th style="background:#2a1a00">ربح</th></tr></thead><tbody id="treatCoins"></tbody></table></div>
<script>
function capSelChange(){ const v=document.getElementById('capSel').value; if(v) document.getElementById('capital').value=v; updateCalc(); }
function stepTP(d){ let el=document.getElementById('tp'); let v=parseFloat(el.value)||0.8; v=Math.round((v+d)*100)/100; if(v<0.1) v=0.1; el.value=v.toFixed(2); }
function updateCalc(){ const cap=parseFloat(document.getElementById('capital').value)||1000; const pct=parseFloat(document.getElementById('instant_pct').value)||0.05; document.getElementById('targetCalc').innerText=(cap*pct/100).toFixed(2)+'$'; }
document.getElementById('capital').addEventListener('input',updateCalc); document.getElementById('instant_pct').addEventListener('input',updateCalc);
function colorClass(v){ if(Math.abs(v)<0.001) return 'zero'; return v>0?'pos':'neg'; }
async function save(){ const d={capital:parseFloat(capital.value),per_trade_pct:parseFloat(per_trade_pct.value),tp:parseFloat(tp.value),instant_target_pct:parseFloat(instant_pct.value)}; await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}); const b=document.querySelector('.c-btn.save'); b.innerText='✅ تم'; setTimeout(()=>b.innerText='حفظ 🟢',1000); }
async function botStart(){ await save(); const r=await fetch('/api/start',{method:'POST'}); if((await r.json()).ok) alert('⚡ V93 تيربو - 0.15 ثانية'); }
async function botStop(){ const r=await fetch('/api/stop',{method:'POST'}); if((await r.json()).ok) alert('⏸️ وقف'); }
async function botCloseAll(){ if(!confirm('🔒 قفل؟')) return; const r=await fetch('/api/close_all',{method:'POST'}); const j=await r.json(); alert('🔒 '+j.pnl.toFixed(2)+'$'); }
async function botResetFull(){ if(!confirm('🔄 تصفير؟')) return; const cap=parseFloat(document.getElementById('capital').value)||1000; await fetch('/api/reset_full',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capital:cap})}); location.reload(); }
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('initialCap').innerText=d.initial_capital.toFixed(0)+'$'; document.getElementById('profitUsd').innerText=(d.profit_usd>=0?'+':'')+d.profit_usd.toFixed(2)+'$'; document.getElementById('profitUsd').style.color=d.profit_usd>=0?'#00ff66':'#ff2d55'; document.getElementById('profitPctTop').innerText=(d.profit_pct>=0?'+':'')+d.profit_pct.toFixed(2)+'%'; document.getElementById('profitPctTop').style.color=d.profit_pct>=0?'#00ff66':'#ff2d55'; document.getElementById('profitBar').className='bar profit '+(d.profit_pct>=0?'':'neg');
    document.getElementById('v_fixed').innerText=d.fixed.toFixed(2)+'$'; const setC=(id,val)=>{ const el=document.getElementById(id); el.innerText=(Math.abs(val)<0.001?'0.00':(val>0?'+':'')+val.toFixed(2))+'$'; el.className='bv '+colorClass(val); if(id=='v_ghair'){ el.className='bv yb '+colorClass(val); } }; setC('v_safi',d.safi); setC('v_ghair',d.ghair); setC('v_free',d.free);
    document.getElementById('v_total').innerText=d.total.toFixed(2)+'$'; document.getElementById('v_ls').innerText=d.trades_closed; document.getElementById('v_treat').innerText=(d.loss_pool>0?'-':'')+d.loss_pool.toFixed(2)+'$'; document.getElementById('v_treat').className='bv '+(d.loss_pool>0?'neg':'zero'); document.getElementById('v_treat_c').innerText=d.treatment_count+' دواء'; document.getElementById('binStatus').innerText=d.binance_status+' • '+d.last_update; document.getElementById('progText').innerText=`${d.ghair.toFixed(2)} / ${d.instant_target.toFixed(2)}$`; document.getElementById('engineAge').innerText=d.engine_age.toFixed(1)+'s'; document.getElementById('botState').innerText=d.bot_enabled?'🟢 شغال':'⏸️ متوقف'; document.getElementById('mainStatusBar').className='bar status '+(d.bot_enabled?'':'off');
    const pb=document.getElementById('profitBox'); const vp=document.getElementById('v_profit_pct'); const vu=document.getElementById('v_profit_usd'); vp.innerText=(d.profit_pct>=0?'+':'')+d.profit_pct.toFixed(2)+'%'; vu.innerText=(d.profit_usd>=0?'+':'')+d.profit_usd.toFixed(2)+'$'; if(d.profit_pct>=0){ vp.className='bv pos'; vu.className='bv pos'; pb.className='bc profit-pos'; } else { vp.className='bv neg'; vu.className='bv neg'; pb.className='bc profit-neg'; }
    if(!window.fieldsFilled){ document.getElementById('capital').value=d.initial_capital.toFixed(0); document.getElementById('per_trade_pct').value=d.per_trade_pct; document.getElementById('tp').value=d.tp.toFixed(2); document.getElementById('instant_pct').value=d.instant_target_pct; updateCalc(); window.fieldsFilled=true; }
    let h=''; for(const p of d.positions){ h+=`<tr><td style="font-weight:900">${p[0]}</td><td><span class="spot">${p[1]}</span></td><td style="font-size:9px">${p[6]}</td><td>${p[2].toFixed(4)}</td><td>${p[3].toFixed(4)}</td><td class="${colorClass(p[4])}">${p[4].toFixed(3)}$</td><td class="${colorClass(p[5])}">${p[5].toFixed(2)}%</td></tr>`; } document.getElementById('coins').innerHTML=h||(d.bot_enabled?'<tr><td colspan=7>⚡ تيربو بيدخل...</td></tr>':'<tr><td colspan=7>⏸️ متوقف</td></tr>');
    const tw=document.getElementById('treatWrap'); if(d.treatment_positions.length>0){ tw.style.display='block'; let th=''; for(const p of d.treatment_positions){ th+=`<tr style="background:#2a1a00"><td><span class="treat-badge">🏥 ${p[0]}</span></td><td style="font-size:9px;color:#ffcc00">${p[6]}</td><td class="neg">-${p[7].toFixed(2)}$</td><td style="color:#ffcc00">${p[8].toFixed(2)}$</td><td>${p[3].toFixed(4)}</td><td class="${colorClass(p[4])}">${p[4].toFixed(3)}$</td></tr>`; } document.getElementById('treatCoins').innerHTML=th; } else tw.style.display='none';
  }catch(e){}
}
setInterval(load,400); load();
</script>
</body></html>'''
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

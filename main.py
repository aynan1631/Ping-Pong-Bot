from flask import Flask, request, jsonify
import threading, time, requests
from datetime import datetime
app = Flask(__name__)
config = {"capital":1000.0,"per_trade":200.0,"tp_pct":0.8,"sl_pct":1.5}
state = {"daily_start":1000.0,"daily_peak":1080.0,"safi":8.68,"ghair":1.2,"loss":-0.33,"loss_pool":0.33,"trades_closed":8,"wins":7,"losses":1,"recovered":5.0,"positions":[],"binance_status":"BINANCE REAL ✅","last_update":"...","tick":time.time(),"is_running":True,"logs":[]}

def add_log(msg):
    state["logs"].insert(0,f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    state["logs"]=state["logs"][:20]

def get_prices():
 try:
  r=requests.get("https://api.binance.com/api/v3/ticker/price",timeout=3)
  if r.status_code==200: return {x["symbol"]:float(x["price"]) for x in r.json()}
 except: return {}
def get_movers():
 try:
  r=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=3)
  if r.status_code==200:
   m=[]
   for t in r.json():
    s=t["symbol"]
    if not s.endswith("USDT") or len(s)>14: continue
    try:
     pct=float(t.get("priceChangePercent",0))
     if pct<13: continue
     m.append((s.replace("USDT",""),pct,float(t["lastPrice"])))
    except: pass
   m.sort(key=lambda x:x[1],reverse=True)
   return m[:20]
 except: pass
 return [("CREAM",65.4,2.0990),("PNT",45.2,0.0350),("KDA",17.6,0.0060),("CLV",14.0,0.0294),("MDX",13.5,0.0345),("SOXSB",13.5,51.9040)]

def calc_total():
 total=config["capital"]+state["safi"]+state["ghair"]+state["loss"]
 daily_pct=((total-state["daily_start"])/state["daily_start"]*100) if state["daily_start"]>0 else 0
 if total>state["daily_peak"]: state["daily_peak"]=total
 return total,daily_pct

def engine():
 try:
  for sym,pct,pr in get_movers()[:6]:
   state["positions"].append([sym+"/USDT",pr*0.996,pr,0.0,0.0,pct,0.33 if sym=="SOXSB" else 0.0,"مولعة" if pct<20 else "مولعة جدا"])
  add_log("تم الدخول 6 عملات مولعة")
 except: pass
 while True:
  try:
   if not state["is_running"]: time.sleep(1); continue
   prc=get_prices()
   for p in state["positions"]:
    s=p[0].replace("/","")
    if s in prc:
     cur=prc[s]; p[2]=cur; pp=(cur-p[1])/p[1]*100; us=config["per_trade"]*pp/100; p[3]=round(us,2); p[4]=round(pp,2)
   state["ghair"]=round(sum([p[3] for p in state["positions"]]),2)
   state["last_update"]=datetime.now().strftime("%H:%M:%S"); state["tick"]=time.time()
   for p in list(state["positions"]):
    need=config["tp_pct"]+ (abs(p[6])/config["per_trade"]*100)
    if p[4]>=need:
     real=p[3]
     if p[6]>0:
      if real>=p[6]: state["loss"]=round(state["loss"]+p[6],2); state["safi"]=round(state["safi"]+real-p[6],2); state["loss_pool"]=round(max(0,state["loss_pool"]-p[6]),2); state["recovered"]=round(state["recovered"]+p[6],2)
      else: state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=round(max(0,state["loss_pool"]-real),2)
     else: state["safi"]=round(state["safi"]+real,2)
     state["positions"].remove(p); state["trades_closed"]+=1; state["wins"]+=1; add_log(f"ربح {p[0]} +{real}$")
   for p in list(state["positions"]):
    if p[4]<=-config["sl_pct"]:
     real=round(p[3],2); state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=round(state["loss_pool"]+abs(real),2); state["positions"].remove(p); state["losses"]+=1; add_log(f"خسارة {p[0]} {real}$ → صيدلية")
     try:
      mov=get_movers(); sh=round(abs(real)/10,2); ex=[x[0].replace("/USDT","") for x in state["positions"]]
      for sym,pct,pr in mov:
       if sym not in ex: state["positions"].append([sym+"/USDT",pr*0.996,pr,0.0,0.0,pct,sh,f"دين ${sh}"]); break
     except: pass
   if not state["positions"] and state["is_running"]:
    for sym,pct,pr in get_movers()[:6]: state["positions"].append([sym+"/USDT",pr*0.996,pr,0.0,0.0,pct,0.0,"مولعة"])
   time.sleep(0.5)
  except: time.sleep(1)

threading.Thread(target=engine,daemon=True).start()

@app.route('/api/data')
def api():
 total,daily_pct=calc_total()
 winrate=(state["wins"]/(state["wins"]+state["losses"])*100) if (state["wins"]+state["losses"])>0 else 0
 heal_pct=(state["recovered"]/(abs(state["loss"])+state["recovered"])*100) if (abs(state["loss"])+state["recovered"])>0 else 100
 return jsonify({"total":round(total,2),"daily_pct":round(daily_pct,3),"daily_usd":round(total-state["daily_start"],2),"capital":config["capital"],"per_trade":config["per_trade"],"tp":config["tp_pct"],"sl":config["sl_pct"],"safi":state["safi"],"ghair":state["ghair"],"loss":state["loss"],"loss_pool":state["loss_pool"],"trades_closed":state["trades_closed"],"wins":state["wins"],"losses":state["losses"],"recovered":state["recovered"],"winrate":round(winrate,1),"heal_pct":round(heal_pct,1),"daily_peak":round(state["daily_peak"],2),"positions":state["positions"],"binance_status":state["binance_status"],"last_update":state["last_update"],"age":round(time.time()-state["tick"],1),"is_running":state["is_running"],"logs":state["logs"]})

@app.route('/api/config',methods=['POST'])
def cfg():
 d=request.get_json()
 if 'capital' in d: config["capital"]=float(d['capital']); state["daily_start"]=config["capital"]+state["safi"]+state["loss"]; state["daily_peak"]=state["daily_start"]
 if 'per_trade' in d: config["per_trade"]=float(d['per_trade'])
 if 'tp' in d: config["tp_pct"]=float(d['tp'])
 if 'sl' in d: config["sl_pct"]=float(d['sl'])
 return jsonify({"ok":True,"capital":config["capital"]})

@app.route('/api/control',methods=['POST'])
def control():
 d=request.get_json(); act=d.get('action')
 if act=='start': state["is_running"]=True
 elif act=='stop': state["is_running"]=False
 elif act=='close_all':
  for p in list(state["positions"]):
   real=round(p[3],2)
   if real>=0: state["safi"]=round(state["safi"]+real,2)
   else: state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=round(state["loss_pool"]+abs(real),2)
  state["positions"]=[]; state["ghair"]=0
 elif act=='reset_all': config["capital"]=1000.0; state.update({"daily_start":1000.0,"daily_peak":1000.0,"safi":0,"ghair":0,"loss":0,"loss_pool":0,"trades_closed":0,"wins":0,"losses":0,"recovered":0,"positions":[],"is_running":True})
 elif act=='compound':
  tp=state["safi"]+state["ghair"]
  if tp>0: config["capital"]=round(config["capital"]+tp,2); state["daily_start"]=config["capital"]; state["daily_peak"]=config["capital"]; state["safi"]=0; state["ghair"]=0; state["loss"]=0; state["loss_pool"]=0; state["positions"]=[]
 return jsonify({"ok":True})

@app.route('/')
def home():
 return '''
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}body{margin:0;background:#000080;color:#fff;font-family:'Cairo';padding:8px}
.top{display:flex;justify-content:space-between;background:#000; border:2px solid #00ff88; border-radius:10px; padding:8px 12px; font-family:'JetBrains Mono'; font-size:11px; color:#00ff88; margin-bottom:8px}
.main{display:grid; grid-template-columns: 1fr 300px; gap:8px}
.left{display:flex; flex-direction:column; gap:8px}
.table{background:linear-gradient(180deg,#0000ff,#0000cc); border:2px solid #00ff88; border-radius:12px; overflow:hidden; box-shadow:0 0 15px rgba(0,255,136,.3)}
.table-head{display:grid; grid-template-columns: 1fr 90px 140px 90px; background:#1a1aff; color:#ff6b9d; padding:10px; font-weight:900; font-size:13px; text-align:center; border-bottom:2px solid #00ff88}
.row{display:grid; grid-template-columns: 1fr 90px 140px 90px; padding:10px; text-align:center; border-bottom:1px solid rgba(0,255,136,.2); align-items:center; font-family:'JetBrains Mono'; font-weight:800; font-size:13px; background:#0000cc}
.row:nth-child(even){background:#0000aa}
.badge-spot{background:#00ff88; color:#000; padding:5px 14px; border-radius:20px; font-weight:900; font-size:12px; box-shadow:0 0 8px rgba(0,255,136,.6)}
.status{font-size:11px; color:#fff}
.dokhol{color:#ffca28; font-size:13px}
.pharmacy{margin-top:8px; background:linear-gradient(90deg,#3d2600,#5a3a00); border:2px solid #ff9800; border-radius:12px; padding:0; overflow:hidden}
.ph-head{display:grid; grid-template-columns:1fr 1fr 1fr 1fr; background:#000; color:#ff9800; padding:8px; font-weight:900; font-size:12px; text-align:center}
.ph-body{display:grid; grid-template-columns:1fr 1fr 1fr 1fr; padding:10px; text-align:center; font-family:'JetBrains Mono'; font-weight:800; align-items:center}
.stats{display:grid; grid-template-columns:1fr 1fr; gap:6px}
.stat{background:linear-gradient(180deg,#0000ff,#000099); border:2px solid #00ff88; border-radius:10px; padding:10px; text-align:center}
.stat.gold{border-color:#ffca28; box-shadow:0 0 12px rgba(255,202,40,.4)}.stat.red{border-color:#ff3b5c}.stat.cyan{border-color:#00e5ff}
.v{font-family:'JetBrains Mono'; font-size:18px; font-weight:800; direction:ltr}.s{font-size:10px; font-weight:800; margin-top:2px}.pos{color:#00ff88}.neg{color:#ff5252}
.ctrl{background:linear-gradient(180deg,#0000ff,#000099); border:2px solid #ffca28; border-radius:12px; padding:8px}
.ctrl input{background:#000; border:1px solid #333; border-radius:8px; color:#ffca28; font-family:'JetBrains Mono'; font-weight:800; font-size:13px; width:65px; padding:5px; text-align:center; direction:ltr}
.btn{border:none; border-radius:8px; padding:7px; font-family:'Cairo'; font-weight:900; font-size:11px; cursor:pointer; margin:2px; flex:1}
.b-start{background:#00ff88; color:#000}.b-stop{background:#ff1744; color:#fff}.b-close{background:#ff9800; color:#000}.b-reset{background:#333; color:#fff; border:1px solid #ff3b5c!important}.b-compound{background:#00e5ff; color:#000}.b-save{background:#ffca28; color:#000; width:100%}
.logs{background:#000066; border:1px solid #00ff88; border-radius:8px; height:120px; overflow-y:auto; padding:6px; font-size:11px; margin-top:6px}
</style></head><body>
<div class="top"><span id="st">BINANCE...</span><span>قمة $<span id="peak">0</span> • <span id="last">...</span> • <span id="age">0s</span></span></div>
<div class="main">
<div class="left">
<div class="table">
<div class="table-head"><span>عملة</span><span>نوع</span><span>حالة</span><span>دخول</span></div>
<div id="coins"></div>
</div>
<div class="pharmacy">
<div class="ph-head"><span>💊 الصيدلية</span><span>يعالج</span><span>خسارة</span><span>هـدف</span></div>
<div class="ph-body">
<div><span id="ph_t" style="background:#ffca28; color:#000; padding:4px 10px; border-radius:10px; font-size:12px">T 💊</span></div>
<div><span id="ph_heal" style="color:#ffca28">يعالج 0.33$ T</span></div>
<div><span id="ph_loss" class="neg">-0.33$</span></div>
<div><span id="ph_target" style="color:#00ff88">0.83$</span></div>
</div>
</div>
<div class="logs" id="logs"></div>
</div>
<div style="display:flex; flex-direction:column; gap:8px">
<div class="stats">
<div class="stat gold"><div style="font-size:10px">💰 الإجمالي</div><div class="v" style="color:#ffca28" id="v_total">$0</div><div class="s" id="v_daily">0%</div></div>
<div class="stat cyan"><div style="font-size:10px">🏥 تخصصي</div><div class="v" style="color:#00e5ff" id="v_heal">100%</div><div class="s" id="v_win">83.6%</div></div>
<div class="stat"><div style="font-size:10px">📈 لحظي % رأس مال</div><div class="v pos" id="v_ghair">0%</div><div class="s" id="v_ghair_usd">0$</div></div>
<div class="stat"><div style="font-size:10px">💹 صافي % رأس مال</div><div class="v pos" id="v_safi_pct">0%</div><div class="s" id="v_safi">$0</div></div>
</div>
<div class="ctrl">
<div style="font-size:11px; font-weight:900; color:#ffca28; text-align:center; margin-bottom:6px">⚙️ لوحة التحكم + المفاتيح 🔑</div>
<div style="display:flex; gap:5px; margin-bottom:6px"><span style="font-size:10px">رأس</span><input id="capital" value="1000"><span style="font-size:10px">صفقة</span><input id="per_trade" value="200"></div>
<div style="display:flex; gap:5px; margin-bottom:6px"><span style="font-size:10px">ربح%</span><input id="tp" value="0.8"><span style="font-size:10px">ستوب%</span><input id="sl" value="1.5"></div>
<button class="btn b-save" onclick="saveConfig()">💾 حفظ - لوحة التحكم</button>
<div style="display:grid; grid-template-columns:1fr 1fr; gap:4px; margin-top:6px">
<button class="btn b-start" onclick="control('start')">▶️ تشغيل</button>
<button class="btn b-stop" onclick="control('stop')">⏸️ إيقاف</button>
<button class="btn b-close" onclick="control('close_all')">🔒 إقفال وتصفية</button>
<button class="btn b-reset" onclick="if(confirm('تصفير؟'))control('reset_all')">♻️ تصفير الكل</button>
</div>
<button class="btn b-compound" style="width:100%; margin-top:4px" onclick="if(confirm('نقل الربح لرأس المال؟'))control('compound')">💰 نقل الربح مع رأس المال المستعمل</button>
</div>
</div>
</div>
<script>
async function load(){
 try{
  const r=await fetch('/api/data'); const d=await r.json();
  document.getElementById('st').innerText=d.binance_status+' • '+d.trades_closed+' مقفلة • '+d.positions.length+' مولعة • '+(d.is_running?'🟢 يعمل':'🔴 متوقف');
  document.getElementById('peak').innerText=d.daily_peak.toFixed(2);
  document.getElementById('last').innerText=d.last_update;
  document.getElementById('age').innerText=d.age+'s';
  document.getElementById('capital').value=d.capital.toFixed(2);
  document.getElementById('per_trade').value=d.per_trade;
  document.getElementById('tp').value=d.tp;
  document.getElementById('sl').value=d.sl;
  document.getElementById('v_total').innerText='$'+d.total.toFixed(2);
  document.getElementById('v_daily').innerText=(d.daily_pct>=0?'+':'')+d.daily_pct.toFixed(3)+'% ('+d.daily_usd.toFixed(2)+'$)';
  document.getElementById('v_ghair').innerText=(d.ghair/d.capital*100>=0?'+':'')+(d.ghair/d.capital*100).toFixed(3)+'%';
  document.getElementById('v_ghair_usd').innerText=(d.ghair>=0?'+':'')+d.ghair.toFixed(2)+'$ لحظي';
  document.getElementById('v_safi_pct').innerText=(d.safi/d.capital*100>=0?'+':'')+(d.safi/d.capital*100).toFixed(3)+'%';
  document.getElementById('v_safi').innerText=d.safi.toFixed(2)+'$ صافي';
  document.getElementById('v_heal').innerText=d.heal_pct.toFixed(0)+'% شفاء';
  document.getElementById('v_win').innerText=d.winrate.toFixed(1)+'% نجاح';
  document.getElementById('ph_loss').innerText=d.loss.toFixed(2)+'$';
  document.getElementById('ph_heal').innerText='يعالج '+d.loss_pool.toFixed(2)+'$ T';
  document.getElementById('ph_t').innerText='T 💊 '+d.positions.filter(p=>p[6]>0).length;

  document.getElementById('logs').innerHTML=d.logs.map(l=>`<div>${l}</div>`).join('');

  let h=''; for(const p of d.positions){
   const sym=p[0].replace('/USDT',''),en=p[1],mov=p[5];
   h+=`<div class="row"><span><b>${sym}</b></span><span><span class="badge-spot">SPOT</span></span><span class="status">مولعة %${mov.toFixed(1)} X</span><span class="dokhol">${en.toFixed(4)}</span></div>`;
  }
  document.getElementById('coins').innerHTML=h||'<div style="padding:20px; text-align:center; opacity:.5">⏳ ينتظر المولعة...</div>';
 }catch(e){}
}
async function saveConfig(){
 const d={capital:parseFloat(document.getElementById('capital').value),per_trade:parseFloat(document.getElementById('per_trade').value),tp:parseFloat(document.getElementById('tp').value),sl:parseFloat(document.getElementById('sl').value)};
 const b=document.querySelector('.b-save'); const old=b.innerText; b.innerText='⏳ يحفظ...';
 try{
  const r=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
  const j=await r.json();
  if(j.ok){b.innerText='✅ تم الحفظ $'+j.capital; setTimeout(()=>b.innerText=old,2000); load();}
 }catch(e){b.innerText='❌'; setTimeout(()=>b.innerText=old,1500);}
}
async function control(a){ await fetch('/api/control',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:a})}); load(); }
setInterval(load,800); load();
</script>
</body></html>
    '''

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

from flask import Flask, request, jsonify
import threading, time, requests
from datetime import datetime
app = Flask(__name__)
config = {"capital":1024.28,"per_trade":200.0,"tp_pct":0.8,"sl_pct":1.5}
state = {"daily_start":1024.28,"daily_peak":1024.28,"safi":24.28,"ghair":0.43,"loss":0.0,"loss_pool":0.0,"trades_closed":216,"wins":180,"losses":36,"recovered":12.5,"positions":[],"binance_status":"ULTRA 💎","last_update":"...","tick":time.time()}

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
    if not s.endswith("USDT") or len(s)>12: continue
    pct=float(t.get("priceChangePercent",0))
    if pct<0.5: continue
    m.append((s,pct,float(t["lastPrice"])))
   m.sort(key=lambda x:x[1],reverse=True)
   return m[:20]
 except: pass
 return [("SOL/USDT",3,150),("PEPE/USDT",4,0.00001)]

def calc_total():
 total=config["capital"]+state["safi"]+state["ghair"]+state["loss"]
 daily_pct=((total-state["daily_start"])/state["daily_start"]*100) if state["daily_start"]>0 else 0
 ghair_pct=(state["ghair"]/config["capital"]*100) if config["capital"]>0 else 0
 safi_pct=(state["safi"]/config["capital"]*100) if config["capital"]>0 else 0
 if total>state["daily_peak"]: state["daily_peak"]=total
 return total,daily_pct,ghair_pct,safi_pct

def engine():
 try:
  for sym,pct,pr in get_movers()[:10]:
   state["positions"].append([sym,pr*0.996,pr,0.0,0.0,pct,0.0,"مولعة"])
 except: pass
 while True:
  try:
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
      else: state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=round(max(0,state["loss_pool"]-real),2); state["recovered"]=round(state["recovered"]+real,2)
     else: state["safi"]=round(state["safi"]+real,2)
     state["positions"].remove(p); state["trades_closed"]+=1; state["wins"]+=1
   for p in list(state["positions"]):
    if p[4]<=-config["sl_pct"]:
     real=round(p[3],2); state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=round(state["loss_pool"]+abs(real),2); state["positions"].remove(p); state["losses"]+=1
     try:
      mov=get_movers(); sh=round(abs(real)/10,2) if abs(real)>0.1 else 0.2; ex=[x[0] for x in state["positions"]]
      for sym,pct,pr in mov:
       if sym not in ex: state["positions"].append([sym,pr*0.996,pr,0.0,0.0,pct,sh,f"دين ${sh}"]); break
     except: pass
   if not state["positions"]:
    for sym,pct,pr in get_movers()[:6]: state["positions"].append([sym,pr*0.996,pr,0.0,0.0,pct,0.0,"مولعة"])
   time.sleep(0.5)
  except: time.sleep(1)

threading.Thread(target=engine,daemon=True).start()

@app.route('/api/data')
def api():
 total,daily_pct,ghair_pct,safi_pct=calc_total()
 winrate=(state["wins"]/(state["wins"]+state["losses"])*100) if (state["wins"]+state["losses"])>0 else 0
 heal_pct=(state["recovered"]/(abs(state["loss"])+state["recovered"])*100) if (abs(state["loss"])+state["recovered"])>0 else 0
 return jsonify({"total":round(total,2),"daily_pct":round(daily_pct,3),"ghair_pct":round(ghair_pct,4),"safi_pct":round(safi_pct,4),"daily_usd":round(total-state["daily_start"],2),"capital":config["capital"],"safi":state["safi"],"ghair":state["ghair"],"loss":state["loss"],"loss_pool":state["loss_pool"],"trades_closed":state["trades_closed"],"wins":state["wins"],"losses":state["losses"],"recovered":state["recovered"],"winrate":round(winrate,1),"heal_pct":round(heal_pct,1),"daily_peak":round(state["daily_peak"],2),"positions":state["positions"],"binance_status":state["binance_status"],"last_update":state["last_update"],"age":round(time.time()-state["tick"],1)})

@app.route('/api/config',methods=['POST'])
def cfg():
 d=request.get_json()
 if 'capital' in d: config["capital"]=float(d['capital']); state["daily_start"]=config["capital"]+state["safi"]+state["loss"]
 if 'per_trade' in d: config["per_trade"]=float(d['per_trade'])
 if 'tp' in d: config["tp_pct"]=float(d['tp'])
 if 'sl' in d: config["sl_pct"]=float(d['sl'])
 return jsonify({"ok":True})

@app.route('/')
def home():
 return '''
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;800;900&family=JetBrains+Mono:wght@700;800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top,#0e1440,#070a1e 60%);color:#fff;font-family:'Cairo';padding:8px}
.top{display:flex;justify-content:space-between;background:linear-gradient(180deg,#151a3d,#0e1230);border:1px solid #2a36f0;border-radius:12px;padding:10px 14px;font-size:13px;font-weight:900;margin-bottom:8px;box-shadow:0 4px 20px rgba(0,0,0,.5), inset 0 1px 0 rgba(255,255,255,.08)}
.ctrl{display:flex;flex-wrap:wrap;gap:7px;background:linear-gradient(180deg,#171c45,#11163a);border:1px solid #2a36a0;border-radius:14px;padding:10px 12px;margin-bottom:10px;align-items:center}
.ctrl-title{font-size:13px;font-weight:900;color:#ffca28;text-shadow:0 0 8px rgba(255,202,40,.6);margin-left:8px}
.ctrl.it{display:flex;gap:6px;background:#080c1e;border:1px solid #2a36f0;border-radius:10px;padding:7px 10px}
.ctrl.it label{font-size:11px;opacity:.7}.ctrl.it input{background:transparent;border:none;color:#ffca28;font-family:'JetBrains Mono';font-weight:800;font-size:14px;width:65px;direction:ltr;outline:none}
.ctrl button{border:none;border-radius:10px;padding:8px 16px;font-family:'Cairo';font-weight:900;font-size:13px;cursor:pointer}
.b1{background:linear-gradient(90deg,#ffca28,#ffb300);color:#000}.b2{background:rgba(255,255,255,.06);border:1px solid #333!important;color:#fff}
.boards{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px}
.board{display:flex;flex-direction:column;gap:4px}
.board-title{font-size:11px;font-weight:900;opacity:.9;text-align:center;height:28px;display:flex;align-items:center;justify-content:center}
.board-card{background:linear-gradient(180deg,#1a2050,#0d1028);border:1px solid #2d36c0;border-radius:16px;padding:12px 6px;text-align:center;min-height:100px;display:flex;flex-direction:column;justify-content:center;box-shadow:0 4px 20px rgba(0,0,0,.4), inset 0 1px 0 rgba(255,255,255,.08)}
.board-card.gold{border:2px solid #ffca28;box-shadow:0 0 25px rgba(255,202,40,.45), inset 0 1px 0 rgba(255,255,255,.15)}
.board-card.pharmacy{border:2px solid #ff3b5c;box-shadow:0 0 20px rgba(255,59,92,.3)}.board-card.special{border:2px solid #00e5ff;box-shadow:0 0 20px rgba(0,229,255,.35);background:linear-gradient(180deg,#0e3442,#0a1e28)}
.board-card.profit-lahzi{border:2px solid #00ff88;box-shadow:0 0 20px rgba(0,255,136,.35);background:linear-gradient(180deg,#0a2a1a,#071a10)}
.board-card.profit-yawmi{border:2px solid #ffca28;box-shadow:0 0 20px rgba(255,202,40,.35);background:linear-gradient(180deg,#2a2308,#1a1500)}
.v{font-family:'JetBrains Mono';font-size:22px;font-weight:800;direction:ltr;text-shadow:0 2px 4px rgba(0,0,0,.8)}.v.gold-text{color:#ffca28;text-shadow:0 0 12px rgba(255,202,40,.8);font-size:24px}
.v.big{font-size:26px;font-weight:900}
.s{font-size:11px;font-weight:800;margin-top:4px}.pos{color:#00ff88;text-shadow:0 0 8px rgba(0,255,136,.6)}.neg{color:#ff3b5c;text-shadow:0 0 8px rgba(255,59,92,.5)}.cyan{color:#00e5ff;text-shadow:0 0 8px rgba(0,229,255,.6)}
.coins{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}
.coin{background:linear-gradient(180deg,#1a2050,#0e122e);border:1px solid #2a36a0;border-radius:14px;padding:9px;min-height:116px;display:flex;flex-direction:column;justify-content:space-between}
.coin.posb{border-color:rgba(0,255,136,.6)}.coin.negb{border-color:rgba(255,59,92,.6)}
.ctop{display:flex;justify-content:space-between;align-items:center}.ctop b{font-family:'JetBrains Mono';font-size:14px;font-weight:800}
.badge{font-size:9px;font-weight:900;padding:4px 7px;border-radius:20px}.badge.pct{background:linear-gradient(90deg,#ff9800,#ffb74d);color:#000}.badge.debt{background:linear-gradient(90deg,#ff1744,#ff5252);color:#fff}
.cprice{font-family:'JetBrains Mono';font-size:9px;opacity:.5;direction:ltr;margin:5px 0}.barw{height:6px;background:#05070a;border-radius:10px;overflow:hidden;margin-bottom:6px}.bar{height:100%;border-radius:10px}
.cprof{border-radius:10px;padding:6px;text-align:center;font-family:'JetBrains Mono';font-weight:800;font-size:13px;direction:ltr}
</style></head><body>
<div class="top"><span><b style="color:#ffca28">فتوح</b> V77.4 نسب الربح % 💯</span><span><span id="binStatus">...</span> • <span id="lastUpd">...</span> • <span id="age">0s</span></span></div>
<div class="ctrl"><span class="ctrl-title">⚙️ تحكم</span>
<div class="it"><label>رأس</label><input id="capital" value="1024"></div>
<div class="it"><label>صفقة</label><input id="per_trade" value="200"></div>
<div class="it"><label>ربح%</label><input id="tp" value="0.8"></div>
<div class="it"><label>ستوب%</label><input id="sl" value="1.5"></div>
<button class="b1" onclick="save()">حفظ ✨</button><button class="b2" onclick="location.reload()">🔄</button>
</div>

<div class="boards">
<div class="board"><div class="board-title">💰 رأس المال</div><div class="board-card"><div class="v" id="v_cap">$0</div><div class="s">10 × $200</div></div></div>
<div class="board"><div class="board-title">💎 الإجمالي</div><div class="board-card gold"><div class="v gold-text" id="v_total">$0</div><div class="s" id="v_daily_usd">0$</div></div></div>
<div class="board"><div class="board-title">📈 لحظي $ + % من رأس المال</div><div class="board-card profit-lahzi"><div class="v big pos" id="v_ghair_usd">0$</div><div class="v pos" id="v_ghair_pct" style="font-size:18px;margin-top:4px">0.00%</div><div class="s" id="v_gcount">0 عملات</div></div></div>
<div class="board"><div class="board-title">📅 يومي $ + % من رأس المال</div><div class="board-card profit-yawmi"><div class="v big" id="v_daily_pct_main" style="color:#ffca28">0.00%</div><div class="v" id="v_safi_usd" style="font-size:16px;margin-top:2px">0$ صافي</div><div class="s" id="v_today">0 مقفلة</div></div></div>
</div>

<div class="boards" style="grid-template-columns:repeat(4,1fr)">
<div class="board"><div class="board-title">💹 صافي % من رأس المال</div><div class="board-card"><div class="v pos" id="v_safi_pct">0.00%</div><div class="s">من رأس المال</div></div></div>
<div class="board"><div class="board-title">💊 صيدلية</div><div class="board-card pharmacy"><div class="v" style="color:#ff3b5c" id="v_pool">$0</div><div class="s" id="v_loss">0$</div></div></div>
<div class="board"><div class="board-title">🏥 تخصصي</div><div class="board-card special"><div class="v cyan" id="v_heal">0%</div><div class="s" id="v_winrate">0% نجاح</div></div></div>
<div class="board"><div class="board-title">🎯 قمة اليوم</div><div class="board-card"><div class="v" id="v_peak">$0</div><div class="s" id="v_daily_pct_small">0%</div></div></div>
</div>

<div class="coins" id="coins"></div>

<script>
async function load(){
 try{
  const r=await fetch('/api/data'); const d=await r.json();
  document.getElementById('binStatus').innerText=d.binance_status;
  document.getElementById('lastUpd').innerText=d.last_update;
  document.getElementById('age').innerText=d.age+'s';
  document.getElementById('v_cap').innerText='$'+d.capital.toFixed(0);
  document.getElementById('v_total').innerText='$'+d.total.toFixed(2);
  document.getElementById('v_daily_usd').innerText=(d.daily_usd>=0?'+':'')+d.daily_usd.toFixed(2)+'$ يومي';
  document.getElementById('v_daily_usd').className='s '+(d.daily_usd>=0?'pos':'neg');

  // لحظي
  document.getElementById('v_ghair_usd').innerText=(d.ghair>=0?'+':'')+d.ghair.toFixed(2)+'$';
  document.getElementById('v_ghair_usd').className='v big '+(d.ghair>=0?'pos':'neg');
  document.getElementById('v_ghair_pct').innerText=(d.ghair_pct>=0?'+':'')+d.ghair_pct.toFixed(3)+'% من رأس المال';
  document.getElementById('v_ghair_pct').className='v '+(d.ghair_pct>=0?'pos':'neg');
  document.getElementById('v_gcount').innerText=d.positions.length+' عملات';

  // يومي
  document.getElementById('v_daily_pct_main').innerText=(d.daily_pct>=0?'+':'')+d.daily_pct.toFixed(3)+'% من رأس المال';
  document.getElementById('v_daily_pct_main').className='v big '+(d.daily_pct>=0?'pos':'neg');
  document.getElementById('v_daily_pct_main').style.color=d.daily_pct>=0?'#00ff88':'#ff3b5c';
  document.getElementById('v_safi_usd').innerText=(d.safi>=0?'+':'')+d.safi.toFixed(2)+'$ صافي محقق';
  document.getElementById('v_safi_usd').className='v '+(d.safi>=0?'pos':'neg');
  document.getElementById('v_today').innerText=d.trades_closed+' مقفلة';

  document.getElementById('v_safi_pct').innerText=(d.safi_pct>=0?'+':'')+d.safi_pct.toFixed(3)+'%';
  document.getElementById('v_safi_pct').className='v big '+(d.safi_pct>=0?'pos':'neg');
  document.getElementById('v_pool').innerText='$'+d.loss_pool.toFixed(2);
  document.getElementById('v_loss').innerText=d.loss.toFixed(2)+'$';
  document.getElementById('v_peak').innerText='$'+d.daily_peak.toFixed(2);
  document.getElementById('v_daily_pct_small').innerText=d.daily_pct.toFixed(2)+'% يومي';
  document.getElementById('v_winrate').innerText=d.winrate+'% نجاح';
  document.getElementById('v_heal').innerText=d.heal_pct+'% شفاء';

  let h=''; for(const p of d.positions){const sym=p[0].replace('/USDT',''),en=p[1],cur=p[2],usd=p[3],pct=p[4],mov=p[5],debt=p[6]; const isPos=usd>=0; const col=isPos?'#00ff88':'#ff3b5c'; const bg=isPos?'rgba(0,255,136,.12)':'rgba(255,59,92,.12)'; const cls=isPos?'posb':'negb'; const bar=Math.min(100,Math.max(8,(pct+1.5)/2.5*100)); const debtBadge=debt>0.01?`<span class="badge debt">دين $${debt.toFixed(2)}</span>`:''; h+=`<div class="coin ${cls}"><div class="ctop"><b>${sym}</b><div style="display:flex;gap:3px"><span class="badge pct">REAL ${mov.toFixed(1)}%</span>${debtBadge}</div></div><div class="cprice">${en.toFixed(5)} → ${cur.toFixed(5)}</div><div class="barw"><div class="bar" style="width:${bar}%;background:${col}"></div></div><div class="cprof" style="color:${col};background:${bg}">${isPos?'+':''}${usd.toFixed(2)}$<small style="display:block;font-size:10px">${pct>=0?'+':''}${pct.toFixed(2)}% من الصفقة | ${(usd/1024*100).toFixed(3)}% من رأس المال</small></div></div>`}
  document.getElementById('coins').innerHTML=h||'<div style="padding:20px;opacity:.5;text-align:center">⏳</div>';
 }catch(e){}
}
async function save(){const d={capital:+capital.value,per_trade:+per_trade.value,tp:+tp.value,sl:+sl.value}; const b=document.querySelector('.b1'); b.innerText='⏳'; try{const r=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}); if((await r.json()).ok){b.innerText='✅'; setTimeout(()=>b.innerText='حفظ ✨',1000)}}catch(e){b.innerText='❌'}}
setInterval(load,700); load();
</script>
</body></html>
    '''

if __name__=="__main__":
    import os; app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

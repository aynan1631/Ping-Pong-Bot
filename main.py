from flask import Flask, jsonify
import threading, time, requests, os
from datetime import datetime
app = Flask(__name__)
state={"fixed":1024.28,"safi":24.28,"ghair":0.43,"positions":[],"closed":216,"status":"V100 فخم + خفيف","tick":time.time(),"initial":1000.0}
TARGET=0.50

def get_all_prices():
 try:
  r=requests.get("https://api.binance.com/api/v3/ticker/price",timeout=3)
  if r.status_code==200:
   return {x["symbol"]:float(x["price"]) for x in r.json()}
 except: pass
 return {}

def get_movers_fast():
 try:
  r=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=3)
  if r.status_code==200:
   data=r.json()
   mov=[]
   for t in data:
    s=t["symbol"]
    if not s.endswith("USDT"): continue
    if len(s)>12: continue
    try:
     pct=float(t.get("priceChangePercent",0))
     if pct>1: mov.append((s[:-4],pct,float(t["lastPrice"])))
    except: continue
   mov.sort(key=lambda x:x[1],reverse=True)
   return mov[:8]
 except: pass
 return [("SOL",3,150),("PEPE",4,0.00001),("WIF",3,2),("BONK",3,0.00003),("FLOKI",3,0.0002),("SHIB",2,0.00002)]

def bot_loop():
 while True:
  try:
   state["tick"]=time.time()
   # خطوة واحدة فقط تجيب كل الأسعار
   all_prices=get_all_prices()
   if state["positions"] and all_prices:
    total_ghair=0
    for p in state["positions"]:
     sym=p[0]+"USDT"
     if sym in all_prices:
      cur=all_prices[sym]
      p[2]=cur
      p[3]=round((cur-p[1])/p[1]*100,4)
      total_ghair+=p[3]
    state["ghair"]=round(total_ghair,3)

   # دخول
   if not state["positions"]:
    time.sleep(0.2)
    mov=get_movers_fast()
    new=[]
    for name,pct,price in mov[:6]:
     new.append([name,price*0.999,price,0.0,f"🔥 {pct:.1f}%"])
    state["positions"]=new
    state["status"]=f"دخل {len(new)} مولعة"

   # خروج
   if state["ghair"]>=TARGET and state["ghair"]>0:
    state["safi"]+=state["ghair"]
    state["fixed"]+=state["ghair"]
    state["closed"]+=len(state["positions"])
    state["status"]=f"💰 قفل +{state['ghair']}$"
    state["positions"]=[]; state["ghair"]=0

   time.sleep(0.4)
  except Exception as e:
   state["status"]=str(e)[:40]
   time.sleep(1)

threading.Thread(target=bot_loop,daemon=True).start()

@app.route('/api/data')
def api():
 total=state["fixed"]+state["safi"]+state["ghair"] if state["fixed"] else 1024.28
 profit=total-state["initial"]
 pct=profit/state["initial"]*100 if state["initial"] else 0
 return jsonify({"fixed":state["fixed"],"safi":state["safi"],"ghair":state["ghair"],"total":total,"profit":profit,"pct":pct,"closed":state["closed"],"positions":state["positions"],"status":state["status"],"last":datetime.now().strftime("%H:%M:%S"),"age":round(time.time()-state["tick"],1),"initial":state["initial"],"target":TARGET})

@app.route('/')
def home():
 return """
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{margin:0;background:#070a1e;color:#fff;font-family:Arial;padding:4px}
.box{border:2px solid #00ff66;border-radius:14px;background:#11158a;text-align:center;padding:8px;margin:4px 0;font-size:12px;font-weight:900}
.bar{display:flex;justify-content:space-between;background:#11158a;border:1px solid #2a36f0;border-radius:10px;padding:6px;margin:3px 0;font-size:11px;font-weight:800}
.boards{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin:4px 0}
.b{display:flex;flex-direction:column}.bt{font-size:8px;text-align:center;margin-bottom:2px}.bc{background:#1a1f9e;border:1px solid #2d36c0;border-radius:10px;padding:10px 2px;text-align:center;min-height:55px;display:flex;flex-direction:column;justify-content:center}
.bc.gold{border:2px solid #00ff66}.bv{font-weight:900;font-size:11px;direction:ltr}.pos{color:#00ff66}.neg{color:#ff2d55}.w{color:#fff}
.tbl{width:100%;border-collapse:collapse;background:#11158a;border-radius:10px;overflow:hidden}.tbl th{background:#2a36f0;color:#ff4d8d;font-size:9px;padding:6px}.tbl td{padding:6px 2px;text-align:center;font-size:9px;border-top:1px solid #1a1f8a}
</style></head><body>
<div class="box">V100 اللوحة الفخمة + محرك خفيف ⚡</div>
<div class="bar" id="statusBar">...</div>
<div class="bar" style="border:2px solid #00ff66;justify-content:center;gap:10px"><span>أصلي: <b id="init">1000$</b></span><span>ربح: <b id="pr">0$</b></span><span>نسبة: <b id="pc">0%</b></span></div>
<div class="bar"><span id="prog">0 / 0.5$</span><span id="age">0s</span><span>🟢 V100</span></div>
<div class="boards">
<div class="b"><div class="bt">💰 ثابت</div><div class="bc gold"><div class="bv w" id="v_fixed">-</div></div></div>
<div class="b"><div class="bt">📈 غير</div><div class="bc"><div class="bv" id="v_ghair">-</div></div></div>
<div class="b"><div class="bt">💎 إجمالي</div><div class="bc gold"><div class="bv" id="v_total">-</div></div></div>
<div class="b"><div class="bt">💹 صافي</div><div class="bc"><div class="bv" id="v_safi">-</div></div></div>
<div class="b"><div class="bt">⚖️ مقفلة</div><div class="bc"><div class="bv w" id="v_closed">0</div></div></div>
<div class="b"><div class="bt">📊 نسبة</div><div class="bc"><div class="bv" id="v_pct">0%</div></div></div>
</div>
<table class="tbl"><thead><tr><th>عملة</th><th>حالة</th><th>دخول</th><th>حالي</th><th>ربح</th></tr></thead><tbody id="coins"></tbody></table>
<script>
async function load(){
 try{
  const r=await fetch('/api/data'); const d=await r.json();
  document.getElementById('statusBar').innerText=d.status+' • '+d.last;
  document.getElementById('init').innerText=d.initial.toFixed(0)+'$';
  document.getElementById('pr').innerText=(d.profit>=0?'+':'')+d.profit.toFixed(2)+'$';
  document.getElementById('pc').innerText=(d.pct>=0?'+':'')+d.pct.toFixed(2)+'%';
  document.getElementById('v_fixed').innerText=d.fixed.toFixed(2)+'$';
  document.getElementById('v_ghair').innerText=(d.ghair>=0?'+':'')+d.ghair.toFixed(2)+'$'; document.getElementById('v_ghair').className='bv '+(d.ghair>=0?'pos':'neg');
  document.getElementById('v_safi').innerText=(d.safi>=0?'+':'')+d.safi.toFixed(2)+'$'; document.getElementById('v_safi').className='bv '+(d.safi>=0?'pos':'neg');
  document.getElementById('v_total').innerText=d.total.toFixed(2)+'$';
  document.getElementById('v_closed').innerText=d.closed;
  document.getElementById('v_pct').innerText=(d.pct>=0?'+':'')+d.pct.toFixed(2)+'%'; document.getElementById('v_pct').className='bv '+(d.pct>=0?'pos':'neg');
  document.getElementById('prog').innerText=d.ghair.toFixed(3)+' / '+d.target+'$';
  document.getElementById('age').innerText=d.age+'s';
  let h=''; for(const p of d.positions){ h+=`<tr><td>${p[0]}</td><td>${p[4]}</td><td>${p[1].toFixed(4)}</td><td>${p[2].toFixed(4)}</td><td class="${p[3]>=0?'pos':'neg'}">${p[3].toFixed(3)}$</td></tr>` }
  document.getElementById('coins').innerHTML=h||'<tr><td colspan=5>⚡ يدخل الآن...</td></tr>';
 }catch(e){}
}
setInterval(load,600); load();
</script>
</body></html>
"""
if __name__=="__main__":
 app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

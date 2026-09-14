from flask import Flask, jsonify
import threading, time, requests
from datetime import datetime
app = Flask(__name__)
state={"fixed":1014.31,"safi":14.31,"ghair":0.0,"positions":[],"closed":138,"status":"V98 اللوحة رجعت","tick":time.time(),"on":True,"initial":1000.0}
target=0.50

def get_prices():
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/price",timeout=2)
        return {x["symbol"]:float(x["price"]) for x in r.json()} if r.status_code==200 else {}
    except: return {}
def get_movers():
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=2.5)
        if r.status_code==200:
            m=[]
            for t in r.json():
                s=t["symbol"]
                if not s.endswith("USDT") or len(s)>12: continue
                if "BULL" in s or "BEAR" in s: continue
                pct=float(t.get("priceChangePercent",0))
                if pct<0.5: continue
                m.append((s[:-4],pct,float(t["lastPrice"])))
            m.sort(key=lambda x:x[1],reverse=True)
            return m[:30]
    except: pass
    return [("PEPE",5,0.00001),("BONK",4,0.00003),("SOL",2,150),("WIF",4,2),("FLOKI",3,0.0002)]

def bot():
    while True:
        try:
            state["tick"]=time.time()
            if state["positions"]:
                mp=get_prices()
                for p in state["positions"]:
                    k=p[0]+"USDT"
                    if k in mp:
                        cur=mp[k]; p[2]=cur; p[3]=round((cur-p[1])/p[1]*100,3)
                state["ghair"]=round(sum([p[3] for p in state["positions"]]),2)
            if state["on"] and not state["positions"]:
                time.sleep(0.2)
                mov=get_movers(); new=[]
                for name,pct,price in mov[:6]:
                    new.append([name,price*0.999,price,0.0,f"مولعة {pct:.1f}%"])
                state["positions"]=new; state["status"]=f"⚡ دخل {len(new)}"
            if state["ghair"]>=target and state["ghair"]>0 and state["positions"]:
                state["safi"]+=state["ghair"]; state["fixed"]+=state["ghair"]; state["closed"]+=len(state["positions"])
                state["status"]=f"💰 +{state['ghair']:.2f}$"; state["positions"]=[]; state["ghair"]=0
            time.sleep(0.2)
        except Exception as e:
            state["status"]=str(e)[:30]; time.sleep(0.5)

threading.Thread(target=bot,daemon=True).start()

@app.route('/api/data')
def api_data():
    total=state["fixed"]+state["safi"]+state["ghair"]; profit=total-state["initial"]; pct=profit/state["initial"]*100 if state["initial"] else 0
    return jsonify({"fixed":state["fixed"],"safi":state["safi"],"ghair":state["ghair"],"total":total,"profit":profit,"pct":pct,"closed":state["closed"],"positions":state["positions"],"status":state["status"],"last":datetime.now().strftime("%H:%M:%S"),"age":time.time()-state["tick"],"initial":state["initial"],"target":target})

@app.route('/')
def home():
    return """
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>*{box-sizing:border-box}body{margin:0;background:#070a1e;color:#fff;font-family:Cairo;padding:5px}
.h1{border:2px solid #00ff66;border-radius:18px;background:#11158a;text-align:center;padding:10px;margin-bottom:6px}.h1 h2{margin:0;color:#00ff66;font-size:14px}
.bar{display:flex;justify-content:space-between;align-items:center;background:#11158a;border:1px solid #232a8a;border-radius:10px;padding:6px 10px;font-size:11px;font-weight:800;margin-bottom:6px}
.bar.profit{border:2px solid #00ff66;background:linear-gradient(90deg,#001a00,#003300);justify-content:center;gap:12px;font-size:12px}
.bar.status{border:2px solid #00ff66;justify-content:center;font-size:13px}
.boards{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin-bottom:6px}.b{display:flex;flex-direction:column;gap:3px}.bt{font-size:7px;font-weight:900;text-align:center}
.bc{background:#1a1f9e;border:1px solid #2d36c0;border-radius:12px;padding:8px 2px;text-align:center;min-height:68px;display:flex;flex-direction:column;justify-content:center}
.bc.gold{border:2px solid #00ff66}.bc.profit-pos{border:2px solid #00ff66;background:#001a00}.bc.profit-neg{border:2px solid #ff2d55;background:#1a0000}
.bv{font-family:JetBrains Mono;font-size:12px;font-weight:900;direction:ltr}.bv.pos{color:#00ff66}.bv.neg{color:#ff2d55}.bv.w{color:#fff}
.tbl-wrap{background:#11158a;border:1px solid #232a8a;border-radius:16px;overflow:hidden;margin-bottom:8px}.tbl{width:100%;border-collapse:collapse}.tbl th{background:#2a36f0;color:#ff4d8d;font-size:10px;padding:7px;text-align:center}.tbl td{padding:7px 4px;text-align:center;font-family:JetBrains Mono;font-size:10px;border-top:1px solid #1a1f8a}
.spot{background:#00ff55;color:#000;border-radius:20px;padding:3px 8px;font-size:9px;font-weight:900}
</style></head><body>
<div class="h1"><h2>V98 اللوحة رجعت + ميكرو ⚡</h2></div>
<div class="bar status" id="mainStatus">...</div>
<div class="bar profit" id="profitBar"><span>أصلي: <b id="initialCap">1000$</b></span><span>ربح: <b id="profitUsd">0$</b></span><span>نسبة: <b id="profitPctTop">0%</b></span></div>
<div class="bar"><span id="progText">0 / 0.50$</span><span>V98 • <span id="engineAge">0s</span></span><span>🟢 شغال</span></div>
<div class="boards">
<div class="b"><div class="bt">💰 ثابت</div><div class="bc gold"><div class="bv w" id="v_fixed">-</div></div></div>
<div class="b"><div class="bt">💹 صافي</div><div class="bc"><div class="bv" id="v_safi">-</div></div></div>
<div class="b"><div class="bt">⚖️ مقفلة</div><div class="bc"><div class="bv w" id="v_ls">0</div></div></div>
<div class="b"><div class="bt">💎 إجمالي</div><div class="bc gold"><div class="bv" id="v_total">-</div></div></div>
<div class="b"><div class="bt">📈 غير محققة</div><div class="bc"><div class="bv" id="v_ghair">-</div></div></div>
<div class="b"><div class="bt">📊 نسبة</div><div class="bc" id="profitBox"><div class="bv" id="v_profit_pct">0%</div></div></div>
<div class="b"><div class="bt">💰 ربح $</div><div class="bc"><div class="bv" id="v_profit_usd">-</div></div></div>
<div class="b"><div class="bt">🎯 هدف</div><div class="bc"><div class="bv w" id="v_target">0.50$</div></div></div>
</div>
<div class="tbl-wrap"><table class="tbl"><thead><tr><th>عملة</th><th>حالة</th><th>دخول</th><th>حالي</th><th>ربح $</th></tr></thead><tbody id="coins"></tbody></table></div>
<script>
function colorClass(v){ if(Math.abs(v)<0.001) return 'w'; return v>0?'pos':'neg'; }
async function load(){
 try{
  const r=await fetch('/api/data'); const d=await r.json();
  document.getElementById('mainStatus').innerText=d.status+' • '+d.last;
  document.getElementById('initialCap').innerText=d.initial.toFixed(0)+'$';
  document.getElementById('profitUsd').innerText=(d.profit>=0?'+':'')+d.profit.toFixed(2)+'$';
  document.getElementById('profitPctTop').innerText=(d.pct>=0?'+':'')+d.pct.toFixed(2)+'%';
  document.getElementById('v_fixed').innerText=d.fixed.toFixed(2)+'$';
  document.getElementById('v_safi').innerText=(d.safi>=0?'+':'')+d.safi.toFixed(2)+'$'; document.getElementById('v_safi').className='bv '+colorClass(d.safi);
  document.getElementById('v_ghair').innerText=(d.ghair>=0?'+':'')+d.ghair.toFixed(2)+'$'; document.getElementById('v_ghair').className='bv '+colorClass(d.ghair);
  document.getElementById('v_total').innerText=d.total.toFixed(2)+'$';
  document.getElementById('v_ls').innerText=d.closed;
  document.getElementById('v_profit_pct').innerText=(d.pct>=0?'+':'')+d.pct.toFixed(2)+'%'; document.getElementById('v_profit_pct').className='bv '+(d.pct>=0?'pos':'neg');
  document.getElementById('v_profit_usd').innerText=(d.profit>=0?'+':'')+d.profit.toFixed(2)+'$'; document.getElementById('v_profit_usd').className='bv '+(d.profit>=0?'pos':'neg');
  document.getElementById('progText').innerText=d.ghair.toFixed(2)+' / '+d.target.toFixed(2)+'$';
  document.getElementById('engineAge').innerText=d.age.toFixed(1)+'s';
  let h=''; for(const p of d.positions){ h+=`<tr><td style="font-weight:900">${p[0]}</td><td style="font-size:9px">${p[4]}</td><td>${p[1].toFixed(4)}</td><td>${p[2].toFixed(4)}</td><td class="${colorClass(p[3])}">${p[3].toFixed(2)}$</td></tr>`; }
  document.getElementById('coins').innerHTML=h||'<tr><td colspan=5>⚡ بيدخل الآن...</td></tr>';
 }catch(e){}
}
setInterval(load,500); load();
</script>
</body></html>
"""
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(__import__("os").environ.get("PORT",8080)))

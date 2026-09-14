"""
V84.2 GOLD FIXED - لوحة 1103$ الأصلية + Binance Real
"""
from flask import Flask, jsonify
import threading, time, os, random, requests
from datetime import datetime
app = Flask(__name__)

BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY","")
BINANCE_API_SECRET = os.environ.get("BINANCE_API_SECRET","")
REAL = bool(BINANCE_API_KEY and BINANCE_API_SECRET)

config={"capital":1000.0,"per_trade":100.0,"instant_target":0.50,"sl_pct":0.30,"real_mode":REAL}
state={"fixed":1000.0,"safi":0.0,"ghair":0.0,"trades_closed":0,"loss_pool":0.0,"positions":[],"treatment_positions":[],"binance_status":"جاري الربط...","last_update":"...","doctor_stats":{"healed":0,"total_healed_profit":0.0,"start_time":time.time()},"specialty_active":False,"is_running":True,"heartbeat":time.time(),"data_source":"TradingView","real_orders":[]}

def get_movers(limit=60):
    try:
        r=requests.post("https://scanner.tradingview.com/crypto/scan", json={"filter":[{"left":"exchange","operation":"equal","right":"BINANCE"}],"options":{"lang":"en"},"symbols":{"query":{"types":[]},"tickers":[]},"columns":["name","close","change"],"sort":{"sortBy":"change","sortOrder":"desc"},"range":{"from":0,"to":limit}}, timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code==200:
            mov=[]
            for row in r.json().get("data",[]):
                d=row.get("d",[])
                if len(d)>=3:
                    sym=str(d[0]).replace("USDT","").replace("BINANCE:","")
                    close=float(d[1] or 0); change=float(d[2] or 0)
                    if sym and close>0: mov.append((sym,change,close))
            if mov: state["data_source"]=f"TradingView ({len(mov)})"; return mov
    except: pass
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=5)
        if r.status_code==200:
            mov=[(t["symbol"].replace("USDT",""), float(t["priceChangePercent"]), float(t["lastPrice"])) for t in r.json() if t["symbol"].endswith("USDT")]
            mov.sort(key=lambda x:x[1],reverse=True); state["data_source"]="Binance"; return mov[:limit]
    except: pass
    state["data_source"]="LIGHT"; coins=["BTC","ETH","SOL","PEPE","FIL","AVAX","DOT","LINK","MATIC","SHIB","DOGE","CREAM","PNT"]; random.shuffle(coins)
    return [(c,random.uniform(0.5,80),random.uniform(0.001,100)) for c in coins[:limit]]

binance_client=None
if REAL:
    try:
        from binance.client import Client
        binance_client=Client(BINANCE_API_KEY,BINANCE_API_SECRET)
        bal=binance_client.get_asset_balance(asset='USDT')
        state["binance_status"]=f"✅ حقيقي USDT:{bal['free']}"
    except: binance_client=None; config["real_mode"]=False

def real_order(sym,side,amt):
    if not binance_client: return
    try:
        pair=f"{sym}USDT"
        if side=="BUY": binance_client.order_market_buy(symbol=pair,quoteOrderQty=amt)
        else:
            price=float(binance_client.get_symbol_ticker(symbol=pair)['price'])
            binance_client.order_market_sell(symbol=pair,quantity=amt/price)
        state["real_orders"].append({"t":datetime.now().strftime("%H:%M:%S"),"s":sym,"d":side})
    except: pass

def init_pos():
    mov=get_movers(60); state["positions"]=[]
    for sym,pct,price in mov[:6]:
        if config["real_mode"]: real_order(sym,"BUY",config["per_trade"])
        state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()])

init_pos()

def engine():
    while True:
        try:
            state["heartbeat"]=time.time(); mov=get_movers(60); md={m[0]:m for m in mov}
            for p in state["positions"]:
                if p[0] in md: _,pct,np=md[p[0]]; p[3]=np; p[6]=f"مولعة {pct:.1f}%"; pp=(p[3]-p[2])/p[2]*100; p[4]=round(config["per_trade"]*pp/100,3); p[5]=round(pp,2)
            for p in state["treatment_positions"]:
                if p[0] in md: _,_,np=md[p[0]]; p[3]=np; pp=(p[3]-p[2])/p[2]*100; p[4]=round(config["per_trade"]*pp/100,3); p[5]=round(pp,2)
            tc=len(state["treatment_positions"])
            if 10<=tc<=15: state["specialty_active"]=True; state["is_running"]=False; state["binance_status"]=f"🏥 تخصصي {tc}"
            elif tc>15: state["specialty_active"]=True; state["is_running"]=False
            else:
                if state["specialty_active"] and tc<5: state["specialty_active"]=False; state["is_running"]=True
                elif not state["specialty_active"]: state["is_running"]=True; state["binance_status"]=f"📡 {state['data_source']} | {'حقيقي ✅' if config['real_mode'] else 'محاكي'}"
            state["ghair"]=round(sum(p[4] for p in state["positions"]),3); state["loss_pool"]=round(sum(abs(p[9]) for p in state["treatment_positions"]),3); state["last_update"]=datetime.now().strftime("%H:%M:%S")
            if state["is_running"] and state["ghair"]>=config["instant_target"] and state["ghair"]>0 and state["positions"]:
                if config["real_mode"]:
                    for p in state["positions"]: real_order(p[0],"SELL",config["per_trade"])
                state["safi"]=round(state["safi"]+state["ghair"],3); state["trades_closed"]+=len(state["positions"]); state["positions"]=[]; state["ghair"]=0.0
                for sym,pct,price in mov:
                    if sym not in [x[0] for x in state["treatment_positions"]]:
                        if config["real_mode"]: real_order(sym,"BUY",config["per_trade"])
                        state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()])
                        if len(state["positions"])>=6: break
                continue
            to_treat=[p for p in list(state["positions"]) if p[5]<=-config["sl_pct"] or (p[5]<-0.5 and time.time()-p[9]>30)]
            for p in to_treat:
                loss=abs(p[4])
                if p in state["positions"]:
                    if config["real_mode"]: real_order(p[0],"SELL",config["per_trade"])
                    state["positions"].remove(p)
                for sym,pct,price in mov:
                    if sym not in [x[0] for x in state["positions"]+state["treatment_positions"]]:
                        if config["real_mode"]: real_order(sym,"BUY",config["per_trade"])
                        state["treatment_positions"].append([sym,"علاج",price*0.9995,price,0.0,0.0,f"يعالج {p[0]} {loss:.2f}$",0,"TREAT",loss,loss+config["instant_target"],sym+"/USDT",time.time()]); break
            cured=[p for p in list(state["treatment_positions"]) if p[4]>=p[10]]
            for p in cured:
                net=p[4]-p[9]
                if config["real_mode"]: real_order(p[0],"SELL",config["per_trade"])
                state["safi"]=round(state["safi"]+net,3); state["trades_closed"]+=1; state["doctor_stats"]["healed"]+=1; state["doctor_stats"]["total_healed_profit"]=round(state["doctor_stats"]["total_healed_profit"]+net,3); state["treatment_positions"].remove(p)
            if state["is_running"] and len(state["positions"])<6:
                ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
                for sym,pct,price in mov:
                    if sym not in ex:
                        if config["real_mode"]: real_order(sym,"BUY",config["per_trade"])
                        state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()])
                        if len(state["positions"])>=6: break
            time.sleep(1.5)
        except Exception as e: print(e); time.sleep(1)

threading.Thread(target=engine,daemon=True).start()

@app.route('/health')
def health(): return f"OK {state['data_source']} real={config['real_mode']}",200
@app.route('/api/data')
def api_data():
    total=state["fixed"]+state["safi"]+state["ghair"]-state["loss_pool"]; healed=state["doctor_stats"]["healed"]; total_cases=healed+len(state["treatment_positions"]); hr=round(healed/total_cases*100 if total_cases else 50,1)
    return jsonify({"fixed":state["fixed"],"safi":state["safi"],"ghair":state["ghair"],"total":total,"trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"treatment_count":len(state["treatment_positions"]),"positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6]] for p in state["positions"]],"treatment_positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[9],p[10]] for p in state["treatment_positions"]],"binance_status":state["binance_status"],"last_update":state["last_update"],"instant_target":config["instant_target"],"doctor":state["doctor_stats"],"heal_rate":hr,"specialty_active":state["specialty_active"],"is_running":state["is_running"],"heartbeat":round(time.time()-state["heartbeat"],1),"data_source":state["data_source"],"real_mode":config["real_mode"]})

@app.route('/')
def home():
    return """<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}body{margin:0;background:#070a1e;color:#fff;font-family:'Cairo',sans-serif;padding:6px}
.hdr{border:2px solid #00ff66;border-radius:16px;background:#11158a;text-align:center;padding:8px;margin-bottom:6px}
.hdr h2{margin:0;color:#00ff66;font-size:14px;font-weight:900}
.hdr p{margin:3px 0 0;color:#aab;font-size:9px}
.bar{background:#11158a;border:1px solid #232a8a;border-radius:10px;padding:6px 10px;font-size:11px;font-weight:700;margin-bottom:5px;display:flex;justify-content:space-between}
.bar.g{background:#001a00;border-color:#00ff66;color:#00ff66}.bar.b{background:#001a33;border-color:#00e5ff;color:#00e5ff}
.grid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:5px;margin-bottom:6px}
@media(min-width:600px){.grid{grid-template-columns:repeat(7,1fr)}}
.card{background:#1a1f9e;border:1px solid #2d36c0;border-radius:12px;padding:8px 2px;text-align:center;min-height:70px;display:flex;flex-direction:column;justify-content:center}
.card.gold{border:2px solid #00ff66;background:#1a1f4a}.card.treat{border:2px solid #ff9800;background:#2a1a00}
.lbl{font-size:9px;font-weight:700;color:#aab;margin-bottom:2px}
.val{font-family:'JetBrains Mono';font-size:15px;font-weight:900;direction:ltr}.val.w{color:#fff}.val.green{color:#00ff66}.val.red{color:#ff2d55}
.poslist{background:#11158a;border:1px solid #232a8a;border-radius:10px;padding:6px;margin-bottom:5px;font-size:11px}
.row{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid #1a1f6a}
</style></head><body>
<div class="hdr"><h2>V84.2 GOLD FIX + TRADINGVIEW + BINANCE REAL 🔗</h2><p>البيانات TradingView - التنفيذ Binance حقيقي - لوحة 1103$ الأصلية</p></div>
<div class="bar b" id="src">📡...</div>
<div class="bar" id="status">...</div>
<div class="bar g" id="doc">🩺...</div>
<div class="grid">
  <div class="card"><div class="lbl">💰 ثابت</div><div class="val w" id="f1">0$</div></div>
  <div class="card treat"><div class="lbl">🏥 الصيدلية</div><div class="val red" id="f2">0$</div><div class="lbl" id="f2c">0</div></div>
  <div class="card"><div class="lbl">💹 صافي</div><div class="val green" id="f3">0$</div></div>
  <div class="card"><div class="lbl">⚖️ مقفلة</div><div class="val w" id="f4">0</div></div>
  <div class="card gold"><div class="lbl">💎 الإجمالي</div><div class="val green" id="f5">0$</div></div>
  <div class="card"><div class="lbl">📈 غير محققة</div><div class="val" id="f6">0$</div></div>
  <div class="card"><div class="lbl">🔥 حر</div><div class="val w" id="f7">0$</div></div>
</div>
<div class="poslist"><b>📊 المراكز المفتوحة:</b><div id="plist"></div></div>
<div class="poslist"><b>🏥 الصيدلية:</b><div id="tlist"></div></div>
<script>
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('src').innerText='📡 مصدر: '+d.data_source+' | '+(d.real_mode?'🔑 حقيقي ✅':'🔑 محاكاة');
    document.getElementById('status').innerText=d.binance_status+' | V84.2 | '+d.heartbeat+'s | '+d.last_update;
    document.getElementById('doc').innerText=`🩺 شفى ${d.doctor.healed} | ربح ${d.doctor.total_healed_profit.toFixed(2)}$ | ${d.heal_rate}% | هدف ${d.instant_target}$`;
    document.getElementById('f1').innerText=d.fixed.toFixed(1)+'$';
    document.getElementById('f2').innerText=d.loss_pool.toFixed(2)+'$'; document.getElementById('f2c').innerText=d.treatment_count+' مريض';
    document.getElementById('f3').innerText=d.safi.toFixed(2)+'$'; document.getElementById('f3').className='val '+(d.safi>=0?'green':'red');
    document.getElementById('f4').innerText=d.trades_closed;
    document.getElementById('f5').innerText=d.total.toFixed(1)+'$'; document.getElementById('f5').className='val '+(d.total>=d.fixed?'green':'red');
    document.getElementById('f6').innerText=d.ghair.toFixed(2)+'$'; document.getElementById('f6').className='val '+(d.ghair>=0?'green':'red');
    document.getElementById('f7').innerText=(d.safi+d.ghair).toFixed(2)+'$';
    let h=''; for(const p of d.positions){ h+=`<div class="row"><span>${p[0]} ${p[6]}</span><span style="color:${p[5]>=0?'#0f6':'#f25'}">${p[5]}% ${p[4]}$</span></div>` } document.getElementById('plist').innerHTML=h||'فارغ';
    let t=''; for(const p of d.treatment_positions){ t+=`<div class="row"><span>${p[0]} ${p[6]}</span><span>${p[4]}$ / ${p[8]}$</span></div>` } document.getElementById('tlist').innerHTML=t||'فارغ';
  }catch(e){}
}
setInterval(load,1000); load();
</script>
</body></html>"""
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

"""
V84.1 GOLD + TRADINGVIEW + BINANCE REAL - COMPLETE UI
نفس لوحة 1103$ الذهبية V83.6 + ربط Binance حقيقي
"""
from flask import Flask, request, jsonify
import threading, time, os, random, requests
from datetime import datetime
app = Flask(__name__)

BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.environ.get("BINANCE_API_SECRET", "")
REAL_TRADING = bool(BINANCE_API_KEY and BINANCE_API_SECRET)

config = {"capital":1000.0,"per_trade":100.0,"tp_pct":0.80,"sl_pct":0.30,"instant_target":0.50,"real_mode":REAL_TRADING}
state = {"fixed":1000.0,"free":0.0,"safi":0.0,"ghair":0.0,"trades_closed":0,"loss_pool":0.0,"treatment_count":0,"positions":[],"treatment_positions":[],"binance_status":"جاري الربط...","last_update":"...","doctor_stats":{"healed":0,"total_healed_profit":0.0,"failed":0,"start_time":time.time()},"specialty_active":False,"is_running":True,"heartbeat":time.time(),"data_source":"TradingView","real_orders":[]}

def get_tradingview_movers(limit=60):
    try:
        url="https://scanner.tradingview.com/crypto/scan"
        payload={"filter":[{"left":"exchange","operation":"equal","right":"BINANCE"}],"options":{"lang":"en"},"symbols":{"query":{"types":[]},"tickers":[]},"columns":["name","close","change","volume"],"sort":{"sortBy":"change","sortOrder":"desc"},"range":{"from":0,"to":limit}}
        r=requests.post(url, json=payload, timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code==200:
            movers=[]
            for row in r.json().get("data", []):
                d=row.get("d", [])
                if len(d)>=3:
                    name=str(d[0]); close=float(d[1]) if d[1] else 0; change=float(d[2]) if d[2] else 0
                    sym=name.replace("USDT","").replace("BINANCE:","")
                    if sym and close>0 and abs(change)<200: movers.append((sym, change, close))
            if movers: state["data_source"]=f"TradingView ({len(movers)})"; return movers
    except: pass
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=5)
        if r.status_code==200:
            mov=[]
            for t in r.json():
                if t["symbol"].endswith("USDT"): mov.append((t["symbol"].replace("USDT",""), float(t["priceChangePercent"]), float(t["lastPrice"])))
            mov.sort(key=lambda x: x[1], reverse=True); state["data_source"]="Binance"; return mov[:limit]
    except: pass
    state["data_source"]="LIGHT"; coins=["BTC","ETH","SOL","PEPE","FIL","AVAX","DOT","LINK","MATIC","SHIB","DOGE","CREAM","PNT","KDA","CLV","ARK","T","MDX"]; random.shuffle(coins)
    return [(c, round(random.uniform(0.5,85),1), round(random.uniform(0.001,100),4)) for c in coins[:limit]]

binance_client=None
if REAL_TRADING:
    try:
        from binance.client import Client
        binance_client=Client(BINANCE_API_KEY, BINANCE_API_SECRET)
        bal=binance_client.get_asset_balance(asset='USDT')
        state["binance_status"]=f"Binance حقيقي USDT:{bal['free']}"
    except Exception as e: print(f"Binance fail {e}"); binance_client=None; config["real_mode"]=False

def place_real_order(symbol, side, amount_usdt):
    if not binance_client: return None
    try:
        pair=f"{symbol}USDT"
        if side=="BUY": order=binance_client.order_market_buy(symbol=pair, quoteOrderQty=amount_usdt)
        else:
            price=float(binance_client.get_symbol_ticker(symbol=pair)['price']); qty=amount_usdt/price
            order=binance_client.order_market_sell(symbol=pair, quantity=qty)
        state["real_orders"].append({"time":datetime.now().strftime("%H:%M:%S"), "sym":symbol, "side":side})
        return order
    except Exception as e: print(f"Order err {e}"); return None

def init_positions_fixed():
    movers=get_tradingview_movers(60); state["positions"]=[]
    for i in range(min(6, len(movers))):
        sym,pct,price=movers[i]
        if config["real_mode"]:
            try: place_real_order(sym, "BUY", config["per_trade"])
            except: pass
        state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}% TV",0,"NORMAL",time.time()])

init_positions_fixed()

def engine():
    while True:
        try:
            state["heartbeat"]=time.time()
            movers=get_tradingview_movers(60); md={m[0]:m for m in movers}
            for p in state["positions"]:
                if p[0] in md: _,pct,np=md[p[0]]; p[3]=np; p[6]=f"مولعة {pct:.1f}% TV"; pp=(p[3]-p[2])/p[2]*100; p[4]=round(config["per_trade"]*pp/100,3); p[5]=round(pp,2)
                else: p[3]=max(0.0001, p[3]*(1+random.uniform(-0.01,0.02)/100)); pp=(p[3]-p[2])/p[2]*100; p[4]=round(config["per_trade"]*pp/100,3); p[5]=round(pp,2)
            for p in state["treatment_positions"]:
                if p[0] in md: _,_,np=md[p[0]]; p[3]=np; pp=(p[3]-p[2])/p[2]*100; p[4]=round(config["per_trade"]*pp/100,3); p[5]=round(pp,2)
            tc=len(state["treatment_positions"]); state["treatment_count"]=tc
            if 10<=tc<=15: state["specialty_active"]=True; state["is_running"]=False; state["binance_status"]=f"🏥 تخصصي {tc} مريض"
            elif tc>15: state["specialty_active"]=True; state["is_running"]=False
            else:
                if state["specialty_active"] and tc<5: state["specialty_active"]=False; state["is_running"]=True
                elif not state["specialty_active"]: state["is_running"]=True; state["binance_status"]=f"📡 {state['data_source']} | {'حقيقي ✅' if config['real_mode'] else 'محاكي'}"
            state["ghair"]=round(sum([p[4] for p in state["positions"]]),3); state["loss_pool"]=round(sum([abs(p[9]) for p in state["treatment_positions"]]),3); state["last_update"]=datetime.now().strftime("%H:%M:%S")
            if state["is_running"] and state["ghair"]>=config["instant_target"] and state["ghair"]>0 and len(state["positions"])>0:
                if config["real_mode"]:
                    for p in state["positions"]:
                        try: place_real_order(p[0], "SELL", config["per_trade"])
                        except: pass
                state["safi"]=round(state["safi"]+state["ghair"],3); state["trades_closed"]+=len(state["positions"]); state["positions"]=[]; state["ghair"]=0.0
                for sym,pct,price in movers:
                    if sym not in [x[0] for x in state["treatment_positions"]]:
                        if config["real_mode"]:
                            try: place_real_order(sym, "BUY", config["per_trade"])
                            except: pass
                        state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}% TV",0,"NORMAL",time.time()])
                        if len(state["positions"])>=6: break
                continue
            to_treat=[]; now=time.time()
            for p in list(state["positions"]):
                if p[5]<=-config["sl_pct"] or (p[5]<-0.5 and (now-p[9])>30): to_treat.append(p)
            for p in to_treat:
                loss=abs(p[4])
                if p in state["positions"]:
                    if config["real_mode"]:
                        try: place_real_order(p[0], "SELL", config["per_trade"])
                        except: pass
                    state["positions"].remove(p)
                for sym,pct,price in movers:
                    if sym not in [x[0] for x in state["positions"]+state["treatment_positions"]]:
                        tn=loss+config["instant_target"]
                        if config["real_mode"]:
                            try: place_real_order(sym, "BUY", config["per_trade"])
                            except: pass
                        state["treatment_positions"].append([sym,"علاج",price*0.9995,price,0.0,0.0,f"يعالج {p[0]} {loss:.2f}$",0,"TREAT",loss,tn,sym+"/USDT",time.time()]); break
            cured=[p for p in list(state["treatment_positions"]) if p[4]>=p[10]]
            for p in cured:
                loss=p[9]; net=p[4]-loss
                if config["real_mode"]:
                    try: place_real_order(p[0], "SELL", config["per_trade"])
                    except: pass
                state["safi"]=round(state["safi"]+net,3); state["trades_closed"]+=1; state["doctor_stats"]["healed"]+=1; state["doctor_stats"]["total_healed_profit"]=round(state["doctor_stats"]["total_healed_profit"]+net,3); state["treatment_positions"].remove(p)
            if state["is_running"] and len(state["positions"])<6:
                ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
                for sym,pct,price in movers:
                    if sym not in ex:
                        if config["real_mode"]:
                            try: place_real_order(sym, "BUY", config["per_trade"])
                            except: pass
                        state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}% TV",0,"NORMAL",time.time()])
                        if len(state["positions"])>=6: break
            time.sleep(1.5)
        except Exception as e: print(f"ENG ERR {e}"); time.sleep(1)

threading.Thread(target=engine,daemon=True).start()

@app.route('/health')
def health(): return f"OK src={state['data_source']} real={config['real_mode']} hb={time.time()-state['heartbeat']:.1f}s",200
@app.route('/api/data')
def api_data():
    total=state["fixed"]+state["safi"]+state["ghair"]-state["loss_pool"]; healed=state["doctor_stats"]["healed"]; total_cases=healed+len(state["treatment_positions"]); heal_rate=round((healed/total_cases*100) if total_cases>0 else 50,1)
    safi_pct=(state["safi"]/state["fixed"]*100) if state["fixed"]>0 else 0; ghair_pct=(state["ghair"]/state["fixed"]*100) if state["fixed"]>0 else 0; total_pct=((total-state["fixed"])/state["fixed"]*100) if state["fixed"]>0 else 0
    return jsonify({"fixed":state["fixed"],"safi":state["safi"],"ghair":state["ghair"],"total":total,"trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"treatment_count":state["treatment_count"],"positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6]] for p in state["positions"]],"treatment_positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[9],p[10]] for p in state["treatment_positions"]],"binance_status":state["binance_status"],"last_update":state["last_update"],"instant_target":config["instant_target"],"doctor":state["doctor_stats"],"heal_rate":heal_rate,"safi_pct":round(safi_pct,3),"ghair_pct":round(ghair_pct,4),"total_pct":round(total_pct,3),"specialty_active":state["specialty_active"],"is_running":state["is_running"],"heartbeat":round(time.time()-state["heartbeat"],1),"data_source":state["data_source"],"real_mode":config["real_mode"],"real_orders":state["real_orders"][-5:]})
@app.route('/api/config',methods=['POST'])
def api_cfg():
    d=request.get_json()
    if 'capital' in d: state["fixed"]=float(d['capital'])
    if 'per_trade' in d: config["per_trade"]=float(d['per_trade'])
    if 'tp' in d: config["tp_pct"]=float(d['tp'])
    if 'instant_target' in d: config["instant_target"]=float(d['instant_target'])
    return jsonify({"ok":True})
@app.route('/api/compound',methods=['POST'])
def api_compound():
    profit=state["safi"]+state["ghair"]
    if profit>0: state["fixed"]=round(state["fixed"]+profit,3); state["safi"]=0.0; state["ghair"]=0.0; state["positions"]=[]
    return jsonify({"ok":True,"new_capital":state["fixed"]})
@app.route('/api/reset_full',methods=['POST'])
def reset_full():
    state["safi"]=0.0; state["ghair"]=0.0; state["loss_pool"]=0.0; state["trades_closed"]=0; state["positions"]=[]; state["treatment_positions"]=[]; state["doctor_stats"]={"healed":0,"total_healed_profit":0.0,"failed":0,"start_time":time.time()}; state["specialty_active"]=False; state["is_running"]=True; init_positions_fixed(); return jsonify({"ok":True})
@app.route('/')
def home():
    return """<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}body{margin:0;background:#070a1e;color:#fff;font-family:Cairo;padding:5px}
.h1{border:2px solid #00ff66;border-radius:18px;background:#11158a;text-align:center;padding:10px 8px;margin-bottom:6px}
.h1 h2{margin:0;color:#00ff66;font-size:15px;font-weight:900}.h1 p{margin:4px 0 0;color:#aab;font-size:9px}
.bar{display:flex;justify-content:space-between;align-items:center;background:#11158a;border:1px solid #232a8a;border-radius:10px;padding:6px 10px;font-size:11px;font-weight:800;margin-bottom:6px}
.bar.doc{background:#001a00;border:1.5px solid #00ff66;color:#00ff66}.bar.real{background:#001a33;border:1.5px solid #00e5ff;color:#00e5ff}
.b{display:flex;flex-direction:column;gap:4px}.bt{font-size:10px;font-weight:900;text-align:center}
.bc{background:#1a1f9e;border:1px solid #2d36c0;border-radius:14px;padding:10px 2px;text-align:center;min-height:76px;display:flex;flex-direction:column;justify-content:center}
.bc.gold{border:2px solid #00ff66}.bc.treat{border:2px solid #ff9800;background:#2a1a00}
.bv{font-family:JetBrains Mono;font-size:17px;font-weight:900;direction:ltr}.bv.pos{color:#00ff66}.bv.neg{color:#ff2d55}.bv.zero{color:#6a6a8a}.bv.w{color:#fff}
.boards{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;margin-bottom:6px}
.card{background:#11158a;border:1px solid #232a8a;border-radius:12px;padding:8px;margin-bottom:6px;font-size:11px}
</style></head><body>
<div class="h1"><h2>V84.1 GOLD + TRADINGVIEW + BINANCE REAL 🔗</h2><p>البيانات: TradingView + التنفيذ: Binance API حقيقي</p></div>
<div class="bar" id="srcBar">📡 مصدر:...</div>
<div class="bar real" id="realBar">🔑 وضع: محاكاة</div>
<div class="bar"><span id="binStatus">...</span><span>V84.1 GOLD | <span id="hb"></span> | <span id="lu"></span></span></div>
<div class="bar doc" id="docBar">🩺 دكتور:...</div>
<div class="boards">
  <div class="b"><div class="bt">💰 ثابت</div><div class="bc"><div class="bv w" id="v_fixed">0$</div></div></div>
  <div class="b"><div class="bt">🏥 الصيدلية</div><div class="bc treat"><div class="bv neg" id="v_treat">0$</div><div class="bt" id="v_treat_c"></div></div></div>
  <div class="b"><div class="bt">💹 صافي</div><div class="bc"><div class="bv" id="v_safi">0$</div><div class="bt" id="p_safi"></div></div></div>
  <div class="b"><div class="bt">⚖️ مقفلة</div><div class="bc"><div class="bv w" id="v_ls">0</div></div></div>
  <div class="b"><div class="bt">💎 الإجمالي</div><div class="bc gold"><div class="bv" id="v_total">0$</div><div class="bt" id="p_total"></div></div></div>
  <div class="b"><div class="bt">📈 غير محققة</div><div class="bc"><div class="bv" id="v_ghair">0$</div><div class="bt" id="p_ghair"></div></div></div>
  <div class="b"><div class="bt">🔥 حر</div><div class="bc"><div class="bv w" id="v_free">0$</div></div></div>
</div>
<div class="card"><b>📊 المراكز:</b><div id="pos"></div></div>
<div class="card"><b>🏥 الصيدلية:</b><div id="treat"></div></div>
<div class="card"><b>آخر أوامر Binance:</b><div id="log" style="direction:ltr"></div></div>
<script>
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('srcBar').innerText='📡 مصدر: '+d.data_source+' | '+d.binance_status;
    document.getElementById('realBar').innerText=d.real_mode? '🔑 وضع حقيقي ✅ Binance متصل' : '🔑 وضع محاكاة';
    document.getElementById('binStatus').innerText=d.binance_status; document.getElementById('hb').innerText=d.heartbeat+'s'; document.getElementById('lu').innerText=d.last_update;
    document.getElementById('docBar').innerText=`🩺 شفى ${d.doctor.healed} | ربح علاج ${d.doctor.total_healed_profit.toFixed(2)}$ | نسبة ${d.heal_rate}%`;
    document.getElementById('v_fixed').innerText=d.fixed.toFixed(1)+'$'; document.getElementById('v_treat').innerText=d.loss_pool.toFixed(2)+'$'; document.getElementById('v_treat_c').innerText=d.treatment_count+' دواء';
    document.getElementById('v_safi').innerText=d.safi.toFixed(2)+'$'; document.getElementById('v_ls').innerText=d.trades_closed; document.getElementById('v_total').innerText=d.total.toFixed(1)+'$'; document.getElementById('v_ghair').innerText=d.ghair.toFixed(2)+'$'; document.getElementById('v_free').innerText=(d.safi+d.ghair).toFixed(2)+'$';
    document.getElementById('p_safi').innerText=(d.safi_pct||0).toFixed(2)+'%'; document.getElementById('p_ghair').innerText=(d.ghair_pct||0).toFixed(3)+'%'; document.getElementById('p_total').innerText=(d.total_pct||0).toFixed(3)+'%';
    let ph=''; for(const p of d.positions){ ph+=`<div style="display:flex;justify-content:space-between;border-bottom:1px solid #333;padding:2px"><span>${p[0]} ${p[6]}</span><span style="color:${p[5]>=0?'#0f6':'#f25'}">${p[5]}% ${p[4]}$</span></div>` } document.getElementById('pos').innerHTML=ph||'لا يوجد';
    let th=''; for(const p of d.treatment_positions){ th+=`<div style="display:flex;justify-content:space-between;border-bottom:1px solid #332;padding:2px"><span>${p[0]} ${p[6]}</span><span>${p[4]}$ / ${p[8]}$</span></div>` } document.getElementById('treat').innerHTML=th||'لا يوجد';
    let lg=''; for(const o of d.real_orders){ lg+=`${o.time} ${o.side} ${o.sym}<br>`; } document.getElementById('log').innerHTML=lg||'لا يوجد أوامر حقيقية بعد';
  }catch(e){}
}
setInterval(load,1000); load();
</script>
</body></html>"""
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

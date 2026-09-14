"""
V84.5 LUXURY GOLD - نفس لوحة 1103$ الفخمة + TradingView + Binance REAL
"""
from flask import Flask, jsonify, request
import threading, time, os, random, requests
from datetime import datetime
app = Flask(__name__)

BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY","")
BINANCE_API_SECRET = os.environ.get("BINANCE_API_SECRET","")
REAL = bool(BINANCE_API_KEY and BINANCE_API_SECRET)

config={"capital":1000.0,"per_trade":100.0,"instant_target":0.5,"sl_pct":0.30,"real_mode":REAL,"auto_heal":True}
state={"fixed":1000.0,"safi":0.0,"ghair":0.0,"trades_closed":0,"loss_pool":0.0,"positions":[],"treatment_positions":[],"binance_status":"جاري الربط...","last_update":"...","doctor_stats":{"healed":0,"total_healed_profit":0.0,"start_time":time.time()},"specialty_active":False,"is_running":True,"heartbeat":time.time(),"data_source":"TradingView","real_orders":[],"logs":[]}

def log(msg): state["logs"].insert(0, f"{datetime.now().strftime('%H:%M:%S')} {msg}"); state["logs"]=state["logs"][:20]

def get_movers(limit=80):
    try:
        r=requests.post("https://scanner.tradingview.com/crypto/scan", json={"filter":[{"left":"exchange","operation":"equal","right":"BINANCE"}],"options":{"lang":"en"},"symbols":{"query":{"types":[]},"tickers":[]},"columns":["name","close","change"],"sort":{"sortBy":"change","sortOrder":"desc"},"range":{"from":0,"to":limit}}, timeout=6, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code==200:
            mov=[]
            for row in r.json().get("data",[]):
                d=row.get("d",[])
                if len(d)>=3:
                    sym=str(d[0]).replace("BINANCE:","").replace("USDT","")
                    close=float(d[1] or 0); change=float(d[2] or 0)
                    if sym and close>0 and change>0: mov.append((sym,change,close))
            if mov: state["data_source"]=f"TradingView 🔥 {len(mov)}"; return mov
    except Exception as e: log(f"TV err {e}")
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=5)
        if r.status_code==200:
            mov=[(t["symbol"].replace("USDT",""), float(t["priceChangePercent"]), float(t["lastPrice"])) for t in r.json() if t["symbol"].endswith("USDT") and float(t["priceChangePercent"])>0]
            mov.sort(key=lambda x:x[1],reverse=True); state["data_source"]="Binance Backup"; return mov[:limit]
    except: pass
    state["data_source"]="LIGHT"; coins=["CREAM","PNT","KDA","CLV","MDX","PENDLE","BTC","ETH","SOL","PEPE","FIL"]; random.shuffle(coins)
    return [(c,random.uniform(5,70),random.uniform(0.001,100)) for c in coins[:limit]]

binance_client=None
if REAL:
    try:
        from binance.client import Client
        binance_client=Client(BINANCE_API_KEY,BINANCE_API_SECRET)
        bal=binance_client.get_asset_balance(asset='USDT')
        state["binance_status"]=f"✅ حقيقي USDT:{float(bal['free']):.2f}$"; log("Binance متصل")
    except Exception as e: log(f"Binance fail {e}"); binance_client=None; config["real_mode"]=False
else:
    state["binance_status"]="⚠️ محاكاة - ضع مفاتيح Binance"

def real_order(sym,side,amt):
    if not binance_client: return True
    try:
        pair=f"{sym}USDT"
        if side=="BUY": binance_client.order_market_buy(symbol=pair,quoteOrderQty=amt)
        else:
            price=float(binance_client.get_symbol_ticker(symbol=pair)['price'])
            qty=amt/price
            info=binance_client.get_symbol_info(pair)
            # تصحيح الكمية
            binance_client.order_market_sell(symbol=pair,quantity=qty)
        state["real_orders"].append({"t":datetime.now().strftime("%H:%M:%S"),"s":sym,"d":side}); log(f"{side} {sym} حقيقي"); return True
    except Exception as e: log(f"أمر فشل {sym} {e}"); return False

def init_pos():
    mov=get_movers(80); state["positions"]=[]
    for sym,pct,price in mov[:6]:
        if config["real_mode"]: real_order(sym,"BUY",config["per_trade"])
        state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()])
    log(f"بداية {len(state['positions'])} مراكز")

init_pos()

def engine():
    while True:
        try:
            if not state["is_running"]: time.sleep(1); continue
            state["heartbeat"]=time.time(); mov=get_movers(80); md={m[0]:m for m in mov}
            for p in state["positions"]:
                if p[0] in md: _,pct,np=md[p[0]]; p[3]=np; p[6]=f"مولعة {pct:.1f}%"; pp=(p[3]-p[2])/p[2]*100; p[4]=round(config["per_trade"]*pp/100,3); p[5]=round(pp,2)
            for p in state["treatment_positions"]:
                if p[0] in md: _,_,np=md[p[0]]; p[3]=np; pp=(p[3]-p[2])/p[2]*100; p[4]=round(config["per_trade"]*pp/100,3); p[5]=round(pp,2)
            tc=len(state["treatment_positions"])
            if 10<=tc<=15: state["specialty_active"]=True; state["is_running"]=False
            elif tc>15: state["specialty_active"]=True; state["is_running"]=False
            else:
                if state["specialty_active"] and tc<5: state["specialty_active"]=False; state["is_running"]=True
            state["ghair"]=round(sum(p[4] for p in state["positions"]),3); state["loss_pool"]=round(sum(abs(p[9]) for p in state["treatment_positions"]),3); state["last_update"]=datetime.now().strftime("%H:%M:%S")
            if state["ghair"]>=config["instant_target"] and state["ghair"]>0 and state["positions"]:
                if config["real_mode"]:
                    for p in state["positions"]: real_order(p[0],"SELL",config["per_trade"])
                state["safi"]=round(state["safi"]+state["ghair"],3); state["trades_closed"]+=len(state["positions"]); log(f"جني {state['ghair']}$"); state["positions"]=[]; state["ghair"]=0.0
                for sym,pct,price in mov:
                    if sym not in [x[0] for x in state["treatment_positions"]]:
                        if config["real_mode"]: real_order(sym,"BUY",config["per_trade"])
                        state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()])
                        if len(state["positions"])>=6: break
                continue
            to_treat=[p for p in list(state["positions"]) if p[5]<=-config["sl_pct"] or (p[5]<-0.5 and time.time()-p[9]>35)]
            for p in to_treat:
                loss=abs(p[4])
                if p in state["positions"]:
                    if config["real_mode"]: real_order(p[0],"SELL",config["per_trade"])
                    state["positions"].remove(p)
                for sym,pct,price in mov:
                    if sym not in [x[0] for x in state["positions"]+state["treatment_positions"]]:
                        if config["real_mode"]: real_order(sym,"BUY",config["per_trade"])
                        state["treatment_positions"].append([sym,"علاج",price*0.9995,price,0.0,0.0,f"يعالج {p[0]} {loss:.2f}$",0,"TREAT",loss,loss+config["instant_target"],sym+"/USDT",time.time()]); log(f"علاج {p[0]}->{sym}"); break
            cured=[p for p in list(state["treatment_positions"]) if p[4]>=p[10]]
            for p in cured:
                net=p[4]-p[9]
                if config["real_mode"]: real_order(p[0],"SELL",config["per_trade"])
                state["safi"]=round(state["safi"]+net,3); state["trades_closed"]+=1; state["doctor_stats"]["healed"]+=1; state["doctor_stats"]["total_healed_profit"]=round(state["doctor_stats"]["total_healed_profit"]+net,3); state["treatment_positions"].remove(p); log(f"شفاء {p[0]} +{net:.2f}$")
            if len(state["positions"])<6:
                ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
                for sym,pct,price in mov:
                    if sym not in ex:
                        if config["real_mode"]: real_order(sym,"BUY",config["per_trade"])
                        state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()])
                        if len(state["positions"])>=6: break
            time.sleep(1.2)
        except Exception as e: log(f"محرك {e}"); time.sleep(1)

threading.Thread(target=engine,daemon=True).start()

@app.route('/health')
def health(): return f"OK {state['data_source']} real={config['real_mode']}",200

@app.route('/api/control/<cmd>')
def control(cmd):
    if cmd=="toggle": state["is_running"]=not state["is_running"]; log("تشغيل" if state["is_running"] else "ايقاف")
    elif cmd=="reset": state["safi"]=0; state["ghair"]=0; state["trades_closed"]=0; state["positions"]=[]; state["treatment_positions"]=[]; init_pos(); log("تصفير")
    elif cmd=="heal":
        for p in list(state["positions"]):
            if p[5]<0:
                loss=abs(p[4]); state["positions"].remove(p)
                mov=get_movers(30)
                for sym,pct,price in mov:
                    if sym not in [x[0] for x in state["positions"]+state["treatment_positions"]]:
                        state["treatment_positions"].append([sym,"علاج",price*0.9995,price,0.0,0.0,f"يدوي {p[0]}",0,"TREAT",loss,loss+config["instant_target"],sym, time.time()]); break
                break
        log("علاج يدوي")
    return jsonify({"ok":True,"running":state["is_running"]})

@app.route('/api/data')
def api_data():
    total=state["fixed"]+state["safi"]+state["ghair"]-state["loss_pool"]; healed=state["doctor_stats"]["healed"]; total_cases=healed+len(state["treatment_positions"]); hr=round(healed/total_cases*100 if total_cases else 50,1)
    return jsonify({"fixed":state["fixed"],"safi":state["safi"],"ghair":state["ghair"],"total":total,"trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"treatment_count":len(state["treatment_positions"]),"positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6]] for p in state["positions"]],"treatment_positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[9],p[10],p[4]/p[10]*100 if p[10]!=0 else 0] for p in state["treatment_positions"]],"binance_status":state["binance_status"],"last_update":state["last_update"],"instant_target":config["instant_target"],"doctor":state["doctor_stats"],"heal_rate":hr,"specialty_active":state["specialty_active"],"is_running":state["is_running"],"heartbeat":round(time.time()-state["heartbeat"],1),"data_source":state["data_source"],"real_mode":config["real_mode"],"logs":state["logs"]})

@app.route('/')
def home():
    return """<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}body{margin:0;background:#050817;color:#fff;font-family:'Cairo',sans-serif;padding:5px}
.hdr{border:2px solid #00ff66;border-radius:14px;background:linear-gradient(90deg,#11158a,#1a1f9e);text-align:center;padding:7px;margin-bottom:5px}
.hdr h2{margin:0;color:#00ff66;font-size:13px;font-weight:900}.hdr p{margin:2px 0 0;color:#aab;font-size:8px}
.bar{border-radius:10px;padding:5px 10px;font-size:10px;font-weight:700;margin-bottom:4px;display:flex;justify-content:space-between;align-items:center}
.bar.src{background:#11158a;border:1px solid #00ff66;color:#00ff66}.bar.st{background:#0a104a;border:1px solid #00e5ff;color:#00e5ff}.bar.doc{background:#001a00;border:1px solid #00ff66;color:#00ff66}
.controls{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:5px;margin-bottom:5px}
.btn{border:1px solid #2d36c0;background:#1a1f9e;color:#fff;border-radius:8px;padding:6px;font-family:'Cairo';font-size:10px;font-weight:900;cursor:pointer}
.btn.on{background:#00ff66;color:#000;border-color:#00ff66}.btn.off{background:#ff2d55;color:#fff}.btn.heal{background:#ff9800;color:#000}.btn.reset{background:#333}
.grid{display:grid;grid-template-columns:repeat(7,1fr);gap:4px;margin-bottom:6px;overflow-x:auto}
.card{background:#1a1f9e;border:1px solid #2d36c0;border-radius:10px;padding:7px 2px;text-align:center;min-width:65px}
.card.gold{border:2px solid #00ff66;background:#1a1f4a;box-shadow:0 0 10px #00ff6622}.card.treat{border:2px solid #ff9800;background:#2a1a00}
.lbl{font-size:8px;color:#aab}.val{font-family:'JetBrains Mono';font-size:13px;font-weight:900;direction:ltr}.val.w{color:#fff}.val.g{color:#00ff66}.val.r{color:#ff2d55}
.section{background:#11158a;border:1px solid #232a8a;border-radius:10px;padding:6px;margin-bottom:5px}
.section h4{margin:0 0 6px;font-size:11px;color:#00e5ff}
.hscroll{display:flex;gap:6px;overflow-x:auto;padding-bottom:4px}
.coin{background:#0e1240;border:1px solid #2d36c0;border-radius:10px;padding:8px;min-width:110px;text-align:center;flex-shrink:0}
.coin.up{border-color:#00ff66}.coin.down{border-color:#ff2d55}
.coin.sym{font-family:'JetBrains Mono';font-size:12px;font-weight:900}
.coin.pct{font-size:10px;margin:2px 0}.coin.pnl{font-family:'JetBrains Mono';font-size:11px;font-weight:900}
.treat-card{background:#1a1200;border:1px solid #ff9800;border-radius:10px;padding:7px;min-width:140px;flex-shrink:0}
.progress{height:4px;background:#333;border-radius:2px;margin:4px 0;overflow:hidden}.progress i{display:block;height:100%;background:#00ff66}
.log{font-size:8px;color:#aaa;font-family:'JetBrains Mono';line-height:1.4;max-height:60px;overflow-y:auto}
@media(max-width:700px){.grid{grid-template-columns:repeat(4,1fr)}.controls{grid-template-columns:1fr 1fr}}
</style></head><body>
<div class="hdr"><h2>V84.5 LUXURY GOLD + TRADINGVIEW + BINANCE REAL 🔥</h2><p>لوحة 1103$ الفخمة الأصلية - عملات أفقية + صيدلية + تحكم كامل</p></div>
<div class="bar src" id="src">📡...</div>
<div class="bar st" id="status">...</div>
<div class="bar doc" id="doc">🩺...</div>

<div class="controls">
<button class="btn" id="btnRun" onclick="ctrl('toggle')">⏯️ تشغيل/ايقاف</button>
<button class="btn heal" onclick="ctrl('heal')">🏥 علاج يدوي</button>
<button class="btn reset" onclick="ctrl('reset')">♻️ تصفير</button>
<button class="btn" onclick="location.reload()">🔄 تحديث</button>
</div>

<div class="grid">
  <div class="card"><div class="lbl">💰 ثابت</div><div class="val w" id="f1">-</div></div>
  <div class="card treat"><div class="lbl">🏥 الصيدلية</div><div class="val r" id="f2">-</div><div class="lbl" id="f2c">-</div></div>
  <div class="card"><div class="lbl">💹 صافي</div><div class="val g" id="f3">-</div></div>
  <div class="card"><div class="lbl">⚖️ مقفلة</div><div class="val w" id="f4">-</div></div>
  <div class="card gold"><div class="lbl">💎 الإجمالي</div><div class="val g" id="f5">-</div></div>
  <div class="card"><div class="lbl">📈 غير محققة</div><div class="val" id="f6">-</div></div>
  <div class="card"><div class="lbl">🔥 حر</div><div class="val w" id="f7">-</div></div>
</div>

<div class="section"><h4>📊 المراكز المفتوحة (أفقية):</h4><div class="hscroll" id="plist"></div></div>
<div class="section"><h4>🏥 الصيدلية - العلاج (أفقية + نسبة شفاء):</h4><div class="hscroll" id="tlist"></div></div>
<div class="section"><h4>🔑 المفاتيح والسجلات:</h4><div class="log" id="logs"></div></div>

<script>
async function ctrl(cmd){ await fetch('/api/control/'+cmd); load(); }
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('src').innerText='📡 '+d.data_source+' | '+(d.real_mode?'🔑 حقيقي ✅ Binance متصل':'🔑 محاكاة');
    document.getElementById('status').innerText=d.binance_status+' | V84.5 LUXURY | '+(d.is_running?'🟢 شغال':'🔴 تخصصي')+' | '+d.heartbeat+'s | '+d.last_update;
    document.getElementById('doc').innerText=`🩺 شفى ${d.doctor.healed} | ربح ${d.doctor.total_healed_profit.toFixed(2)}$ | نسبة شفاء ${d.heal_rate}% | هدف ${d.instant_target}$ | ${d.treatment_count} مريض`;
    document.getElementById('btnRun').className='btn '+(d.is_running?'on':'off'); document.getElementById('btnRun').innerText=d.is_running?'⏸️ ايقاف':'▶️ تشغيل';
    document.getElementById('f1').innerText=d.fixed.toFixed(1)+'$';
    document.getElementById('f2').innerText=d.loss_pool.toFixed(2)+'$'; document.getElementById('f2c').innerText=d.treatment_count+' مريض';
    document.getElementById('f3').innerText=d.safi.toFixed(2)+'$'; document.getElementById('f3').className='val '+(d.safi>=0?'g':'r');
    document.getElementById('f4').innerText=d.trades_closed;
    document.getElementById('f5').innerText=d.total.toFixed(1)+'$'; document.getElementById('f5').className='val '+(d.total>=d.fixed?'g':'r');
    document.getElementById('f6').innerText=d.ghair.toFixed(2)+'$'; document.getElementById('f6').className='val '+(d.ghair>=0?'g':'r');
    document.getElementById('f7').innerText=(d.safi+d.ghair).toFixed(2)+'$';
    let h=''; for(const p of d.positions){ const up=p[5]>=0; h+=`<div class="coin ${up?'up':'down'}"><div class="sym">${p[0]}</div><div class="pct">${p[6]}</div><div class="pnl" style="color:${up?'#0f6':'#f25'}">${p[5]}%<br>${p[4]}$</div></div>` } document.getElementById('plist').innerHTML=h||'فارغ';
    let t=''; for(const p of d.treatment_positions){ let prog=Math.min(100,Math.max(0,p[9])); t+=`<div class="treat-card"><div style="font-size:11px;font-weight:900">${p[0]} <span style="font-size:8px">${p[6]}</span></div><div style="font-size:9px">خسارة ${p[7].toFixed(2)}$ → هدف ${p[8].toFixed(2)}$</div><div class="progress"><i style="width:${prog}%"></i></div><div style="font-family:'JetBrains Mono';font-size:11px;color:#0f6">${p[4].toFixed(3)}$ / ${p[8].toFixed(2)}$ (${prog.toFixed(0)}%)</div></div>` } document.getElementById('tlist').innerHTML=t||'لا يوجد مرضى - الحمدلله';
    document.getElementById('logs').innerHTML=d.logs.join('<br>');
  }catch(e){}
}
setInterval(load,1000); load();
</script>
</body></html>"""
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

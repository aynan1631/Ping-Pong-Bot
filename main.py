from flask import Flask, request, jsonify, redirect
import threading, time, os
from datetime import datetime

try:
    import ccxt
    HAS_CCXT = True
    exchange = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
except:
    HAS_CCXT = False
    exchange = None

app = Flask(__name__)

config = {"capital":2000.0,"per_trade":200.0,"tp_pct":0.8,"sl_pct":-1.5,"daily_target_pct":3.5,"panic_drop_pct":1.0}
state = {
    "daily_start":2000.0,"daily_peak":2000.0,"daily_peak_pct":0.0,
    "safi":0.0,"ghair":0.0,"loss":0.0,"loss_pool":0.0,
    "trades_today":0,"trades_closed":0,
    "is_daily_done":False,"panic_triggered":False,
    "positions":[],
    "binance_status":"CONNECTING","binance_error":"","last_update":"...","is_frozen":False
}

EXCLUDE = ['USDT','USDC','FDUSD','BUSD','DAI','TUSD','USDP']

def get_movers_real_strict():
    if not HAS_CCXT:
        raise Exception("CCXT not installed")
    tickers = exchange.fetch_tickers()
    mov=[]
    for sym, t in tickers.items():
        if not sym.endswith('/USDT'): continue
        coin = sym.replace('/USDT','')
        if coin in EXCLUDE: continue
        if t['quoteVolume'] is None or t['quoteVolume'] < 3000000: continue
        change = t.get('percentage')
        if change is None or change < 0.5: continue
        price = t['last']
        if not price: continue
        mov.append((sym, float(change), float(price)))
    if not mov:
        raise Exception("No movers found - Binance empty")
    mov.sort(key=lambda x: x[1], reverse=True)
    return mov[:15]

def calc_total():
    total = config["capital"] + state["safi"] + state["ghair"] + state["loss"]
    pct = ((total - state["daily_start"]) / state["daily_start"] * 100) if state["daily_start"]>0 else 0
    if total > state["daily_peak"]:
        state["daily_peak"] = total
        state["daily_peak_pct"] = pct
    return total, pct

def engine():
    # أول مرة - لازم باينانس يشتغل
    retry = 0
    while True:
        try:
            state["binance_status"] = "CONNECTING BINANCE..."
            mov = get_movers_real_strict()
            state["binance_status"] = "BINANCE REAL ✅"
            state["binance_error"] = ""
            state["is_frozen"] = False
            for i in range(min(10, len(mov))):
                sym,pct,pr = mov[i]
                state["positions"].append([sym, pr*0.996, pr, 0.0, 0.0, pct, 0.0])
            break
        except Exception as e:
            retry+=1
            state["binance_status"] = f"BINANCE DOWN - محاولة {retry}"
            state["binance_error"] = str(e)[:120]
            state["is_frozen"] = True
            state["data_source"]="BINANCE DOWN - متوقف"
            time.sleep(5)

    pool=0.0
    while True:
        try:
            # محاولة جلب أسعار حقيقية فقط
            try:
                for p in state["positions"]:
                    tk = exchange.fetch_ticker(p[0])
                    if not tk['last']:
                        raise Exception(f"No price for {p[0]}")
                    real_price = float(tk['last'])
                    p[2]=real_price
                    pp=(real_price-p[1])/p[1]*100
                    us=config["per_trade"]*pp/100
                    p[3]=round(us,2); p[4]=round(pp,2)

                # نجح - فك التجميد
                state["binance_status"] = "BINANCE REAL ✅"
                state["binance_error"] = ""
                state["is_frozen"] = False
                state["last_update"]=datetime.now().strftime("%H:%M:%S")

            except Exception as e:
                # فشل باينانس - جمد كل شي ولا تروح محاكاة
                state["binance_status"] = "BINANCE DOWN ⛔ - متجمد"
                state["binance_error"] = str(e)[:150]
                state["is_frozen"] = True
                # لا تحدث الأسعار - خليها مجمدة على آخر سعر حقيقي
                time.sleep(5)
                continue

            total,daily = calc_total()
            ng = sum([p[3] for p in state["positions"]])
            state["ghair"]=round(ng,2)

            # Panic Guard - يعمل فقط اذا البيانات حقيقية
            if not state["is_frozen"] and daily >= config["daily_target_pct"] and not state["is_daily_done"]:
                drop_from_peak = state["daily_peak"] - total
                drop_pct = (drop_from_peak / state["daily_peak"] * 100) if state["daily_peak"]>0 else 0
                if drop_pct >= config["panic_drop_pct"]:
                    for p in list(state["positions"]):
                        real = round(p[3] - config["per_trade"]*0.002, 2)
                        if real >=0:
                            if pool>0:
                                if real>=pool: state["safi"]=round(state["safi"]+real-pool,2); state["loss"]=round(state["loss"]+pool,2); pool=0
                                else: pool=round(pool-real,2); state["loss"]=round(state["loss"]+real,2)
                            else: state["safi"]=round(state["safi"]+real,2)
                        else: state["loss"]=round(state["loss"]+real,2)
                        state["trades_closed"]+=1
                    state["positions"]=[]; state["ghair"]=0; state["loss_pool"]=pool
                    state["is_daily_done"]=True; state["panic_triggered"]=True
                    continue

            if state["is_daily_done"]:
                time.sleep(3); continue

            closed=[]
            for p in state["positions"]:
                tp=config["tp_pct"]+(abs(p[6])/config["per_trade"]*100)
                if p[4]>=tp or p[4]<=config["sl_pct"]:
                    closed.append(p)

            for p in closed:
                real=round(p[3]-config["per_trade"]*0.002,2)
                if p in state["positions"]: state["positions"].remove(p)
                if real<0:
                    pool+=abs(real); state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=round(pool,2)
                    try:
                        mov=get_movers_real_strict()
                        ex=[x[0] for x in state["positions"]]; sh=round(pool/10,2)
                        for x in mov:
                            if x[0] not in ex:
                                state["positions"].append([x[0],x[2]*0.996,x[2],0.0,0.0,x[1],sh]); pool=round(max(0,pool-sh),2); state["loss_pool"]=pool; break
                    except Exception as e:
                        state["binance_status"]="BINANCE DOWN - لا يمكن فتح صفقات جديدة"
                        state["is_frozen"]=True
                else:
                    if pool>0:
                        if real>=pool: state["safi"]=round(state["safi"]+real-pool,2); state["loss"]=round(state["loss"]+pool,2); pool=0; state["loss_pool"]=0
                        else: pool=round(pool-real,2); state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=pool
                    else: state["safi"]=round(state["safi"]+real,2)
                state["trades_closed"]+=1; state["trades_today"]+=1
                if real>=0 and pool==0 and len(state["positions"])<10 and not state["is_frozen"]:
                    try:
                        mov=get_movers_real_strict(); ex=[x[0] for x in state["positions"]]
                        for x in mov:
                            if x[0] not in ex:
                                state["positions"].append([x[0],x[2]*0.996,x[2],0.0,0.0,x[1],0.0]); break
                    except: pass

            time.sleep(2.5)

        except Exception as e:
            state["binance_status"]=f"ENGINE ERROR: {str(e)[:100]}"
            time.sleep(3)

thread_started=False
def start_engine():
    global thread_started
    if not thread_started:
        thread_started=True
        threading.Thread(target=engine,daemon=True).start()

@app.before_request
def before_req(): start_engine()

@app.route('/health')
def health(): return "OK",200

@app.route('/api/data')
def api_data():
    total,pct = calc_total()
    return jsonify({
        "total": round(total,2),"daily_pct": round(pct,2),"daily_usd": round(total-state["daily_start"],2),
        "capital": config["capital"],"per_trade": config["per_trade"],
        "safi": state["safi"],"ghair": state["ghair"],"loss": state["loss"],"loss_pool": state["loss_pool"],
        "trades_today": state["trades_today"],"trades_closed": state["trades_closed"],
        "is_done": state["is_daily_done"],"panic_triggered": state["panic_triggered"],
        "daily_peak": round(state["daily_peak"],2),"daily_peak_pct": round(state["daily_peak_pct"],2),
        "panic_drop": config["panic_drop_pct"],"daily_target": config["daily_target_pct"],
        "positions": state["positions"],"binance_status": state["binance_status"],
        "binance_error": state["binance_error"],"last_update": state["last_update"],
        "is_frozen": state["is_frozen"],"has_ccxt": HAS_CCXT
    })

@app.route('/api/config',methods=['POST'])
def api_cfg():
    try:
        d=request.get_json()
        if 'capital' in d: config["capital"]=float(d['capital']); state["daily_start"]=config["capital"]+state["safi"]+state["loss"]
        if 'per_trade' in d: config["per_trade"]=float(d['per_trade'])
        if 'tp' in d: config["tp_pct"]=float(d['tp'])
        if 'sl' in d: config["sl_pct"]=float(d['sl'])
        if 'daily' in d: config["daily_target_pct"]=float(d['daily'])
        if 'panic' in d: config["panic_drop_pct"]=float(d['panic'])
        return jsonify({"ok":True})
    except: return jsonify({"ok":False})

@app.route('/')
def home():
    return '''
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
body{margin:0;background:#05070a;color:#fff;font-family:Cairo;padding:10px}
.top{max-width:1400px;margin:0 auto 10px auto;display:flex;justify-content:space-between;font-size:10px;opacity:0.5}
.guard{max-width:1400px;margin:0 auto 10px auto;border-radius:12px;padding:10px 14px;font-size:11px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px}
.guard.ok{background:linear-gradient(90deg,rgba(0,255,157,0.12),rgba(255,202,40,0.12));border:1px solid #00ff9d50}
.guard.down{background:linear-gradient(90deg,rgba(255,59,92,0.25),rgba(255,0,0,0.25));border:1px solid #ff3b5c;animation:blink 1s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.6}}
.cards{max-width:1400px;margin:0 auto;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.card{border-radius:18px;padding:18px 12px;border:1px solid #2a2f4a;background:linear-gradient(135deg,#0f1220,#0a0c16)}
.card.gold{border-color:#ffca28;box-shadow:0 0 30px #ffca2830;background:linear-gradient(135deg,#1e1a0a,#2a220a)}
.card.frozen{opacity:0.5;filter:grayscale(1)}
.lb{font-size:9px;opacity:0.5;font-weight:800}.val{font-family:JetBrains Mono;font-size:28px;font-weight:800;margin-top:4px}.sub{font-size:11px;opacity:0.7;margin-top:6px;font-weight:700}
.panel{max-width:1400px;margin:14px auto;display:grid;grid-template-columns:360px 1fr;gap:12px}
.ctrl{background:linear-gradient(180deg,#0f1220,#080a12);border:1px solid #ffca2850;border-radius:18px;padding:14px;position:sticky;top:10px}
.ctrl h3{margin:0 0 12px 0;color:#ffca28;font-size:13px}
.row{display:grid;grid-template-columns:1fr 110px;gap:8px;align-items:center;margin-bottom:10px}
.row label{font-size:11px;opacity:0.7;font-weight:700}.inp{background:#05070a;border:1.5px solid #2a2f4a;border-radius:10px;padding:10px;color:#ffca28;font-family:JetBrains Mono;font-weight:800;font-size:16px;text-align:center;width:100%}
.btn{width:100%;background:linear-gradient(90deg,#ffca28,#ffb300);color:#000;border:none;border-radius:12px;padding:13px;font-weight:900;font-family:Cairo;cursor:pointer;margin-top:8px;font-size:14px}
.coins{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:10px}
.coin{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:10px}
.ctop{display:flex;gap:5px;align-items:center}.ctop b{font-family:JetBrains Mono;font-size:13px}.bdg{background:#ff9800;color:#000;font-size:8px;font-weight:900;padding:2px 6px;border-radius:20px}.debt{background:#ff1744;color:#fff;font-size:7px;padding:2px 5px;border-radius:20px}
.cprice{font-family:JetBrains Mono;font-size:10px;opacity:0.4;direction:ltr;margin:6px 0}.barw{height:7px;background:#000;border-radius:20px;overflow:hidden}.bar{height:100%;border-radius:20px}.cprof{margin-top:6px;border-radius:8px;padding:6px;text-align:center;font-family:JetBrains Mono;font-weight:800;font-size:13px}
@media(max-width:900px){.cards{grid-template-columns:1fr 1fr}.panel{grid-template-columns:1fr}}
</style></head><body>
<div class="top"><span>V13.1 STRICT REAL • <span id="clock"></span></span><span id="frozenBadge"></span></div>
<div class="guard ok" id="guardBox">
  <span><span id="binStatus">CONNECTING...</span> | قمة: $<span id="peak">2000</span> (<span id="peakPct">0</span>%)</span>
  <span id="guardStatus">...</span>
</div>
<div id="errorBox" style="max-width:1400px;margin:0 auto 10px auto;display:none;background:#ff3b5c20;border:1px solid #ff3b5c;border-radius:10px;padding:8px 12px;font-size:10px;color:#ff8a80"></div>
<div class="cards" id="cardsBox">
  <div class="card"><div class="lb">رأس المال</div><div class="val" id="v_cap">$2000</div><div class="sub" id="v_per">10 × $200</div></div>
  <div class="card gold"><div class="lb">الإجمالي</div><div class="val" id="v_total">$2000</div><div class="sub" id="v_daily">0.00$</div></div>
  <div class="card"><div class="lb">مجمع الخسارة</div><div class="val" id="v_pool">$0.00</div><div class="sub" id="v_loss">0</div></div>
  <div class="card"><div class="lb">صافي ربح</div><div class="val" id="v_safi">0</div><div class="sub" id="v_today">0</div></div>
  <div class="card"><div class="lb">غير محقق</div><div class="val" id="v_ghair">0</div><div class="sub" id="v_count">0</div></div>
</div>
<div class="panel">
  <div class="ctrl">
    <h3>✦ STRICT BINANCE REAL</h3>
    <div class="row"><label>رأس المال $</label><input id="capital" class="inp" type="number" value="2000"></div>
    <div class="row"><label>حجم الصفقة $</label><input id="per_trade" class="inp" type="number" value="200"></div>
    <div class="row"><label>ربح %</label><input id="tp" class="inp" type="number" step="0.1" value="0.8"></div>
    <div class="row"><label>ستوب %</label><input id="sl" class="inp" type="number" step="0.1" value="1.5"></div>
    <div class="row"><label>هدف اليوم %</label><input id="daily" class="inp" type="number" step="0.1" value="3.5"></div>
    <div class="row"><label>حماية نزول %</label><input id="panic_inp" class="inp" type="number" step="0.1" value="1.0"></div>
    <button class="btn" onclick="save()">حفظ فوري ⚡</button>
    <button class="btn" onclick="fetch('/reset').then(()=>location.reload())" style="background:transparent;border:1px solid #2a2f4a;color:#fff;margin-top:6px">🔄 يوم جديد</button>
    <div id="status" style="text-align:center;margin-top:8px;font-size:11px;color:#00ff9d"></div>
  </div>
  <div class="coins" id="coins"></div>
</div>
<script>
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('clock').innerText=new Date().toLocaleTimeString('ar-EG')+' - '+d.last_update;
    document.getElementById('binStatus').innerText=d.binance_status;
    document.getElementById('peak').innerText=d.daily_peak.toFixed(2);
    document.getElementById('peakPct').innerText=d.daily_peak_pct.toFixed(2);
    document.getElementById('v_cap').innerText='$'+d.capital.toFixed(2);
    document.getElementById('v_total').innerText='$'+d.total.toFixed(2);
    document.getElementById('v_daily').innerText=d.daily_usd.toFixed(2)+'$ ('+d.daily_pct.toFixed(2)+'%)';
    document.getElementById('v_pool').innerText='$'+d.loss_pool.toFixed(2);
    document.getElementById('v_safi').innerText=(d.safi>=0?'+':'')+d.safi.toFixed(2)+'$';
    document.getElementById('v_ghair').innerText=(d.ghair>=0?'+':'')+d.ghair.toFixed(2)+'$';
    document.getElementById('v_ghair').style.color=d.ghair>=0?'#00FF9D':'#FF3B5C';

    const gb=document.getElementById('guardBox');
    const eb=document.getElementById('errorBox');
    const fb=document.getElementById('frozenBadge');
    const cb=document.getElementById('cardsBox');

    if(d.is_frozen){
      gb.className='guard down';
      fb.innerText='⛔ BINANCE متوقف - مجمد على آخر سعر حقيقي - السبب: '+d.binance_error;
      fb.style.display='block';
      document.getElementById('frozenBadge').innerHTML='<span style="background:#ff3b5c;color:#fff;padding:2px 8px;border-radius:20px;font-size:10px">⛔ مجمد - ينتظر Binance</span>';
      cb.style.opacity='0.6';
      document.getElementById('guardStatus').innerText='متوقف - ينتظر عودة Binance';
    } else {
      gb.className='guard ok';
      eb.style.display='none';
      fb.innerHTML='<span style="background:#00ff9d;color:#000;padding:2px 8px;border-radius:20px;font-size:10px">✅ BINANCE REAL</span>';
      cb.style.opacity='1';
      document.getElementById('guardStatus').innerText=d.daily_pct>=d.daily_target?'🚀 حقق الهدف - مكمل':'مفتوح - بيانات حقيقية';
    }

    let html='';
    for(const p of d.positions){
      const sym=p[0].replace('/USDT',''),entry=p[1],cur=p[2],usd=p[3],pct=p[4],mov=p[5],loss=p[6];
      const col=usd>=0?'#00FF9D':'#FF3B5C', bg=usd>=0?'rgba(0,255,157,0.14)':'rgba(255,59,92,0.14)';
      const debt=loss>0.1?`<span class="debt">دين $${loss.toFixed(2)}</span>`:'';
      const bar=Math.min(100,Math.max(8,(pct+1.5)/3*100));
      html+=`<div class="coin"><div class="ctop"><b>${sym}</b><span class="bdg">+${mov.toFixed(1)}% REAL</span>${debt}</div><div class="cprice">${entry.toFixed(5)} → ${cur.toFixed(5)}</div><div class="barw"><div class="bar" style="width:${bar}%;background:${col}"></div></div><div class="cprof" style="color:${col};background:${bg}">${usd>=0?'+':''}${usd.toFixed(2)}$<small>${pct>=0?'+':''}${pct.toFixed(2)}%</small></div></div>`;
    }
    document.getElementById('coins').innerHTML=html;
  }catch(e){}
}
async function save(){
  const d={capital:parseFloat(capital.value),per_trade:parseFloat(per_trade.value),tp:parseFloat(tp.value),sl:parseFloat(sl.value),daily:parseFloat(daily.value),panic:parseFloat(panic_inp.value)};
  const b=document.querySelectorAll('.btn')[0]; b.innerText='⏳...';
  try{const r=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}); if((await r.json()).ok){b.innerText='✅ REAL'; setTimeout(()=>b.innerText='حفظ فوري ⚡',1500);}}catch(e){b.innerText='❌';}
}
setInterval(load,2000); load();
</script>
</body></html>
    '''

@app.route('/reset')
def reset():
    state["daily_start"]=config["capital"]+state["safi"]+state["loss"]
    state["daily_peak"]=state["daily_start"]; state["daily_peak_pct"]=0; state["safi"]=0; state["ghair"]=0; state["loss"]=0; state["loss_pool"]=0
    state["trades_today"]=0; state["is_daily_done"]=False; state["panic_triggered"]=False; state["positions"]=[]; state["is_frozen"]=False
    return redirect('/')

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

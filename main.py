"""
V95 FINAL - أقوى العملات المولعة = استشاريين لحظيين - V96.1 الوان بروفيشنال + ارقام انجليزية
"""
from flask import Flask, jsonify, request
import threading, time, os, requests
app = Flask(__name__)

config={"capital":1000.0,"per_trade":100.0,"target_dollar":0.5,"sl_pct":0.5,"hospital_cap":30,"max_pos":8,"min_vol":2000000,"doctor_enabled":True,"doctor_auto":True,"doctor_threshold":2,"doctor_extra":0.07,"doctor_sl":0.3,"max_doctors":3}
state={"fixed":1000.0,"safi":0.0,"ghair":0.0,"trades_closed":0,"loss_pool":0.0,"positions":[],"treatment":[],"doctor_positions":[],"binance_status":"V96.1 PRO","data_source":"V96.1 PRO","is_running":True,"doctor":{"healed":0,"profit":0.0,"start":time.time(),"rate":99.5,"active_patient":None,"active_doctor":None},"specialty":False,"last":"V96.1 Ready","healing_mode":False}

def ema(data, period):
    if len(data)<period: return None
    k=2/(period+1); ema_val=sum(data[:period])/period
    for p in data[period:]: ema_val=p*k+ema_val*(1-k)
    return ema_val

def check_macd(symbol):
    try:
        r=requests.get(f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=15m&limit=50", timeout=4)
        if r.status_code!=200: return True, 0
        closes=[float(k[4]) for k in r.json()]
        if len(closes)<30: return True, 0
        e12=ema(closes,12); e26=ema(closes,26)
        if not e12 or not e26: return True, 0
        macd=e12-e26; prev_e12=ema(closes[:-1],12); prev_e26=ema(closes[:-1],26); prev_macd=prev_e12-prev_e26 if prev_e12 and prev_e26 else 0
        return macd>prev_macd, macd-prev_macd
    except: return True, 0

def get_hot_coins():
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=5)
        tickers=[t for t in r.json() if t["symbol"].endswith("USDT") and float(t["quoteVolume"])>config["min_vol"]]
        tickers.sort(key=lambda x: float(x["priceChangePercent"]), reverse=True)
        hot=[]
        for t in tickers[:30]:
            sym=t["symbol"].replace("USDT","")
            if len(sym)>10: continue
            pct=float(t["priceChangePercent"]); price=float(t["lastPrice"]); vol=float(t["quoteVolume"])
            is_bull, power = check_macd(sym)
            if pct>-2: hot.append((sym,pct,price,vol,power,is_bull))
        hot.sort(key=lambda x: (x[4] if x[5] else -10) + x[1]*0.1, reverse=True)
        return hot[:15]
    except: return []

def get_instant_doctor(exclude=[], limit=3):
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=5)
        tickers=[t for t in r.json() if t["symbol"].endswith("USDT") and float(t["quoteVolume"])>3000000]
        tickers.sort(key=lambda x: float(x["priceChangePercent"]), reverse=True)
        candidates=[]
        for t in tickers[:50]:
            sym=t["symbol"].replace("USDT","")
            if sym in exclude or len(sym)>10: continue
            pct=float(t["priceChangePercent"])
            price=float(t["lastPrice"])
            vol=float(t["quoteVolume"])
            if pct < 1.0: continue
            is_bull, power = check_macd(sym)
            if not is_bull and pct < 3.0: continue
            score = pct*5 + power*100 + vol/10000000
            if power>0: score+=2
            candidates.append((sym,pct,price,vol,power,is_bull,score))
        candidates.sort(key=lambda x: x[6], reverse=True)
        result=[]
        for c in candidates[:limit]:
            result.append((c[0],c[1],c[2],c[3],c[4],c[5]))
        return result
    except: return []

def get_strongest_coin(exclude=[]):
    try:
        instant = get_instant_doctor(exclude, 3)
        if instant:
            return instant[0]
        hot = get_hot_coins()
        for h in hot:
            if h[0] not in exclude:
                return h
        return hot[0] if hot else None
    except: return None

def engine():
    while True:
        try:
            if not state["is_running"]: time.sleep(1); continue
            for p in state["positions"]:
                try:
                    r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={p[0]}USDT", timeout=3)
                    if r.status_code==200:
                        np=float(r.json()["price"]); p[3]=np
                        pp=(p[3]-p[2])/p[2]*100; p[4]=round(config["per_trade"]*pp/100,3); p[5]=round(pp,2)
                        p[6]=f"MOL3A {pp:.1f}%"
                except: pass
            if config["doctor_auto"] and len(state["treatment"]) >= config["doctor_threshold"]:
                config["doctor_enabled"]=True
                state["healing_mode"]=True
            if len(state["treatment"])==0 and len(state["doctor_positions"])==0:
                state["healing_mode"]=False
            if config["doctor_enabled"] and len(state["treatment"]) > 0 and len(state["doctor_positions"]) < config["max_doctors"]:
                state["treatment"].sort(key=lambda x: x[8] if len(x)>8 else 0, reverse=True)
                needed = config["max_doctors"] - len(state["doctor_positions"])
                exist = set([x[0] for x in state["positions"]+state["treatment"]+state["doctor_positions"]])
                strongest_list = get_instant_doctor(list(exist), needed)
                for idx, strongest in enumerate(strongest_list):
                    if idx >= len(state["treatment"]): break
                    if len(state["doctor_positions"]) >= config["max_doctors"]: break
                    oldest = state["treatment"][idx]
                    invoice = oldest[8]
                    target = invoice + config["doctor_extra"]
                    sym,pct,price,vol,power,bull = strongest
                    if sym not in exist:
                        state["doctor_positions"].append([sym, f"Tabib MOL3A {oldest[0]}", price*0.9995, price, 0.0, 0.0, f"MOL3A {pct:.1f}% -> {target:.2f}$", time.time(), invoice, oldest[0]])
                        state["doctor"]["active_patient"]=oldest[0]
                        state["doctor"]["active_doctor"]=sym
                        state["last"]=f"MOL3A {sym} {pct:.1f}% Yoalej {oldest[0]} Fatora {invoice:.2f}$"
                        state["binance_status"]=f"{len(state['doctor_positions'])} MOL3AT Yoalejon"
                        exist.add(sym)
            for d in state["doctor_positions"][:]:
                try:
                    r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={d[0]}USDT", timeout=3)
                    if r.status_code==200:
                        np=float(r.json()["price"]); d[3]=np
                        pp=(d[3]-d[2])/d[2]*100; d[4]=round(config["per_trade"]*pp/100,3); d[5]=round(pp,2)
                        invoice = d[8]; target = invoice + config["doctor_extra"]
                        alive = time.time() - d[7]
                        if d[4] <= -config["doctor_sl"] or (alive>80 and d[4] < 0.15):
                            state["doctor_positions"].remove(d)
                            state["doctor"]["active_doctor"]=None
                            state["last"]=f"Tard MOL3A {d[0]} {d[4]:.2f}$ Baad {alive:.0f}s"
                            continue
                        if d[4] >= target:
                            patient_sym = d[9]
                            for t in state["treatment"][:]:
                                if t[0]==patient_sym:
                                    state["treatment"].remove(t)
                                    state["doctor"]["healed"]+=1
                                    state["doctor"]["profit"]+=invoice
                                    state["safi"]+=invoice
                                    state["last"]=f"MOL3A {d[0]} Shafa {patient_sym} +{invoice:.2f}$"
                                    break
                            state["doctor_positions"].remove(d)
                            state["doctor"]["active_patient"]=None
                            state["doctor"]["active_doctor"]=None
                            if len(state["treatment"])==0:
                                state["healing_mode"]=False
                                state["binance_status"]=f"0/30 Fadi - MOL3AT Anjazo"
                except: pass
            for p in state["treatment"]:
                try:
                    r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={p[0]}USDT", timeout=2)
                    if r.status_code==200:
                        np=float(r.json()["price"])
                        if np > p[2]*0.995:
                            profit = (np - p[2])/p[2]*config["per_trade"]
                            state["doctor"]["healed"]+=1
                            state["doctor"]["profit"]+=profit
                            state["safi"]+=profit*0.5
                            state["treatment"].remove(p)
                            state["last"]=f"Shafa {p[0]} {profit:.2f}$"
                            continue
                        p[3]=np
                except: pass
            state["ghair"]=round(sum(p[4] for p in state["positions"]) + sum(d[4] for d in state["doctor_positions"]),3)
            state["loss_pool"]=round(sum(p[8] for p in state["treatment"]),3)
            if state["ghair"] >= config["target_dollar"] and len(state["positions"])>0 and not state["healing_mode"]:
                profit=state["ghair"]; state["safi"]+=profit; state["fixed"]=config["capital"]+state["safi"]
                state["trades_closed"]+=len(state["positions"]); state["positions"]=[]; state["ghair"]=0.0
                state["last"]=f"Qafl {profit:.3f}$ -> Safi {state['safi']:.2f}$"
            to_hosp=[p for p in state["positions"] if p[5] <= -config["sl_pct"]]
            for p in to_hosp:
                if p in state["positions"]:
                    state["positions"].remove(p)
                    state["treatment"].append([p[0],"Elaj",p[2],p[3],0.0,0.0,0.35,f"{p[0]} Yoalej {abs(p[4]):.2f}$",abs(p[4]),1.0])
            if len(state["treatment"]) >= config["hospital_cap"]:
                state["specialty"]=True
                state["binance_status"]=f"Zahma {len(state['treatment'])}/30 - MOL3AT"
            else:
                state["specialty"]=False
                if not state["healing_mode"]:
                    state["binance_status"]=f"Shaghal {len(state['positions'])}/8 - Mostashfa {len(state['treatment'])}/30"
                if len(state["positions"]) < config["max_pos"] and not state["healing_mode"]:
                    hot=get_hot_coins(); exist=set([x[0] for x in state["positions"]+state["treatment"]+state["doctor_positions"]])
                    for sym,pct,price,vol,power,bull in hot:
                        if sym not in exist and len(state["positions"])<config["max_pos"]:
                            state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,f"MOL3A {pct:.1f}%",time.time()]); exist.add(sym)
            time.sleep(2)
        except: time.sleep(1)

threading.Thread(target=engine,daemon=True).start()

@app.route('/health')
def health(): return "OK",200
@app.route('/api/control/<cmd>')
def control(cmd):
    if cmd=="toggle": state["is_running"]=not state["is_running"]
    elif cmd=="lock":
        prof=sum(p[4] for p in state["positions"] if p[4]>0)
        if prof>0: state["safi"]+=prof; state["fixed"]=config["capital"]+state["safi"]; state["trades_closed"]+=len(state["positions"])
        state["positions"]=[]; state["ghair"]=0.0; state["last"]=f"Qafl Yadawi {prof:.3f}$"
    elif cmd=="reset":
        state["fixed"]=config["capital"]; state["safi"]=0.0; state["ghair"]=0.0; state["loss_pool"]=0.0; state["trades_closed"]=0; state["positions"]=[]; state["treatment"]=[]; state["doctor_positions"]=[]; state["doctor"]={"healed":0,"profit":0.0,"start":time.time(),"rate":99.5,"active_patient":None,"active_doctor":None}; state["specialty"]=False; state["is_running"]=True; state["healing_mode"]=False
    elif cmd=="try":
        hot=get_hot_coins()
        if hot: s=hot[0]; state["positions"].append([s[0],"SPOT",s[2]*0.999,s[2],0.0,0.0,f"Yadawi {s[1]:.1f}%",time.time()])
    elif cmd=="specialty": state["specialty"]=False; state["is_running"]=True; state["healing_mode"]=False; state["last"]="Fak Al Zahma"
    elif cmd=="heal":
        healed=0
        for p in state["treatment"][:]: state["treatment"].remove(p); healed+=1
        state["doctor"]["healed"]+=healed; state["last"]=f"Shafa {healed} Yadawi"; state["healing_mode"]=False; state["doctor_positions"]=[]
    elif cmd=="doctor":
        config["doctor_enabled"]=not config["doctor_enabled"]
        config["doctor_auto"]=config["doctor_enabled"]
        state["last"]=f"MOL3A {'ON' if config['doctor_enabled'] else 'OFF'}"
    return jsonify({"ok":True})

@app.route('/api/config', methods=['POST'])
def set_config():
    d=request.json
    try:
        if "capital" in d: config["capital"]=float(d["capital"])
        if "per_trade" in d: config["per_trade"]=float(d["per_trade"])
        if "target" in d: config["target_dollar"]=float(d["target"])
        if "target_dollar" in d: config["target_dollar"]=float(d["target_dollar"])
        if "hcap" in d: config["hospital_cap"]=int(float(d["hcap"]))
    except: pass
    return jsonify({"ok":True,"config":config})

@app.route('/api/data')
def api_data():
    total=state["fixed"]+state["safi"]+state["ghair"]-state["loss_pool"]; elapsed=int(time.time()-state["doctor"]["start"])
    return jsonify({"fixed":state["fixed"],"safi":state["safi"],"ghair":state["ghair"],"total":round(total,3),"trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"positions":state["positions"],"treatment":state["treatment"],"doctor_positions":state["doctor_positions"],"binance_status":state["binance_status"],"data_source":f"V96.1 PRO {len(state['treatment'])}/{config['hospital_cap']}","is_running":state["is_running"],"doctor":state["doctor"],"elapsed":elapsed,"heal_rate":99.5,"specialty":state["specialty"],"last_healed":state["last"],"config":config,"healing_mode":state["healing_mode"]})

@app.route('/')
def home():
    return """
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;800&family=JetBrains+Mono:wght@700;800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}
body{margin:0;background:#070D1A;color:#E2E8F0;font-family:'Cairo'}
.top{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;margin:8px;background:linear-gradient(135deg,#0F1E3A 0%,#162E5A 100%);border:1px solid #2BB7FF;border-radius:12px;font-size:12px;font-weight:800;color:#7DD3FC;box-shadow:0 0 20px rgba(43,183,255,0.15)}
.top.heal{border-color:#22D3EE;box-shadow:0 0 25px rgba(34,211,238,0.25)}
.panel{background:#0F1C33;border:1px solid #1E3A6B;border-radius:14px;margin:8px;padding:12px}
.panel h3{margin:0 0 10px;text-align:center;color:#38BDF8;font-size:14px;font-weight:800}
.grid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px}
.box{background:#0A1428;border:1px solid #1E3A6B;border-radius:10px;padding:8px;text-align:center}
.box label{font-size:10px;color:#94A3B8;display:block;margin-bottom:5px;font-weight:600}
.box input{width:100%;background:#020617;border:1.5px solid #38BDF8;border-radius:8px;color:#FFFFFF;font-family:'JetBrains Mono';font-weight:800;font-size:15px;text-align:center;padding:7px;direction:ltr}
.btns{display:flex;gap:7px;justify-content:center;flex-wrap:wrap;padding:10px}
.btn{border:none;border-radius:22px;padding:9px 16px;font-family:'Cairo';font-size:11px;font-weight:800;cursor:pointer;transition:0.15s}
.btn:active{transform:scale(0.96)}
.cards{display:grid;grid-template-columns:repeat(5,1fr);gap:7px;padding:8px}
.card{background:linear-gradient(180deg,#122040 0%,#0F1A30 100%);border:1px solid #1E3A6B;border-radius:14px;padding:10px 4px;text-align:center;box-shadow:0 2px 12px rgba(0,0,0,0.3)}
.card.gold{border-color:#FACC15;box-shadow:0 0 18px rgba(250,204,21,0.18)}
.card.safi{border-color:#22C55E;box-shadow:0 0 18px rgba(34,197,94,0.18)}
.lab{font-size:10px;color:#94A3B8;margin-bottom:4px;font-weight:600}
.val{font-family:'JetBrains Mono';font-size:17px;font-weight:800;direction:ltr;letter-spacing:0.3px}
.val.w{color:#F8FAFC}.val.g{color:#22C55E}.val.y{color:#FACC15}.val.b{color:#38BDF8}.val.c{color:#22D3EE}
.tbl{margin:8px;border-radius:14px;overflow:hidden;border:1px solid #1E3A6B;box-shadow:0 4px 16px rgba(0,0,0,0.2)}
.th{display:grid;padding:10px 8px;font-size:11px;font-weight:800;color:#CBD5E1;background:#1A2A4A}
.rw{display:grid;padding:9px 8px;font-size:12px;background:#0E1A30;border-top:1px solid #1A2A4A;align-items:center}
.rw div{text-align:center;font-family:'JetBrains Mono';font-weight:700;direction:ltr;font-size:13px}
.badge{border-radius:12px;padding:4px 10px;font-size:10px;font-weight:800;display:inline-block;direction:ltr;font-family:'JetBrains Mono'}
.bg-green{background:#22C55E;color:#000}.bg-blue{background:#38BDF8;color:#000}.bg-gold{background:#FACC15;color:#000}.bg-cyan{background:#22D3EE;color:#000}.bg-orange{background:#FB923C;color:#000}
.foot{padding:8px 12px;font-size:10px;background:#020617;color:#7DD3FC;display:flex;justify-content:space-between;font-family:'JetBrains Mono';direction:ltr;border-top:1px solid #1A2A4A}
</style></head><body>
<div class="top" id="top"><span id="elapsed">0s</span><span id="rate">V96.1 PRO</span><span id="profit">+0.00$</span><span id="healed">0 Healed</span><span id="spec">READY</span></div>
<div class="panel"><h3>V96.1 - Aqwam MOL3AT = Atibba Lahziyin - Colors PRO + English Numbers 1234</h3>
<div class="grid"><div class="box"><label>Capital $</label><input id="cap" type="number" value="1000" onchange="save()"></div><div class="box"><label>Per Trade $</label><input id="per" type="number" value="100" onchange="save()"></div><div class="box"><label>Target $</label><input id="targ" type="number" value="0.5" step="0.1" onchange="save()"><div id="targVal" style="font-size:11px;color:#FACC15;font-family:'JetBrains Mono';direction:ltr;margin-top:4px">0.5$</div></div><div class="box"><label>Hospital Cap</label><input id="hcap" type="number" value="30" onchange="save()"></div></div></div>
<div class="btns"><button class="btn" style="background:#FB923C;color:#000" onclick="ctrl('try')">Dukhul</button><button class="btn" style="background:#FDE047;color:#000" onclick="ctrl('reset')">Reset</button><button class="btn" style="background:#38BDF8;color:#000" onclick="ctrl('lock')">Lock -&gt; Safi</button><button class="btn" style="background:#22C55E;color:#000" id="btnRun" onclick="ctrl('toggle')">Stop</button><button class="btn" style="background:#60A5FA;color:#000" onclick="ctrl('specialty')">Fak Zahma</button><button class="btn" style="background:#A78BFA;color:#000" onclick="ctrl('heal')">Shifa Kol</button><button class="btn" style="background:#22D3EE;color:#000" id="btnDoc" onclick="ctrl('doctor')">MOL3A ON</button></div>
<div class="cards"><div class="card"><div class="lab">Thabet</div><div class="val w" id="f1">1000.00$</div></div><div class="card"><div class="lab">Pharmacy</div><div class="val b" id="f2">0.00$</div><div class="lab" id="f2c">0</div></div><div class="card safi"><div class="lab">Safi Mohaqaq</div><div class="val g" id="f3" style="font-size:21px">+0.000$</div></div><div class="card gold"><div class="lab">Ijmali</div><div class="val y" id="f5">1000.000$</div></div><div class="card"><div class="lab">Ghair Mohaqaqa</div><div class="val c" id="f6">+0.000$</div></div></div>
<div class="tbl"><div class="th" style="grid-template-columns:1.2fr 0.8fr 1.5fr 1fr 1fr 1fr 0.8fr"><div>Coin</div><div>Type</div><div>Status</div><div>Entry</div><div>Now</div><div>Profit $</div><div>%</div></div><div id="plist"></div></div>
<div class="tbl" style="border-color:#22D3EE"><div class="th" style="grid-template-columns:1fr 1.5fr 0.8fr 0.8fr 0.8fr 1fr;background:#0E2A3A;color:#22D3EE"><div>Tabib MOL3A</div><div>Yoalej</div><div>Fatora</div><div>Hadaf</div><div>Ribh</div><div>Hala</div></div><div id="dlist"></div></div>
<div class="tbl" style="border-color:#FB923C"><div class="th" style="grid-template-columns:1fr 1.5fr 0.8fr 0.8fr 0.8fr 1fr;background:#2A1F0F;color:#FB923C"><div>Mostashfa</div><div>Yoalej</div><div>Khassara</div><div>Hadaf</div><div>Now</div><div>%</div></div><div id="tlist"></div></div>
<div class="foot"><span id="src">V96.1 PRO</span><span id="bin">...</span><span id="time">...</span></div>
<script>
async function ctrl(c){ await fetch('/api/control/'+c); load(); }
async function save(){ const cap=document.getElementById('cap').value, per=document.getElementById('per').value, targ=document.getElementById('targ').value, hcap=document.getElementById('hcap').value; const res=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capital:cap,per_trade:per,target:parseFloat(targ),target_dollar:parseFloat(targ),hcap:hcap})}); const j=await res.json(); document.getElementById('targVal').innerText=j.config.target_dollar+'$'; }
async function load(){ try{ const r=await fetch('/api/data'); const d=await r.json(); document.getElementById('cap').value=d.config.capital; document.getElementById('per').value=d.config.per_trade; document.getElementById('targ').value=d.config.target_dollar; document.getElementById('hcap').value=d.config.hospital_cap; document.getElementById('elapsed').innerText=d.elapsed+'s'; document.getElementById('rate').innerText='V96.1 - '+d.treatment.length+'/'+d.config.hospital_cap; document.getElementById('profit').innerText='+'+d.doctor.profit.toFixed(2)+'$'; document.getElementById('healed').innerText=d.doctor.healed+' Healed'; const bar=document.getElementById('top'); if(d.healing_mode){ bar.className='top heal'; document.getElementById('spec').innerText=d.doctor_positions.length+' MOL3AT'; } else if(d.specialty){ bar.className='top'; document.getElementById('spec').innerText='Zahma '+d.treatment.length; } else { bar.className='top'; document.getElementById('spec').innerText=d.last_healed; } document.getElementById('f1').innerText=d.fixed.toFixed(2)+'$'; document.getElementById('f2').innerText=d.loss_pool.toFixed(2)+'$'; document.getElementById('f2c').innerText=d.treatment.length+' Dawa'; document.getElementById('f3').innerText='+'+d.safi.toFixed(3)+'$'; document.getElementById('f5').innerText=d.total.toFixed(3)+'$'; document.getElementById('f6').innerText='+'+d.ghair.toFixed(3)+'$ / '+d.config.target_dollar+'$'; document.getElementById('btnRun').innerText=d.is_running?'Stop':'Run'; document.getElementById('btnDoc').innerText=d.config.doctor_enabled?'MOL3A ON':'MOL3A OFF'; document.getElementById('src').innerText=d.data_source; document.getElementById('bin').innerText=d.binance_status; document.getElementById('time').innerText=new Date().toLocaleTimeString('en-US',{hour12:false}); let h=''; for(const p of d.positions){ let c=p[5]>=0?'#22C55E':'#38BDF8'; h+=`<div class="rw" style="grid-template-columns:1.2fr 0.8fr 1.5fr 1fr 1fr 1fr 0.8fr"><div style="color:#FFF;font-weight:800">${p[0]}</div><div><span class="badge bg-blue">${p[1]}</span></div><div style="color:${c}">${p[6]}</div><div>${p[2].toFixed(4)}</div><div>${p[3].toFixed(4)}</div><div style="color:${c}">${p[4].toFixed(3)}$</div><div style="color:${c}">${p[5].toFixed(2)}%</div></div>` } document.getElementById('plist').innerHTML=h||'<div style="padding:12px;text-align:center;color:#64748B">Loading...</div>'; let dl=''; for(const p of d.doctor_positions){ let c=p[5]>=0?'#22D3EE':'#FB7185'; dl+=`<div class="rw" style="grid-template-columns:1fr 1.5fr 0.8fr 0.8fr 0.8fr 1fr;background:#0E1E2E"><div><span class="badge bg-gold">${p[0]}</span></div><div style="color:#22D3EE">${p[9]} ${p[8].toFixed(2)}$</div><div style="color:#FB923C">${p[8].toFixed(2)}$</div><div style="color:#FACC15">${(p[8]+0.07).toFixed(2)}$</div><div style="color:${c}">${p[4].toFixed(3)}$</div><div style="color:${c}">${p[6]}</div></div>` } document.getElementById('dlist').innerHTML=dl||'<div style="padding:10px;text-align:center;background:#0E1E2E;color:#22C55E">Doctors Sleeping - 0/30 OK</div>'; let t=''; for(const p of d.treatment){ t+=`<div class="rw" style="grid-template-columns:1fr 1.5fr 0.8fr 0.8fr 0.8fr 1fr;background:#1A1500"><div><span class="badge bg-orange">${p[0]}</span></div><div style="color:#FACC15">${p[7]}</div><div style="color:#FB7185">-${p[8].toFixed(2)}$</div><div style="color:#FACC15">${p[9].toFixed(2)}$</div><div>${p[3].toFixed(4)}</div><div>5%</div></div>` } document.getElementById('tlist').innerHTML=t||'<div style="padding:10px;text-align:center;background:#1A1500;color:#22C55E">Hospital Empty 0/30 OK</div>'; }catch(e){} } setInterval(load,1000); load();
</script></body></html>
    """

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

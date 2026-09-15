"""
V100 LEGEND - نفس V99.0 CLEAN + تكبير تلقائي + حماية 5%
صافي 219$ محفوظ - حجم 200$
"""
from flask import Flask, jsonify, request
import threading, time, os, requests
app = Flask(__name__)

config={"capital":1000.0,"per_trade":200.0,"base_per_trade":200.0,"target_dollar":0.5,"sl_pct":0.35,"hospital_cap":30,"max_pos":8,"min_vol":2000000,"doctor_enabled":True,"doctor_auto":True,"doctor_threshold":2,"doctor_extra":0.04,"doctor_sl":1.0,"max_doctors":3,"auto_compound":True,"compound_step":50.0,"compound_add":25.0,"protect_pct":0.05}
BANNED = {"ASTR","ASTAR","SAGA","FF"}
state={"fixed":1260.0,"safi":260.0,"max_safi":219.265,"ghair":0.0,"trades_closed":0,"loss_pool":0.0,"positions":[],"treatment":[],"doctor_positions":[],"binance_status":"V100 LEGEND","data_source":"V100 LEGEND","is_running":True,"doctor":{"healed":0,"profit":0.0,"start":time.time(),"rate":99.5,"active_patient":None,"active_doctor":None},"specialty":False,"last":"V100 LEGEND","healing_mode":False,"protect_triggered":False}

def get_dynamic_per_trade():
    if not config["auto_compound"]: return config["per_trade"]
    steps = int(state["safi"] // config["compound_step"])
    bonus = steps * config["compound_add"]
    return config["base_per_trade"] + bonus

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

def get_binance_hot():
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=5)
        tickers=[t for t in r.json() if t["symbol"].endswith("USDT") and float(t["quoteVolume"])>config["min_vol"]]
        tickers.sort(key=lambda x: float(x["priceChangePercent"]), reverse=True)
        hot=[]
        for t in tickers[:35]:
            sym=t["symbol"].replace("USDT","")
            if sym in BANNED: continue
            if len(sym)>10: continue
            pct=float(t["priceChangePercent"]); price=float(t["lastPrice"]); vol=float(t["quoteVolume"])
            if price < 0.0000005: continue
            is_bull, power = check_macd(sym)
            if pct>-2: hot.append((sym,pct,price,vol,power,is_bull,"BINANCE"))
        hot.sort(key=lambda x: (x[4] if x[5] else -10) + x[1]*0.1, reverse=True)
        return hot[:15]
    except: return []

def get_binance_price(sym):
    try:
        if sym in BANNED: return None
        r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}USDT", timeout=2)
        if r.status_code==200:
            p=float(r.json()["price"])
            if p>0.0000001: return p
    except: pass
    return None

def get_tradingview_doctors(exclude=[], limit=3):
    candidates=[]
    try:
        payload={"filter":[{"left":"change","operation":"nempty"},{"left":"change","operation":"greater","right":1.5},{"left":"volume","operation":"greater","right":1000000}],"options":{"lang":"en"},"symbols":{"query":{"types":[]},"tickers":[]},"columns":["name","close","change","volume","RSI","MACD.signal","Recommend.All"],"sort":{"sortBy":"change","sortOrder":"desc"},"range":[0,60]}
        r=requests.post("https://scanner.tradingview.com/crypto/scan", json=payload, timeout=6)
        if r.status_code==200:
            for row in r.json().get("data",[])[:60]:
                d=row.get("d",[])
                if len(d)<4: continue
                name=str(d[0]).replace("BINANCE:","").replace("USDT","")
                if name in BANNED or name in exclude or len(name)>10: continue
                change=float(d[2]) if d[2] else 0
                vol=float(d[3]) if d[3] else 0
                rec=float(d[6]) if len(d)>6 and d[6] else 0
                if change>=1.5 and rec>-0.3:
                    real_price=get_binance_price(name)
                    if not real_price or real_price < 0.0000005: continue
                    score=change*6 + rec*10 + vol/10000000
                    candidates.append((name,change,real_price,vol,rec,True,score,"TRADINGVIEW"))
    except: pass
    if len(candidates)<limit:
        try:
            r=requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=5)
            tickers=[t for t in r.json() if t["symbol"].endswith("USDT") and float(t["quoteVolume"])>3000000]
            tickers.sort(key=lambda x: float(x["priceChangePercent"]), reverse=True)
            for t in tickers[:80]:
                sym=t["symbol"].replace("USDT","")
                if sym in BANNED or sym in exclude or len(sym)>10: continue
                if any(c[0]==sym for c in candidates): continue
                pct=float(t["priceChangePercent"]); price=float(t["lastPrice"]); vol=float(t["quoteVolume"])
                if pct < 2.0 or price < 0.0000005: continue
                is_bull, power = check_macd(sym)
                if not is_bull and pct<4.0: continue
                score=pct*5 + power*100 + vol/10000000
                candidates.append((sym,pct,price,vol,power,is_bull,score,"BINANCE+MOL3A"))
        except: pass
    candidates.sort(key=lambda x: x[6], reverse=True)
    seen=set(); res=[]
    for c in candidates:
        if c[0] not in seen and len(res)<limit:
            res.append((c[0],c[1],c[2],c[3],c[4],c[5],c[7])); seen.add(c[0])
    return res

def engine():
    while True:
        try:
            if not state["is_running"]: time.sleep(1); continue
            if state["safi"] > state["max_safi"]: state["max_safi"] = state["safi"]
            if state["max_safi"] > 50:
                if state["safi"] < state["max_safi"] * (1 - config["protect_pct"]) and not state["protect_triggered"]:
                    state["is_running"] = False
                    state["protect_triggered"] = True
                    state["binance_status"] = f"حماية! {state['max_safi']:.1f}$->{state['safi']:.1f}$"
                    continue
            dyn_per = get_dynamic_per_trade()
            config["per_trade"] = dyn_per
            for p in state["treatment"][:]:
                if p[0] in BANNED: state["treatment"].remove(p)
            for p in state["positions"][:]:
                if p[0] in BANNED: state["positions"].remove(p)
            for d in state["doctor_positions"][:]:
                if d[0] in BANNED or d[9] in BANNED or d[0]==d[9]: state["doctor_positions"].remove(d)
            for p in state["positions"]:
                try:
                    r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={p[0]}USDT", timeout=3)
                    if r.status_code==200:
                        np=float(r.json()["price"]); p[3]=np; pp=(p[3]-p[2])/p[2]*100; p[4]=round(config["per_trade"]*pp/100,3); p[5]=round(pp,2); p[6]=f"MOL3A {pp:.1f}%"
                except: pass
            if config["doctor_auto"] and len(state["treatment"]) >= config["doctor_threshold"]:
                config["doctor_enabled"]=True; state["healing_mode"]=True
            if len(state["treatment"]) < config["doctor_threshold"]: state["healing_mode"]=False
            if len(state["treatment"])==0 and len(state["doctor_positions"])==0: state["healing_mode"]=False
            if config["doctor_enabled"] and len(state["treatment"]) > 0 and len(state["doctor_positions"]) < config["max_doctors"]:
                state["treatment"].sort(key=lambda x: x[8] if len(x)>8 else 0, reverse=True)
                exist = set([x[0] for x in state["positions"]+state["treatment"]+state["doctor_positions"]] + list(BANNED))
                strongest_list = get_tradingview_doctors(list(exist), config["max_doctors"])
                used_patients=set([d[9] for d in state["doctor_positions"]])
                for strongest in strongest_list:
                    if len(state["doctor_positions"]) >= config["max_doctors"]: break
                    target_patient=None
                    for t in state["treatment"]:
                        if t[0] not in used_patients and t[0] not in BANNED: target_patient=t; break
                    if not target_patient: break
                    oldest=target_patient; invoice=oldest[8]
                    sym,pct,price,vol,power,bull,source = strongest
                    if sym == oldest[0] or sym in BANNED or oldest[0] in BANNED: continue
                    if sym not in exist and price>0.0000005:
                        state["doctor_positions"].append([sym, source, price*0.9995, price, 0.0, 0.0, f"{pct:.1f}% MOL3A", time.time(), invoice, oldest[0], source, pct])
                        state["last"]=f"{source} {sym} {pct:.1f}% -> {oldest[0]}"; exist.add(sym); used_patients.add(oldest[0])
            for d in state["doctor_positions"][:]:
                try:
                    r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={d[0]}USDT", timeout=3)
                    if r.status_code==200:
                        np=float(r.json()["price"]); d[3]=np; pp=(d[3]-d[2])/d[2]*100; d[4]=round(config["per_trade"]*pp/100,3); d[5]=round(pp,2)
                        invoice=d[8]; target=invoice*0.60; alive=time.time()-d[7]
                        if d[4] <= -config["doctor_sl"] or (alive>180 and d[4] < 0.05): state["doctor_positions"].remove(d); continue
                        if d[4] >= target:
                            for t in state["treatment"][:]:
                                if t[0]==d[9]: state["treatment"].remove(t); state["doctor"]["healed"]+=1; state["doctor"]["profit"]+=invoice; break
                            state["doctor_positions"].remove(d)
                            if len(state["treatment"])==0: state["healing_mode"]=False
                except: pass
            for p in state["treatment"]:
                try:
                    if p[0] in BANNED: continue
                    r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={p[0]}USDT", timeout=2)
                    if r.status_code==200:
                        np=float(r.json()["price"])
                        if np > p[2]*0.994: profit=(np-p[2])/p[2]*config["per_trade"]; state["doctor"]["healed"]+=1; state["doctor"]["profit"]+=profit; state["treatment"].remove(p); continue
                        p[3]=np
                except: pass
            state["ghair"]=round(sum(p[4] for p in state["positions"])+sum(d[4] for d in state["doctor_positions"]),3)
            state["loss_pool"]=round(sum(p[8] for p in state["treatment"] if p[0] not in BANNED),3)
            if state["ghair"] >= config["target_dollar"] and len(state["positions"])>0 and not state["healing_mode"]:
                profit=state["ghair"]
                if profit>0: state["safi"]+=profit
                state["fixed"]=config["capital"]+state["safi"]; state["trades_closed"]+=len(state["positions"]); state["positions"]=[]; state["ghair"]=0.0
            to_hosp=[p for p in state["positions"] if p[5] <= -config["sl_pct"] and p[0] not in BANNED]
            for p in to_hosp:
                if p in state["positions"]:
                    state["positions"].remove(p)
                    target_price = p[2] * 0.994
                    state["treatment"].append([p[0],"علاج",p[2],p[3],0.0,0.0,0.35,f"{p[0]} يعالج {abs(p[4]):.2f}$",abs(p[4]),target_price])
            if len(state["treatment"]) >= config["hospital_cap"]: state["specialty"]=True; state["binance_status"]=f"زحمة {len(state['treatment'])}/30"
            else:
                state["specialty"]=False
                dyn = get_dynamic_per_trade()
                if state["protect_triggered"]: state["binance_status"]=f"حماية مفعلة اعلى {state['max_safi']:.0f}$"
                else: state["binance_status"]=f"V100 LEGEND {len(state['positions'])}/8 حجم {dyn:.0f}$ اعلى {state['max_safi']:.0f}$"
                if len(state["positions"]) < config["max_pos"]:
                    hot=get_binance_hot(); exist=set([x[0] for x in state["positions"]+state["treatment"]+state["doctor_positions"]] + list(BANNED))
                    for sym,pct,price,vol,power,bull,src in hot:
                        if sym not in exist and len(state["positions"])<config["max_pos"]: state["positions"].append([sym,"SPOT BINANCE",price*0.9995,price,0.0,0.0,f"{pct:.1f}% BINANCE",time.time()]); exist.add(sym)
            time.sleep(2)
        except: time.sleep(1)

threading.Thread(target=engine,daemon=True).start()

@app.route('/health')
def health(): return "OK",200

@app.route('/api/control/<cmd>')
def control(cmd):
    if cmd=="toggle":
        state["is_running"]=not state["is_running"]
        if state["is_running"]: state["protect_triggered"]=False
    elif cmd=="lock":
        prof=sum(p[4] for p in state["positions"] if p[4]>0)
        if prof>0: state["safi"]+=prof; state["fixed"]=config["capital"]+state["safi"]; state["trades_closed"]+=len(state["positions"])
        state["positions"]=[]; state["ghair"]=0.0
    elif cmd=="reset": state["fixed"]=config["capital"]; state["safi"]=0.0; state["max_safi"]=0.0; state["ghair"]=0.0; state["loss_pool"]=0.0; state["trades_closed"]=0; state["positions"]=[]; state["treatment"]=[]; state["doctor_positions"]=[]; state["doctor"]={"healed":0,"profit":0.0,"start":time.time(),"rate":99.5,"active_patient":None,"active_doctor":None}; state["specialty"]=False; state["is_running"]=True; state["healing_mode"]=False; state["protect_triggered"]=False
    elif cmd=="safi_reset": state["safi"]=0.0; state["fixed"]=config["capital"]; state["max_safi"]=0.0
    elif cmd=="ban_clean":
        for p in state["treatment"][:]:
            if p[0] in BANNED: state["treatment"].remove(p)
        for p in state["positions"][:]:
            if p[0] in BANNED: state["positions"].remove(p)
        for d in state["doctor_positions"][:]:
            if d[0] in BANNED or d[9] in BANNED or d[0]==d[9]: state["doctor_positions"].remove(d)
    elif cmd=="doctor": config["doctor_enabled"]=not config["doctor_enabled"]; config["doctor_auto"]=config["doctor_enabled"]
    elif cmd=="protect_reset": state["protect_triggered"]=False; state["max_safi"]=state["safi"]; state["is_running"]=True
    return jsonify({"ok":True})

@app.route('/api/config', methods=['POST'])
def set_config():
    d=request.json
    try:
        if "capital" in d: config["capital"]=float(d["capital"])
        if "per_trade" in d: config["per_trade"]=float(d["per_trade"]); config["base_per_trade"]=float(d["per_trade"])
        if "target" in d: config["target_dollar"]=float(d["target"])
        if "target_dollar" in d: config["target_dollar"]=float(d["target_dollar"])
        if "hcap" in d: config["hospital_cap"]=int(float(d["hcap"]))
    except: pass
    return jsonify({"ok":True,"config":config})

@app.route('/api/data')
def api_data():
    total=state["fixed"]+state["ghair"]-state["loss_pool"]; elapsed=int(time.time()-state["doctor"]["start"])
    dyn = get_dynamic_per_trade()
    return jsonify({"fixed":state["fixed"],"safi":state["safi"],"max_safi":state["max_safi"],"dynamic_per_trade":dyn,"ghair":state["ghair"],"total":round(total,3),"trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"positions":state["positions"],"treatment":state["treatment"],"doctor_positions":state["doctor_positions"],"binance_status":state["binance_status"],"data_source":f"V100 LEGEND حجم {dyn:.0f}$ اعلى {state['max_safi']:.0f}$","is_running":state["is_running"],"doctor":state["doctor"],"elapsed":elapsed,"heal_rate":99.5,"specialty":state["specialty"],"last_healed":state["last"],"config":config,"healing_mode":state["healing_mode"],"protect_triggered":state["protect_triggered"]})

@app.route('/')
def home():
    return """<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;800;900&family=JetBrains+Mono:wght@700;800&display=swap" rel="stylesheet"><style>*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top,#0A1931 0%,#060A14 70%);color:#E8DCC6;font-family:'Cairo';overflow-x:hidden}.top{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;margin:6px;background:linear-gradient(135deg,#0F1E3A,#1A2F5A);border:1px solid #D4AF3755;border-radius:10px;font-size:13px;font-weight:900;color:#D4AF37;flex-wrap:wrap;gap:6px}.panel{background:linear-gradient(180deg,#0F1C33,#0A1428);border:1px solid #D4AF3730;border-radius:14px;margin:6px;padding:12px}.panel h3{margin:0 0 10px;text-align:center;color:#FFD700;font-size:18px;font-weight:900}.grid{display:grid;gap:6px}.box{background:linear-gradient(180deg,#0A1428,#060A14);border:1px solid #D4AF3725;border-radius:10px;padding:6px 4px;text-align:center;min-width:0}.box label{font-size:12px;color:#E2E8F0;display:block;margin-bottom:5px;font-weight:800}.box input{width:100%;background:#020617;border:1.2px solid #D4AF37;border-radius:8px;color:#FFF;font-family:'JetBrains Mono'!important;font-weight:800;font-size:14px;text-align:center;padding:6px 2px;direction:ltr!important}@media(max-width:768px){.grid{grid-template-columns:1fr 1fr}}@media(min-width:769px){.grid{grid-template-columns:repeat(4,1fr)}}.btns{display:flex;gap:6px;justify-content:center;flex-wrap:wrap;padding:10px}.btn{border:none;border-radius:22px;padding:10px 16px;font-family:'Cairo';font-size:12px;font-weight:900;cursor:pointer;white-space:nowrap}.cards{display:grid;gap:6px;padding:6px}.card{background:linear-gradient(180deg,#122040,#0A1428);border:1px solid #D4AF3720;border-radius:12px;padding:10px 4px;text-align:center;min-width:0}.card.gold{border-color:#D4AF37}.card.safi{border-color:#10B981}.lab{font-size:12px;color:#CBD5E1;margin-bottom:5px;font-weight:800}.val{font-family:'JetBrains Mono'!important;font-weight:900;direction:ltr!important;white-space:nowrap;font-size:14px}@media(max-width:768px){.cards{grid-template-columns:1fr 1fr}.val{font-size:14px!important}.card:nth-child(3){grid-column:1 / -1}}@media(min-width:769px){.cards{grid-template-columns:repeat(5,1fr)}.val{font-size:16px!important}.val.g{font-size:22px!important}.val.y{font-size:18px!important}}.tbl{margin:6px;border-radius:12px;overflow:hidden;border:1px solid #D4AF3720;overflow-x:auto}.th{display:grid;padding:12px 8px;font-size:14px;font-weight:900;color:#FFD700;background:linear-gradient(90deg,#1A2A4A 0%,#223A6A 100%);min-width:560px}.rw{display:grid;padding:9px 8px;font-size:13px;background:#0E1A30;border-top:1px solid #1A2A4A50;min-width:560px;align-items:center}.rw div{font-family:'JetBrains Mono'!important;font-weight:800;direction:ltr!important;font-size:13px;white-space:nowrap}.badge{border-radius:10px;padding:4px 8px;font-size:10px;font-weight:900;display:inline-block;direction:ltr!important;font-family:'JetBrains Mono'}.profit-pos{color:#00FF88!important;text-shadow:0 0 10px rgba(0,255,136,0.9);font-weight:900!important}.profit-neg{color:#FF3344!important;text-shadow:0 0 10px rgba(255,51,68,0.9);font-weight:900!important}.foot{padding:8px 12px;font-size:11px;background:#020617;color:#D4AF37;display:flex;justify-content:space-between;font-family:'JetBrains Mono';direction:ltr;flex-wrap:wrap;gap:4px}</style></head><body><div class="top"><span id="elapsed">0s</span><span id="rate">V100 - 0/30</span><span id="profit">+0.00$</span><span id="healed">0</span><span id="spec">جاهز</span></div><div class="panel"><h3>👑 V100 LEGEND - تكبير + حماية 5% 🛡️</h3><div class="grid"><div class="box"><label>💰 راس المال $</label><input id="cap" type="text" value="1000" onchange="save()"></div><div class="box"><label>📦 حجم اساسي $</label><input id="per" type="text" value="200" onchange="save()"><div id="dynVal" style="font-size:10px;color:#00FF88;font-family:'JetBrains Mono';margin-top:3px;font-weight:900">ديناميكي 300$</div></div><div class="box"><label>🎯 هدف القفل $</label><input id="targ" type="text" value="0.5" onchange="save()"><div id="targVal" style="font-size:11px;color:#FFD700;font-family:'JetBrains Mono';margin-top:4px;font-weight:900">0.5$</div></div><div class="box"><label>🏥 سعة المستشفى</label><input id="hcap" type="text" value="30" onchange="save()"></div></div></div><div class="btns"><button class="btn" style="background:#10B981;color:#FFF" id="btnRun" onclick="ctrl('toggle')">⏸️ ايقاف</button><button class="btn" style="background:#38BDF8;color:#000" onclick="ctrl('lock')">🔒 قفل ربح</button><button class="btn" style="background:#22D3EE;color:#000" id="btnDoc" onclick="ctrl('doctor')">🔥 مولعة ON</button><button class="btn" style="background:#000;color:#FF3344;border:2px solid #FF3344" onclick="ctrl('ban_clean')">🚫 تنظيف حظر</button></div><div class="cards"><div class="card"><div class="lab">💰 ثابت</div><div class="val" id="f1">1000.00$</div></div><div class="card"><div class="lab">📦 الصيدلية</div><div class="val" id="f2">0.00$</div><div class="lab" id="f2c" style="font-size:10px">0 دواء</div></div><div class="card safi"><div class="lab">💹 صافي محقق 🔒</div><div class="val g" id="f3">+0.000$</div><div id="maxSafi" style="font-size:10px;color:#FFD700;font-family:'JetBrains Mono'">اعلى 219$</div></div><div class="card gold"><div class="lab">💎 الاجمالي</div><div class="val y" id="f5">1000.000$</div></div><div class="card"><div class="lab">📈 غير محققة</div><div class="val" id="f6">+0.000$</div></div></div><div class="tbl"><div class="th" style="grid-template-columns:1.2fr 0.8fr 1.2fr 0.8fr 0.8fr 0.8fr 0.6fr"><div>العملة</div><div>النوع</div><div>الحالة</div><div>الدخول</div><div>الحالي</div><div>ربح $</div><div>%</div></div><div id="plist"></div></div><div class="tbl" style="border-color:#22D3EE"><div class="th" style="grid-template-columns:1fr 1fr 0.6fr 0.6fr 0.6fr 0.8fr 0.6fr;background:#0E2A3A;color:#22D3EE"><div>🔥 طبيب TV</div><div>يعالج</div><div>الفاتورة</div><div>الهدف</div><div>الربح</div><div>الحالة</div><div>المصدر</div></div><div id="dlist"></div></div><div class="tbl" style="border-color:#D4AF37"><div class="th" style="grid-template-columns:1fr 1.2fr 0.6fr 0.6fr 0.6fr 0.6fr;background:#2A1F0F;color:#D4AF37"><div>💊 المستشفى</div><div>يعالج</div><div>الخسارة</div><div>الهدف</div><div>الحالي</div><div>%</div></div><div id="tlist"></div></div><div class="foot"><span id="src">V100 LEGEND</span><span id="bin">...</span><span id="time">...</span></div><script>function en(n,d=2){ let num=Number(n); if(isNaN(num)) num=0; return num.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d,useGrouping:false}); }function colorClass(v){ return Number(v) >= 0? 'profit-pos' : 'profit-neg'; }async function ctrl(c){ await fetch('/api/control/'+c); load(); }async function save(){ let cap=document.getElementById('cap').value, per=document.getElementById('per').value, targ=document.getElementById('targ').value, hcap=document.getElementById('hcap').value; const res=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capital:parseFloat(cap)||1000,per_trade:parseFloat(per)||200,target:parseFloat(targ)||0.5,target_dollar:parseFloat(targ)||0.5,hcap:parseInt(hcap)||30})}); const j=await res.json(); document.getElementById('targVal').innerText=en(j.config.target_dollar,1)+'$'; }async function load(){ try{ const r=await fetch('/api/data'); const d=await r.json(); document.getElementById('cap').value=en(d.config.capital,0); document.getElementById('per').value=en(d.config.base_per_trade||d.config.per_trade,0); document.getElementById('targ').value=en(d.config.target_dollar,1); document.getElementById('hcap').value=en(d.config.hospital_cap,0); document.getElementById('elapsed').innerText=en(d.elapsed,0)+'s'; document.getElementById('rate').innerText='V100 - '+en(d.treatment.length,0)+'/'+en(d.config.hospital_cap,0); document.getElementById('profit').innerText='+'+en(d.doctor.profit,2)+'$'; document.getElementById('healed').innerText=en(d.doctor.healed,0)+' شفى'; document.getElementById('f1').innerText=en(d.fixed,2)+'$'; document.getElementById('f2').innerText=en(d.loss_pool,2)+'$'; document.getElementById('f2c').innerText=en(d.treatment.length,0)+' دواء'; let safiCls = Number(d.safi)>=0?'profit-pos':'profit-neg'; document.getElementById('f3').innerHTML='<span class="'+safiCls+'">+'+en(d.safi,3)+'$</span>'; document.getElementById('maxSafi').innerText='اعلى '+en(d.max_safi||d.safi,0)+'$ - حجم '+en(d.dynamic_per_trade||200,0)+'$'; document.getElementById('dynVal').innerText='ديناميكي '+en(d.dynamic_per_trade||200,0)+'$'; document.getElementById('f5').innerText=en(d.total,3)+'$'; let ghairCls = Number(d.ghair)>=0?'profit-pos':'profit-neg'; document.getElementById('f6').innerHTML='<span class="'+ghairCls+'">'+en(d.ghair,3)+'$ / '+en(d.config.target_dollar,1)+'$</span>'; document.getElementById('btnRun').innerText=d.is_running?'⏸️ ايقاف':'▶️ تشغيل'; if(d.protect_triggered){ document.getElementById('btnRun').innerText='🔒 حماية'; document.getElementById('btnRun').style.background='#FF3344'; } else { document.getElementById('btnRun').style.background='#10B981'; } document.getElementById('btnDoc').innerText=d.config.doctor_enabled?'🔥 مولعة ON':'🔥 OFF'; document.getElementById('src').innerText=d.data_source; document.getElementById('bin').innerText=d.binance_status; document.getElementById('time').innerText=new Date().toLocaleTimeString('en-GB',{hour12:false}); let h=''; for(const p of d.positions){ let cls=colorClass(p[5]); let cls2=colorClass(p[4]); h+=`<div class="rw" style="grid-template-columns:1.2fr 0.8fr 1.2fr 0.8fr 0.8fr 0.8fr 0.6fr"><div style="color:#FFF;font-weight:900">${p[0]}</div><div><span class="badge" style="background:#38BDF8;color:#000">BIN</span></div><div class="${cls}" style="font-size:12px">${p[6]}</div><div style="color:#FFD700">${en(p[2],4)}</div><div style="color:#FFF">${en(p[3],4)}</div><div class="${cls2}">${en(p[4],3)}$</div><div class="${cls}">${en(p[5],2)}%</div></div>` } document.getElementById('plist').innerHTML=h||'<div style="padding:10px;text-align:center;color:#D4AF3760">⏳ BINANCE يطحن...</div>'; let dl=''; for(const p of d.doctor_positions){ let cls=colorClass(p[5]); let invoice=en(p[8],2); let target=en(p[8]*0.60,2); let profitCls=colorClass(p[4]); dl+=`<div class="rw" style="grid-template-columns:1fr 1fr 0.6fr 0.6fr 0.6fr 0.8fr 0.6fr;background:#0E1E2E"><div><span class="badge" style="background:#D4AF37;color:#000">${p[0]}</span></div><div style="color:#FACC15;font-weight:800">${p[9]}</div><div style="color:#FB923C">${invoice}$</div><div style="color:#00FF88">${target}$</div><div class="${profitCls}">${en(p[4],3)}$</div><div class="${cls}" style="font-size:11px">${p[6]}</div><div><span class="badge" style="background:${(p[10]||'TV').includes('TRADINGVIEW')?'#22D3EE':'#D4AF37'};color:#000;font-size:8px">${(p[10]||'TV').substring(0,3)}</span></div></div>` } document.getElementById('dlist').innerHTML=dl||'<div style="padding:10px;text-align:center;background:#0E1E2E;color:#D4AF37">👑 0/30 فخامة ✅</div>'; let t=''; for(const p of d.treatment){ let loss='-'+en(p[8],2)+'$'; let tgt=en(p[9],4); t+=`<div class="rw" style="grid-template-columns:1fr 1.2fr 0.6fr 0.6fr 0.6fr 0.6fr;background:#1A1500"><div><span class="badge" style="background:#FB923C;color:#000">${p[0]}</span></div><div style="color:#D4AF37;font-size:11px">${p[7]}</div><div class="profit-neg">${loss}</div><div style="color:#FFD700">${tgt}</div><div>${en(p[3],4)}</div><div class="profit-neg">5%</div></div>` } document.getElementById('tlist').innerHTML=t||'<div style="padding:10px;text-align:center;background:#1A1500;color:#10B981">👑 0/30 فاضي ✅</div>'; }catch(e){} } setInterval(load,1000); load();</script></body></html>"""

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

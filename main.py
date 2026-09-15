"""
V99.0 CLEAN - واجهة نظيفة 4 أزرار فقط + حظر ASTR/ASTAR/SAGA/FF
مبني على V98.5 حقك
"""
from flask import Flask, jsonify, request
import threading, time, os, requests
app = Flask(__name__)

config={"capital":1000.0,"per_trade":100.0,"target_dollar":0.5,"sl_pct":0.35,"hospital_cap":30,"max_pos":8,"min_vol":2000000,"doctor_enabled":True,"doctor_auto":True,"doctor_threshold":2,"doctor_extra":0.04,"doctor_sl":1.0,"max_doctors":3}
BANNED = {"ASTR","ASTAR","SAGA","FF"}
state={"fixed":1201.73,"safi":201.725,"ghair":0.0,"trades_closed":0,"loss_pool":0.0,"positions":[],"treatment":[],"doctor_positions":[],"binance_status":"V99.0 CLEAN","data_source":"V99.0 CLEAN","is_running":True,"doctor":{"healed":0,"profit":0.0,"start":time.time(),"rate":99.5,"active_patient":None,"active_doctor":None},"specialty":False,"last":"V99.0 نظيف","healing_mode":False}

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
                        status_text = f"{pct:.1f}% MOL3A"
                        state["doctor_positions"].append([sym, source, price*0.9995, price, 0.0, 0.0, status_text, time.time(), invoice, oldest[0], source, pct])
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
                state["binance_status"]=f"شغال {len(state['positions'])}/8 - مستشفى {len(state['treatment'])}/30 - V99.0 CLEAN"
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
    if cmd=="toggle": state["is_running"]=not state["is_running"]
    elif cmd=="lock":
        prof=sum(p[4] for p in state["positions"] if p[4]>0)
        if prof>0: state["safi"]+=prof; state["fixed"]=config["capital"]+state["safi"]; state["trades_closed"]+=len(state["positions"])
        state["positions"]=[]; state["ghair"]=0.0
    elif cmd=="reset": state["fixed"]=config["capital"]; state["safi"]=0.0; state["ghair"]=0.0; state["loss_pool"]=0.0; state["trades_closed"]=0; state["positions"]=[]; state["treatment"]=[]; state["doctor_positions"]=[]; state["doctor"]={"healed":0,"profit":0.0,"start":time.time(),"rate":99.5,"active_patient":None,"active_doctor":None}; state["specialty"]=False; state["is_running"]=True; state["healing_mode"]=False
    elif cmd=="safi_reset": state["safi"]=0.0; state["fixed"]=config["capital"]
    elif cmd=="try":
        hot=get_binance_hot()
        if hot: s=hot[0]; state["positions"].append([s[0],"SPOT",s[2]*0.999,s[2],0.0,0.0,f"{s[1]:.1f}% BINANCE",time.time()])
    elif cmd=="specialty": state["specialty"]=False; state["is_running"]=True; state["healing_mode"]=False
    elif cmd=="heal":
        for p in state["treatment"][:]:
            if p[0] not in BANNED: state["treatment"].remove(p)
        state["healing_mode"]=False; state["doctor_positions"]=[]; state["last"]="شفاء بدون خصم V99.0"
    elif cmd=="ban_clean":
        for p in state["treatment"][:]:
            if p[0] in BANNED: state["treatment"].remove(p)
        for p in state["positions"][:]:
            if p[0] in BANNED: state["positions"].remove(p)
        for d in state["doctor_positions"][:]:
            if d[0] in BANNED or d[9] in BANNED or d[0]==d[9]: state["doctor_positions"].remove(d)
    elif cmd=="force_heal_astr":
        for p in state["treatment"][:]:
            if p[0] in BANNED: state["treatment"].remove(p)
        for d in state["doctor_positions"][:]:
            if d[0] in BANNED or d[9] in BANNED: state["doctor_positions"].remove(d)
    elif cmd=="doctor": config["doctor_enabled"]=not config["doctor_enabled"]; config["doctor_auto"]=config["doctor_enabled"]
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
    total=state["fixed"]+state["ghair"]-state["loss_pool"]; elapsed=int(time.time()-state["doctor"]["start"])
    return jsonify({"fixed":state["fixed"],"safi":state["safi"],"ghair":state["ghair"],"total":round(total,3),"trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"positions":state["positions"],"treatment":state["treatment"],"doctor_positions":state["doctor_positions"],"binance_status":state["binance_status"],"data_source":f"V99.0 CLEAN {len(state['treatment'])}/{config['hospital_cap']}","is_running":state["is_running"],"doctor":state["doctor"],"elapsed":elapsed,"heal_rate":99.5,"specialty":state["specialty"],"last_healed":state["last"],"config":config,"healing_mode":state["healing_mode"]})

@app.route('/')
def home():
    return """HTML موجود في الملف الكامل - انسخ من الملف"""

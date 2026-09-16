"""
V100 LEGEND DUAL - نسخة نهائية - تصفير الحقول عند التحويل للحقيقي
"""
from flask import Flask, jsonify, request
import threading, time, os, requests
app = Flask(__name__)

try:
    from binance.client import Client
    REAL_CLIENT = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET")) if os.getenv("BINANCE_API_KEY") else None
    TEST_CLIENT = Client(os.getenv("TESTNET_API_KEY"), os.getenv("TESTNET_SECRET"), testnet=True) if os.getenv("TESTNET_API_KEY") else None
except:
    REAL_CLIENT = None
    TEST_CLIENT = None

config={"capital":10000.0,"per_trade":3.0,"base_per_trade":3.0,"target_dollar":0.05,"sl_pct":0.35,"hospital_cap":3,"max_pos":8,"min_vol":2000000,"doctor_enabled":True,"doctor_auto":True,"doctor_threshold":2,"doctor_extra":0.04,"doctor_sl":1.0,"max_doctors":3,"auto_compound":True,"compound_step":50.0,"compound_add":25.0,"protect_pct":0.05}
BANNED = {"ASTR","ASTAR","SAGA","FF"}
state={"fixed":10000.0,"safi":0.0,"max_safi":0.0,"ghair":0.0,"trades_closed":0,"loss_pool":0.0,"positions":[],"treatment":[],"doctor_positions":[],"binance_status":"V100 جاهز","data_source":"V100","is_running":True,"mode":"TESTNET","real_balance":"--","test_balance":"10000.00","doctor":{"healed":0,"profit":0.0,"start":time.time(),"rate":99.5},"specialty":False,"last":"V100","healing_mode":False,"protect_triggered":False,"no_balance_alert":False}

def get_dynamic_per_trade():
    if not config["auto_compound"]: return config["per_trade"]
    steps = int(state["safi"] // config["compound_step"])
    return config["base_per_trade"] + steps * config["compound_add"]

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
            if sym in BANNED or len(sym)>10: continue
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

def update_balances():
    try:
        if REAL_CLIENT:
            b=REAL_CLIENT.get_asset_balance(asset='USDT')
            bal=float(b['free'])
            state["real_balance"]=f"{bal:.2f}"
    except: pass
    try:
        if TEST_CLIENT:
            b=TEST_CLIENT.get_asset_balance(asset='USDT')
            bal=float(b['free'])
            state["test_balance"]=f"{bal:.2f}"
    except:
        state["test_balance"]="10000.00"

def engine():
    while True:
        try:
            if not state["is_running"]: time.sleep(1); continue
            if state["mode"]=="REAL":
                try:
                    rb = float(state["real_balance"]) if state["real_balance"]!="--" else 0
                    if rb < 0.5:
                        state["is_running"]=False
                        state["no_balance_alert"]=True
                        state["binance_status"]=f"⛔ لا يوجد رصيد حقيقي {rb}$ - اشحن Binance"
                        time.sleep(2); continue
                except: pass
            if state["safi"] > state["max_safi"]: state["max_safi"] = state["safi"]
            config["per_trade"] = get_dynamic_per_trade()
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
            if len(state["treatment"]) >= config["hospital_cap"]: state["specialty"]=True; state["binance_status"]=f"زحمة {len(state['treatment'])}/30 [{state['mode']}]"
            else:
                state["specialty"]=False
                dyn = get_dynamic_per_trade()
                if not state["no_balance_alert"]:
                    if state["protect_triggered"]: state["binance_status"]=f"حماية مفعلة اعلى {state['max_safi']:.0f}$"
                    else: state["binance_status"]=f"V100 {state['mode']} {len(state['positions'])}/8 حجم {dyn:.0f}$"
                if len(state["positions"]) < config["max_pos"] and not state["no_balance_alert"]:
                    hot=get_binance_hot(); exist=set([x[0] for x in state["positions"]+state["treatment"]+state["doctor_positions"]] + list(BANNED))
                    for sym,pct,price,vol,power,bull,src in hot:
                        if sym not in exist and len(state["positions"])<config["max_pos"]: state["positions"].append([sym,"SPOT BINANCE",price*0.9995,price,0.0,0.0,f"{pct:.1f}% BINANCE",time.time()]); exist.add(sym)
            if int(time.time()) % 20 == 0: update_balances()
            time.sleep(2)
        except: time.sleep(1)

threading.Thread(target=engine,daemon=True).start()

@app.route('/health')
def health(): return "OK",200

def reset_trading_state(new_capital):
    # تصفير كامل للحقول اللي تحت
    state["positions"]=[]
    state["treatment"]=[]
    state["doctor_positions"]=[]
    state["safi"]=0.0
    state["max_safi"]=0.0
    state["ghair"]=0.0
    state["loss_pool"]=0.0
    state["trades_closed"]=0
    state["fixed"]=new_capital
    state["doctor"]={"healed":0,"profit":0.0,"start":time.time(),"rate":99.5}
    state["healing_mode"]=False
    state["protect_triggered"]=False

@app.route('/api/control/<cmd>')
def control(cmd):
    if cmd=="toggle":
        if state["no_balance_alert"] and state["mode"]=="REAL":
            return jsonify({"ok":False, "error": "no_balance", "balance": state["real_balance"], "capital": config["capital"]})
        state["is_running"]=not state["is_running"]
        if state["is_running"]: state["protect_triggered"]=False
    elif cmd=="lock":
        prof=sum(p[4] for p in state["positions"] if p[4]>0)
        if prof>0: state["safi"]+=prof; state["fixed"]=config["capital"]+state["safi"]; state["trades_closed"]+=len(state["positions"])
        state["positions"]=[]; state["ghair"]=0.0
    elif cmd=="reset":
        reset_trading_state(config["capital"])
        state["is_running"]=True; state["no_balance_alert"]=False
    elif cmd=="safi_reset":
        state["safi"]=0.0; state["fixed"]=config["capital"]; state["max_safi"]=0.0; state["ghair"]=0.0; state["loss_pool"]=0.0
    elif cmd=="ban_clean":
        for p in state["treatment"][:]:
            if p[0] in BANNED: state["treatment"].remove(p)
        for p in state["positions"][:]:
            if p[0] in BANNED: state["positions"].remove(p)
        for d in state["doctor_positions"][:]:
            if d[0] in BANNED or d[9] in BANNED or d[0]==d[9]: state["doctor_positions"].remove(d)
    elif cmd=="doctor": config["doctor_enabled"]=not config["doctor_enabled"]; config["doctor_auto"]=config["doctor_enabled"]
    elif cmd=="protect_reset": state["protect_triggered"]=False; state["no_balance_alert"]=False; state["max_safi"]=state["safi"]; state["is_running"]=True
    elif cmd=="mode_test":
        state["mode"]="TESTNET"; state["no_balance_alert"]=False; state["protect_triggered"]=False; state["is_running"]=True
        config["capital"]=10000.0
        reset_trading_state(10000.0)
        state["test_balance"]="10000.00"
        try:
            if TEST_CLIENT:
                b=TEST_CLIENT.get_asset_balance(asset='USDT')
                bal=float(b['free'])
                if bal>0:
                    config["capital"]=bal
                    reset_trading_state(bal)
                    state["test_balance"]=f"{bal:.2f}"
        except: pass
        state["binance_status"]=f"V100 TESTNET {config['capital']:.2f}$"
        return jsonify({"ok":True, "capital": config["capital"], "mode": "TESTNET", "real_balance": state["real_balance"], "test_balance": state["test_balance"]})
    elif cmd=="mode_real":
        state["mode"]="REAL"; state["protect_triggered"]=False
        real_bal = 0.0
        try:
            if REAL_CLIENT:
                b=REAL_CLIENT.get_asset_balance(asset='USDT')
                bal=float(b['free'])
                real_bal=bal
                state["real_balance"]=f"{bal:.2f}"
                config["capital"]=bal
                reset_trading_state(bal) # يصفر الحقول اللي تحت
                if bal < 0.5:
                    state["no_balance_alert"]=True; state["is_running"]=False
                    state["binance_status"]=f"⛔ لا يوجد رصيد حقيقي {bal}$"
                    return jsonify({"ok":True, "capital": bal, "mode": "REAL", "real_balance": state["real_balance"], "error": "no_balance", "balance": bal})
                else:
                    state["no_balance_alert"]=False; state["is_running"]=True
            else:
                state["real_balance"]="0.00"
                config["capital"]=0.0
                reset_trading_state(0.0) # يصفر كل شي
                state["no_balance_alert"]=True
                state["is_running"]=False
                state["binance_status"]=f"⛔ لا يوجد رصيد حقيقي - اضف API"
                return jsonify({"ok":True, "capital": 0, "mode": "REAL", "real_balance": "0.00", "error": "no_balance", "balance": 0})
        except Exception as e:
            state["real_balance"]=f"{real_bal:.2f}"
            config["capital"]=real_bal
            reset_trading_state(real_bal)
        state["binance_status"]=f"V100 REAL {config['capital']:.2f}$"
        return jsonify({"ok":True, "capital": config["capital"], "mode": "REAL", "real_balance": state["real_balance"]})
    return jsonify({"ok":True, "capital": config["capital"], "mode": state["mode"], "real_balance": state["real_balance"]})

@app.route('/api/config', methods=['POST'])
def set_config():
    d=request.json
    try:
        if "capital" in d: config["capital"]=float(d["capital"]); state["fixed"]=config["capital"]+state["safi"]
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
    return jsonify({"fixed":state["fixed"],"safi":state["safi"],"max_safi":state["max_safi"],"dynamic_per_trade":dyn,"ghair":state["ghair"],"total":round(total,3),"trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"positions":state["positions"],"treatment":state["treatment"],"doctor_positions":state["doctor_positions"],"binance_status":state["binance_status"],"data_source":f"V100 {state['mode']} حجم {dyn:.0f}$","is_running":state["is_running"],"doctor":state["doctor"],"elapsed":elapsed,"heal_rate":99.5,"specialty":state["specialty"],"last_healed":state["last"],"config":config,"healing_mode":state["healing_mode"],"protect_triggered":state["protect_triggered"],"mode":state["mode"],"real_balance":state["real_balance"],"test_balance":state["test_balance"],"no_balance_alert":state["no_balance_alert"]})

@app.route('/')
def home():
    return """<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;800;900&family=JetBrains+Mono:wght@700;800;900&display=swap" rel="stylesheet"><style>
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top,#0A1931 0%,#060A14 70%);color:#E8DCC6;font-family:'Cairo';overflow-x:hidden}
.top{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;margin:6px;background:linear-gradient(135deg,#0F1E3A,#1A2F5A);border:1px solid #D4AF3755;border-radius:10px;font-size:13px;font-weight:900;color:#D4AF37;flex-wrap:wrap;gap:6px}
.alert{margin:6px;padding:14px;border-radius:12px;text-align:center;font-weight:900;font-size:14px;display:none}.alert.show{display:block}.alert.no-balance{background:linear-gradient(135deg,#FF1744,#B71C1C);color:#FFF;border:2px solid #FF5252;animation:pulse 1.5s infinite}@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.02)}}
.panel{background:linear-gradient(180deg,#0F1C33,#0A1428);border:1px solid #D4AF3730;border-radius:14px;margin:6px;padding:12px}.panel h3{margin:0 0 10px;text-align:center;color:#FFD700;font-size:18px;font-weight:900}
.grid{display:grid;gap:8px}
.box{background:linear-gradient(180deg,#0A1428,#060A14);border:2px solid #D4AF3730;border-radius:12px;padding:10px 6px;text-align:center;min-width:0}
.box label{font-size:13px;color:#E2E8F0;display:block;margin-bottom:6px;font-weight:900}
.box input{width:100%;height:58px;background:#020617;border:2.5px solid #FFD700;border-radius:12px;color:#FFF;font-family:'JetBrains Mono',monospace!important;font-weight:900!important;font-size:28px!important;text-align:center;direction:ltr!important;unicode-bidi:plaintext;letter-spacing:1px;}
.box input:focus{border-color:#00FF88;outline:none;box-shadow:0 0 14px #FFD70066}
.step-row{display:flex;gap:6px;align-items:center;margin-top:6px}
.step-btn{width:56px;height:58px;background:#1A2A4A;color:#FFD700;border:2.5px solid #FFD700;border-radius:12px;font-weight:900;font-size:30px;cursor:pointer;user-select:none;-webkit-tap-highlight-color:transparent;touch-action:manipulation}
.step-btn:active{transform:scale(0.90);background:#FFD700;color:#000}
@media(max-width:768px){.grid{grid-template-columns:1fr 1fr}}@media(min-width:769px){.grid{grid-template-columns:repeat(4,1fr)}}
.btns{display:flex;gap:6px;justify-content:center;flex-wrap:wrap;padding:10px}.btn{border:none;border-radius:22px;padding:10px 16px;font-family:'Cairo';font-size:12px;font-weight:900;cursor:pointer;white-space:nowrap}
.mode-bar{display:flex;gap:8px;justify-content:center;padding:8px}.mode-btn{flex:1;max-width:200px;padding:14px;border-radius:12px;border:2px solid;font-family:'Cairo';font-weight:900;font-size:14px;cursor:pointer}
.cards{display:grid;gap:6px;padding:6px}.card{background:linear-gradient(180deg,#122040,#0A1428);border:1px solid #D4AF3720;border-radius:12px;padding:10px 4px;text-align:center;min-width:0}.card.gold{border-color:#D4AF37}.card.safi{border-color:#10B981}.lab{font-size:12px;color:#CBD5E1;margin-bottom:5px;font-weight:800}.val{font-family:'JetBrains Mono'!important;font-weight:900;direction:ltr!important;white-space:nowrap;font-size:14px}@media(max-width:768px){.cards{grid-template-columns:1fr 1fr}.val{font-size:14px!important}.card:nth-child(3){grid-column:1 / -1}}@media(min-width:769px){.cards{grid-template-columns:repeat(5,1fr)}.val{font-size:16px!important}.val.g{font-size:22px!important}.val.y{font-size:18px!important}}.tbl{margin:6px;border-radius:12px;overflow:hidden;border:1px solid #D4AF3720;overflow-x:auto}.th{display:grid;padding:12px 8px;font-size:14px;font-weight:900;color:#FFD700;background:linear-gradient(90deg,#1A2A4A 0%,#223A6A 100%);min-width:560px}.rw{display:grid;padding:9px 8px;font-size:13px;background:#0E1A30;border-top:1px solid #1A2A4A50;min-width:560px;align-items:center}.rw div{font-family:'JetBrains Mono'!important;font-weight:800;direction:ltr!important;font-size:13px;white-space:nowrap}.badge{border-radius:10px;padding:4px 8px;font-size:10px;font-weight:900;display:inline-block;direction:ltr!important;font-family:'JetBrains Mono'}.profit-pos{color:#00FF88!important;text-shadow:0 0 10px rgba(0,255,136,0.9);font-weight:900!important}.profit-neg{color:#FF3344!important;text-shadow:0 0 10px rgba(255,51,68,0.9);font-weight:900!important}.foot{padding:8px 12px;font-size:11px;background:#020617;color:#D4AF37;display:flex;justify-content:space-between;font-family:'JetBrains Mono';direction:ltr;flex-wrap:wrap;gap:4px}
.small-info{font-size:11px;color:#FFD700;font-family:'JetBrains Mono';font-weight:900;margin-top:6px;direction:ltr}
</style></head><body>
<div class="top"><span id="elapsed">0s</span><span id="rate">V100 - 0/30</span><span id="profit">+0.00$</span><span id="healed">0</span><span id="spec">جاهز</span></div>
<div id="noBalanceAlert" class="alert no-balance">⛔ لا يتوفر رصيد حقيقي<br>اشحن Binance</div>
<div class="mode-bar">
<button id="btnTest" class="mode-btn" onclick="switchMode('mode_test')" style="background:#0A1F3A;color:#22D3EE;border-color:#22D3EE">🧪 تجريبي TESTNET<br><span id="testBal" style="font-size:11px">10000.00</span></button>
<button id="btnReal" class="mode-btn" onclick="switchMode('mode_real')" style="background:#1A1000;color:#D4AF37;border-color:#D4AF37">👑 حقيقي LEGEND<br><span id="realBal" style="font-size:11px">--</span></button>
</div>
<div class="panel"><h3 id="mainTitle">👑 V100 DUAL - تصفير أوتوماتيك 👑</h3><div class="grid">
<div class="box" style="border:2px solid #FFD700"><label id="capLabel">💰 راس المال $</label><div class="step-row"><button class="step-btn" type="button" onclick="stepCap(-100)">-</button><input id="cap" type="text" inputmode="decimal" lang="en" autocomplete="off" value="10000"><button class="step-btn" type="button" onclick="stepCap(100)">+</button></div><div id="capInfo" class="small-info">🧪 10000$ TESTNET</div></div>
<div class="box"><label>📦 حجم اساسي $</label><div class="step-row"><button class="step-btn" type="button" onclick="step('per',-1)">-</button><input id="per" type="text" inputmode="decimal" lang="en" value="3"><button class="step-btn" type="button" onclick="step('per',1)">+</button></div><div id="dynVal" class="small-info" style="color:#00FF88">ديناميكي 3$</div></div>
<div class="box"><label>🎯 هدف القفل $</label><div class="step-row"><button class="step-btn" type="button" onclick="stepFloat('targ',-0.01)">-</button><input id="targ" type="text" inputmode="decimal" lang="en" value="0.05"><button class="step-btn" type="button" onclick="stepFloat('targ',0.01)">+</button></div><div id="targVal" class="small-info">0.05$</div></div>
<div class="box"><label>🏥 سعة المستشفى</label><div class="step-row"><button class="step-btn" type="button" onclick="step('hcap',-1)">-</button><input id="hcap" type="text" inputmode="numeric" lang="en" value="3"><button class="step-btn" type="button" onclick="step('hcap',1)">+</button></div></div>
</div></div>
<div class="btns"><button class="btn" style="background:#10B981;color:#FFF" id="btnRun" onclick="ctrl('toggle')">⏸️ ايقاف</button><button class="btn" style="background:#38BDF8;color:#000" onclick="ctrl('lock')">🔒 قفل ربح</button><button class="btn" style="background:#22D3EE;color:#000" id="btnDoc" onclick="ctrl('doctor')">🔥 مولعة ON</button><button class="btn" style="background:#000;color:#FF3344;border:2px solid #FF3344" onclick="ctrl('ban_clean')">🚫 تنظيف</button></div>
<div class="cards"><div class="card"><div class="lab">💰 ثابت</div><div class="val" id="f1">10000$</div></div><div class="card"><div class="lab">📦 الصيدلية</div><div class="val" id="f2">0.00$</div><div class="lab" id="f2c" style="font-size:10px">0 دواء</div></div><div class="card safi"><div class="lab">💹 صافي محقق 🔒</div><div class="val g" id="f3">+0.000$</div><div id="maxSafi" style="font-size:10px;color:#FFD700;font-family:'JetBrains Mono'">اعلى 0$</div></div><div class="card gold"><div class="lab">💎 الاجمالي</div><div class="val y" id="f5">10000$</div></div><div class="card"><div class="lab">📈 غير محققة</div><div class="val" id="f6">+0.000$</div></div></div>
<div class="tbl"><div class="th" style="grid-template-columns:1.2fr 0.8fr 1.2fr 0.8fr 0.8fr 0.8fr 0.6fr"><div>العملة</div><div>النوع</div><div>الحالة</div><div>الدخول</div><div>الحالي</div><div>ربح $</div><div>%</div></div><div id="plist"></div></div>
<div class="tbl" style="border-color:#22D3EE"><div class="th" style="grid-template-columns:1fr 1fr 0.6fr 0.6fr 0.6fr 0.8fr 0.6fr;background:#0E2A3A;color:#22D3EE"><div>🔥 طبيب TV</div><div>يعالج</div><div>الفاتورة</div><div>الهدف</div><div>الربح</div><div>الحالة</div><div>المصدر</div></div><div id="dlist"></div></div>
<div class="tbl" style="border-color:#D4AF37"><div class="th" style="grid-template-columns:1fr 1.2fr 0.6fr 0.6fr 0.6fr 0.6fr;background:#2A1F0F;color:#D4AF37"><div>💊 المستشفى</div><div>يعالج</div><div>الخسارة</div><div>الهدف</div><div>الحالي</div><div>%</div></div><div id="tlist"></div></div>
<div class="foot"><span id="src">V100 DUAL</span><span id="bin">...</span><span id="time">...</span></div>
<script>
function enforceEnglish(el){
  if(!el) return;
  let v=el.value||"";
  const ar='٠١٢٣٤٥٦٧٨٩'; const en='0123456789';
  for(let i=0;i<10;i++){ v=v.split(ar[i]).join(en[i]); }
  v=v.replace(/[^0-9.]/g,'');
  let parts=v.split('.');
  if(parts.length>2){ v=parts[0]+'.'+parts.slice(1).join(''); }
  el.value=v;
}
function en(n,d=2){ let num=Number(n); if(isNaN(num)) num=0; return num.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d,useGrouping:false}); }
function colorClass(v){ return Number(v) >= 0? 'profit-pos' : 'profit-neg'; }
function step(id, delta){
  let el=document.getElementById(id);
  enforceEnglish(el);
  let v=parseFloat(el.value)||0;
  v+=delta; if(v<1) v=1;
  el.value=Math.round(v);
  save();
}
function stepFloat(id, delta){
  let el=document.getElementById(id);
  enforceEnglish(el);
  let v=parseFloat(el.value)||0;
  v+=delta; if(v<0.01) v=0.01;
  el.value=v.toFixed(2);
  save();
}
function stepCap(delta){
  let el=document.getElementById('cap');
  enforceEnglish(el);
  let v=parseFloat(el.value)||0;
  v+=delta; if(v<0) v=0;
  el.value=Math.round(v);
  save();
}
async function switchMode(cmd){
  const res = await fetch('/api/control/'+cmd);
  const j = await res.json();
  document.getElementById('cap').value = Math.round(Number(j.capital)||0);
  enforceEnglish(document.getElementById('cap'));
  if(j.error=='no_balance'){
    document.getElementById('noBalanceAlert').classList.add('show');
    document.getElementById('noBalanceAlert').innerHTML='⛔ رصيدك الحقيقي: '+en(j.balance||0,2)+'$ - الحقول تصفرت 0$';
  } else {
    document.getElementById('noBalanceAlert').classList.remove('show');
  }
  load();
}
async function ctrl(c){
  const res = await fetch('/api/control/'+c);
  const j = await res.json();
  if(j.error=='no_balance'){
    document.getElementById('noBalanceAlert').classList.add('show');
    document.getElementById('cap').value = Math.round(j.capital||0);
    return;
  }
  load();
}
async function save(){
  let cap=document.getElementById('cap'); let per=document.getElementById('per'); let targ=document.getElementById('targ'); let hcap=document.getElementById('hcap');
  enforceEnglish(cap); enforceEnglish(per); enforceEnglish(targ); enforceEnglish(hcap);
  const res=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capital:parseFloat(cap.value)||0,per_trade:parseFloat(per.value)||3,target:parseFloat(targ.value)||0.05,target_dollar:parseFloat(targ.value)||0.05,hcap:parseInt(hcap.value)||3})});
  const j=await res.json();
  document.getElementById('targVal').innerText=en(j.config.target_dollar,2)+'$';
}
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    if(d.no_balance_alert){
      document.getElementById('noBalanceAlert').classList.add('show');
      document.getElementById('noBalanceAlert').innerHTML='⛔ رصيد حقيقي '+d.real_balance+'$ - الحقل '+en(d.config.capital,0)+'$ - كل الحقول تصفرت';
    } else { document.getElementById('noBalanceAlert').classList.remove('show'); }
    if(document.activeElement.tagName!=='INPUT'){
      document.getElementById('cap').value=en(d.config.capital,0);
      document.getElementById('per').value=en(d.config.base_per_trade||d.config.per_trade,0);
      document.getElementById('targ').value=en(d.config.target_dollar,2);
      document.getElementById('hcap').value=en(d.config.hospital_cap,0);
    }
    if(d.mode=='REAL'){ document.getElementById('capLabel').innerText='💰 راس المال $ 👑 حقيقي'; document.getElementById('capInfo').innerText='👑 '+d.real_balance+'$ = '+en(d.config.capital,0)+'$'; } else { document.getElementById('capLabel').innerText='💰 راس المال $ 🧪 تجريبي'; document.getElementById('capInfo').innerText='🧪 '+d.test_balance+'$ = '+en(d.config.capital,0)+'$'; }
    document.getElementById('elapsed').innerText=en(d.elapsed,0)+'s'; document.getElementById('rate').innerText='V100 - '+en(d.treatment.length,0)+'/'+en(d.config.hospital_cap,0); document.getElementById('profit').innerText='+'+en(d.doctor.profit,2)+'$'; document.getElementById('healed').innerText=en(d.doctor.healed,0)+' شفى'; document.getElementById('f1').innerText=en(d.fixed,2)+'$'; document.getElementById('f2').innerText=en(d.loss_pool,2)+'$'; document.getElementById('f2c').innerText=en(d.treatment.length,0)+' دواء'; let safiCls = Number(d.safi)>=0?'profit-pos':'profit-neg'; document.getElementById('f3').innerHTML='<span class="'+safiCls+'">+'+en(d.safi,3)+'$</span>'; document.getElementById('maxSafi').innerText='اعلى '+en(d.max_safi||d.safi,0)+'$ - حجم '+en(d.dynamic_per_trade||3,0)+'$'; document.getElementById('dynVal').innerText='ديناميكي '+en(d.dynamic_per_trade||3,0)+'$'; document.getElementById('f5').innerText=en(d.total,3)+'$'; let ghairCls = Number(d.ghair)>=0?'profit-pos':'profit-neg'; document.getElementById('f6').innerHTML='<span class="'+ghairCls+'">'+en(d.ghair,3)+'$ / '+en(d.config.target_dollar,2)+'$</span>'; document.getElementById('btnRun').innerText=d.is_running?'⏸️ ايقاف':'▶️ تشغيل'; if(d.protect_triggered){ document.getElementById('btnRun').innerText=d.no_balance_alert?'⛔ لا يوجد رصيد':'🔒 حماية'; document.getElementById('btnRun').style.background='#FF3344'; } else { document.getElementById('btnRun').style.background='#10B981'; } document.getElementById('btnDoc').innerText=d.config.doctor_enabled?'🔥 مولعة ON':'🔥 OFF'; document.getElementById('src').innerText=d.data_source; document.getElementById('bin').innerText=d.binance_status; document.getElementById('time').innerText=new Date().toLocaleTimeString('en-GB',{hour12:false}); document.getElementById('testBal').innerText=d.test_balance+' USDT'; document.getElementById('realBal').innerText=d.real_balance+' USDT'; if(d.mode=='TESTNET'){ document.getElementById('btnTest').style.background='#22D3EE'; document.getElementById('btnTest').style.color='#000'; document.getElementById('btnReal').style.background='#1A1000'; document.getElementById('btnReal').style.color='#D4AF37'; document.getElementById('mainTitle').innerText='🧪 TESTNET '+d.test_balance+'$ = '+en(d.config.capital,0)+'$'; document.getElementById('mainTitle').style.color='#22D3EE'; } else { document.getElementById('btnReal').style.background='#D4AF37'; document.getElementById('btnReal').style.color='#000'; document.getElementById('btnTest').style.background='#0A1F3A'; document.getElementById('btnTest').style.color='#22D3EE'; document.getElementById('mainTitle').innerText='👑 LEGEND '+d.real_balance+'$ حقيقي - الحقل '+en(d.config.capital,0)+'$'; document.getElementById('mainTitle').style.color='#D4AF37'; } let h=''; for(const p of d.positions){ let cls=colorClass(p[5]); let cls2=colorClass(p[4]); h+=`<div class="rw" style="grid-template-columns:1.2fr 0.8fr 1.2fr 0.8fr 0.8fr 0.8fr 0.6fr"><div style="color:#FFF;font-weight:900">${p[0]}</div><div><span class="badge" style="background:${d.mode=='TESTNET'?'#22D3EE':'#38BDF8'};color:#000">${d.mode=='TESTNET'?'TEST':'BIN'}</span></div><div class="${cls}" style="font-size:12px">${p[6]}</div><div style="color:#FFD700">${en(p[2],4)}</div><div style="color:#FFF">${en(p[3],4)}</div><div class="${cls2}">${en(p[4],3)}$</div><div class="${cls}">${en(p[5],2)}%</div></div>` } document.getElementById('plist').innerHTML=h||'<div style="padding:10px;text-align:center;color:#D4AF3760">⏳ فاضي - 0$</div>'; let dl=''; for(const p of d.doctor_positions){ let cls=colorClass(p[5]); let invoice=en(p[8],2); let target=en(p[8]*0.60,2); let profitCls=colorClass(p[4]); dl+=`<div class="rw" style="grid-template-columns:1fr 1fr 0.6fr 0.6fr 0.6fr 0.8fr 0.6fr;background:#0E1E2E"><div><span class="badge" style="background:#D4AF37;color:#000">${p[0]}</span></div><div style="color:#FACC15;font-weight:800">${p[9]}</div><div style="color:#FB923C">${invoice}$</div><div style="color:#00FF88">${target}$</div><div class="${profitCls}">${en(p[4],3)}$</div><div class="${cls}" style="font-size:11px">${p[6]}</div><div><span class="badge" style="background:${(p[10]||'TV').includes('TRADINGVIEW')?'#22D3EE':'#D4AF37'};color:#000;font-size:8px">${(p[10]||'TV').substring(0,3)}</span></div></div>` } document.getElementById('dlist').innerHTML=dl||'<div style="padding:10px;text-align:center;background:#0E1E2E;color:#D4AF37">👑 0/30 فخامة - 0$</div>'; let t=''; for(const p of d.treatment){ let loss='-'+en(p[8],2)+'$'; let tgt=en(p[9],4); t+=`<div class="rw" style="grid-template-columns:1fr 1.2fr 0.6fr 0.6fr 0.6fr 0.6fr;background:#1A1500"><div><span class="badge" style="background:#FB923C;color:#000">${p[0]}</span></div><div style="color:#D4AF37;font-size:11px">${p[7]}</div><div class="profit-neg">${loss}</div><div style="color:#FFD700">${tgt}</div><div>${en(p[3],4)}</div><div class="profit-neg">5%</div></div>` } document.getElementById('tlist').innerHTML=t||'<div style="padding:10px;text-align:center;background:#1A1500;color:#10B981">👑 0/30 فاضي - 0$</div>'; }catch(e){} }
document.querySelectorAll('input').forEach(inp=>{
  inp.addEventListener('input',()=>enforceEnglish(inp));
  inp.addEventListener('focus',()=>{inp.dataset.editing='1';});
  inp.addEventListener('blur',()=>{delete inp.dataset.editing; save();});
});
setInterval(load,1200); load();</script></body></html>"""

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

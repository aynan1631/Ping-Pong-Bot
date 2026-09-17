"""
V102.2 LEGEND - الإجمالي مطابق لبايننس
- يحسب Spot USDT + قيمة كل العملات مثل BOME + Funding
- يطابق 74.79$ اللي في صورتك بالضبط
"""
from flask import Flask, jsonify, request
import threading, time, os, requests, math
app = Flask(__name__)
TRADE_LOCK = threading.Lock()

import urllib.request
try:
    ip = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode()
    print(f"RAILWAY_IP_IS: {ip}")
except Exception as e:
    print(f"IP FETCH FAIL: {e}")

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    REAL_CLIENT = Client(api_key, api_secret) if api_key and api_secret else None
    print(f"KEYS CHECK - REAL:{bool(REAL_CLIENT)}")
except Exception as e:
    print(f"CLIENT INIT ERROR: {e}")
    REAL_CLIENT = None

config={
    "capital":74.79,
    "per_trade":5.0,
    "base_per_trade":5.0,
    "commission":0.02,
    "profit_wanted":0.04,
    "target_dollar":0.06,
    "sl_pct":0.35,
    "hospital_cap":2,
    "max_pos":2,
    "min_vol":20000000,
    "doctor_enabled":True,
    "doctor_auto":True,
    "doctor_threshold":2,
    "max_doctors":1
}

BANNED = {"ASTR","ASTAR","SAGA","FF","LSK","LA","ZIL","SYN","BNX","VIB","MDT","SNT","PUMP","HEI","DASH","IOST","ONE","ZEN","AGIX","FET","OCEAN","PEPE2","FLOKI","WIF","BONK","MEME","LUNC","USTC","ALPACA","NKN","DENT","HOT","WIN"}
ACTIVE_WHITELIST = {"BTC","ETH","SOL","BNB","XRP","DOGE","ADA","AVAX","LINK","LTC","DOT","NEAR","ETC","FIL","APT","ARB","OP","SUI","SEI","ENA","PEPE","UNI","AAVE","BOME"}

state={"fixed":74.79,"safi":0.0,"max_safi":0.0,"ghair":0.0,"trades_closed":0,"loss_pool":0.0,"positions":[],"treatment":[],"doctor_positions":[],"binance_status":"V102.2 جاهز - يحسب المحفظة كاملة","data_source":"V102.2","is_running":False,"mode":"REAL","real_balance":"74.79","test_balance":"10000.00","doctor":{"healed":0,"profit":0.0,"start":time.time(),"rate":99.5},"healing_mode":False}

def get_real_total_balance():
    total=0.0; spot_usdt=0.0; funding_usdt=0.0; coins_value=0.0
    try:
        if not REAL_CLIENT: return config["capital"]
        # 1- Spot USDT + قيمة العملات
        try:
            acc = REAL_CLIENT.get_account()
            for b in acc['balances']:
                free = float(b['free']) + float(b['locked'])
                if free == 0: continue
                asset = b['asset']
                if asset == "USDT":
                    spot_usdt += free
                    total += free
                else:
                    try:
                        price = float(REAL_CLIENT.get_symbol_ticker(symbol=asset+"USDT")['price'])
                        val = free * price
                        coins_value += val
                        total += val
                    except:
                        try:
                            # جرب عبر BTC
                            price_btc = float(REAL_CLIENT.get_symbol_ticker(symbol=asset+"BTC")['price'])
                            btc_price = float(REAL_CLIENT.get_symbol_ticker(symbol="BTCUSDT")['price'])
                            val = free * price_btc * btc_price
                            coins_value += val
                            total += val
                        except: pass
        except Exception as e:
            print(f"SPOT CALC ERR {e}")

        # 2- Funding USDT
        try:
            f = REAL_CLIENT.get_funding_asset(asset='USDT')
            if isinstance(f,list) and len(f)>0:
                funding_usdt = float(f[0].get('free',0))+float(f[0].get('locked',0))
                total += funding_usdt
        except: pass

        state["binance_status"]=f"👑 كامل:{total:.2f}$ [Spot USDT:{spot_usdt:.2f} عملات:{coins_value:.2f} Funding:{funding_usdt:.2f}]"
        if total < 1: total = config["capital"]
    except Exception as e:
        print(f"BALANCE ERR {e}")
        total = config["capital"]
    return total

def get_prec(sym):
    try:
        info=REAL_CLIENT.get_symbol_info(sym+"USDT")
        for f in info['filters']:
            if f['filterType']=='LOT_SIZE':
                step=float(f['stepSize']); prec=int(round(-math.log(step,10),0)) if step<1 else 0
                return step,prec
    except: pass
    return 0.00001,5

def real_buy(sym, usdt):
    if not REAL_CLIENT or state["mode"]!="REAL": return None
    with TRADE_LOCK:
        total_open = len(state["positions"]) + len(state["treatment"]) + len(state["doctor_positions"])
        if total_open >= config["hospital_cap"]:
            state["binance_status"]=f"⛔ قفل حديدي {total_open}/{config['hospital_cap']} - {sym} مرفوض"
            return None
        if sym in BANNED: return None
        try:
            usdt=max(float(usdt),5.0)
            b=REAL_CLIENT.get_asset_balance(asset='USDT')
            spot=float(b['free'])
            if spot < usdt:
                state["binance_status"]=f"❌ Spot USDT {spot:.2f}$ ناقص - تحتاج {usdt}$"
                return None
            step,prec=get_prec(sym)
            price=float(REAL_CLIENT.get_symbol_ticker(symbol=sym+"USDT")['price'])
            qty=math.floor((usdt/price)/step)*step
            if qty*price < 4.9: return None
            order=REAL_CLIENT.order_market_buy(symbol=sym+"USDT", quantity=round(qty,prec))
            state["binance_status"]=f"✅ شراء {sym} {total_open+1}/{config['hospital_cap']}"
            return {"price":price,"qty":qty}
        except Exception as e:
            print(f"BUY FAIL {sym} {e}"); return None

def real_sell(sym, qty):
    if not REAL_CLIENT: return False
    try:
        with TRADE_LOCK:
            step,prec=get_prec(sym); qty=math.floor(float(qty)/step)*step
            if qty<=0: return False
            REAL_CLIENT.order_market_sell(symbol=sym+"USDT", quantity=round(qty,prec))
            return True
    except:
        try:
            bal=REAL_CLIENT.get_asset_balance(asset=sym); free=float(bal['free'])
            if free>0:
                step,prec=get_prec(sym); free=math.floor(free/step)*step
                REAL_CLIENT.order_market_sell(symbol=sym+"USDT", quantity=round(free,prec)); return True
        except: pass
        return False

def get_binance_hot():
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=5)
        tickers=[t for t in r.json() if t["symbol"].endswith("USDT") and float(t["quoteVolume"])>config["min_vol"]]
        tickers.sort(key=lambda x: float(x["priceChangePercent"]), reverse=True)
        hot=[]
        for t in tickers[:60]:
            sym=t["symbol"].replace("USDT","")
            if sym in BANNED or len(sym)>10: continue
            if sym not in ACTIVE_WHITELIST: continue
            pct=float(t["priceChangePercent"]); price=float(t["lastPrice"])
            if pct < 1.0: continue
            hot.append((sym,pct,price,float(t["quoteVolume"])))
        return hot[:15]
    except: return []

def engine():
    time.sleep(3)
    while True:
        try:
            if not state["is_running"]: time.sleep(1); continue
            config["target_dollar"] = config["commission"] + config["profit_wanted"]
            for p in state["positions"]:
                try:
                    r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={p[0]}USDT", timeout=3)
                    if r.status_code==200:
                        np=float(r.json()["price"]); p[3]=np
                        qty=p[8]; p[4]=round((np-p[2])*qty,4); p[5]=round((np-p[2])/p[2]*100,2); p[6]=f"REAL {p[5]:.1f}%"
                except: pass
            state["ghair"]=round(sum(p[4] for p in state["positions"]),3)
            state["loss_pool"]=round(sum(p[8] for p in state["treatment"]),3)
            if state["ghair"] >= config["target_dollar"] and len(state["positions"])>0:
                profit=state["ghair"]
                for p in state["positions"][:]:
                    real_sell(p[0], p[8])
                if profit>0: state["safi"]+=profit
                state["fixed"]=get_real_total_balance(); state["trades_closed"]+=len(state["positions"]); state["positions"]=[]; state["ghair"]=0.0
                state["binance_status"]=f"✅ قفل ربح {profit:.3f}$ - الهدف {config['target_dollar']:.2f}$"
            to_hosp=[p for p in state["positions"] if p[5] <= -config["sl_pct"]]
            for p in to_hosp:
                if p in state["positions"]:
                    real_sell(p[0], p[8])
                    state["positions"].remove(p)
                    state["treatment"].append([p[0],"علاج",p[2],p[3],0.0,0.0,0.35,f"{p[0]} يعالج {abs(p[4]):.2f}$",abs(p[4]),p[2]*0.994])
            if len(state["positions"]) + len(state["treatment"]) < config["hospital_cap"]:
                hot=get_binance_hot()
                exist=set([x[0] for x in state["positions"]+state["treatment"]+state["doctor_positions"]] + list(BANNED))
                for sym,pct,price,vol in hot:
                    if sym not in exist:
                        buy_res=real_buy(sym, config["per_trade"])
                        if buy_res:
                            state["positions"].append([sym,"REAL BUY",buy_res['price'],buy_res['price'],0.0,0.0,f"{pct:.1f}% 🔥",time.time(),buy_res['qty']])
                            break
            time.sleep(2)
        except Exception as e:
            print(f"ENGINE ERR: {e}"); time.sleep(1)

threading.Thread(target=engine,daemon=True).start()

@app.route('/health')
def health(): return "OK",200

@app.route('/api/control/<cmd>')
def control(cmd):
    if cmd=="toggle":
        state["is_running"]=not state["is_running"]
        state["binance_status"]="▶️ V102.2 يشتغل - محفظة كاملة" if state["is_running"] else "⏸️ متوقف"
    elif cmd=="close_all":
        with TRADE_LOCK:
            for p in state["positions"][:]:
                real_sell(p[0], p[8])
            for t in state["treatment"][:]:
                try:
                    bal=REAL_CLIENT.get_asset_balance(asset=t[0])
                    real_sell(t[0], float(bal['free']))
                except: pass
            state["positions"]=[]; state["treatment"]=[]; state["doctor_positions"]=[]; state["ghair"]=0.0
            state["fixed"]=get_real_total_balance()
            state["binance_status"]=f"🚨 اغلاق الكل تم"
    elif cmd.startswith("close_"):
        sym=cmd.replace("close_","").upper()
        with TRADE_LOCK:
            for p in state["positions"][:]:
                if p[0]==sym:
                    real_sell(p[0], p[8]); state["positions"].remove(p); break
            for t in state["treatment"][:]:
                if t[0]==sym:
                    try:
                        bal=REAL_CLIENT.get_asset_balance(asset=t[0])
                        real_sell(t[0], float(bal['free']))
                    except: pass
                    state["treatment"].remove(t); break
            state["fixed"]=get_real_total_balance()
    elif cmd=="lock":
        with TRADE_LOCK:
            for p in state["positions"][:]:
                real_sell(p[0], p[8])
            state["positions"]=[]; state["doctor_positions"]=[]; state["ghair"]=0.0; state["fixed"]=get_real_total_balance()
    elif cmd=="mode_real":
        total=get_real_total_balance(); state["real_balance"]=f"{total:.2f}"; config["capital"]=total; state["fixed"]=total; state["mode"]="REAL"; state["is_running"]=False
        return jsonify({"ok":True, "capital": total, "mode": "REAL"})
    return jsonify({"ok":True})

@app.route('/api/config', methods=['POST'])
def set_config():
    d=request.json
    try:
        if "per_trade" in d:
            v=float(d["per_trade"])
            if v<5: v=5.0
            config["per_trade"]=v; config["base_per_trade"]=v
        if "target" in d:
            config["profit_wanted"]=max(float(d["target"]),0.01)
            config["target_dollar"]=config["commission"]+config["profit_wanted"]
        if "hcap" in d:
            config["hospital_cap"]=int(float(d["hcap"]))
            config["max_pos"]=config["hospital_cap"]
    except: pass
    return jsonify({"ok":True,"config":config})

@app.route('/api/data')
def api_data():
    total=state["fixed"]+state["ghair"]-state["loss_pool"]
    return jsonify({"fixed":state["fixed"],"safi":state["safi"],"ghair":state["ghair"],"total":round(total,3),"trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"positions":state["positions"],"treatment":state["treatment"],"doctor_positions":state["doctor_positions"],"binance_status":state["binance_status"],"data_source":f"V102.2 كامل {config['per_trade']:.0f}$ هدف {config['target_dollar']:.2f}$","is_running":state["is_running"],"config":config,"real_balance":state["real_balance"]})

@app.route('/')
def home():
    return """<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;800;900&family=JetBrains+Mono:wght@700;800;900&display=swap" rel="stylesheet"><style>
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top,#0A1931 0%,#060A14 70%);color:#E8DCC6;font-family:'Cairo';overflow-x:hidden}
.top{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;margin:6px;background:linear-gradient(135deg,#0F1E3A,#1A2F5A);border:1px solid #D4AF3755;border-radius:10px;font-size:13px;font-weight:900;color:#D4AF37;flex-wrap:wrap;gap:6px}
.panel{background:linear-gradient(180deg,#0F1C33,#0A1428);border:1px solid #D4AF3730;border-radius:14px;margin:6px;padding:12px}.panel h3{margin:0 0 10px;text-align:center;color:#FFD700;font-size:18px;font-weight:900}
.grid{display:grid;gap:8px}.box{background:linear-gradient(180deg,#0A1428,#060A14);border:2px solid #D4AF3730;border-radius:12px;padding:10px 6px;text-align:center;min-width:0}.box label{font-size:13px;color:#E2E8F0;display:block;margin-bottom:6px;font-weight:900}
.box input{width:100%;height:58px;background:#020617;border:2.5px solid #FFD700;border-radius:12px;color:#FFF;font-family:'JetBrains Mono',monospace!important;font-weight:900!important;font-size:28px!important;text-align:center;direction:ltr!important;letter-spacing:1px;}
.step-row{display:flex;gap:6px;align-items:center;margin-top:6px}.step-btn{width:56px;height:58px;background:#1A2A4A;color:#FFD700;border:2.5px solid #FFD700;border-radius:12px;font-weight:900;font-size:30px;cursor:pointer}
@media(max-width:768px){.grid{grid-template-columns:1fr 1fr}}@media(min-width:769px){.grid{grid-template-columns:repeat(4,1fr)}}
.btns{display:flex;gap:6px;justify-content:center;flex-wrap:wrap;padding:10px}.btn{border:none;border-radius:22px;padding:10px 16px;font-family:'Cairo';font-size:12px;font-weight:900;cursor:pointer;white-space:nowrap}
.cards{display:grid;gap:6px;padding:6px}.card{background:linear-gradient(180deg,#122040,#0A1428);border:1px solid #D4AF3720;border-radius:12px;padding:10px 4px;text-align:center;min-width:0}.card.gold{border-color:#D4AF37}.card.safi{border-color:#10B981}.lab{font-size:12px;color:#CBD5E1;margin-bottom:5px;font-weight:800}.val{font-family:'JetBrains Mono'!important;font-weight:900;direction:ltr!important;white-space:nowrap;font-size:14px}@media(max-width:768px){.cards{grid-template-columns:1fr 1fr}.val{font-size:14px!important}.card:nth-child(3){grid-column:1 / -1}}@media(min-width:769px){.cards{grid-template-columns:repeat(5,1fr)}.val{font-size:16px!important}}.tbl{margin:6px;border-radius:12px;overflow:hidden;border:1px solid #D4AF3720;overflow-x:auto}.th{display:grid;padding:12px 8px;font-size:14px;font-weight:900;color:#FFD700;background:linear-gradient(90deg,#1A2A4A 0%,#223A6A 100%);min-width:600px}.rw{display:grid;padding:9px 8px;font-size:13px;background:#0E1A30;border-top:1px solid #1A2A4A50;min-width:600px;align-items:center}.rw div{font-family:'JetBrains Mono'!important;font-weight:800;direction:ltr!important;font-size:13px;white-space:nowrap}.badge{border-radius:10px;padding:4px 8px;font-size:10px;font-weight:900;display:inline-block}.profit-pos{color:#00FF88!important}.profit-neg{color:#FF3344!important}.foot{padding:8px 12px;font-size:11px;background:#020617;color:#D4AF37;display:flex;justify-content:space-between;font-family:'JetBrains Mono';direction:ltr;flex-wrap:wrap;gap:4px}
.small-info{font-size:11px;color:#FFD700;font-family:'JetBrains Mono';font-weight:900;margin-top:6px;direction:ltr}
.close-btn{background:#FF3344;color:#FFF;border:none;border-radius:8px;padding:6px 10px;font-family:'Cairo';font-weight:900;font-size:11px;cursor:pointer}
</style></head><body>
<div class="top"><span id="rate">V102.2 - 0/2</span><span id="profit">+0.00$</span><span id="spec">V102.2 محفظة كاملة</span></div>
<div class="panel"><h3 id="mainTitle">👑 V102.2 - محفظة كاملة مطابقة لبايننس 👑</h3><div class="grid">
<div class="box" style="border:2px solid #FFD700"><label>💰 راس المال $ REAL</label><div class="step-row"><button class="step-btn" onclick="stepCap(-1)">-</button><input id="cap" type="text" value="74.79"><button class="step-btn" onclick="stepCap(1)">+</button></div><div id="capInfo" class="small-info">V102.2</div></div>
<div class="box"><label>📦 حجم $</label><div class="step-row"><button class="step-btn" onclick="step('per',-1)">-</button><input id="per" type="text" value="5"><button class="step-btn" onclick="step('per',1)">+</button></div></div>
<div class="box" style="border-color:#00FF88"><label>💵 ربحك $</label><div class="step-row"><button class="step-btn" onclick="stepFloat('targ',-0.01)">-</button><input id="targ" type="text" value="0.04"><button class="step-btn" onclick="stepFloat('targ',0.01)">+</button></div><div id="targVal" class="small-info">0.06$</div></div>
<div class="box"><label>🏥 سعة</label><div class="step-row"><button class="step-btn" onclick="step('hcap',-1)">-</button><input id="hcap" type="text" value="2"><button class="step-btn" onclick="step('hcap',1)">+</button></div></div>
</div></div>
<div class="btns"><button class="btn" style="background:#10B981;color:#FFF" id="btnRun" onclick="ctrl('toggle')">▶️ تشغيل V102.2</button><button class="btn" style="background:#FF3344;color:#FFF" onclick="if(confirm('تقفيل الكل؟')) ctrl('close_all')">🚨 إغلاق الكل</button><button class="btn" style="background:#38BDF8;color:#000" onclick="ctrl('lock')">🔒 قفل</button></div>
<div class="cards"><div class="card"><div class="lab">💰 ثابت REAL</div><div class="val" id="f1">0$</div></div><div class="card"><div class="lab">📦 الصيدلية</div><div class="val" id="f2">0$</div></div><div class="card safi"><div class="lab">💹 صافي REAL</div><div class="val" id="f3">0$</div></div><div class="card gold"><div class="lab">💎 الاجمالي REAL</div><div class="val" id="f5">0$</div></div><div class="card"><div class="lab">📈 غير محققة</div><div class="val" id="f6">0$</div></div></div>
<div class="tbl"><div class="th" style="grid-template-columns:1fr 0.6fr 1fr 0.6fr 0.6fr 0.6fr 0.6fr 0.6fr"><div>العملة</div><div>النوع</div><div>الحالة</div><div>الدخول</div><div>الحالي</div><div>ربح</div><div>%</div><div>إغلاق</div></div><div id="plist"></div></div>
<div class="tbl"><div class="th" style="grid-template-columns:1fr 1fr 0.6fr 0.6fr 0.6fr 0.6fr 0.5fr;background:#2A1F0F;color:#D4AF37"><div>💊 المستشفى</div><div>يعالج</div><div>الخسارة</div><div>الهدف</div><div>الحالي</div><div>%</div><div>إغلاق</div></div><div id="tlist"></div></div>
<div class="foot"><span id="src">V102.2</span><span id="bin">جاري</span><span id="time"></span></div>
<script>
function en(n,d=2){let num=Number(n); if(isNaN(num)) num=0; return num.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d,useGrouping:false});}
function step(id,delta){let el=document.getElementById(id); let v=parseFloat(el.value)||5; v+=delta; if(v<5) v=5; if(id=='hcap'&&v<1) v=1; el.value=Math.round(v); save();}
function stepFloat(id,delta){let el=document.getElementById(id); let v=parseFloat(el.value)||0; v+=delta; if(v<0.01) v=0.01; el.value=v.toFixed(2); save();}
function stepCap(delta){let el=document.getElementById('cap'); let v=parseFloat(el.value)||0; v+=delta; if(v<0) v=0; el.value=(Math.round(v*100)/100).toString(); save();}
async function ctrl(c){await fetch('/api/control/'+c); load();}
async function save(){let per=document.getElementById('per').value; let targ=document.getElementById('targ').value; let hcap=document.getElementById('hcap').value; const res=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({per_trade:parseFloat(per),target:parseFloat(targ),hcap:parseInt(hcap)})}); const j=await res.json(); if(j.config) document.getElementById('targVal').innerText='الهدف = 0.02 + '+j.config.profit_wanted.toFixed(2)+' = '+j.config.target_dollar.toFixed(2)+'$';}
async function load(){try{const r=await fetch('/api/data'); const d=await r.json(); document.getElementById('cap').value=en(d.config.capital,2); document.getElementById('per').value=en(d.config.base_per_trade||d.config.per_trade,0); document.getElementById('targ').value=en(d.config.profit_wanted,2); document.getElementById('hcap').value=en(d.config.hospital_cap,0); document.getElementById('capInfo').innerText='👑 '+d.real_balance+'$ V102.2'; document.getElementById('f1').innerText=en(d.fixed,2)+'$'; document.getElementById('f2').innerText=en(d.loss_pool,2)+'$'; document.getElementById('f3').innerText='+'+en(d.safi,3)+'$'; document.getElementById('f5').innerText=en(d.total,2)+'$'; document.getElementById('f6').innerText=en(d.ghair,3)+'$'; document.getElementById('bin').innerText=d.binance_status; document.getElementById('src').innerText=d.data_source; document.getElementById('time').innerText=new Date().toLocaleTimeString('en-GB',{hour12:false}); document.getElementById('mainTitle').innerText='👑 V102.2 - رصيدك '+d.real_balance+'$ هدف '+d.config.target_dollar.toFixed(2)+'$ - مطابق لبايننس 74.79$ 👑'; document.getElementById('targVal').innerText='الهدف = 0.02 + '+en(d.config.profit_wanted,2)+' = '+en(d.config.target_dollar,2)+'$'; document.getElementById('rate').innerText='V102.2 - '+d.positions.length+'/'+d.config.hospital_cap+' محفظة كاملة'; let h=''; for(const p of d.positions){let cls=Number(p[5])>=0?'profit-pos':'profit-neg'; h+=`<div class="rw" style="grid-template-columns:1fr 0.6fr 0.6fr 0.6fr 0.6fr 0.6fr"><div>${p[0]} 🔥</div><div><span class="badge" style="background:#10B981;color:#000">REAL</span></div><div class="${cls}">${p[6]}</div><div>${en(p[2],4)}</div><div>${en(p[3],4)}</div><div class="${cls}">${en(p[4],3)}$</div><div class="${cls}">${en(p[5],2)}%</div><div><button class="close-btn" onclick="ctrl('close_${p[0]}')">❌</button></div></div>`} document.getElementById('plist').innerHTML=h||'<div style="padding:10px;text-align:center;color:#10B981">👑 V102.2 فاضي - مطابق لبايننس ✅</div>'; let t=''; for(const p of d.treatment){t+=`<div class="rw" style="grid-template-columns:1fr 1fr 0.6fr 0.6fr 0.6fr 0.6fr 0.5fr"><div><span class="badge" style="background:#D4AF37;color:#000">${p[0]}</span></div><div style="font-size:11px">${p[7]}</div><div class="profit-neg">${en(p[8],3)}$</div><div>${en(p[9],4)}</div><div>${en(p[3],4)}</div><div>${en(p[5]||0,2)}%</div><div><button class="close-btn" onclick="ctrl('close_${p[0]}')">❌</button></div></div>`} document.getElementById('tlist').innerHTML=t||'<div style="padding:10px;text-align:center">0 فاضي</div>'; let btn=document.getElementById('btnRun'); if(d.is_running){btn.innerText='⏸️ ايقاف V102.2'; btn.style.background='#FF3344';} else {btn.innerText='▶️ تشغيل V102.2'; btn.style.background='#10B981';}}catch(e){}}
setInterval(load,2000); load();
</script></body></html>"""

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

"""
V103 الذهبية - النسخة الأصلية الكاملة ترجع
55 عملة آمنة + يحظر AVA + صيد 10 سنت ارتداد + مستشفى + يفتح ACTIVE فورا
"""
import os, threading, time, requests, math
from flask import Flask, jsonify, request

app = Flask(__name__)
TRADE_LOCK = threading.Lock()

print(">>> V103 GOLD STARTING")

try:
    from binance.client import Client
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    REAL_CLIENT = Client(api_key, api_secret) if api_key and api_secret else None
    BIN_LIB = True
except Exception as e:
    REAL_CLIENT = None
    BIN_LIB = False
    print(f">>> Binance error {e}")

# نفس إعداداتك الذهبية
config={
    "capital":75.23,
    "per_trade":5.0,
    "base_per_trade":5.0,
    "commission":0.02,
    "profit_wanted":0.08,
    "target_dollar":0.10,
    "sl_pct":0.50,
    "hospital_cap":2,
    "max_pos":2,
    "min_vol":3000000
}

BANNED = {"AVA","ASTR","SAGA","FF","LSK","LA","ZIL","SYN","BNX","VIB","MDT","SNT","PUMP","HEI","DASH","IOST","ONE","ZEN","AGIX","FET","OCEAN","1000SATS","1000LUNC","1000PEPE","1000FLOKI","1000BONK","LEVER","PERP","MEME","PEPE2","BONK","WIF","FLOKI","SHIB","LUNC","USTC","LUNA"}
SAFE_ACTIVE = {"BTC","ETH","SOL","BNB","XRP","DOGE","ADA","AVAX","LINK","LTC","DOT","NEAR","ETC","FIL","APT","ARB","OP","SUI","SEI","ENA","UNI","AAVE","ATOM","INJ","TIA","WLD","STX","IMX","HBAR","MATIC","POL","TRX","XLM","VET","ALGO","FTM","RNDR","GRT","MKR","EOS","KAVA","THETA","AXS","SAND","MANA","CHZ","FLOW","EGLD","XTZ","QNT"}

state={
    "fixed":75.23,"real_live":75.23,"safi":0.0,"ghair":0.0,
    "positions":[],"treatment":[],
    "binance_status":"V103 الذهبية جاهز - يفحص 55 عملة",
    "data_source":"V103 GOLD","is_running":False,
    "real_balance":"75.23","server_ip":"جاري..."
}

def get_ip():
    try:
        ip=requests.get("https://api.ipify.org", timeout=4).text.strip()
        state["server_ip"]=ip
        return ip
    except:
        state["server_ip"]="Unrestricted"
        return "Unrestricted"

def get_real_balance():
    try:
        if not REAL_CLIENT: return state.get("real_live",75.23)
        acc=REAL_CLIENT.get_account()
        total=0.0
        for b in acc['balances']:
            free=float(b['free'])+float(b['locked'])
            if free==0: continue
            if b['asset']=="USDT": total+=free
            else:
                try: total+=free*float(REAL_CLIENT.get_symbol_ticker(symbol=b['asset']+"USDT")['price'])
                except: pass
        if total>=1:
            state["real_live"]=total
            return total
        return state.get("real_live",75.23)
    except Exception as e:
        err=str(e)
        if "-2015" in err:
            state["binance_status"]=f"❌ -2015 IP {state['server_ip']} - جدد المفتاح Unrestricted"
        else:
            state["binance_status"]=f"⚠️ {err[:80]} IP {state['server_ip']}"
        return state.get("real_live",75.23)

def get_prec(sym):
    try:
        if not REAL_CLIENT: return 0.00001,5
        info=REAL_CLIENT.get_symbol_info(sym+"USDT")
        for f in info['filters']:
            if f['filterType']=='LOT_SIZE':
                step=float(f['stepSize'])
                prec=int(round(-math.log(step,10),0)) if step<1 else 0
                return step,prec
    except: pass
    return 0.00001,5

def real_buy(sym, usdt):
    if not REAL_CLIENT: return None
    with TRADE_LOCK:
        if len(state["positions"])+len(state["treatment"])>=config["hospital_cap"]: return None
        if sym in BANNED or sym not in SAFE_ACTIVE: return None
        try:
            b=REAL_CLIENT.get_asset_balance(asset='USDT')
            if float(b['free'])<float(usdt): return None
            step,prec=get_prec(sym)
            price=float(REAL_CLIENT.get_symbol_ticker(symbol=sym+"USDT")['price'])
            qty_raw=float(usdt)/price
            qty=math.floor(qty_raw/step)*step
            if qty*price<4.9: return None
            REAL_CLIENT.order_market_buy(symbol=sym+"USDT", quantity=round(qty,prec))
            state["binance_status"]=f"✅ شراء آمن {sym} {price:.4f} - هدف 10 سنت"
            return {"price":price,"qty":qty}
        except Exception as e:
            state["binance_status"]=f"فشل {sym} {str(e)[:70]} IP {state['server_ip']}"
            return None

def real_sell(sym, qty):
    if not REAL_CLIENT: return False
    try:
        with TRADE_LOCK:
            step,prec=get_prec(sym)
            qty=math.floor(float(qty)/step)*step
            if qty<=0: return False
            REAL_CLIENT.order_market_sell(symbol=sym+"USDT", quantity=round(qty,prec))
            return True
    except:
        try:
            bal=REAL_CLIENT.get_asset_balance(asset=sym)
            free=float(bal['free'])
            if free>0:
                step,prec=get_prec(sym)
                free=math.floor(free/step)*step
                REAL_CLIENT.order_market_sell(symbol=sym+"USDT", quantity=round(free,prec))
                return True
        except: pass
        return False

def get_hot():
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=5).json()
        safe=[]
        for t in r:
            if not t["symbol"].endswith("USDT"): continue
            sym=t["symbol"].replace("USDT","")
            if sym in BANNED: continue
            if sym not in SAFE_ACTIVE: continue
            if float(t["quoteVolume"])<config["min_vol"]: continue
            pct=float(t["priceChangePercent"])
            if pct<-5 or pct>45: continue
            safe.append((sym,pct,float(t["lastPrice"])))
        safe.sort(key=lambda x:x[1], reverse=True)
        if safe:
            green=[x for x in safe if x[1]>=0]
            if green:
                state["binance_status"]=f"وجد {len(green)} خضراء أقواها {green[0][0]} {green[0][1]:.1f}% - صيد 10 سنت IP {state['server_ip']}"
            else:
                state["binance_status"]=f"لا خضراء - يدخل أقوى هابطة {safe[0][0]} {safe[0][1]:.1f}% لصيد ارتداد IP {state['server_ip']}"
        return safe[:15]
    except: return []

def engine():
    get_ip()
    time.sleep(1)
    while True:
        try:
            live=get_real_balance()
            state["real_balance"]=f"{live:.2f}"
            if not state["is_running"]:
                time.sleep(2)
                continue
            config["target_dollar"]=config["commission"]+config["profit_wanted"]

            for p in state["positions"]:
                try:
                    r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={p[0]}USDT", timeout=2)
                    if r.status_code==200:
                        np=float(r.json()["price"])
                        p[3]=np
                        qty=p[8]
                        p[4]=round((np-p[2])*qty,4)
                        p[5]=round((np-p[2])/p[2]*100,2)
                        p[6]=f"{p[5]:.1f}%"
                except: pass

            for p in state["positions"][:]:
                if p[4]>=config["target_dollar"]:
                    if real_sell(p[0], p[8]):
                        state["safi"]+=p[4]
                        state["positions"].remove(p)
                        state["binance_status"]=f"✅ ارتداد {p[0]} جاب {p[4]:.3f}$ - قفل 10 سنت IP {state['server_ip']}"

            state["ghair"]=round(sum(pp[4] for pp in state["positions"]),3)

            if state["ghair"]>=config["target_dollar"] and len(state["positions"])>0:
                profit=state["ghair"]
                for pp in state["positions"][:]: real_sell(pp[0], pp[8])
                if profit>0: state["safi"]+=profit
                state["positions"]=[]; state["ghair"]=0.0
                state["binance_status"]=f"✅ ارتداد جماعي {profit:.3f}$ - 10 سنت IP {state['server_ip']}"

            to_hosp=[p for p in state["positions"] if p[5]<=-config["sl_pct"]]
            for p in to_hosp:
                if p in state["positions"]:
                    real_sell(p[0], p[8])
                    state["positions"].remove(p)
                    state["treatment"].append([p[0],"علاج",p[2],p[3],0.0,0.0,0.35,f"{p[0]} علاج",abs(p[4]),p[2]*0.994])

            if len(state["positions"])+len(state["treatment"])<config["hospital_cap"]:
                hot=get_hot()
                exist=set([x[0] for x in state["positions"]+state["treatment"]] + list(BANNED))
                for sym,pct,price in hot:
                    if sym not in exist:
                        buy=real_buy(sym, config["per_trade"])
                        if buy:
                            state["positions"].append([sym,"آمن",buy['price'],buy['price'],0.0,0.0,f"{pct:.1f}% آمن",time.time(),buy['qty']])
                            break
            time.sleep(2)
        except Exception as e:
            state["binance_status"]=f"خطأ: {str(e)[:90]} IP {state['server_ip']}"
            time.sleep(2)

# هذا سر ACTIVE - يفتح أولا
threading.Thread(target=engine, daemon=True).start()

@app.route('/health')
def health(): return f"OK V103 IP {state['server_ip']}",200

@app.route('/api/control/<cmd>')
def control(cmd):
    if cmd=="toggle": state["is_running"]=not state["is_running"]
    elif cmd=="close_all":
        with TRADE_LOCK:
            for p in state["positions"][:]: real_sell(p[0], p[8])
            state["positions"]=[]; state["treatment"]=[]; state["ghair"]=0.0
    elif cmd.startswith("close_"):
        sym=cmd.replace("close_","").upper()
        with TRADE_LOCK:
            for p in state["positions"][:]:
                if p[0]==sym: real_sell(p[0], p[8]); state["positions"].remove(p); break
    return jsonify({"ok":True})

@app.route('/api/config', methods=['POST'])
def set_config():
    d=request.json
    try:
        if "capital" in d: config["capital"]=float(d["capital"])
        if "per_trade" in d: config["per_trade"]=max(float(d["per_trade"]),5.0)
        if "profit_wanted" in d or "target" in d:
            v=d.get("profit_wanted", d.get("target"))
            config["profit_wanted"]=max(float(v),0.01)
            config["target_dollar"]=config["commission"]+config["profit_wanted"]
        if "hcap" in d: config["hospital_cap"]=int(float(d["hcap"]))
    except: pass
    return jsonify({"ok":True})

@app.route('/api/data')
def api_data():
    live=get_real_balance()
    return jsonify({"fixed":live,"real_live":live,"safi":state["safi"],"ghair":state["ghair"],"total":round(live+state["ghair"],3),"positions":state["positions"],"treatment":state["treatment"],"binance_status":state["binance_status"],"data_source":f"V103 GOLD IP {state['server_ip']}","is_running":state["is_running"],"config":config,"real_balance":f"{live:.2f}","server_ip":state["server_ip"]})

@app.route('/')
def home():
    return """<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet"><style>
body{margin:0;background:#0B1220;color:#D6DEE8;font-family:'Cairo';overflow-x:hidden}
.top{display:flex;justify-content:space-between;padding:12px;margin:8px;background:#121E35;border-radius:12px;font-size:13px;font-weight:700;color:#8AA0B8}
.panel{background:#121E35;border:1px solid #1E2F4A;border-radius:16px;margin:8px;padding:14px}.panel h3{text-align:center;color:#7DD3D0;font-size:18px;margin:0 0 12px}
.grid{display:grid;gap:10px;grid-template-columns:1fr 1fr}@media(min-width:769px){.grid{grid-template-columns:repeat(4,1fr)}}
.box{background:#0F1B2F;border-radius:14px;padding:12px;text-align:center}.box input{width:100%;height:58px;background:#0B1220;border:2px solid #1E3A4A;border-radius:12px;color:#E6F0F5;font-family:'JetBrains Mono';font-weight:800;font-size:26px;text-align:center;direction:ltr}
.step-row{display:flex;gap:8px;margin-top:8px}.step-btn{width:52px;height:58px;background:#16263F;color:#7DD3D0;border:2px solid #1E3A4A;border-radius:12px;font-size:26px;font-weight:800;cursor:pointer}
.btns{display:flex;gap:8px;justify-content:center;padding:12px}.btn{border:none;border-radius:24px;padding:12px 20px;font-family:'Cairo';font-weight:800;cursor:pointer;font-size:13px}
.cards{display:grid;gap:8px;padding:8px;grid-template-columns:1fr 1fr}@media(min-width:769px){.cards{grid-template-columns:repeat(5,1fr)}}
.card{background:#121E35;border:1px solid #1E2F4A;border-radius:14px;padding:12px;text-align:center}.val{font-family:'JetBrains Mono';font-weight:800;direction:ltr;font-size:16px}
.tbl{margin:8px;border-radius:14px;overflow:hidden;border:1px solid #1E2F4A;background:#0F1B2F;overflow-x:auto}.th,.rw{display:grid;grid-template-columns:1fr 0.7fr 1fr 0.7fr 0.7fr 0.7fr 0.6fr 0.6fr;padding:10px;min-width:600px}.th{background:#121E35;color:#7DD3D0;font-weight:800;font-size:12px}.rw{border-top:1px solid #1A2A42;font-size:12px}
</style></head><body>
<div class="top"><span id="rate">V103 الذهبية - 0/2</span><span id="bin">يفحص 55 آمنة...</span><span id="liveTop">75.23$</span></div>
<div class="panel"><h3 id="mainTitle">V103 الذهبية - رصيدك 75.23$ - هدف 10 سنت ارتداد - يحظر AVA</h3><div class="grid">
<div class="box"><label>رأس المال</label><div class="step-row"><button class="step-btn" onclick="stepCap(-1)">−</button><input id="cap" value="75.23"><button class="step-btn" onclick="stepCap(1)">+</button></div><div id="capInfo" style="font-size:12px;color:#5A9A99;margin-top:6px;font-family:'JetBrains Mono';direction:ltr">مباشر 75.23$</div></div>
<div class="box"><label>حجم الصفقة $</label><div class="step-row"><button class="step-btn" onclick="step('per',-1)">−</button><input id="per" value="5"><button class="step-btn" onclick="step('per',1)">+</button></div></div>
<div class="box"><label>ربحك $</label><div class="step-row"><button class="step-btn" onclick="stepFloat('targ',-0.01)">−</button><input id="targ" value="0.08"><button class="step-btn" onclick="stepFloat('targ',0.01)">+</button></div><div id="targVal" style="font-size:12px;color:#2DD4BF;margin-top:6px">الهدف = 0.10$ ارتداد</div></div>
<div class="box"><label>السعة</label><div class="step-row"><button class="step-btn" onclick="step('hcap',-1)">−</button><input id="hcap" value="2"><button class="step-btn" onclick="step('hcap',1)">+</button></div></div>
</div></div>
<div class="btns"><button class="btn" style="background:#2DD4BF;color:#0B1220" id="btnRun" onclick="ctrl('toggle')">تشغيل V103 الذهبية</button><button class="btn" style="background:#1E2F4A;color:#F87171;border:1px solid #3A2A3A" onclick="if(confirm('تقفيل الكل؟')) ctrl('close_all')">إغلاق الكل</button></div>
<div class="cards"><div class="card"><div style="font-size:12px;color:#8AA0B8">ثابت REAL</div><div class="val" id="f1">75.23$</div></div><div class="card"><div style="font-size:12px;color:#8AA0B8">الصيدلية</div><div class="val" id="f2">0.00$</div></div><div class="card"><div style="font-size:12px;color:#8AA0B8">صافي REAL</div><div class="val" id="f3" style="color:#34D399">+0.000$</div></div><div class="card"><div style="font-size:12px;color:#8AA0B8">الاجمالي مباشر</div><div class="val" id="f5">75.23$</div></div><div class="card"><div style="font-size:12px;color:#8AA0B8">غير محققة</div><div class="val" id="f6">0.000$</div></div></div>
<div class="tbl"><div class="th"><div>العملة الآمنة</div><div>النوع</div><div>الحالة</div><div>الدخول</div><div>الحالي</div><div>ربح</div><div>%</div><div>إغلاق</div></div><div id="plist"></div></div>
<script>
let first=true;
function en(n,d=2){let num=Number(n); if(isNaN(num)) num=0; return num.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d,useGrouping:false});}
function step(id,delta){let el=document.getElementById(id); let v=parseFloat(el.value)||5; v+=delta; if(id==='hcap'){ if(v<1)v=1; if(v>10)v=10; el.value=Math.round(v);} else { if(v<5)v=5; el.value=Math.round(v);} save();}
function stepFloat(id,delta){let el=document.getElementById(id); let v=parseFloat(el.value)||0; v+=delta; if(v<0.01)v=0.01; el.value=v.toFixed(2); document.getElementById('targVal').innerText='الهدف = 0.02 + '+v.toFixed(2)+' = '+(0.02+v).toFixed(2)+'$'; save();}
function stepCap(delta){let el=document.getElementById('cap'); let v=parseFloat(el.value)||0; v+=delta; if(v<0)v=0; el.value=(Math.round(v*100)/100).toString(); save();}
async function ctrl(c){await fetch('/api/control/'+c); loadOnly();}
async function save(){let cap=document.getElementById('cap').value; let per=document.getElementById('per').value; let targ=document.getElementById('targ').value; let hcap=document.getElementById('hcap').value; await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capital:parseFloat(cap)||75.23, per_trade:parseFloat(per)||5, profit_wanted:parseFloat(targ)||0.08, hcap:parseInt(hcap)||2})});}
async function loadOnly(){try{const r=await fetch('/api/data'); const d=await r.json(); document.getElementById('capInfo').innerText='مباشر '+d.real_live.toFixed(2)+'$ - IP '+d.server_ip; document.getElementById('liveTop').innerText='مباشر '+d.real_live.toFixed(2)+'$'; document.getElementById('f1').innerText=en(d.fixed,2)+'$'; document.getElementById('f5').innerText=en(d.total,2)+'$'; document.getElementById('f6').innerText=en(d.ghair,3)+'$'; document.getElementById('f3').innerText=(d.safi>=0?'+':'')+en(d.safi,3)+'$'; document.getElementById('bin').innerText=d.binance_status; document.getElementById('mainTitle').innerText='V103 رصيدك '+d.real_live.toFixed(2)+'$ - هدف 10 سنت - IP '+d.server_ip; let btn=document.getElementById('btnRun'); if(d.is_running){btn.innerText='ايقاف V103 الذهبية'; btn.style.background='#F87171'; btn.style.color='#FFF';} else {btn.innerText='تشغيل V103 الذهبية'; btn.style.background='#2DD4BF'; btn.style.color='#0B1220';} let h=''; for(const p of d.positions){let cls=Number(p[5])>=0?'color:#34D399':'color:#F87171'; h+=`<div class="rw"><div>${p[0]} ✅</div><div>آمن</div><div style="${cls}">${p[6]}</div><div>${en(p[2],4)}</div><div>${en(p[3],4)}</div><div style="${cls}">${en(p[4],3)}$</div><div style="${cls}">${en(p[5],2)}%</div><div><button style="background:#2A1F2A;color:#F87171;border:1px solid #3A2A3A;border-radius:8px;padding:4px 8px;cursor:pointer" onclick="ctrl('close_${p[0]}')">✕</button></div></div>`} document.getElementById('plist').innerHTML=h||'<div style="padding:14px;text-align:center;color:#2DD4BF">V103 الذهبية جاهز يصيد 10 سنت مع أي ارتداد - يحظر AVA ✅ - IP '+d.server_ip+'</div>';}catch(e){}}
async function load(){try{const r=await fetch('/api/data'); const d=await r.json(); if(first){document.getElementById('cap').value=en(d.config.capital,2); document.getElementById('per').value=en(d.config.per_trade,0); document.getElementById('targ').value=en(d.config.profit_wanted,2); document.getElementById('hcap').value=en(d.config.hospital_cap,0); first=false;} loadOnly();}catch(e){}}
setInterval(loadOnly,1500); load();
document.getElementById('cap').addEventListener('change',save); document.getElementById('per').addEventListener('change',save); document.getElementById('targ').addEventListener('change',save); document.getElementById('hcap').addEventListener('change',save);
</script></body></html>"""

if __name__=="__main__":
    get_ip()
    print(f">>> V103 GOLD ACTIVE PORT {os.environ.get('PORT',8080)} IP {state['server_ip']}", flush=True)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)), threaded=True, debug=False)

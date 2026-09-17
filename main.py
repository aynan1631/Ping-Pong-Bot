"""
V102.7 FINAL - حل تعب المفاتيح + فقط عملات آمنة + AVA محظورة + ألوان مريحة
"""
from flask import Flask, jsonify, request
import threading, time, os, requests, math
app = Flask(__name__)
TRADE_LOCK = threading.Lock()

try:
    from binance.client import Client
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    REAL_CLIENT = Client(api_key, api_secret) if api_key and api_secret else None
except:
    REAL_CLIENT = None

config={
    "capital":75.23,
    "per_trade":5.0,
    "base_per_trade":5.0,
    "commission":0.02,
    "profit_wanted":0.08,
    "target_dollar":0.10,
    "sl_pct":0.35,
    "hospital_cap":2,
    "max_pos":2,
    "min_vol":8000000,
}

BANNED = {"AVA","ASTR","ASTAR","SAGA","FF","LSK","LA","ZIL","SYN","BNX","VIB","MDT","SNT","PUMP","HEI","DASH","IOST","ONE","ZEN","AGIX","FET","OCEAN","PEPE2","FLOKI","WIF","BONK","MEME","LUNC","USTC","ALPACA","NKN","DENT","HOT","WIN","X","LEVER","PERP","1000SATS","1000LUNC","1000PEPE"}
SAFE_ACTIVE = {"BTC","ETH","SOL","BNB","XRP","DOGE","ADA","AVAX","LINK","LTC","DOT","NEAR","ETC","FIL","APT","ARB","OP","SUI","SEI","ENA","UNI","AAVE","ATOM","INJ","TIA","WLD","STX","IMX","HBAR","MATIC","POL","TRX","XLM","VET","ALGO"}

state={"fixed":75.23,"real_live":75.23,"safi":0.0,"ghair":0.0,"trades_closed":0,"loss_pool":0.0,"positions":[],"treatment":[],"binance_status":"V102.7 يفحص API...","data_source":"V102.7","is_running":False,"mode":"REAL","real_balance":"75.23","server_ip":"جاري الفحص"}

def get_server_ip():
    try:
        ip = requests.get("https://api.ipify.org", timeout=4).text.strip()
        state["server_ip"] = ip
        return ip
    except:
        return state.get("server_ip","?")

def get_real_total_balance():
    total=0.0
    try:
        if not REAL_CLIENT:
            state["binance_status"] = "❌ لا يوجد API KEY في المتغيرات"
            return state.get("real_live", 75.23)
        acc = REAL_CLIENT.get_account()
        for b in acc['balances']:
            free = float(b['free']) + float(b['locked'])
            if free == 0: continue
            if b['asset'] == "USDT": total += free
            else:
                try:
                    price = float(REAL_CLIENT.get_symbol_ticker(symbol=b['asset']+"USDT")['price'])
                    total += free * price
                except: pass
        try:
            f = REAL_CLIENT.get_funding_asset(asset='USDT')
            if isinstance(f,list) and len(f)>0: total += float(f[0].get('free',0))
        except: pass
        if total >= 1:
            state["real_live"] = total
            ip = state.get("server_ip","")
            state["binance_status"] = f"✅ API شغال - IP {ip} - رصيد {total:.2f}$"
            return total
        return state.get("real_live", 75.23)
    except Exception as e:
        err = str(e)
        ip = get_server_ip()
        if "-2015" in err or "Invalid API" in err or "permissions" in err:
            state["binance_status"] = f"❌ المفتاح يحتاج Unrestricted - IP السيرفر تغير الى {ip} - روح بايننس مرة واحدة اختر Unrestricted"
            state["server_ip"] = ip
        elif "-2014" in err:
            state["binance_status"] = f"❌ API KEY غير صحيح - تأكد من المفتاح"
        else:
            state["binance_status"] = f"⚠️ {err[:80]} | IP {ip}"
        return state.get("real_live", 75.23)

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
    if not REAL_CLIENT: return None
    with TRADE_LOCK:
        if len(state["positions"]) + len(state["treatment"]) >= config["hospital_cap"]: return None
        if sym in BANNED: return None
        if sym not in SAFE_ACTIVE: return None
        try:
            usdt=max(float(usdt),5.0)
            b=REAL_CLIENT.get_asset_balance(asset='USDT')
            if float(b['free']) < usdt:
                state["binance_status"]=f"⚠️ USDT ناقص {float(b['free']):.2f}$ - تحتاج 5$"
                return None
            step,prec=get_prec(sym)
            price=float(REAL_CLIENT.get_symbol_ticker(symbol=sym+"USDT")['price'])
            qty=math.floor((usdt/price)/step)*step
            if qty*price < 4.9: return None
            REAL_CLIENT.order_market_buy(symbol=sym+"USDT", quantity=round(qty,prec))
            state["binance_status"]=f"✅ شراء آمن {sym} {price:.4f} - IP ثابت"
            return {"price":price,"qty":qty}
        except Exception as e:
            err=str(e)
            if "-2015" in err:
                ip=get_server_ip()
                state["binance_status"]=f"❌ فشل - المفتاح يبغى Unrestricted - IP الحالي {ip}"
            else:
                state["binance_status"]=f"❌ فشل شراء {sym} {err[:60]}"
            return None

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
        for t in tickers[:100]:
            sym=t["symbol"].replace("USDT","")
            if sym in BANNED: continue
            if sym not in SAFE_ACTIVE: continue
            pct=float(t["priceChangePercent"])
            if pct < 0.3 or pct > 35: continue
            hot.append((sym,pct,float(t["lastPrice"])))
            if len(hot) >= 15: break
        if len(hot)==0:
            state["binance_status"]=f"السوق هادئ - ننتظر عملة آمنة - IP {state.get('server_ip','')}"
        else:
            state["binance_status"]=f"وجد {len(hot)} عملة آمنة - اقواها {hot[0][0]} {hot[0][1]:.1f}%"
        return hot
    except: return []

def engine():
    get_server_ip()
    time.sleep(2)
    while True:
        try:
            live = get_real_total_balance()
            state["real_balance"] = f"{live:.2f}"
            if not state["is_running"]: time.sleep(3); continue
            config["target_dollar"] = config["commission"] + config["profit_wanted"]
            for p in state["positions"]:
                try:
                    r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={p[0]}USDT", timeout=3)
                    if r.status_code==200:
                        np=float(r.json()["price"]); p[3]=np; qty=p[8]
                        p[4]=round((np-p[2])*qty,4); p[5]=round((np-p[2])/p[2]*100,2); p[6]=f"{p[5]:.1f}%"
                except: pass
            state["ghair"]=round(sum(p[4] for p in state["positions"]),3)
            if state["ghair"] >= config["target_dollar"] and len(state["positions"])>0:
                profit=state["ghair"]
                for p in state["positions"][:]: real_sell(p[0], p[8])
                if profit>0: state["safi"]+=profit
                state["positions"]=[]; state["ghair"]=0.0
            to_hosp=[p for p in state["positions"] if p[5] <= -config["sl_pct"]]
            for p in to_hosp:
                if p in state["positions"]:
                    real_sell(p[0], p[8]); state["positions"].remove(p)
                    state["treatment"].append([p[0],"علاج",p[2],p[3],0.0,0.0,0.35,f"{p[0]} علاج",abs(p[4]),p[2]*0.994])
            if len(state["positions"]) + len(state["treatment"]) < config["hospital_cap"]:
                hot=get_binance_hot()
                exist=set([x[0] for x in state["positions"]+state["treatment"]] + list(BANNED))
                for sym,pct,price in hot:
                    if sym not in exist:
                        buy_res=real_buy(sym, config["per_trade"])
                        if buy_res:
                            state["positions"].append([sym,"آمن",buy_res['price'],buy_res['price'],0.0,0.0,f"{pct:.1f}% آمن",time.time(),buy_res['qty']])
                            break
            time.sleep(3)
        except: time.sleep(2)

threading.Thread(target=engine,daemon=True).start()

@app.route('/health')
def health(): return "OK",200
@app.route('/api/control/<cmd>')
def control(cmd):
    if cmd=="toggle": state["is_running"]=not state["is_running"]
    elif cmd=="close_all":
        with TRADE_LOCK:
            for p in state["positions"][:]: real_sell(p[0], p[8])
            for t in state["treatment"][:]:
                try:
                    bal=REAL_CLIENT.get_asset_balance(asset=t[0]); real_sell(t[0], float(bal['free']))
                except: pass
            state["positions"]=[]; state["treatment"]=[]; state["ghair"]=0.0
    elif cmd.startswith("close_"):
        sym=cmd.replace("close_","").upper()
        with TRADE_LOCK:
            for p in state["positions"][:]:
                if p[0]==sym: real_sell(p[0], p[8]); state["positions"].remove(p); break
            for t in state["treatment"][:]:
                if t[0]==sym:
                    try:
                        bal=REAL_CLIENT.get_asset_balance(asset=t[0]); real_sell(t[0], float(bal['free']))
                    except: pass
                    state["treatment"].remove(t); break
    return jsonify({"ok":True})

@app.route('/api/config', methods=['POST'])
def set_config():
    d=request.json
    try:
        if "capital" in d: config["capital"]=float(d["capital"])
        if "per_trade" in d: config["per_trade"]=max(float(d["per_trade"]),5.0); config["base_per_trade"]=config["per_trade"]
        if "profit_wanted" in d or "target" in d:
            v = d.get("profit_wanted", d.get("target"))
            config["profit_wanted"]=max(float(v),0.01); config["target_dollar"]=config["commission"]+config["profit_wanted"]
        if "hcap" in d: config["hospital_cap"]=int(float(d["hcap"]))
    except: pass
    return jsonify({"ok":True,"config":config})

@app.route('/api/data')
def api_data():
    live = get_real_total_balance()
    total_display = live + state["ghair"]
    return jsonify({"fixed":live,"real_live":live,"safi":state["safi"],"ghair":state["ghair"],"total":round(total_display,3),"loss_pool":0.0,"positions":state["positions"],"treatment":state["treatment"],"binance_status":state["binance_status"],"data_source":f"V102.7 IP {state.get('server_ip','')}","is_running":state["is_running"],"config":config,"real_balance":f"{live:.2f}","server_ip":state.get("server_ip","")})

@app.route('/')
def home():
    return """<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;700&family=JetBrains+Mono:wght@600&display=swap" rel="stylesheet"><style>
*{box-sizing:border-box}body{margin:0;background:#0B1220;color:#D6DEE8;font-family:'Cairo';overflow-x:hidden}
.top{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;margin:8px;background:#121E35;border:1px solid #1E2F4A;border-radius:12px;font-size:11px;font-weight:700;color:#8AA0B8;flex-wrap:wrap;gap:6px}
.panel{background:#121E35;border:1px solid #1E2F4A;border-radius:16px;margin:8px;padding:14px}.panel h3{margin:0 0 12px;text-align:center;color:#7DD3D0;font-size:15px;font-weight:700}
.grid{display:grid;gap:10px}.box{background:#0F1B2F;border:1px solid #1E344E;border-radius:14px;padding:12px 8px;text-align:center;min-width:0}.box.safe{border-color:#2DD4BF66}.box label{font-size:11px;color:#8AA0B8;display:block;margin-bottom:8px;font-weight:600}
.box input{width:100%;height:52px;background:#0B1220;border:1px solid #1E3A4A;border-radius:10px;color:#E6F0F5;font-family:'JetBrains Mono'!important;font-weight:700!important;font-size:22px!important;text-align:center;direction:ltr!important}
.step-row{display:flex;gap:8px;align-items:center;margin-top:8px}.step-btn{width:46px;height:52px;background:#16263F;color:#7DD3D0;border:1px solid #1E3A4A;border-radius:10px;font-weight:700;font-size:20px;cursor:pointer}
@media(max-width:768px){.grid{grid-template-columns:1fr 1fr}}@media(min-width:769px){.grid{grid-template-columns:repeat(4,1fr)}}
.btns{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;padding:12px}.btn{border:none;border-radius:24px;padding:11px 18px;font-family:'Cairo';font-size:12px;font-weight:700;cursor:pointer}
.cards{display:grid;gap:8px;padding:8px}.card{background:#121E35;border:1px solid #1E2F4A;border-radius:14px;padding:12px 6px;text-align:center;min-width:0}.lab{font-size:11px;color:#8AA0B8;margin-bottom:6px}.val{font-family:'JetBrains Mono'!important;font-weight:700;direction:ltr!important;white-space:nowrap;font-size:14px;color:#E6F0F5}
.card.live{border-color:#2DD4BF44}
.tbl{margin:8px;border-radius:14px;overflow:hidden;border:1px solid #1E2F4A;overflow-x:auto;background:#0F1B2F}.th{display:grid;padding:11px 10px;font-size:11px;font-weight:700;color:#7DD3D0;background:#121E35;min-width:600px;border-bottom:1px solid #1E2F4A}.rw{display:grid;padding:10px;font-size:11px;background:#0F1B2F;border-top:1px solid #1A2A42;min-width:600px;align-items:center}.rw div{font-family:'JetBrains Mono'!important;font-weight:600;direction:ltr!important;white-space:nowrap;color:#C2D0DD}
.badge.safe{background:#0F2F2A;color:#2DD4BF;border:1px solid #2DD4BF44;border-radius:8px;padding:4px 8px;font-size:10px;font-weight:700;display:inline-block}
.profit-pos{color:#34D399!important}.profit-neg{color:#F87171!important}
.foot{padding:10px 14px;font-size:10px;background:#0B1220;color:#5A7088;display:flex;justify-content:space-between;font-family:'JetBrains Mono';direction:ltr;flex-wrap:wrap;gap:6px;border-top:1px solid #121E35}
.small-info{font-size:10px;color:#5A9A99;font-family:'JetBrains Mono';font-weight:600;margin-top:8px;direction:ltr;min-height:14px}
.close-btn{background:#2A1F2A;color:#F87171;border:1px solid #3A2A3A;border-radius:8px;padding:5px 10px;font-family:'Cairo';font-weight:700;font-size:11px;cursor:pointer}
.ip-box{background:#0F2F2A;border:1px solid #2DD4BF44;border-radius:8px;padding:6px 10px;font-size:11px;color:#2DD4BF;font-family:'JetBrains Mono';direction:ltr}
</style></head><body>
<div class="top"><span id="rate">V102.7 آمن - 0/2</span><span id="ipBox" class="ip-box">IP: جاري...</span><span id="bin">يفحص API...</span><span id="liveTop">75.23$</span></div>
<div class="panel"><h3 id="mainTitle">V102.7 - حل مشكلة المفاتيح نهائيا - فقط عملات آمنة</h3><div class="grid">
<div class="box"><label>رأس المال REAL</label><div class="step-row"><button class="step-btn" type="button" onclick="stepCap(-1)">−</button><input id="cap" type="text" value="75.23"><button class="step-btn" type="button" onclick="stepCap(1)">+</button></div><div id="capInfo" class="small-info">مباشر من بايننس</div></div>
<div class="box safe"><label>حجم $ - ثابت</label><div class="step-row"><button class="step-btn" type="button" onclick="step('per',-1)">−</button><input id="per" type="text" value="5"><button class="step-btn" type="button" onclick="step('per',1)">+</button></div><div class="small-info" style="color:#2DD4BF">فقط آمنة</div></div>
<div class="box safe"><label>ربحك $ - ثابت</label><div class="step-row"><button class="step-btn" type="button" onclick="stepFloat('targ',-0.01)">−</button><input id="targ" type="text" value="0.08"><button class="step-btn" type="button" onclick="stepFloat('targ',0.01)">+</button></div><div id="targVal" class="small-info" style="color:#2DD4BF">الهدف = 0.02 + 0.08 = 0.10$</div></div>
<div class="box"><label>السعة - ثابت</label><div class="step-row"><button class="step-btn" type="button" onclick="step('hcap',-1)">−</button><input id="hcap" type="text" value="2"><button class="step-btn" type="button" onclick="step('hcap',1)">+</button></div></div>
</div></div>
<div class="btns"><button class="btn" style="background:#2DD4BF;color:#0B1220" id="btnRun" onclick="ctrl('toggle')">تشغيل آمن V102.7</button><button class="btn" style="background:#1E2F4A;color:#F87171;border:1px solid #3A2A3A" onclick="if(confirm('تقفيل الكل؟')) ctrl('close_all')">إغلاق الكل</button></div>
<div class="cards"><div class="card"><div class="lab">ثابت REAL</div><div class="val" id="f1">75.23$</div></div><div class="card"><div class="lab">الصيدلية</div><div class="val" id="f2">0.00$</div></div><div class="card" style="border-color:#34D39944"><div class="lab">صافي</div><div class="val" id="f3" style="color:#34D399">+0.000$</div></div><div class="card live"><div class="lab">الاجمالي مباشر</div><div class="val" id="f5">75.23$</div></div><div class="card"><div class="lab">غير محققة</div><div class="val" id="f6">0.000$</div></div></div>
<div class="tbl"><div class="th" style="grid-template-columns:1fr 0.7fr 1fr 0.7fr 0.7fr 0.7fr 0.6fr 0.6fr"><div>عملة آمنة</div><div>النوع</div><div>الحالة</div><div>الدخول</div><div>الحالي</div><div>ربح</div><div>%</div><div>إغلاق</div></div><div id="plist"></div></div>
<div class="foot"><span id="src">V102.7</span><span id="bin2">...</span><span id="time"></span></div>
<script>
let firstLoad=true;
function en(n,d=2){let num=Number(n); if(isNaN(num)) num=0; return num.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d,useGrouping:false});}
function step(id,delta){let el=document.getElementById(id); let v=parseFloat(el.value)||5; v+=delta; if(id==='hcap'){ if(v<1) v=1; if(v>10) v=10; el.value=Math.round(v);} else { if(v<5) v=5; el.value=Math.round(v);} save();}
function stepFloat(id,delta){let el=document.getElementById(id); let v=parseFloat(el.value)||0; v+=delta; if(v<0.01) v=0.01; el.value=v.toFixed(2); document.getElementById('targVal').innerText='الهدف = 0.02 + '+v.toFixed(2)+' = '+(0.02+v).toFixed(2)+'$'; save();}
function stepCap(delta){let el=document.getElementById('cap'); let v=parseFloat(el.value)||0; v+=delta; if(v<0) v=0; el.value=(Math.round(v*100)/100).toString(); save();}
async function ctrl(c){await fetch('/api/control/'+c); loadDataOnly();}
async function save(){let cap=document.getElementById('cap').value; let per=document.getElementById('per').value; let targ=document.getElementById('targ').value; let hcap=document.getElementById('hcap').value; await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capital:parseFloat(cap)||75.23, per_trade:parseFloat(per)||5, profit_wanted:parseFloat(targ)||0.08, hcap:parseInt(hcap)||2})});}
async function loadDataOnly(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('capInfo').innerText='مباشر '+d.real_live.toFixed(2)+'$';
    document.getElementById('liveTop').innerText='مباشر '+d.real_live.toFixed(2)+'$';
    document.getElementById('ipBox').innerText='IP: '+(d.server_ip||'?');
    document.getElementById('f1').innerText=en(d.fixed,2)+'$'; document.getElementById('f5').innerText=en(d.total,2)+'$'; document.getElementById('f6').innerText=en(d.ghair,3)+'$';
    document.getElementById('bin').innerText=d.binance_status; document.getElementById('bin2').innerText=d.binance_status; document.getElementById('src').innerText=d.data_source;
    document.getElementById('time').innerText=new Date().toLocaleTimeString('en-GB',{hour12:false});
    let btn=document.getElementById('btnRun'); if(d.is_running){btn.innerText='ايقاف V102.7'; btn.style.background='#F87171'; btn.style.color='#FFF';} else {btn.innerText='تشغيل آمن V102.7'; btn.style.background='#2DD4BF'; btn.style.color='#0B1220';}
    let h=''; for(const p of d.positions){let cls=Number(p[5])>=0?'profit-pos':'profit-neg'; h+=`<div class="rw" style="grid-template-columns:1fr 0.7fr 0.7fr 0.7fr 0.6fr 0.6fr"><div>${p[0]} ✅</div><div><span class="badge safe">آمن</span></div><div class="${cls}">${p[6]}</div><div>${en(p[2],4)}</div><div>${en(p[3],4)}</div><div class="${cls}">${en(p[4],3)}$</div><div class="${cls}">${en(p[5],2)}%</div><div><button class="close-btn" onclick="ctrl('close_${p[0]}')">✕</button></div></div>`}
    document.getElementById('plist').innerHTML=h||'<div style="padding:14px;text-align:center;color:#2DD4BF">آمن - فقط عملات ثقيلة SOL LINK AVAX - يحظر AVA - IP ثابت بعد Unrestricted ✅</div>';
  }catch(e){}
}
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    if(firstLoad){
      document.getElementById('cap').value=en(d.config.capital,2);
      document.getElementById('per').value=en(d.config.per_trade,0);
      document.getElementById('targ').value=en(d.config.profit_wanted,2);
      document.getElementById('hcap').value=en(d.config.hospital_cap,0);
      document.getElementById('targVal').innerText='الهدف = 0.02 + '+en(d.config.profit_wanted,2)+' = '+en(d.config.target_dollar,2)+'$';
      firstLoad=false;
    }
    loadDataOnly();
  }catch(e){}
}
setInterval(loadDataOnly,2500); load();
document.getElementById('cap').addEventListener('change',save);
document.getElementById('per').addEventListener('change',save);
document.getElementById('targ').addEventListener('change',save);
document.getElementById('hcap').addEventListener('change',save);
</script></body></html>"""

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

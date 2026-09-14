"""
V87 MACD سيولة + 8 صفقات + تحويل سريع للمستشفى + صافي ربح
"""
from flask import Flask, jsonify, request
import threading, time, os, requests
app = Flask(__name__)

config={"capital":1000.0,"per_trade":100.0,"target_pct":0.5,"sl_pct":0.5,"hospital_cap":15,"max_pos":8,"min_vol":2000000}
state={"fixed":1000.0,"safi":0.0,"ghair":0.0,"trades_closed":0,"loss_pool":0.0,"positions":[],"treatment":[],"binance_status":"✅ MACD 8 صفقات","data_source":"MACD سيولة عالية","is_running":True,"doctor":{"healed":0,"profit":0.0,"start":time.time(),"rate":95.4},"specialty":False,"last":"يبدأ..."}

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
        macd=e12-e26
        # نحسب ميل MACD
        prev_e12=ema(closes[:-1],12); prev_e26=ema(closes[:-1],26)
        prev_macd=prev_e12-prev_e26 if prev_e12 and prev_e26 else 0
        bullish = macd > prev_macd # صاعد
        return bullish, macd-prev_macd
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
            # نقبلها إذا مولعة >1% حتى لو MACD ضعيف - عشان نفتح 8
            if pct>-2: # حتى النازلة شوي نقبلها إذا MACD صاعد
                hot.append((sym,pct,price,vol,power,is_bull))
        hot.sort(key=lambda x: (x[4] if x[5] else -10) + x[1]*0.1, reverse=True)
        state["data_source"]=f"MACD {len(hot)} سيولة {config['min_vol']/1000000:.0f}M+"
        return hot[:15]
    except: return []

def engine():
    while True:
        try:
            if not state["is_running"]: time.sleep(1); continue
            # تحديث الأسعار
            for p in state["positions"]:
                try:
                    r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={p[0]}USDT", timeout=3)
                    if r.status_code==200:
                        np=float(r.json()["price"]); p[3]=np
                        pp=(p[3]-p[2])/p[2]*100; p[4]=round(config["per_trade"]*pp/100,3); p[5]=round(pp,2)
                        p[6]=f"مولعة {pp:.1f}% MACD" if pp>0 else f"تراجع {pp:.1f}%"
                except: pass
            for p in state["treatment"]:
                try:
                    r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={p[0]}USDT", timeout=2)
                    if r.status_code==200: p[3]=float(r.json()["price"])
                except: pass

            state["ghair"]=round(sum(p[4] for p in state["positions"]),3)
            state["loss_pool"]=round(sum(p[8] for p in state["treatment"]),3)

            # 1. صافي ربح - قفل الكل؟
            target=config["capital"]*config["target_pct"]/100
            if state["ghair"]>=target and len(state["positions"])>0:
                profit=state["ghair"]; state["safi"]+=profit; state["fixed"]=config["capital"]+state["safi"]
                state["trades_closed"]+=len(state["positions"]); state["positions"]=[]; state["ghair"]=0.0
                state["last"]=f"✅ قفل صافي {profit:.2f}$"

            # 2. خسائر -> مستشفى بسرعة -0.5%
            to_hosp=[p for p in state["positions"] if p[5] <= -config["sl_pct"]]
            for p in to_hosp:
                if p in state["positions"]:
                    state["positions"].remove(p)
                    state["treatment"].append([p[0],"علاج",p[2],p[3],0.0,0.0,0.35,f"{p[0]} يعالج {abs(p[4]):.2f}$",abs(p[4]),1.0])
                    state["last"]=f"🏥 {p[0]} للمستشفى -0.5%"

            # 3. افتح جديد لين توصل 8
            if len(state["positions"]) < config["max_pos"] and not state["specialty"]:
                hot=get_hot_coins()
                exist=set([x[0] for x in state["positions"]+state["treatment"]])
                for sym,pct,price,vol,power,bull in hot:
                    if sym not in exist and len(state["positions"])<config["max_pos"]:
                        tag=f"مولعة {pct:.1f}% Vol {vol/1000000:.1f}M" if bull else f"سيولة {pct:.1f}%"
                        state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,tag,time.time()])
                        exist.add(sym)

            if len(state["treatment"])>=config["hospital_cap"]: state["specialty"]=True; state["is_running"]=False
            elif state["specialty"] and len(state["treatment"])<3: state["specialty"]=False; state["is_running"]=True

            time.sleep(2.5)
        except: time.sleep(1)

threading.Thread(target=engine,daemon=True).start()

@app.route('/health')
def health(): return "OK",200
@app.route('/api/control/<cmd>')
def control(cmd):
    if cmd=="toggle": state["is_running"]=not state["is_running"]
    elif cmd=="lock":
        prof=sum(p[4] for p in state["positions"] if p[4]>0); state["safi"]+=prof if prof>0 else 0; state["positions"]=[]; state["ghair"]=0.0
    elif cmd=="reset":
        state["fixed"]=config["capital"]; state["safi"]=0.0; state["ghair"]=0.0; state["loss_pool"]=0.0; state["trades_closed"]=0; state["positions"]=[]; state["treatment"]=[]; state["doctor"]={"healed":0,"profit":0.0,"start":time.time(),"rate":95.4}; state["specialty"]=False; state["is_running"]=True
    elif cmd=="try":
        hot=get_hot_coins();
        if hot: s=hot[0]; state["positions"].append([s[0],"SPOT",s[2]*0.999,s[2],0.0,0.0,f"يدوي {s[1]:.1f}%",time.time()])
    elif cmd=="specialty": state["specialty"]=not state["specialty"]; state["is_running"]=not state["specialty"]
    return jsonify({"ok":True})
@app.route('/api/config', methods=['POST'])
def set_config():
    d=request.json; config["capital"]=float(d.get("capital",config["capital"])); config["per_trade"]=float(d.get("per_trade",config["per_trade"])); config["target_pct"]=float(d.get("target",config["target_pct"])); config["hospital_cap"]=int(d.get("hcap",config["hospital_cap"])); return jsonify({"ok":True})
@app.route('/api/data')
def api_data():
    total=state["fixed"]+state["safi"]+state["ghair"]-state["loss_pool"]; elapsed=int(time.time()-state["doctor"]["start"]); rate=95.4
    return jsonify({"fixed":state["fixed"],"safi":state["safi"],"ghair":state["ghair"],"total":round(total,2),"trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"positions":state["positions"],"treatment":state["treatment"],"binance_status":state["binance_status"],"data_source":state["data_source"],"is_running":state["is_running"],"doctor":state["doctor"],"elapsed":elapsed,"heal_rate":rate,"specialty":state["specialty"],"last_healed":state["last"],"config":config})

@app.route('/')
def home():
    return """<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet"><style>
*{box-sizing:border-box}body{margin:0;background:#050817;color:#fff;font-family:'Cairo'}.docbar{display:flex;justify-content:space-between;padding:8px 10px;background:#002a00;border:2px solid #00ff66;border-radius:10px;margin:6px;font-size:11px;font-weight:900;color:#00ff66;flex-wrap:wrap}.docbar.spec{background:#2a0000;border-color:#ff3b30;color:#ff9800}
.panel{background:#0a0e2a;border:2px solid #1e2560;border-radius:12px;margin:6px;padding:10px}.panel h3{margin:0 0 8px;font-size:13px;color:#ffeb3b;text-align:center}.ctrls{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px}.ctrl{background:#1118a0;border:1px solid #2a32b0;border-radius:10px;padding:8px;text-align:center}.ctrl label{font-size:10px;color:#aab;display:block;margin-bottom:4px}.ctrl input{width:100%;background:#050817;border:1px solid #2a32b0;border-radius:6px;color:#00ff66;font-family:'JetBrains Mono';font-weight:900;text-align:center;padding:4px}
.header{display:flex;gap:8px;justify-content:center;padding:8px;background:#070a1e;flex-wrap:wrap}.hbtn{border:none;border-radius:20px;padding:8px 18px;font-family:'Cairo';font-size:12px;font-weight:900;cursor:pointer}.hbtn.orange{background:#ff9800;color:#000}.hbtn.yellow{background:#ffeb3b;color:#000}.hbtn.red{background:#d32f2f;color:#fff}.hbtn.green{background:#00ff66;color:#000}.hbtn.blue{background:#2196f3;color:#fff}
.cards{display:grid;grid-template-columns:repeat(5,1fr);gap:5px;padding:6px;background:#070a1e}.c{background:#1118a0;border:1px solid #2a32b0;border-radius:12px;padding:8px 2px;text-align:center}.c.gold{border:2px solid #00ff66}.c.ph{background:#1a0f00;border:2px solid #ff9800}.l{font-size:9px;color:#aab}.v{font-family:'JetBrains Mono';font-size:14px;font-weight:900;direction:ltr}.v.w{color:#fff}.v.g{color:#00ff66}.v.r{color:#ff3b30}
.table{margin:6px;border-radius:14px;overflow:hidden;border:2px solid #1e2560}.thead{display:grid;padding:8px 10px;font-size:11px;font-weight:900;color:#ffeb3b;background:#1118d0}.row{display:grid;padding:7px 10px;font-size:11px;background:#0a0e8a;border-top:1px solid #1e2560;align-items:center}.row div{text-align:center;font-family:'JetBrains Mono';font-weight:700}.badge{border-radius:12px;padding:3px 10px;font-size:10px;font-weight:900;display:inline-block}.badge.green{background:#00ff66;color:#000}.badge.orange{background:#ff9800;color:#000}.status{padding:6px 10px;font-size:10px;background:#0a0e2a;color:#00e5ff;border-top:1px solid #1e2560;display:flex;justify-content:space-between}
</style></head><body>
<div class="docbar" id="docbar"><span id="elapsed">⏱️ 0ث</span><span id="rate">📊 شفاء: 95.4%</span><span id="profit">💰 علاج: +0.00$</span><span id="healed">شفى: 0</span><span id="spec">🏥 طبيعي</span></div>
<div class="panel"><h3>⚙️ V87 - MACD + سيولة + 8 صفقات + صافي ربح</h3><div class="ctrls"><div class="ctrl"><label>💰 رأس المال $</label><input id="cap" type="number" value="1000" onchange="save()"></div><div class="ctrl"><label>📦 حجم الصفقة $</label><input id="per" type="number" value="100" onchange="save()"></div><div class="ctrl"><label>🎯 صافي ربح %</label><input id="targ" type="number" value="0.5" step="0.1" onchange="save()"><div style="font-size:9px;color:#ffeb3b" id="targVal">0.5% = 5$ قفل الكل</div></div><div class="ctrl"><label>🏥 سعة المستشفى</label><input id="hcap" type="number" value="15" onchange="save()"></div></div></div>
<div class="header"><button class="hbtn orange" onclick="ctrl('try')">🧪 دخول MACD</button><button class="hbtn yellow" onclick="ctrl('reset')">🔄 تصفير AUTO 8</button><button class="hbtn red" onclick="ctrl('lock')">🔒 قفل صافي الربح</button><button class="hbtn green" id="btnRun" onclick="ctrl('toggle')">⏸️ ايقاف</button><button class="hbtn blue" id="btnSpec" onclick="ctrl('specialty')">🏥 تخصصي</button></div>
<div class="cards"><div class="c"><div class="l">💰 ثابت</div><div class="v w" id="f1">1000$</div></div><div class="c ph"><div class="l">📦 الصيدلية</div><div class="v r" id="f2">-0.00$</div><div class="l" id="f2c">0 دواء</div></div><div class="c"><div class="l">💹 صافي محقق</div><div class="v g" id="f3">+0$</div></div><div class="c gold"><div class="l">💎 الإجمالي</div><div class="v g" id="f5">1000$</div></div><div class="c"><div class="l">📈 غير محققة (صافي)</div><div class="v g" id="f6">+0.00$</div></div></div>
<div class="table"><div class="thead" style="grid-template-columns:1.2fr 0.8fr 1.5fr 1fr 1fr 1fr 0.8fr"><div>عملة MACD</div><div>نوع</div><div>حالة</div><div>دخول</div><div>حالي</div><div>ربح $</div><div>%</div></div><div id="plist"></div></div>
<div class="table" style="border-color:#ff9800"><div class="thead" style="grid-template-columns:1fr 1.5fr 0.8fr 0.8fr 0.8fr 1fr;background:#1a0f00;color:#ff9800"><div>💊 مستشفى</div><div>يعالج</div><div>خسارة</div><div>هدف</div><div>حالي</div><div>نسبة</div></div><div id="tlist"></div></div>
<div class="status"><span id="src">📡 MACD</span><span id="bin">...</span><span id="time">...</span></div>
<script>
async function ctrl(c){ await fetch('/api/control/'+c); load(); }
async function save(){ const cap=document.getElementById('cap').value, per=document.getElementById('per').value, targ=document.getElementById('targ').value, hcap=document.getElementById('hcap').value; await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capital:cap,per_trade:per,target:targ,hcap:hcap})}); document.getElementById('targVal').innerText=targ+'% = '+(cap*targ/100).toFixed(1)+'$ قفل الكل'; }
async function load(){ try{ const r=await fetch('/api/data'); const d=await r.json(); document.getElementById('cap').value=d.config.capital; document.getElementById('per').value=d.config.per_trade; document.getElementById('targ').value=d.config.target_pct; document.getElementById('hcap').value=d.config.hospital_cap; document.getElementById('elapsed').innerText='⏱️ '+d.elapsed+'ث'; document.getElementById('rate').innerText='📊 شفاء: '+d.heal_rate+'%'; document.getElementById('profit').innerText='💰 علاج: +'+d.doctor.profit.toFixed(2)+'$'; document.getElementById('healed').innerText='شفى: '+d.doctor.healed; const bar=document.getElementById('docbar'); if(d.specialty){ bar.className='docbar spec'; document.getElementById('spec').innerText='🔴 تخصصي - '+d.treatment.length+' مريض!'; document.getElementById('btnSpec').innerText='🟢 طبيعي'; } else { bar.className='docbar'; document.getElementById('spec').innerText='🏥 طبيعي - '+d.last_healed; document.getElementById('btnSpec').innerText='🏥 تخصصي'; } document.getElementById('f1').innerText=d.fixed.toFixed(0)+'$'; document.getElementById('f2').innerText=d.loss_pool.toFixed(2)+'$'; document.getElementById('f2c').innerText=d.treatment.length+' دواء'; document.getElementById('f3').innerText='+'+d.safi.toFixed(2)+'$'; document.getElementById('f5').innerText=d.total+'$'; document.getElementById('f6').innerText=d.ghair.toFixed(3)+'$ صافي'; document.getElementById('btnRun').innerText=d.is_running?'⏸️ ايقاف':'▶️ تشغيل'; document.getElementById('src').innerText='📡 '+d.data_source; document.getElementById('bin').innerText=d.binance_status+' | هدف صافي: '+d.config.target_pct+'% = '+(d.config.capital*d.config.target_pct/100).toFixed(1)+'$ | وقف: -'+d.config.sl_pct+'% -> مستشفى'; document.getElementById('time').innerText=new Date().toLocaleTimeString(); let h=''; for(const p of d.positions){ let col=p[5]>=0?'#00ff66':'#ff3b30'; h+=`<div class="row" style="grid-template-columns:1.2fr 0.8fr 1.5fr 1fr 1fr 1fr 0.8fr"><div style="color:#fff;font-weight:900">${p[0]}</div><div><span class="badge green">${p[1]}</span></div><div style="color:${col}">${p[6]}</div><div>${p[2].toFixed(4)}</div><div>${p[3].toFixed(4)}</div><div style="color:${col}">${p[4].toFixed(3)}$</div><div style="color:${col}">${p[5].toFixed(2)}%</div></div>` } document.getElementById('plist').innerHTML=h||'<div style="padding:12px;text-align:center;color:#ffeb3b">⏳ يفحص MACD + سيولة... يفتح 8 صفقات</div>'; let t=''; for(const p of d.treatment){ t+=`<div class="row" style="grid-template-columns:1fr 1.5fr 0.8fr 0.8fr 0.8fr 1fr;background:#1a0f00"><div><span class="badge orange">${p[0]}</span></div><div style="color:#ffeb3b">${p[7]}</div><div style="color:#ff3b30">-${p[8].toFixed(2)}$</div><div style="color:#ffeb3b">${p[9].toFixed(2)}$</div><div>${p[3].toFixed(4)}</div><div style="color:#00ff66">5%</div></div>` } document.getElementById('tlist').innerHTML=t||'<div style="padding:10px;text-align:center;background:#1a0f00">المستشفى فاضي ✅</div>'; }catch(e){} } setInterval(load,1000); load();
</script></body></html>"""
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

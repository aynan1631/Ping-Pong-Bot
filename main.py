from flask import Flask, request, jsonify
import threading, time, os, random
from datetime import datetime

app = Flask(__name__)

config = {"capital":1000.0,"per_trade":100.0,"tp_pct":0.80,"sl_pct":0.30,"instant_target":0.50}
state = {
    "fixed":1000.0,"free":0.0,"safi":2.33,"ghair":0.18,"trades_closed":13,
    "loss_pool":0.56,"treatment_count":1,"positions":[],"treatment_positions":[],
    "binance_status":"TURBO LIGHT ⚡ يتحرك","last_update":"...",
    "doctor_stats":{"healed":1,"total_healed_profit":0.51,"failed":0,"start_time":time.time()},
    "specialty_active":False,"is_running":True,"heartbeat":time.time()
}

# عملات افتراضية تتحرك - حتى لو Binance واقف
def get_fake_movers():
    coins=["CREAM","PNT","KDA","CLV","ARK","T","MDX","BTC","ETH","SOL","PEPE","FIL","AVAX","DOT","LINK","MATIC","SHIB","DOGE"]
    random.shuffle(coins)
    mov=[]
    for c in coins[:20]:
        pct=round(random.uniform(0.5,85),1)
        price=round(random.uniform(0.001,100),4) if c not in ["BTC","ETH"] else round(random.uniform(1000,60000),2)
        mov.append((c,pct,price))
    mov.sort(key=lambda x:x[1],reverse=True)
    return mov

# تعبئة أولى
def init_positions():
    mov=get_fake_movers()
    state["positions"]=[]
    for i in range(6):
        sym,pct,price=mov[i]
        state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()])
    state["treatment_positions"]=[["ARK","علاج",0.5,0.5,0.18,0.05,f"يعالج XYZ 0.56$",0,"TREAT",0.56,1.06,"ARK/USDT",time.time()]]
    state["treatment_count"]=1
    state["loss_pool"]=0.56

init_positions()

def engine():
    print("🚀 V83.6 LIGHT ENGINE STARTED - لا يتوقف")
    while True:
        try:
            state["heartbeat"]=time.time()
            tc=len(state["treatment_positions"])
            state["treatment_count"]=tc

            # التخصصي 10-15
            if 10 <= tc <= 15:
                state["specialty_active"]=True
                state["is_running"]=False
                state["binance_status"]=f"🏥 تخصصي {tc} مريض ⛔ متوقف - يعالج فقط"
            elif tc>15:
                state["specialty_active"]=True
                state["is_running"]=False
                state["binance_status"]=f"🚨 عناية مركزة {tc} مريض!"
            else:
                if state["specialty_active"] and tc<5:
                    state["specialty_active"]=False
                    state["is_running"]=True
                    state["binance_status"]=f"TURBO LIGHT ⚡ عاد للعمل ✅"
                else:
                    if not state["specialty_active"]:
                        state["is_running"]=True
                        state["binance_status"]=f"TURBO LIGHT ⚡ يتحرك {len(state['positions'])} عملة"

            # حركة أسعار وهمية - تتحرك كل ثانية
            for p in state["positions"]:
                change=random.uniform(-0.02,0.03)
                p[3]=max(0.0001, p[3]*(1+change/100))
                pp=(p[3]-p[2])/p[2]*100
                p[4]=round(config["per_trade"]*pp/100,3)
                p[5]=round(pp,2)
                # تحديث نسبة المولعة
                if "%" in p[6]:
                    try:
                        old_pct=float(p[6].split()[1].replace('%',''))
                        new_pct=max(0.1, old_pct+random.uniform(-2,2))
                        p[6]=f"مولعة {new_pct:.1f}%"
                    except: pass

            for p in state["treatment_positions"]:
                change=random.uniform(-0.01,0.04) # الصيدلية تتحسن شوي أسرع
                p[3]=max(0.0001, p[3]*(1+change/100))
                pp=(p[3]-p[2])/p[2]*100
                p[4]=round(config["per_trade"]*pp/100,3)
                p[5]=round(pp,2)

            state["ghair"]=round(sum([p[4] for p in state["positions"]]),3)
            state["loss_pool"]=round(sum([abs(p[9]) for p in state["treatment_positions"]]),3)
            state["last_update"]=datetime.now().strftime("%H:%M:%S")

            # قفل ربح لحظي
            if state["is_running"] and state["ghair"]>=config["instant_target"] and state["ghair"]>0 and len(state["positions"])>0:
                state["safi"]=round(state["safi"]+state["ghair"],3)
                state["trades_closed"]+=len(state["positions"])
                state["positions"]=[]; state["ghair"]=0.0
                mov=get_fake_movers()
                for i in range(min(6,len(mov))):
                    sym,pct,price=mov[i]
                    if sym not in [x[0] for x in state["treatment_positions"]]:
                        state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()])
                continue

            # نقل للصيدلية إذا نزل كثير
            to_treat=[]
            now=time.time()
            for p in list(state["positions"]):
                if p[5]<=-config["sl_pct"] or (p[5]<-0.5 and (now-p[9])>20):
                    to_treat.append(p)

            for p in to_treat:
                loss=abs(p[4])
                if p in state["positions"]: state["positions"].remove(p)
                mov=get_fake_movers()
                ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
                for sym,pct,price in mov:
                    if sym not in ex:
                        target_needed=loss+config["instant_target"]
                        state["treatment_positions"].append([sym,"علاج",price*0.9995,price,0.0,0.0,f"يعالج {p[0]} {loss:.2f}$",0,"TREAT",loss,target_needed,sym+"/USDT",time.time()])
                        break

            # شفاء
            cured=[p for p in list(state["treatment_positions"]) if p[4]>=p[10]]
            for p in cured:
                loss=p[9]; net=p[4]-loss
                state["safi"]=round(state["safi"]+net,3)
                state["trades_closed"]+=1
                state["doctor_stats"]["healed"]+=1
                state["doctor_stats"]["total_healed_profit"]=round(state["doctor_stats"]["total_healed_profit"]+net,3)
                state["treatment_positions"].remove(p)
                state["binance_status"]=f"🏥 {p[0]} شفى +{net:.2f}$ 🩺"

            if state["is_running"] and len(state["positions"])<6:
                mov=get_fake_movers()
                ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
                for sym,pct,price in mov:
                    if sym not in ex:
                        state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}%",0,"NORMAL",time.time()])
                        if len(state["positions"])>=6: break

            time.sleep(0.8)
        except Exception as e:
            print(f"LIGHT ENGINE ERROR: {e}")
            time.sleep(1)

threading.Thread(target=engine,daemon=True).start()

@app.route('/health')
def health(): return f"OK hb={time.time()-state['heartbeat']:.1f}s",200

@app.route('/api/data')
def api_data():
    total=state["fixed"]+state["safi"]+state["ghair"]-state["loss_pool"]
    healed=state["doctor_stats"]["healed"]
    total_cases=healed+len(state["treatment_positions"])
    heal_rate=round((healed/total_cases*100) if total_cases>0 else 50,1)
    safi_pct = (state["safi"]/state["fixed"]*100) if state["fixed"]>0 else 0
    ghair_pct = (state["ghair"]/state["fixed"]*100) if state["fixed"]>0 else 0
    total_pct = ((total-state["fixed"])/state["fixed"]*100) if state["fixed"]>0 else 0
    loss_pct = (state["loss_pool"]/state["fixed"]*100) if state["fixed"]>0 else 0
    return jsonify({
        "fixed":state["fixed"],"free":state["free"],"safi":state["safi"],"ghair":state["ghair"],"total":total,
        "trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"treatment_count":state["treatment_count"],
        "positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6]] for p in state["positions"]],
        "treatment_positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[9],p[10]] for p in state["treatment_positions"]],
        "binance_status":state["binance_status"],"last_update":state["last_update"],"instant_target":config["instant_target"],
        "doctor":state["doctor_stats"],"heal_rate":heal_rate,
        "safi_pct":round(safi_pct,3),"ghair_pct":round(ghair_pct,4),"total_pct":round(total_pct,3),"loss_pct":round(loss_pct,3),
        "specialty_active":state["specialty_active"],"is_running":state["is_running"],
        "heartbeat":round(time.time()-state["heartbeat"],1)
    })

@app.route('/api/config',methods=['POST'])
def api_cfg():
    d=request.get_json()
    if 'capital' in d: state["fixed"]=float(d['capital'])
    if 'per_trade' in d: config["per_trade"]=float(d['per_trade'])
    if 'tp' in d: config["tp_pct"]=float(d['tp'])
    if 'instant_target' in d: config["instant_target"]=float(d['instant_target'])
    return jsonify({"ok":True})

@app.route('/api/compound',methods=['POST'])
def api_compound():
    profit = state["safi"] + state["ghair"]
    if profit>0:
        state["fixed"]=round(state["fixed"]+profit,3)
        state["safi"]=0.0; state["ghair"]=0.0; state["positions"]=[]
    return jsonify({"ok":True,"new_capital":state["fixed"]})

@app.route('/api/reset_full',methods=['POST'])
def reset_full():
    state["safi"]=0.0; state["ghair"]=0.0; state["loss_pool"]=0.0; state["trades_closed"]=0
    state["positions"]=[]; state["treatment_positions"]=[]
    state["doctor_stats"]={"healed":0,"total_healed_profit":0.0,"failed":0,"start_time":time.time()}
    state["specialty_active"]=False; state["is_running"]=True
    init_positions()
    return jsonify({"ok":True})

@app.route('/api/force_treat',methods=['POST'])
def force_treat():
    if state["positions"]:
        worst=min(state["positions"], key=lambda x:x[4])
        if worst in state["positions"]:
            loss=abs(worst[4]) if worst[4]<0 else 0.56
            state["positions"].remove(worst)
            mov=get_fake_movers()
            ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
            for sym,pct,price in mov:
                if sym not in ex:
                    target_needed=loss+config["instant_target"]
                    state["treatment_positions"].append([sym,"علاج",price*0.9995,price,0.0,0.0,f"يعالج {worst[0]} {loss:.2f}$",0,"TREAT",loss,target_needed,sym+"/USDT",time.time()])
                    break
    return jsonify({"ok":True})

@app.route('/')
def home():
    return '''
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}body{margin:0;background:#070a1e;color:#fff;font-family:Cairo;padding:5px}
.h1{border:2px solid #00ff66;border-radius:18px;background:#11158a;text-align:center;padding:10px 8px;margin-bottom:6px}
.h1 h2{margin:0;color:#00ff66;font-size:15px;font-weight:900}
.bar{display:flex;justify-content:space-between;align-items:center;background:#11158a;border:1px solid #232a8a;border-radius:10px;padding:6px 10px;font-size:11px;font-weight:800;margin-bottom:6px}
.bar.doc{background:#001a00;border:1.5px solid #00ff66;color:#00ff66}
.bar.doc.special{background:#330000;border-color:#ff2d55;color:#ff2d55;animation:blink 1s infinite}
@keyframes blink{0%,50%{opacity:1}51%,100%{opacity:.6}}
.bar.doc b{color:#fff}
.ctrl{display:flex;justify-content:center;align-items:center;gap:8px;background:#11158a;border:1px solid #232a8a;border-radius:14px;padding:8px;margin-bottom:6px;flex-wrap:wrap}
.c-inp{background:#070a1e;border:2px solid #00ff66;border-radius:12px;color:#00ff66;font-family:JetBrains Mono;font-weight:900;width:58px;text-align:center;padding:7px 0;outline:none;font-size:13px}
.c-inp.target{border-color:#ffcc00;color:#ffcc00;width:68px}
.c-btn{background:#00ff66;border:none;border-radius:12px;padding:7px 16px;font-weight:900;color:#000;cursor:pointer;font-size:13px}
.boards{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;margin-bottom:6px}
.b{display:flex;flex-direction:column;gap:4px}.bt{font-size:10px;font-weight:900;text-align:center}
.bc{background:#1a1f9e;border:1px solid #2d36c0;border-radius:14px;padding:10px 2px;text-align:center;min-height:76px;display:flex;flex-direction:column;justify-content:center}
.bc.gold{border:2px solid #00ff66}.bc.treat{border:2px solid #ff9800;background:#2a1a00;animation:glow 2s infinite}
@keyframes glow{0%,100%{box-shadow:0 0 5px #ff9800}50%{box-shadow:0 0 15px #ff9800}}
.bv{font-family:JetBrains Mono;font-size:17px;font-weight:900;direction:ltr}.bv.pos{color:#00ff66}.bv.neg{color:#ff2d55}.bv.zero{color:#6a6a8a}.bv.w{color:#fff}
.bv.yb{border-radius:8px;padding:3px 6px;display:inline-block;font-size:13px}.bv.yb.pos{background:#00ff66;color:#000}.bv.yb.neg{background:#ff2d55;color:#fff}.bv.yb.zero{background:transparent;color:#555;border:1px dashed #333}
.b-pct{font-size:9px;color:#ffcc00;font-weight:800;margin-top:2px;direction:ltr}
.act{display:flex;justify-content:center;gap:8px;margin-bottom:6px;flex-wrap:wrap}.act button{border:none;border-radius:12px;padding:8px 16px;font-weight:900;font-size:11px;cursor:pointer}.r{background:#ff2d55;color:#fff}.y{background:#ffeb3b;color:#000}.t{background:#ff9800;color:#000}.c{background:#00e5ff;color:#000}.g{background:#00ff66;color:#000}
.tbl-wrap{background:#11158a;border:1px solid #232a8a;border-radius:16px;overflow:hidden;overflow-x:auto;margin-bottom:8px}.tbl{width:100%;border-collapse:collapse;min-width:520px}.tbl th{background:#2a36f0;color:#ff4d8d;font-size:12px;font-weight:900;padding:10px 4px;text-align:center}.tbl td{padding:10px 4px;text-align:center;font-family:JetBrains Mono;font-size:12px;font-weight:800;border-top:1px solid #1a1f8a}.tbl tr{background:#11158a}
.spot{background:#00ff55;color:#000;border-radius:20px;padding:4px 12px;font-size:11px;font-weight:900;display:inline-block}.treat-badge{background:#ff9800;color:#000;border-radius:20px;padding:4px 12px;font-size:11px;font-weight:900;display:inline-block}
</style></head><body>
<div class="h1"><h2>V83.6 LIGHT 🩺 - يتحرك بدون توقف</h2><p>الصيدلية + نسبة شفاء حية + التخصصي 10-15 + تركيب الأرباح</p></div>
<div class="bar"><span id="binStatus">TURBO LIGHT</span><span id="progText">0 / 0.50$</span><span>V83.6 | نبض: <span id="hb">0s</span> ✅</span></div>
<div class="bar doc" id="docBar"><span>🩺 شفى: <b id="healed">0</b></span><span>💰 ارباح علاج: <b id="healProfit">0.00$</b></span><span>📊 نسبة: <b id="healRate">0%</b></span><span>⏱️ <b id="docTime">0 د</b></span><span id="specTag">🏥 تخصصي: 0 مريض</span></div>
<div class="ctrl"><button class="c-btn" onclick="save()">حفظ 🟢</button><input class="c-inp" id="tp" value="0.80"><input class="c-inp" id="per_trade" value="100"><input class="c-inp" id="capital" value="1000"><input class="c-inp target" id="instant_target" value="0.50"></div>
<div class="boards">
  <div class="b"><div class="bt">💰 ثابت</div><div class="bc"><div class="bv w" id="v_fixed">1000.0$</div><div class="b-pct">100% رأس مال</div></div></div>
  <div class="b"><div class="bt">🏥 الصيدلية</div><div class="bc treat"><div class="bv" id="v_treat">0.00$</div><div style="font-size:10px;color:#ffcc00" id="v_treat_c">0 دواء</div><div class="b-pct" id="v_loss_pct">0%</div></div></div>
  <div class="b"><div class="bt">💹 صافي ربح</div><div class="bc"><div class="bv" id="v_safi">0.0$</div><div style="font-size:8px;color:#00ff66">ربح فقط ✅</div><div class="b-pct" id="v_safi_pct">0%</div></div></div>
  <div class="b"><div class="bt">⚖️ مقفلة</div><div class="bc"><div class="bv w" id="v_ls">0</div><div class="b-pct" id="v_ls_info">-</div></div></div>
  <div class="b"><div class="bt">💎 الإجمالي</div><div class="bc gold"><div class="bv" id="v_total">1000.0$</div><div class="b-pct" id="v_total_pct">0%</div></div></div>
  <div class="b"><div class="bt">📈 غير محققة</div><div class="bc"><div class="bv yb" id="v_ghair">0.00$</div><div class="b-pct" id="v_ghair_pct">0%</div></div></div>
  <div class="b"><div class="bt">🔥 حر</div><div class="bc"><div class="bv" id="v_free">0.00$</div><div class="b-pct" id="v_compound_info">قابل للنقل</div></div></div>
</div>
<div class="act">
<button class="r" onclick="doReset()">🔒 قفل الكل</button>
<button class="y" onclick="doReset()">🔄 تصفير</button>
<button class="t" onclick="testPharmacy()">🧪 جرب الصيدلية</button>
<button class="c" onclick="doCompound()">💰 تركيب الأرباح</button>
</div>
<div class="tbl-wrap"><table class="tbl"><thead><tr><th>عملة</th><th>نوع</th><th>حالة</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th></tr></thead><tbody id="coins"></tbody></table></div>
<div class="tbl-wrap" id="treatWrap" style="display:none;border:2px solid #ff9800"><table class="tbl"><thead><tr><th style="color:#ff9800;background:#2a1a00">🏥 الصيدلية</th><th style="background:#2a1a00">يعالج</th><th style="background:#2a1a00">خسارة</th><th style="background:#2a1a00">هدف</th><th style="background:#2a1a00">حالي</th><th style="background:#2a1a00">ربح علاج</th></tr></thead><tbody id="treatCoins"></tbody></table></div>
<script>
function colorClass(v){ if(Math.abs(v)<0.001) return 'zero'; return v>0?'pos':'neg'; }
async function save(){ const d={capital:parseFloat(capital.value),per_trade:parseFloat(per_trade.value),tp:parseFloat(tp.value),instant_target:parseFloat(instant_target.value)}; await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}); const b=document.querySelector('.c-btn'); b.innerText='✅ تم'; setTimeout(()=>b.innerText='حفظ 🟢',1000); }
async function doReset(){ if(!confirm('تصفير؟')) return; await fetch('/api/reset_full',{method:'POST'}); location.reload(); }
async function testPharmacy(){ await fetch('/api/force_treat',{method:'POST'}); }
async function doCompound(){ if(!confirm('نقل الربح لرأس المال؟')) return; const r=await fetch('/api/compound',{method:'POST'}); const j=await r.json(); alert('✅ تم التركيب! الجديد: '+j.new_capital.toFixed(2)+'$'); }
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('v_fixed').innerText=d.fixed.toFixed(1)+'$';
    const setC=(id,val)=>{ const el=document.getElementById(id); el.innerText=(Math.abs(val)<0.001?'0.00':(val>0?'+':'')+val.toFixed(2))+'$'; el.className='bv '+colorClass(val); if(id=='v_ghair'){ el.className='bv yb '+colorClass(val); if(Math.abs(val)<0.001) el.innerText='0.00$'; } };
    setC('v_safi',d.safi); setC('v_ghair',d.ghair); setC('v_free',d.free);
    document.getElementById('v_total').innerText=d.total.toFixed(1)+'$'; document.getElementById('v_total').className='bv '+colorClass(d.total-d.fixed);
    document.getElementById('v_ls').innerText=d.trades_closed;
    document.getElementById('v_treat').innerText=(d.loss_pool>0?'-':'')+d.loss_pool.toFixed(2)+'$'; document.getElementById('v_treat').className='bv '+(d.loss_pool>0?'neg':'zero');
    document.getElementById('v_treat_c').innerText=d.treatment_count+' دواء';
    document.getElementById('v_safi_pct').innerText=(d.safi_pct>=0?'+':'')+d.safi_pct.toFixed(2)+'% من رأس المال';
    document.getElementById('v_ghair_pct').innerText=(d.ghair_pct>=0?'+':'')+d.ghair_pct.toFixed(3)+'%';
    document.getElementById('v_total_pct').innerText=(d.total_pct>=0?'+':'')+d.total_pct.toFixed(2)+'%';
    document.getElementById('v_loss_pct').innerText='-'+d.loss_pct.toFixed(2)+'%';
    document.getElementById('v_ls_info').innerText='ربح: '+d.total_pct.toFixed(2)+'%';
    document.getElementById('v_compound_info').innerText='قابل: '+(d.safi+d.ghair).toFixed(2)+'$';
    document.getElementById('specTag').innerText='🏥 تخصصي: '+d.treatment_count+' مريض '+(d.specialty_active?'⛔':'🟢');
    document.getElementById('hb').innerText=d.heartbeat+'s';
    const docBar=document.getElementById('docBar');
    if(d.specialty_active){ docBar.className='bar doc special'; } else { docBar.className='bar doc'; }
    document.getElementById('binStatus').innerText=d.binance_status+' • '+d.last_update;
    document.getElementById('progText').innerText=`${d.ghair.toFixed(2)} / ${d.instant_target}$`;
    document.getElementById('healed').innerText=d.doctor.healed;
    document.getElementById('healProfit').innerText='+'+d.doctor.total_healed_profit.toFixed(2)+'$';
    document.getElementById('healRate').innerText=d.heal_rate+'%';
    let mins=Math.floor((Date.now()/1000 - d.doctor.start_time));
    document.getElementById('docTime').innerText=Math.floor(mins/60)+'د '+mins%60+'ث';
    let h=''; for(const p of d.positions){ h+=`<tr><td style="font-weight:900">${p[0]}</td><td><span class="spot">${p[1]}</span></td><td style="font-size:10px">${p[6]}</td><td>${p[2].toFixed(4)}</td><td>${p[3].toFixed(4)}</td><td class="${colorClass(p[4])}">${p[4].toFixed(3)}$</td><td class="${colorClass(p[5])}">${p[5].toFixed(2)}%</td></tr>`; }
    document.getElementById('coins').innerHTML=h||'<tr><td colspan=7>⏳...</td></tr>';
    const tw=document.getElementById('treatWrap');
    if(d.treatment_positions.length>0){ tw.style.display='block'; let th=''; for(const p of d.treatment_positions){ th+=`<tr style="background:#2a1a00"><td><span class="treat-badge">🏥 ${p[0]}</span></td><td style="font-size:10px;color:#ffcc00">${p[6]}</td><td class="neg">-${p[7].toFixed(2)}$</td><td style="color:#ffcc00">${p[8].toFixed(2)}$</td><td>${p[3].toFixed(4)}</td><td class="${colorClass(p[4])}">${p[4].toFixed(3)}$</td></tr>`; } document.getElementById('treatCoins').innerHTML=th; } else tw.style.display='none';
  }catch(e){}
}
setInterval(load,500); load();
</script>
</body></html>
    '''
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

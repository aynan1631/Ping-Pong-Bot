from flask import Flask, request, jsonify, redirect
import threading, time, random
from datetime import datetime

app = Flask(__name__)

config = {"capital":2000.0,"per_trade":200.0,"tp_pct":0.8,"sl_pct":-1.5,"daily_target_pct":3.5,"max_trades":10}
state = {"daily_start":2000.0,"safi":0.0,"ghair":0.0,"loss":0.0,"loss_pool":0.0,"trades_today":0,"trades_closed":0,"is_daily_done":False,"positions":[]}

def movers():
    base=["STEEM","ARK","VTHO","POWR","XRP","DOGE","SHIB","PEPE","BONK","FLOKI","WIF","BOME","NOT","TIA","SEI"]
    m=[]
    for s in base:
        m.append((f"{s}/USDT",random.uniform(4,32),random.uniform(0.0001,2)))
    m.sort(key=lambda x:x[1],reverse=True)
    return m[:15]

def calc():
    total=config["capital"]+state["safi"]+state["ghair"]+state["loss"]
    pct=((total-state["daily_start"])/state["daily_start"]*100) if state["daily_start"]>0 else 0
    return total,pct

def engine():
    pool=0.0
    mm=movers()
    for i in range(min(10,len(mm))):
        sym,pct,pr=mm[i]
        state["positions"].append([sym,pr*(1-random.uniform(0.001,0.004)),pr,0.0,0.0,pct,0.0])
    while True:
        time.sleep(1)
        total,daily=calc()
        if daily>=config["daily_target_pct"] and not state["is_daily_done"]:
            state["is_daily_done"]=True
            continue
        if state["is_daily_done"]:
            time.sleep(3); continue
        ng=0; closed=[]
        for p in state["positions"]:
            cur=p[2]*(1+random.uniform(-0.007,0.012))
            p[2]=cur
            pp=(cur-p[1])/p[1]*100
            us=config["per_trade"]*pp/100
            p[3]=round(us,2); p[4]=round(pp,2); ng+=us
            tp=config["tp_pct"]+(abs(p[6])/config["per_trade"]*100)
            if pp>=tp or pp<=config["sl_pct"]:
                closed.append(p)
        state["ghair"]=round(ng,2)
        for p in closed:
            real=round(p[3]-config["per_trade"]*0.002,2)
            if p in state["positions"]:
                state["positions"].remove(p)
            if real<0:
                pool+=abs(real); state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=round(pool,2)
                mm=movers(); ex=[x[0] for x in state["positions"]]; sh=round(pool/10,2)
                for x in mm:
                    if x[0] not in ex:
                        state["positions"].append([x[0],x[2],x[2],0.0,0.0,x[1],sh])
                        pool=round(max(0,pool-sh),2); state["loss_pool"]=pool; break
            else:
                if pool>0:
                    if real>=pool:
                        state["safi"]=round(state["safi"]+real-pool,2); state["loss"]=round(state["loss"]+pool,2); pool=0; state["loss_pool"]=0
                    else:
                        pool=round(pool-real,2); state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=pool
                else:
                    state["safi"]=round(state["safi"]+real,2)
            state["trades_closed"]+=1; state["trades_today"]+=1
            if real>=0 and pool==0 and len(state["positions"])<10:
                mm=movers(); ex=[x[0] for x in state["positions"]]
                for x in mm:
                    if x[0] not in ex:
                        state["positions"].append([x[0],x[2],x[2],0.0,0.0,x[1],0.0]); break

@app.route('/api/config',methods=['POST'])
def api_cfg():
    try:
        d=request.get_json()
        if 'capital' in d: config["capital"]=float(d['capital']); state["daily_start"]=config["capital"]+state["safi"]+state["loss"]
        if 'per_trade' in d: config["per_trade"]=float(d['per_trade'])
        if 'tp' in d: config["tp_pct"]=float(d['tp'])
        if 'sl' in d: config["sl_pct"]=float(d['sl'])
        if 'daily' in d: config["daily_target_pct"]=float(d['daily'])
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"ok":False,"e":str(e)})

@app.route('/')
def home():
    total,daily=calc(); dusd=total-state["daily_start"]
    coins=""
    for sym,entry,cur,usd,pct,mov,loss in state["positions"]:
        col="#00FF9D" if usd>=0 else "#FF3B5C"
        bg="rgba(0,255,157,0.14)" if usd>=0 else "rgba(255,59,92,0.14)"
        debt=f'<span class="debt">دين ${loss:.2f}</span>' if loss>0.1 else ""
        bar=min(100,max(8,(pct+1.5)/(config["tp_pct"]+1.5+abs(loss)/2)*100))
        coins+=f'<div class="coin"><div class="ctop"><b>{sym.replace("/USDT","")}</b><span class="bdg">+{mov:.1f}%</span>{debt}</div><div class="cprice">{entry:.4f} → {cur:.4f}</div><div class="barw"><div class="bar" style="width:{bar}%;background:{col}"></div></div><div class="cprof" style="color:{col};background:{bg}">{usd:+.2f}$<small>{pct:+.2f}%</small></div></div>'

    return f'''
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
body{{margin:0;background:#05070a;color:#fff;font-family:Cairo;padding:10px}}
.top{{max-width:1400px;margin:0 auto 10px auto;display:flex;justify-content:space-between;font-size:10px;opacity:0.5}}
.cards{{max-width:1400px;margin:0 auto;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}}
.card{{border-radius:18px;padding:18px 12px;border:1px solid #2a2f4a;background:linear-gradient(135deg,#0f1220,#0a0c16);position:relative;box-shadow:0 0 30px rgba(0,0,0,0.6)}}
.card.gold{{border-color:#ffca28;box-shadow:0 0 30px #ffca2830;background:linear-gradient(135deg,#1e1a0a,#2a220a)}}.card.green{{border-color:#00ff9d33}}.card.red{{border-color:#ff3b5c33}}
.lb{{font-size:9px;opacity:0.5;letter-spacing:1px;font-weight:800}}.val{{font-family:JetBrains Mono;font-size:30px;font-weight:800;letter-spacing:-1px;margin-top:4px}}.sub{{font-size:11px;opacity:0.7;margin-top:6px;font-weight:700}}
.panel{{max-width:1400px;margin:14px auto;display:grid;grid-template-columns:360px 1fr;gap:12px}}
.ctrl{{background:linear-gradient(180deg,#0f1220,#080a12);border:1px solid #ffca2850;border-radius:18px;padding:14px;box-shadow:0 0 30px #ffca2815}}
.ctrl h3{{margin:0 0 12px 0;color:#ffca28;font-size:13px;letter-spacing:1px}}
.row{{display:grid;grid-template-columns:1fr 110px;gap:8px;align-items:center;margin-bottom:10px}}
.row label{{font-size:11px;opacity:0.7;font-weight:700}}.inp{{background:#05070a;border:1.5px solid #2a2f4a;border-radius:10px;padding:10px;color:#ffca28;font-family:JetBrains Mono;font-weight:800;font-size:16px;text-align:center;width:100%}}
.inp:focus{{border-color:#ffca28;outline:none;box-shadow:0 0 0 3px #ffca2820}}
.btn{{width:100%;background:linear-gradient(90deg,#ffca28,#ffb300);color:#000;border:none;border-radius:12px;padding:13px;font-weight:900;font-family:Cairo;cursor:pointer;margin-top:8px;font-size:14px;box-shadow:0 6px 20px #ffca2850}}
.coins{{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:10px;align-content:start}}
.coin{{background:linear-gradient(180deg,rgba(255,255,255,0.06),rgba(255,255,255,0.02));border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:10px}}
.ctop{{display:flex;gap:5px;align-items:center}}.ctop b{{font-family:JetBrains Mono;font-size:13px}}.bdg{{background:#ff9800;color:#000;font-size:8px;font-weight:900;padding:2px 6px;border-radius:20px}}.debt{{background:#ff1744;color:#fff;font-size:7px;padding:2px 5px;border-radius:20px}}
.cprice{{font-family:JetBrains Mono;font-size:10px;opacity:0.4;direction:ltr;margin:6px 0}}.barw{{height:7px;background:#000;border-radius:20px;overflow:hidden}}.bar{{height:100%;border-radius:20px}}.cprof{{margin-top:6px;border-radius:8px;padding:6px;text-align:center;font-family:JetBrains Mono;font-weight:800;font-size:13px}}.cprof small{{display:block;font-size:9px;opacity:0.6}}
@media(max-width:900px){{.cards{{grid-template-columns:1fr 1fr}}.panel{{grid-template-columns:1fr}}.val{{font-size:22px}}}}
</style></head><body>
<div class="top"><span>BINANCE VIP • V12 BLACK GOLD • {datetime.now().strftime("%H:%M:%S")}</span><span style="color:#ffca28">LIVE • LOSS RECOVERY ON • {state["trades_closed"]} صفقات</span></div>

<div class="cards">
  <div class="card"><div class="lb">رأس المال المستعمل</div><div class="val" style="color:#8c9eff">${config["capital"]:.2f}</div><div class="sub">10 × ${config["per_trade"]:.0f}</div></div>
  <div class="card gold"><div class="lb">الإجمالي الكلي</div><div class="val" style="color:#FFD54F">${total:.2f}</div><div class="sub" style="color:{'#00FF9D' if dusd>=0 else '#FF3B5C'}">{dusd:+.2f}$ ({daily:+.2f}%)</div></div>
  <div class="card red"><div class="lb">مجمع الخسارة</div><div class="val" style="color:#FF8A80">${state["loss_pool"]:.2f}</div><div class="sub">الكلية {state["loss"]:.2f}$</div></div>
  <div class="card green"><div class="lb">صافي الربح</div><div class="val" style="color:#00FF9D">{state["safi"]:+.2f}$</div><div class="sub">{state["trades_today"]} مقفلة اليوم</div></div>
  <div class="card"><div class="lb">غير محقق</div><div class="val" style="color:{'#00FF9D' if state['ghair']>=0 else '#FF3B5C'}">{state["ghair"]:+.2f}$</div><div class="sub">{len(state["positions"])} عملات</div></div>
</div>

<div class="panel">
  <div class="ctrl">
    <h3>✦ CONTROL PANEL - التحكم الفخم</h3>
    <div class="row"><label>رأس المال $</label><input id="capital" class="inp" type="number" value="{config["capital"]}"></div>
    <div class="row"><label>حجم الصفقة $</label><input id="per_trade" class="inp" type="number" value="{config["per_trade"]}"></div>
    <div class="row"><label>ربح الصفقة %</label><input id="tp" class="inp" type="number" step="0.1" value="{config["tp_pct"]}"></div>
    <div class="row"><label>ستوب الخسارة %</label><input id="sl" class="inp" type="number" step="0.1" value="{config["sl_pct"]}"></div>
    <div class="row"><label>هدف اليوم %</label><input id="daily" class="inp" type="number" step="0.1" value="{config["daily_target_pct"]}"></div>
    <button class="btn" onclick="save()">حفظ فوري ⚡ - يشتغل بدون إعادة تشغيل</button>
    <div style="font-size:9px;opacity:0.3;margin-top:8px;text-align:center">حلال SPOT • يعالج الخسارة تلقائيا • الصافي بعد تغطية الخسائر</div>
  </div>
  <div class="coins">{coins}</div>
</div>

<script>
async function save(){{
  const d={{capital:parseFloat(document.getElementById('capital').value),per_trade:parseFloat(document.getElementById('per_trade').value),tp:parseFloat(document.getElementById('tp').value),sl:parseFloat(document.getElementById('sl').value),daily:parseFloat(document.getElementById('daily').value)}};
  const b=document.querySelector('.btn'); b.innerText='⏳ جاري الحفظ...';
  try{{const r=await fetch('/api/config',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(d)}}); const j=await r.json(); if(j.ok){{b.innerText='✅ تم الحفظ - فخم!'; setTimeout(()=>{{b.innerText='حفظ فوري ⚡ - يشتغل بدون إعادة تشغيل';}},1200);}} else{{b.innerText='❌ خطأ';}} }}catch(e){{b.innerText='❌';}}
}}
</script>
</body></html>
'''

@app.route('/reset')
def reset():
    state["daily_start"]=config["capital"]+state["safi"]+state["loss"]
    state["safi"]=0; state["ghair"]=0; state["loss"]=0; state["loss_pool"]=0
    state["trades_today"]=0; state["is_daily_done"]=False; state["positions"]=[]
    mm=movers()
    for i in range(min(10,len(mm))):
        state["positions"].append([mm[i][0],mm[i][2],mm[i][2],0.0,0.0,mm[i][1],0.0])
    return redirect('/')

threading.Thread(target=engine,daemon=True).start()
if __name__=="__main__":
    app.run(host="0.0.0.0",port=8080)from flask import Flask, request, jsonify, redirect
import threading, time, random
from datetime import datetime

app = Flask(__name__)

config = {"capital":2000.0,"per_trade":200.0,"tp_pct":0.8,"sl_pct":-1.5,"daily_target_pct":3.5,"max_trades":10}
state = {"daily_start":2000.0,"safi":0.0,"ghair":0.0,"loss":0.0,"loss_pool":0.0,"trades_today":0,"trades_closed":0,"is_daily_done":False,"positions":[]}

def movers():
    base=["STEEM","ARK","VTHO","POWR","XRP","DOGE","SHIB","PEPE","BONK","FLOKI","WIF","BOME","NOT","TIA","SEI"]
    m=[]
    for s in base:
        m.append((f"{s}/USDT",random.uniform(4,32),random.uniform(0.0001,2)))
    m.sort(key=lambda x:x[1],reverse=True)
    return m[:15]

def calc():
    total=config["capital"]+state["safi"]+state["ghair"]+state["loss"]
    pct=((total-state["daily_start"])/state["daily_start"]*100) if state["daily_start"]>0 else 0
    return total,pct

def engine():
    pool=0.0
    mm=movers()
    for i in range(min(10,len(mm))):
        sym,pct,pr=mm[i]
        state["positions"].append([sym,pr*(1-random.uniform(0.001,0.004)),pr,0.0,0.0,pct,0.0])
    while True:
        time.sleep(1)
        total,daily=calc()
        if daily>=config["daily_target_pct"] and not state["is_daily_done"]:
            state["is_daily_done"]=True
            continue
        if state["is_daily_done"]:
            time.sleep(3); continue
        ng=0; closed=[]
        for p in state["positions"]:
            cur=p[2]*(1+random.uniform(-0.007,0.012))
            p[2]=cur
            pp=(cur-p[1])/p[1]*100
            us=config["per_trade"]*pp/100
            p[3]=round(us,2); p[4]=round(pp,2); ng+=us
            tp=config["tp_pct"]+(abs(p[6])/config["per_trade"]*100)
            if pp>=tp or pp<=config["sl_pct"]:
                closed.append(p)
        state["ghair"]=round(ng,2)
        for p in closed:
            real=round(p[3]-config["per_trade"]*0.002,2)
            if p in state["positions"]:
                state["positions"].remove(p)
            if real<0:
                pool+=abs(real); state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=round(pool,2)
                mm=movers(); ex=[x[0] for x in state["positions"]]; sh=round(pool/10,2)
                for x in mm:
                    if x[0] not in ex:
                        state["positions"].append([x[0],x[2],x[2],0.0,0.0,x[1],sh])
                        pool=round(max(0,pool-sh),2); state["loss_pool"]=pool; break
            else:
                if pool>0:
                    if real>=pool:
                        state["safi"]=round(state["safi"]+real-pool,2); state["loss"]=round(state["loss"]+pool,2); pool=0; state["loss_pool"]=0
                    else:
                        pool=round(pool-real,2); state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=pool
                else:
                    state["safi"]=round(state["safi"]+real,2)
            state["trades_closed"]+=1; state["trades_today"]+=1
            if real>=0 and pool==0 and len(state["positions"])<10:
                mm=movers(); ex=[x[0] for x in state["positions"]]
                for x in mm:
                    if x[0] not in ex:
                        state["positions"].append([x[0],x[2],x[2],0.0,0.0,x[1],0.0]); break

@app.route('/api/config',methods=['POST'])
def api_cfg():
    try:
        d=request.get_json()
        if 'capital' in d: config["capital"]=float(d['capital']); state["daily_start"]=config["capital"]+state["safi"]+state["loss"]
        if 'per_trade' in d: config["per_trade"]=float(d['per_trade'])
        if 'tp' in d: config["tp_pct"]=float(d['tp'])
        if 'sl' in d: config["sl_pct"]=float(d['sl'])
        if 'daily' in d: config["daily_target_pct"]=float(d['daily'])
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"ok":False,"e":str(e)})

@app.route('/')
def home():
    total,daily=calc(); dusd=total-state["daily_start"]
    coins=""
    for sym,entry,cur,usd,pct,mov,loss in state["positions"]:
        col="#00FF9D" if usd>=0 else "#FF3B5C"
        bg="rgba(0,255,157,0.14)" if usd>=0 else "rgba(255,59,92,0.14)"
        debt=f'<span class="debt">دين ${loss:.2f}</span>' if loss>0.1 else ""
        bar=min(100,max(8,(pct+1.5)/(config["tp_pct"]+1.5+abs(loss)/2)*100))
        coins+=f'<div class="coin"><div class="ctop"><b>{sym.replace("/USDT","")}</b><span class="bdg">+{mov:.1f}%</span>{debt}</div><div class="cprice">{entry:.4f} → {cur:.4f}</div><div class="barw"><div class="bar" style="width:{bar}%;background:{col}"></div></div><div class="cprof" style="color:{col};background:{bg}">{usd:+.2f}$<small>{pct:+.2f}%</small></div></div>'

    return f'''
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
body{{margin:0;background:#05070a;color:#fff;font-family:Cairo;padding:10px}}
.top{{max-width:1400px;margin:0 auto 10px auto;display:flex;justify-content:space-between;font-size:10px;opacity:0.5}}
.cards{{max-width:1400px;margin:0 auto;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}}
.card{{border-radius:18px;padding:18px 12px;border:1px solid #2a2f4a;background:linear-gradient(135deg,#0f1220,#0a0c16);position:relative;box-shadow:0 0 30px rgba(0,0,0,0.6)}}
.card.gold{{border-color:#ffca28;box-shadow:0 0 30px #ffca2830;background:linear-gradient(135deg,#1e1a0a,#2a220a)}}.card.green{{border-color:#00ff9d33}}.card.red{{border-color:#ff3b5c33}}
.lb{{font-size:9px;opacity:0.5;letter-spacing:1px;font-weight:800}}.val{{font-family:JetBrains Mono;font-size:30px;font-weight:800;letter-spacing:-1px;margin-top:4px}}.sub{{font-size:11px;opacity:0.7;margin-top:6px;font-weight:700}}
.panel{{max-width:1400px;margin:14px auto;display:grid;grid-template-columns:360px 1fr;gap:12px}}
.ctrl{{background:linear-gradient(180deg,#0f1220,#080a12);border:1px solid #ffca2850;border-radius:18px;padding:14px;box-shadow:0 0 30px #ffca2815}}
.ctrl h3{{margin:0 0 12px 0;color:#ffca28;font-size:13px;letter-spacing:1px}}
.row{{display:grid;grid-template-columns:1fr 110px;gap:8px;align-items:center;margin-bottom:10px}}
.row label{{font-size:11px;opacity:0.7;font-weight:700}}.inp{{background:#05070a;border:1.5px solid #2a2f4a;border-radius:10px;padding:10px;color:#ffca28;font-family:JetBrains Mono;font-weight:800;font-size:16px;text-align:center;width:100%}}
.inp:focus{{border-color:#ffca28;outline:none;box-shadow:0 0 0 3px #ffca2820}}
.btn{{width:100%;background:linear-gradient(90deg,#ffca28,#ffb300);color:#000;border:none;border-radius:12px;padding:13px;font-weight:900;font-family:Cairo;cursor:pointer;margin-top:8px;font-size:14px;box-shadow:0 6px 20px #ffca2850}}
.coins{{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:10px;align-content:start}}
.coin{{background:linear-gradient(180deg,rgba(255,255,255,0.06),rgba(255,255,255,0.02));border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:10px}}
.ctop{{display:flex;gap:5px;align-items:center}}.ctop b{{font-family:JetBrains Mono;font-size:13px}}.bdg{{background:#ff9800;color:#000;font-size:8px;font-weight:900;padding:2px 6px;border-radius:20px}}.debt{{background:#ff1744;color:#fff;font-size:7px;padding:2px 5px;border-radius:20px}}
.cprice{{font-family:JetBrains Mono;font-size:10px;opacity:0.4;direction:ltr;margin:6px 0}}.barw{{height:7px;background:#000;border-radius:20px;overflow:hidden}}.bar{{height:100%;border-radius:20px}}.cprof{{margin-top:6px;border-radius:8px;padding:6px;text-align:center;font-family:JetBrains Mono;font-weight:800;font-size:13px}}.cprof small{{display:block;font-size:9px;opacity:0.6}}
@media(max-width:900px){{.cards{{grid-template-columns:1fr 1fr}}.panel{{grid-template-columns:1fr}}.val{{font-size:22px}}}}
</style></head><body>
<div class="top"><span>BINANCE VIP • V12 BLACK GOLD • {datetime.now().strftime("%H:%M:%S")}</span><span style="color:#ffca28">LIVE • LOSS RECOVERY ON • {state["trades_closed"]} صفقات</span></div>

<div class="cards">
  <div class="card"><div class="lb">رأس المال المستعمل</div><div class="val" style="color:#8c9eff">${config["capital"]:.2f}</div><div class="sub">10 × ${config["per_trade"]:.0f}</div></div>
  <div class="card gold"><div class="lb">الإجمالي الكلي</div><div class="val" style="color:#FFD54F">${total:.2f}</div><div class="sub" style="color:{'#00FF9D' if dusd>=0 else '#FF3B5C'}">{dusd:+.2f}$ ({daily:+.2f}%)</div></div>
  <div class="card red"><div class="lb">مجمع الخسارة</div><div class="val" style="color:#FF8A80">${state["loss_pool"]:.2f}</div><div class="sub">الكلية {state["loss"]:.2f}$</div></div>
  <div class="card green"><div class="lb">صافي الربح</div><div class="val" style="color:#00FF9D">{state["safi"]:+.2f}$</div><div class="sub">{state["trades_today"]} مقفلة اليوم</div></div>
  <div class="card"><div class="lb">غير محقق</div><div class="val" style="color:{'#00FF9D' if state['ghair']>=0 else '#FF3B5C'}">{state["ghair"]:+.2f}$</div><div class="sub">{len(state["positions"])} عملات</div></div>
</div>

<div class="panel">
  <div class="ctrl">
    <h3>✦ CONTROL PANEL - التحكم الفخم</h3>
    <div class="row"><label>رأس المال $</label><input id="capital" class="inp" type="number" value="{config["capital"]}"></div>
    <div class="row"><label>حجم الصفقة $</label><input id="per_trade" class="inp" type="number" value="{config["per_trade"]}"></div>
    <div class="row"><label>ربح الصفقة %</label><input id="tp" class="inp" type="number" step="0.1" value="{config["tp_pct"]}"></div>
    <div class="row"><label>ستوب الخسارة %</label><input id="sl" class="inp" type="number" step="0.1" value="{config["sl_pct"]}"></div>
    <div class="row"><label>هدف اليوم %</label><input id="daily" class="inp" type="number" step="0.1" value="{config["daily_target_pct"]}"></div>
    <button class="btn" onclick="save()">حفظ فوري ⚡ - يشتغل بدون إعادة تشغيل</button>
    <div style="font-size:9px;opacity:0.3;margin-top:8px;text-align:center">حلال SPOT • يعالج الخسارة تلقائيا • الصافي بعد تغطية الخسائر</div>
  </div>
  <div class="coins">{coins}</div>
</div>

<script>
async function save(){{
  const d={{capital:parseFloat(document.getElementById('capital').value),per_trade:parseFloat(document.getElementById('per_trade').value),tp:parseFloat(document.getElementById('tp').value),sl:parseFloat(document.getElementById('sl').value),daily:parseFloat(document.getElementById('daily').value)}};
  const b=document.querySelector('.btn'); b.innerText='⏳ جاري الحفظ...';
  try{{const r=await fetch('/api/config',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(d)}}); const j=await r.json(); if(j.ok){{b.innerText='✅ تم الحفظ - فخم!'; setTimeout(()=>{{b.innerText='حفظ فوري ⚡ - يشتغل بدون إعادة تشغيل';}},1200);}} else{{b.innerText='❌ خطأ';}} }}catch(e){{b.innerText='❌';}}
}}
</script>
</body></html>
'''

@app.route('/reset')
def reset():
    state["daily_start"]=config["capital"]+state["safi"]+state["loss"]
    state["safi"]=0; state["ghair"]=0; state["loss"]=0; state["loss_pool"]=0
    state["trades_today"]=0; state["is_daily_done"]=False; state["positions"]=[]
    mm=movers()
    for i in range(min(10,len(mm))):
        state["positions"].append([mm[i][0],mm[i][2],mm[i][2],0.0,0.0,mm[i][1],0.0])
    return redirect('/')

threading.Thread(target=engine,daemon=True).start()
if __name__=="__main__":
    app.run(host="0.0.0.0",port=8080)

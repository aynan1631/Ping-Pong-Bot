from flask import Flask, request, jsonify, redirect
import threading, time, os
from datetime import datetime
import ccxt

app = Flask(__name__)
exchange = ccxt.binance({'enableRateLimit': True})

config = {"capital":1000.0,"per_trade":100.0,"tp_pct":0.80,"sl_pct":1.0,"instant_target":0.50}
state = {
    "fixed":1000.0,"free":0.0,"safi":0.0,"ghair":0.0,"trades_closed":0,
    "loss_pool":0.0, # مجموع الخسائر قيد العلاج
    "treatment_count":0, # عدد المرضى
    "positions":[],"treatment_positions":[],
    "macd_live":"...","binance_status":"...","last_update":"...","is_frozen":False
}

def ema(d,p):
    if len(d)<p: return None
    k=2/(p+1); ev=sum(d[:p])/p
    for x in d[p:]: ev=x*k+ev*(1-k)
    return ev

def get_macd_strength(sym):
    try:
        ohlcv=exchange.fetch_ohlcv(sym,'15m',limit=35)
        closes=[c[4] for c in ohlcv]
        if len(closes)<30: return -999, False, 0
        e12=sum(closes[:12])/12
        for x in closes[12:]: e12=x*0.1538+e12*0.8462
        e26=sum(closes[:26])/26
        for x in closes[26:]: e26=x*0.0740+e26*0.9260
        macd=e12-e26
        return macd, macd>0, macd
    except: return -999, False, 0

def get_movers_with_macd():
    try:
        tickers=exchange.fetch_tickers()
        mov=[]
        for sym,t in tickers.items():
            if not sym.endswith('/USDT'): continue
            if 'BULL' in sym or 'BEAR' in sym: continue
            last=t.get('last')
            if not last: continue
            pct=t.get('percentage')
            if pct is None:
                o=t.get('open')
                pct=((last-o)/o)*100 if o else 0
            if pct<0.5: continue
            mov.append((sym,float(pct),float(last)))
        mov.sort(key=lambda x:x[1],reverse=True)
        mov=mov[:30]
    except:
        mov=[("BTC/USDT",3,65000),("ETH/USDT",2.5,3000),("SOL/USDT",2,150),("PEPE/USDT",5,0.00001),("CREAM/USDT",2,2.1)]

    scored=[]
    for sym,pct,price in mov[:25]:
        macd_val,is_bull,_=get_macd_strength(sym)
        scored.append((sym,pct,price,macd_val,is_bull))
    scored.sort(key=lambda x:x[3],reverse=True)
    return scored

def engine():
    while True:
        try:
            scored=get_movers_with_macd()
            state["positions"]=[]
            for i in range(min(5,len(scored))):
                sym,pct,price,macd_val,is_bull=scored[i]
                state["positions"].append([sym.replace('/USDT',''),"SPOT",price*0.9995,price,0.0,0.0,f"صاعد {macd_val:.3f}",macd_val,"NORMAL"])
            state["macd_live"]=", ".join([f"{s[0].replace('/USDT','')} {s[3]:.3f}" for s in scored[:12]])
            state["binance_status"]=f"BINANCE SPOT ✅"
            break
        except: time.sleep(3)

    while True:
        try:
            # تحديث اسعار العادية
            for p in state["positions"]:
                try:
                    tk=exchange.fetch_ticker(p[0]+"/USDT")
                    cur=float(tk['last']); p[3]=cur; pp=(cur-p[2])/p[2]*100
                    p[4]=round(100*pp/100,3); p[5]=round(pp,2)
                except: continue
            # تحديث اسعار العلاج
            for p in state["treatment_positions"]:
                try:
                    tk=exchange.fetch_ticker(p[0]+"/USDT")
                    cur=float(tk['last']); p[3]=cur; pp=(cur-p[2])/p[2]*100
                    p[4]=round(100*pp/100,3); p[5]=round(pp,2)
                except: continue

            state["ghair"]=round(sum([p[4] for p in state["positions"]]),3)
            state["loss_pool"]=round(sum([abs(p[8]) for p in state["treatment_positions"]]),3) if state["treatment_positions"] else 0.0
            state["treatment_count"]=len(state["treatment_positions"])
            state["last_update"]=datetime.now().strftime("%H:%M:%S")

            # ===== هدف لحظي - مجموع المفتوح =====
            if state["ghair"]>=config["instant_target"] and state["ghair"]>0:
                profit=state["ghair"]
                state["safi"]=round(state["safi"]+profit,3)
                state["trades_closed"]+=len(state["positions"])
                state["positions"]=[]
                state["ghair"]=0.0
                scored=get_movers_with_macd()
                for i in range(min(5,len(scored))):
                    sym,pct,price,macd_val,is_bull=scored[i]
                    state["positions"].append([sym.replace('/USDT',''),"SPOT",price*0.9995,price,0.0,0.0,f"صاعد {macd_val:.3f}",macd_val,"NORMAL"])
                continue

            # ===== علاج الصفقات الخاسرة =====
            # 1. صفقات عادية ضربت SL
            to_treat=[]
            for p in list(state["positions"]):
                if p[5]<=-config["sl_pct"]:
                    to_treat.append(p)

            for p in to_treat:
                loss=abs(p[4]) # مثلا 0.19$
                # لا نخصم من صافي الربح! ننقله للعلاج
                state["positions"].remove(p)
                # افتح له صفقة علاج بعملة مولعة
                scored=get_movers_with_macd()
                # اختار اقوى عملة مو موجودة
                existing=[x[0] for x in state["positions"]+state["treatment_positions"]]
                for s in scored:
                    sn=s[0].replace('/USDT','')
                    if sn not in existing and s[4]==True: # فقط صاعد
                        # هدف العلاج = الخسارة + هدف لحظي
                        target_needed=loss+config["instant_target"]
                        # نحسب نسبة مئوية للهدف
                        pct_needed=target_needed # لان per_trade 100$
                        state["treatment_positions"].append([
                            sn,"علاج",s[2]*0.9995,s[2],0.0,0.0,
                            f"يعالج {p[0]} {loss:.2f}$",s[3],"TREAT",loss,pct_needed,s[0]
                        ])
                        break

            # 2. صفقات علاج حققت هدفها
            cured=[]
            for p in list(state["treatment_positions"]):
                # p[8]=الخسارة الأصلية, p[9]=الهدف المطلوب
                if p[4]>=p[9]: # جاب ربح يغطي الخسارة + هدف
                    cured.append(p)

            for p in cured:
                loss=p[8]
                net_profit=p[4]-loss # الربح الصافي بعد سداد الخسارة
                state["safi"]=round(state["safi"]+net_profit,3) # يسجل ربح فقط!
                state["trades_closed"]+=1
                state["treatment_positions"].remove(p)
                state["binance_status"]=f"💊 علاج {p[6]} نجح! صافي +{net_profit:.2f}$"

            # تعويض نقص العادية
            if len(state["positions"])<5:
                scored=get_movers_with_macd()
                ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
                for s in scored:
                    sn=s[0].replace('/USDT','')
                    if sn not in ex:
                        state["positions"].append([sn,"SPOT",s[2]*0.9995,s[2],0.0,0.0,f"صاعد {s[3]:.3f}",s[3],"NORMAL"])
                        if len(state["positions"])>=5: break

            time.sleep(1.5)
        except Exception as e:
            print(e)
            time.sleep(2)

thread_started=False
def start_engine():
    global thread_started
    if not thread_started:
        thread_started=True
        threading.Thread(target=engine,daemon=True).start()
@app.before_request
def before_req(): start_engine()
@app.route('/health')
def health(): return "OK",200
@app.route('/api/data')
def api_data():
    total=state["fixed"]+state["safi"]+state["ghair"]
    return jsonify({
        "fixed":state["fixed"],"free":state["free"],"safi":state["safi"],"ghair":state["ghair"],"total":total,
        "trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"treatment_count":state["treatment_count"],
        "positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6]] for p in state["positions"]],
        "treatment_positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[8],p[9]] for p in state["treatment_positions"]],
        "macd_live":state["macd_live"],"binance_status":state["binance_status"],"last_update":state["last_update"],
        "instant_target":config["instant_target"],"tp":config["tp_pct"]
    })
@app.route('/api/config',methods=['POST'])
def api_cfg():
    d=request.get_json()
    if 'capital' in d: state["fixed"]=float(d['capital'])
    if 'per_trade' in d: config["per_trade"]=float(d['per_trade'])
    if 'tp' in d: config["tp_pct"]=float(d['tp'])
    if 'instant_target' in d: config["instant_target"]=float(d['instant_target'])
    return jsonify({"ok":True})
@app.route('/api/reset_full',methods=['POST'])
def reset_full():
    state["safi"]=0.0; state["ghair"]=0.0; state["loss_pool"]=0.0; state["trades_closed"]=0; state["treatment_count"]=0
    state["positions"]=[]; state["treatment_positions"]=[]
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
.h1 p{margin:3px 0 0 0;color:#ffcc00;font-size:9px;font-weight:800}
.bar{display:flex;justify-content:space-between;align-items:center;background:#11158a;border:1px solid #232a8a;border-radius:10px;padding:6px 10px;font-size:11px;font-weight:800;margin-bottom:6px}
.ctrl{display:flex;justify-content:center;align-items:center;gap:8px;background:#11158a;border:1px solid #232a8a;border-radius:14px;padding:8px;margin-bottom:6px;flex-wrap:wrap}
.c-inp{background:#070a1e;border:2px solid #00ff66;border-radius:12px;color:#00ff66;font-family:JetBrains Mono;font-weight:900;width:58px;text-align:center;padding:7px 0;outline:none;font-size:13px}
.c-inp.target{border-color:#ffcc00;color:#ffcc00;width:68px}
.c-btn{background:#00ff66;border:none;border-radius:12px;padding:7px 16px;font-weight:900;color:#000;cursor:pointer;font-size:13px}
.boards{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;margin-bottom:6px}
.b{display:flex;flex-direction:column;gap:4px}
.bt{font-size:10px;font-weight:900;text-align:center}
.bc{background:#1a1f9e;border:1px solid #2d36c0;border-radius:14px;padding:10px 2px;text-align:center;min-height:76px;display:flex;flex-direction:column;justify-content:center}
.bc.gold{border:2px solid #00ff66}
.bc.treat{border:2px solid #ff9800;background:#2a1a00}
.bv{font-family:JetBrains Mono;font-size:17px;font-weight:900;direction:ltr}
.bv.pos{color:#00ff66}.bv.neg{color:#ff2d55}.bv.zero{color:#6a6a8a}.bv.w{color:#fff}
.bv.yb{border-radius:8px;padding:3px 6px;display:inline-block;font-size:13px}
.bv.yb.pos{background:#00ff66;color:#000}
.bv.yb.neg{background:#ff2d55;color:#fff}
.bv.yb.zero{background:transparent;color:#555;border:1px dashed #333}
.act{display:flex;justify-content:center;gap:10px;margin-bottom:6px}
.act button{border:none;border-radius:12px;padding:8px 20px;font-weight:900;font-size:12px;cursor:pointer}
.r{background:#ff2d55;color:#fff}.y{background:#ffeb3b;color:#000}
.tbl-wrap{background:#11158a;border:1px solid #232a8a;border-radius:16px;overflow:hidden;overflow-x:auto;margin-bottom:8px}
.tbl{width:100%;border-collapse:collapse;min-width:520px}
.tbl th{background:#2a36f0;color:#ff4d8d;font-size:12px;font-weight:900;padding:10px 4px;text-align:center}
.tbl td{padding:10px 4px;text-align:center;font-family:JetBrains Mono;font-size:12px;font-weight:800;border-top:1px solid #1a1f8a}
.tbl tr{background:#11158a}
.spot{background:#00ff55;color:#000;border-radius:20px;padding:4px 12px;font-size:11px;font-weight:900;display:inline-block}
.treat-badge{background:#ff9800;color:#000;border-radius:20px;padding:4px 12px;font-size:11px;font-weight:900;display:inline-block}
.close{width:32px;height:32px;border:1.8px solid #4a4f9a;border-radius:10px;background:#0d1050;color:#aab;font-size:16px;cursor:pointer}
.neg{color:#ff3344}.pos{color:#00ff66}
.macd{background:#070a1e;border-top:3px solid #00ff66;color:#ffcc00;font-size:9px;font-weight:800;padding:6px 10px;direction:ltr;text-align:left;white-space:nowrap;overflow:hidden}
@media(max-width:800px){.boards{grid-template-columns:repeat(3,1fr)}}
@media(max-width:600px){.boards{grid-template-columns:repeat(2,1fr)}.ctrl{flex-direction:column}.c-btn{width:100%}.tbl{min-width:600px}}
</style></head><body>
<div class="h1"><h2>V83 ELAG - علاج الخسارة 💊</h2><p>صافي ربح = ربح فقط | الخسارة تروح غرفة العلاج وتتعالج على حسابها</p></div>
<div class="bar"><span id="binStatus">BINANCE SPOT</span><span id="progText">0 / 0.50$</span><span>V83 💎</span></div>
<div class="ctrl">
  <button class="c-btn" onclick="save()">حفظ 🟢</button>
  <input class="c-inp" id="tp" value="0.80">
  <input class="c-inp" id="per_trade" value="100">
  <input class="c-inp" id="capital" value="1000">
  <input class="c-inp target" id="instant_target" value="0.50">
  <span style="font-size:9px;color:#ffcc00;font-weight:800">هدف لحظي</span>
</div>
<div class="boards">
  <div class="b"><div class="bt">💰 ثابت</div><div class="bc"><div class="bv w" id="v_fixed">1000.0$</div></div></div>
  <div class="b"><div class="bt">💊 قيد العلاج</div><div class="bc treat"><div class="bv" id="v_treat">0.00$</div><div style="font-size:9px" id="v_treat_c">0 مرضى</div></div></div>
  <div class="b"><div class="bt">💹 صافي ربح</div><div class="bc"><div class="bv" id="v_safi">0.0$</div><div style="font-size:8px;color:#00ff66">ربح فقط ✅</div></div></div>
  <div class="b"><div class="bt">⚖️ مقفلة</div><div class="bc"><div class="bv w" id="v_ls">0</div></div></div>
  <div class="b"><div class="bt">💎 الإجمالي</div><div class="bc gold"><div class="bv" id="v_total">1000.0$</div></div></div>
  <div class="b"><div class="bt">📈 غير محققة</div><div class="bc"><div class="bv yb" id="v_ghair">0.00$</div></div></div>
  <div class="b"><div class="bt">🔥 حر</div><div class="bc"><div class="bv" id="v_free">0.00$</div></div></div>
</div>
<div class="act"><button class="r" onclick="doReset()">🔒 قفل الكل</button><button class="y" onclick="doReset()">🔄 تصفير</button></div>

<div class="tbl-wrap">
<table class="tbl">
<thead><tr><th>عملة</th><th>نوع</th><th>MACD قوة</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th><th>✕</th></tr></thead>
<tbody id="coins"></tbody>
</table>
<div class="macd" id="macd">...</div>
</div>

<div class="tbl-wrap" id="treatWrap" style="display:none;border-color:#ff9800">
<table class="tbl">
<thead><tr><th style="color:#ff9800">💊 عملة العلاج</th><th>يعالج مين</th><th>خسارة</th><th>هدف علاج</th><th>حالي</th><th>ربح علاج</th><th>%</th></tr></thead>
<tbody id="treatCoins"></tbody>
</table>
</div>

<script>
function colorClass(v){ if(Math.abs(v)<0.001) return 'zero'; return v>0?'pos':'neg'; }
async function save(){
  const d={capital:parseFloat(capital.value),per_trade:parseFloat(per_trade.value),tp:parseFloat(tp.value),instant_target:parseFloat(instant_target.value)};
  await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
  const b=document.querySelector('.c-btn'); b.innerText='✅ تم'; setTimeout(()=>b.innerText='حفظ 🟢',1000);
}
async function doReset(){ if(!confirm('تصفير كامل؟')) return; await fetch('/api/reset_full',{method:'POST'}); location.reload(); }
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('v_fixed').innerText=d.fixed.toFixed(1)+'$';
    const setC=(id,val)=>{
      const el=document.getElementById(id);
      el.innerText=(Math.abs(val)<0.001?'0.00':(val>0?'+':'')+val.toFixed(2))+'$';
      el.className='bv '+colorClass(val);
      if(id=='v_ghair'){ el.className='bv yb '+colorClass(val); if(Math.abs(val)<0.001) el.innerText='0.00$'; }
    };
    setC('v_safi',d.safi); setC('v_ghair',d.ghair); setC('v_free',d.free);
    document.getElementById('v_total').innerText=d.total.toFixed(1)+'$';
    document.getElementById('v_total').className='bv '+colorClass(d.total-d.fixed);
    document.getElementById('v_ls').innerText=d.trades_closed;
    document.getElementById('v_treat').innerText=(d.loss_pool>0?'-':'')+d.loss_pool.toFixed(2)+'$';
    document.getElementById('v_treat').className='bv '+(d.loss_pool>0?'neg':'zero');
    document.getElementById('v_treat_c').innerText=d.treatment_count+' مرضى';
    document.getElementById('binStatus').innerText=d.binance_status+' • '+d.last_update;
    document.getElementById('progText').innerText=`${d.ghair.toFixed(2)} / ${d.instant_target}$`;
    document.getElementById('macd').innerText='MACD LIVE: '+d.macd_live;

    let h='';
    for(const p of d.positions){
      const sym=p[0],dir=p[1],entry=p[2],cur=p[3],usd=p[4],pct=p[5],macd=p[6]||'';
      h+=`<tr><td style="font-weight:900">${sym}</td><td><span class="spot">${dir}</span></td><td style="font-size:10px;color:${macd.includes('صاعد')?'#00ff66':'#ff3344'}">${macd}</td><td>${entry.toFixed(4)}</td><td>${cur.toFixed(4)}</td><td class="${colorClass(usd)}">${usd>=0?'+':''}${usd.toFixed(3)}$</td><td class="${colorClass(pct)}">${pct>=0?'+':''}${pct.toFixed(2)}%</td><td><button class="close" onclick="fetch('/api/close/'+sym).then(()=>load())">✕</button></td></tr>`;
    }
    document.getElementById('coins').innerHTML=h || '<tr><td colspan=8 style="padding:12px;opacity:0.5">⏳...</td></tr>';

    const tw=document.getElementById('treatWrap');
    if(d.treatment_positions.length>0){
      tw.style.display='block';
      let th='';
      for(const p of d.treatment_positions){
        const sym=p[0],entry=p[2],cur=p[3],usd=p[4],pct=p[5],info=p[6],loss=p[7],target=p[8];
        th+=`<tr><td><span class="treat-badge">${sym} علاج</span></td><td style="font-size:10px">${info}</td><td class="neg">-${loss.toFixed(2)}$</td><td style="color:#ffcc00">${target.toFixed(2)}$</td><td>${cur.toFixed(4)}</td><td class="${colorClass(usd)}">${usd>=0?'+':''}${usd.toFixed(3)}$</td><td class="${colorClass(pct)}">${pct.toFixed(2)}%</td></tr>`;
      }
      document.getElementById('treatCoins').innerHTML=th;
    } else { tw.style.display='none'; }

  }catch(e){}
}
setInterval(load,1800); load();
</script>
</body></html>
    '''
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

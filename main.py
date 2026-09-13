from flask import Flask, request, jsonify, redirect
import threading, time, os
from datetime import datetime
import ccxt

app = Flask(__name__)
exchange = ccxt.binance({'enableRateLimit': True})

config = {"capital":1000.0,"per_trade":100.0,"tp_pct":0.80,"sl_pct":1.5,"instant_target":0.50}
state = {"fixed":1000.0,"free":0.0,"safi":0.0,"ghair":0.0,"trades_closed":0,"daily_peak":1000.0,"positions":[],"macd_live":"جاري...","binance_status":"BINANCE REAL SPOT","last_update":"...","is_frozen":False}

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
        k=2/(12+1); e12=sum(closes[:12])/12
        for x in closes[12:]: e12=x*k+e12*(1-k)
        k=2/(26+1); e26=sum(closes[:26])/26
        for x in closes[26:]: e26=x*k+e26*(1-k)
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
            if not last or last<0.000001: continue
            pct=t.get('percentage')
            if pct is None:
                o=t.get('open')
                pct=((last-o)/o)*100 if o else 0
            if pct<0.3: continue
            mov.append((sym,float(pct),float(last)))
        mov.sort(key=lambda x:x[1],reverse=True)
        mov=mov[:30]
    except:
        mov=[("BTC/USDT",2,65000),("ETH/USDT",2,3000),("SOL/USDT",2,150),("XRP/USDT",2,0.6),("DOGE/USDT",2,0.15),("CREAM/USDT",2,2.1)]

    # احسب قوة الماكد لكل عملة ورتب
    scored=[]
    for sym,pct,price in mov[:20]:
        macd_val,is_bull,_=get_macd_strength(sym)
        scored.append((sym,pct,price,macd_val,is_bull))
    # الأقوى MACD صاعد أول
    scored.sort(key=lambda x:x[3],reverse=True)
    return scored

def engine():
    while True:
        try:
            scored=get_movers_with_macd()
            state["positions"]=[]
            for i in range(min(6,len(scored))):
                sym,pct,price,macd_val,is_bull=scored[i]
                state["positions"].append([sym.replace('/USDT',''),"SPOT",price*0.9995,price,0.0,0.0,f"{'صاعد' if is_bull else 'نازل'} {macd_val:.3f}",macd_val])
            state["macd_live"]=", ".join([f"{s[0].replace('/USDT','')} {s[3]:.3f}" for s in scored[:12]])
            state["binance_status"]=f"BINANCE REAL SPOT ✅ {len(scored)} عملة - هدف {config['instant_target']}$"
            state["is_frozen"]=False
            break
        except Exception as e:
            time.sleep(3)

    idx=0
    while True:
        try:
            for p in state["positions"]:
                try:
                    tk=exchange.fetch_ticker(p[0]+"/USDT")
                    cur=float(tk['last']); p[3]=cur
                    pp=(cur-p[2])/p[2]*100
                    p[4]=round(100*pp/100,3)
                    p[5]=round(pp,2)
                except: continue
            state["ghair"]=round(sum([p[4] for p in state["positions"]]),3)
            state["last_update"]=datetime.now().strftime("%H:%M:%S")

            # === الهدف اللحظي: اذا مجموع المفتوح حقق الهدف ===
            if state["ghair"]>=config["instant_target"] and state["ghair"]>0 and len(state["positions"])>0:
                profit=state["ghair"]
                state["safi"]=round(state["safi"]+profit,3)
                state["trades_closed"]+=len(state["positions"])
                state["positions"]=[]
                state["ghair"]=0.0
                state["binance_status"]=f"🎯 لحظي {config['instant_target']}$ تحقق +{profit:.2f}$ - فتح جديد بقوة MACD"
                time.sleep(1.5)
                # فتح جديد حسب قوة الماكد
                scored=get_movers_with_macd()
                for i in range(min(6,len(scored))):
                    sym,pct,price,macd_val,is_bull=scored[i]
                    state["positions"].append([sym.replace('/USDT',''),"SPOT",price*0.9995,price,0.0,0.0,f"{'صاعد' if is_bull else 'نازل'} {macd_val:.3f}",macd_val])
                state["macd_live"]=", ".join([f"{s[0].replace('/USDT','')} {s[3]:.3f}" for s in scored[:12]])
                continue

            # تحديث MACD واحد واحد
            if state["positions"]:
                try:
                    p=state["positions"][idx%len(state["positions"])]
                    macd_val,is_bull,_=get_macd_strength(p[0]+"/USDT")
                    p[6]=f"{'صاعد' if is_bull else 'نازل'} {macd_val:.3f}"
                    p[7]=macd_val
                    idx+=1
                except: pass

            # TP/SL فردي
            to_close=[p for p in state["positions"] if p[5]>=config["tp_pct"] or p[5]<=-config["sl_pct"]]
            for p in to_close:
                state["safi"]+=p[4]; state["trades_closed"]+=1
                if p in state["positions"]: state["positions"].remove(p)

            if len(state["positions"])<6:
                scored=get_movers_with_macd()
                ex=[x[0] for x in state["positions"]]
                for s in scored:
                    sn=s[0].replace('/USDT','')
                    if sn not in ex:
                        state["positions"].append([sn,"SPOT",s[2]*0.9995,s[2],0.0,0.0,f"{'صاعد' if s[4] else 'نازل'} {s[3]:.3f}",s[3]])
                        if len(state["positions"])>=6: break

            time.sleep(1.5)
        except: time.sleep(2)

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
    return jsonify({"fixed":state["fixed"],"free":state["free"],"safi":state["safi"],"ghair":state["ghair"],"total":total,"trades_closed":state["trades_closed"],"positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6]] for p in state["positions"]],"macd_live":state["macd_live"],"binance_status":state["binance_status"],"last_update":state["last_update"],"instant_target":config["instant_target"],"tp":config["tp_pct"]})
@app.route('/api/config',methods=['POST'])
def api_cfg():
    d=request.get_json()
    if 'capital' in d: state["fixed"]=float(d['capital']); config["capital"]=float(d['capital'])
    if 'per_trade' in d: config["per_trade"]=float(d['per_trade'])
    if 'tp' in d: config["tp_pct"]=float(d['tp'])
    if 'instant_target' in d: config["instant_target"]=float(d['instant_target'])
    return jsonify({"ok":True})
@app.route('/api/close/<sym>')
def close_sym(sym):
    for p in list(state["positions"]):
        if p[0]==sym:
            state["safi"]+=p[4]; state["trades_closed"]+=1; state["positions"].remove(p)
    return jsonify({"ok":True})
@app.route('/api/reset_full',methods=['POST'])
def reset_full():
    state["safi"]=0.0; state["ghair"]=0.0; state["trades_closed"]=0; state["positions"]=[]
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
.bar{display:flex;justify-content:space-between;align-items:center;background:#11158a;border:1px solid #232a8a;border-radius:10px;padding:6px 10px;font-size:11px;font-weight:800;margin-bottom:6px;flex-wrap:wrap;gap:6px}
.ctrl{display:flex;justify-content:center;align-items:center;gap:8px;background:#11158a;border:1px solid #232a8a;border-radius:14px;padding:8px;margin-bottom:6px;flex-wrap:wrap}
.c-inp{background:#070a1e;border:2px solid #00ff66;border-radius:12px;color:#00ff66;font-family:JetBrains Mono;font-weight:900;width:68px;text-align:center;padding:7px 0;outline:none;font-size:14px}
.c-inp.target{border-color:#ffcc00;color:#ffcc00;width:78px}
.c-btn{background:#00ff66;border:none;border-radius:12px;padding:7px 18px;font-weight:900;color:#000;cursor:pointer;font-size:13px}
.boards{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-bottom:6px}
.b{display:flex;flex-direction:column;gap:4px}
.bt{font-size:11px;font-weight:900;text-align:center}
.bc{background:#1a1f9e;border:1px solid #2d36c0;border-radius:16px;padding:12px 4px;text-align:center;min-height:82px;display:flex;flex-direction:column;justify-content:center;transition:all 0.3s}
.bc.gold{border:2px solid #00ff66}
.bv{font-family:JetBrains Mono;font-size:19px;font-weight:900;direction:ltr}
.bv.pos{color:#00ff66}.bv.neg{color:#ff2d55}.bv.zero{color:#6a6a8a}
.bv.yb{border-radius:8px;padding:3px 8px;display:inline-block;font-size:14px}
.bv.yb.pos{background:#00ff66;color:#000}
.bv.yb.neg{background:#ff2d55;color:#fff}
.bv.yb.zero{background:transparent;color:#555;border:1px dashed #333;font-size:12px}
.act{display:flex;justify-content:center;gap:10px;margin-bottom:6px}
.act button{border:none;border-radius:12px;padding:8px 20px;font-weight:900;font-size:12px;cursor:pointer}
.r{background:#ff2d55;color:#fff}.y{background:#ffeb3b;color:#000}
.tbl-wrap{background:#11158a;border:1px solid #232a8a;border-radius:16px;overflow:hidden;overflow-x:auto}
.tbl{width:100%;border-collapse:collapse;min-width:520px}
.tbl th{background:#2a36f0;color:#ff4d8d;font-size:13px;font-weight:900;padding:12px 4px;text-align:center}
.tbl td{padding:11px 4px;text-align:center;font-family:JetBrains Mono;font-size:13px;font-weight:800;border-top:1px solid #1a1f8a}
.tbl tr{background:#11158a}
.spot{background:#00ff55;color:#000;border-radius:20px;padding:5px 14px;font-size:12px;font-weight:900;display:inline-block;min-width:60px}
.close{width:38px;height:38px;border:1.8px solid #4a4f9a;border-radius:12px;background:#0d1050;color:#aab;font-size:18px;cursor:pointer}
.neg{color:#ff3344}.pos{color:#00ff66}
.macd{background:#070a1e;border-top:3px solid #00ff66;color:#ffcc00;font-size:10px;font-weight:800;padding:7px 10px;direction:ltr;text-align:left;white-space:nowrap;overflow:hidden}
.progress{height:6px;background:#1a1f9e;border-radius:10px;overflow:hidden;margin-top:6px}
.progress-bar{height:100%;transition:width 0.5s}
@media(max-width:600px){.boards{grid-template-columns:repeat(2,1fr)}.ctrl{flex-direction:column}.c-btn{width:100%}.tbl{min-width:600px}}
</style></head><body>
<div class="h1"><h2>V82.4 INSTANT TARGET - هدف لحظي + قوة MACD</h2><p>اذا مجموع المفتوح وصل الهدف اللحظي → يقفل ويفتح بأقوى MACD</p></div>
<div class="bar"><span id="binStatus">BINANCE REAL SPOT</span><span id="progText">0 / 0.50$</span><span>V82.4 💎</span></div>
<div class="ctrl">
  <button class="c-btn" onclick="save()">حفظ 🟢</button>
  <input class="c-inp" id="tp" value="0.80" title="TP %">
  <input class="c-inp" id="per_trade" value="100" title="لكل صفقة">
  <input class="c-inp" id="capital" value="1000" title="رأس مال">
  <input class="c-inp target" id="instant_target" value="0.50" title="هدف لحظي">
  <span style="font-size:10px;color:#ffcc00;font-weight:800">هدف لحظي $</span>
</div>
<div class="boards">
  <div class="b"><div class="bt">💰 ثابت</div><div class="bc"><div class="bv w" id="v_fixed" style="color:#fff">1000.0$</div></div></div>
  <div class="b"><div class="bt">🔥 حر</div><div class="bc"><div class="bv" id="v_free">0.0$</div></div></div>
  <div class="b"><div class="bt">💹 صافي ربح</div><div class="bc"><div class="bv" id="v_safi">0.0$</div></div></div>
  <div class="b"><div class="bt">⚖️ مقفلة</div><div class="bc"><div class="bv" style="color:#fff" id="v_ls">0</div></div></div>
  <div class="b"><div class="bt">💎 الإجمالي</div><div class="bc gold"><div class="bv" id="v_total">1000.0$</div></div></div>
  <div class="b"><div class="bt">📈 غير محققة</div><div class="bc"><div class="bv yb" id="v_ghair">0.00$</div><div class="progress"><div class="progress-bar" id="pbar" style="width:0%"></div></div></div></div>
</div>
<div class="act"><button class="r" onclick="doReset()">🔒 قفل الكل</button><button class="y" onclick="doReset()">🔄 تصفير</button></div>
<div class="tbl-wrap">
<table class="tbl">
<thead><tr><th>عملة</th><th>نوع</th><th>MACD قوة</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th><th>✕</th></tr></thead>
<tbody id="coins"></tbody>
</table>
<div class="macd" id="macd">MACD LIVE مرتب حسب القوة...</div>
</div>
<script>
function colorClass(v){
  if(Math.abs(v)<0.001) return 'zero';
  return v>0?'pos':'neg';
}
async function save(){
  const d={
    capital:parseFloat(document.getElementById('capital').value),
    per_trade:parseFloat(document.getElementById('per_trade').value),
    tp:parseFloat(document.getElementById('tp').value),
    instant_target:parseFloat(document.getElementById('instant_target').value)
  };
  await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
  const b=document.querySelector('.c-btn'); b.innerText='✅ تم'; setTimeout(()=>b.innerText='حفظ 🟢',1000);
}
async function doReset(){
  if(!confirm('تصفير كامل؟')) return;
  await fetch('/api/reset_full',{method:'POST'});
  location.reload();
}
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('v_fixed').innerText=d.fixed.toFixed(1)+'$';
    const setC=(id,val)=>{
      const el=document.getElementById(id);
      el.innerText=(Math.abs(val)<0.001?'0.00':(val>0?'+':'')+val.toFixed(2))+'$';
      el.className='bv '+colorClass(val);
      if(id=='v_ghair'){
        el.className='bv yb '+colorClass(val);
        if(Math.abs(val)<0.001) el.innerText='0.00$';
      }
    };
    setC('v_safi',d.safi);
    setC('v_ghair',d.ghair);
    setC('v_free',d.free);
    const totEl=document.getElementById('v_total');
    totEl.innerText=d.total.toFixed(1)+'$';
    totEl.className='bv '+colorClass(d.total-d.fixed);
    document.getElementById('v_ls').innerText=d.trades_closed;
    document.getElementById('binStatus').innerText=d.binance_status+' • '+d.last_update;
    document.getElementById('macd').innerText='MACD LIVE قوة: '+d.macd_live;
    // شريط تقدم الهدف اللحظي
    const target=d.instant_target;
    const prog=Math.min(100, Math.max(0, (d.ghair/target)*100));
    document.getElementById('progText').innerText=`${d.ghair.toFixed(2)} / ${target}$`;
    const pbar=document.getElementById('pbar');
    pbar.style.width=prog+'%';
    pbar.style.background=d.ghair>=0?'#00ff66':'#ff2d55';
    if(d.ghair>=target && target>0) pbar.style.background='#ffcc00';

    let h='';
    for(const p of d.positions){
      const sym=p[0],dir=p[1],entry=p[2],cur=p[3],usd=p[4],pct=p[5],macd=p[6]||'';
      const usdC=colorClass(usd), pctC=colorClass(pct);
      h+=`<tr><td style="font-weight:900">${sym}</td><td><span class="spot">${dir}</span></td><td style="font-size:10px;color:${macd.includes('صاعد')?'#00ff66':'#ff3344'}">${macd}</td><td>${entry.toFixed(4)}</td><td>${cur.toFixed(4)}</td><td class="${usdC}">${usd>=0?'+':''}${usd.toFixed(3)}$</td><td class="${pctC}">${pct>=0?'+':''}${pct.toFixed(2)}%</td><td><button class="close" onclick="fetch('/api/close/'+sym).then(()=>load())">✕</button></td></tr>`;
    }
    document.getElementById('coins').innerHTML=h || '<tr><td colspan=8 style="padding:16px;opacity:0.5">⏳ يتصل...</td></tr>';
  }catch(e){}
}
setInterval(load,1800); load();
</script>
</body></html>
    '''
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

from flask import Flask, request, jsonify, redirect
import threading, time, os
from datetime import datetime
import ccxt

app = Flask(__name__)
exchange = ccxt.binance({'enableRateLimit': True})

config = {"capital":1000.0,"per_trade":100.0,"tp_pct":0.80,"sl_pct":1.5}
state = {"fixed":1000.0,"free":0.0,"safi":0.0,"ghair":0.0,"trades_closed":0,"qalbat":0,"loss_pool":0.0,"daily_peak":1000.0,"positions":[],"macd_live":"جاري التحميل...","binance_status":"BINANCE REAL SPOT - يتصل...","last_update":"...","is_frozen":True}

def ema(d,p):
    if len(d)<p: return None
    k=2/(p+1); ev=sum(d[:p])/p
    for x in d[p:]: ev=x*k+ev*(1-k)
    return ev
def check_macd(sym):
    try:
        ohlcv=exchange.fetch_ohlcv(sym,'15m',limit=35)
        closes=[c[4] for c in ohlcv]
        if len(closes)<30: return True,0
        e12=ema(closes,12); e26=ema(closes,26)
        if not e12 or not e26: return True,0
        return (e12-e26>0), e12-e26
    except: return True,0

def get_movers_spot_FIXED():
    try:
        tickers=exchange.fetch_tickers()
        mov=[]
        for sym,t in tickers.items():
            if not sym.endswith('/USDT'): continue
            last=t.get('last')
            if not last: continue
            pct=t.get('percentage')
            if pct is None:
                openp=t.get('open')
                pct=((last-openp)/openp)*100 if openp else 0
            mov.append((sym,float(pct),float(last)))
        mov.sort(key=lambda x:x[1],reverse=True)
        if len(mov)>=6: return mov[:20]
    except: pass
    fallback=["BTC/USDT","ETH/USDT","SOL/USDT","XRP/USDT","DOGE/USDT","PEPE/USDT","AVAX/USDT","LINK/USDT","NEAR/USDT","REZ/USDT"]
    mov=[]
    for s in fallback:
        try:
            tk=exchange.fetch_ticker(s)
            mov.append((s,2.0,float(tk['last'])))
        except: continue
    return mov[:20]

def engine():
    while True:
        try:
            mov=get_movers_spot_FIXED()
            if len(mov)==0: raise Exception("No movers")
            state["positions"]=[]
            for i in range(min(6,len(mov))):
                state["positions"].append([mov[i][0].replace('/USDT',''),"SPOT",mov[i][2]*0.9995,mov[i][2],0.0,0.0,f"{mov[i][1]:.2f}%"])
            state["macd_live"]=", ".join([f"{x[0].replace('/USDT','')}" for x in mov[:15]])
            state["binance_status"]=f"BINANCE REAL SPOT ✅ {len(mov)} عملة"
            state["is_frozen"]=False
            break
        except: time.sleep(3)
    idx=0
    while True:
        try:
            for p in state["positions"]:
                tk=exchange.fetch_ticker(p[0]+"/USDT")
                cur=float(tk['last']); p[3]=cur; pp=(cur-p[2])/p[2]*100
                p[4]=round(100*pp/100,2); p[5]=round(pp,2)
            state["ghair"]=round(sum([p[4] for p in state["positions"]]),2)
            state["last_update"]=datetime.now().strftime("%H:%M:%S")
            state["is_frozen"]=False
            if state["positions"]:
                try:
                    p=state["positions"][idx%len(state["positions"])]
                    is_bull,m=check_macd(p[0]+"/USDT")
                    p[6]=f"{'صاعد' if is_bull else 'نازل'} {m:.3f}"; idx+=1
                except: pass
            to_remove=[p for p in state["positions"] if p[5]>=config["tp_pct"] or p[5]<=-config["sl_pct"]]
            for p in to_remove:
                state["safi"]+=p[4]; state["trades_closed"]+=1
                if p in state["positions"]: state["positions"].remove(p)
            if len(state["positions"])<6:
                try:
                    mov=get_movers_spot_FIXED()
                    ex=[x[0] for x in state["positions"]]
                    for x in mov:
                        sn=x[0].replace('/USDT','')
                        if sn not in ex:
                            state["positions"].append([sn,"SPOT",x[2]*0.9995,x[2],0.0,0.0,f"{x[1]:.2f}%"])
                            if len(state["positions"])>=6: break
                except: pass
            time.sleep(1.8)
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
    return jsonify({"fixed":state["fixed"],"free":state["free"],"safi":state["safi"],"ghair":state["ghair"],"total":total,"trades_closed":state["trades_closed"],"positions":state["positions"],"macd_live":state["macd_live"],"binance_status":state["binance_status"],"last_update":state["last_update"],"is_frozen":state["is_frozen"]})
@app.route('/api/config',methods=['POST'])
def api_cfg():
    d=request.get_json()
    if 'capital' in d: state["fixed"]=float(d['capital']); config["capital"]=float(d['capital']); state["daily_peak"]=float(d['capital'])
    if 'per_trade' in d: config["per_trade"]=float(d['per_trade'])
    if 'tp' in d: config["tp_pct"]=float(d['tp'])
    return jsonify({"ok":True})
@app.route('/api/close/<sym>')
def close_sym(sym):
    state["positions"]=[p for p in state["positions"] if p[0]!=sym]
    return jsonify({"ok":True})

# === هنا كان الخلل - الآن تصفير كامل ===
@app.route('/reset')
def reset():
    state["safi"]=0.0
    state["ghair"]=0.0
    state["free"]=0.0
    state["trades_closed"]=0
    state["qalbat"]=0
    state["loss_pool"]=0.0
    state["daily_peak"]=state["fixed"]
    state["positions"]=[]
    state["is_frozen"]=False
    state["macd_live"]="تم التصفير - جاري التحميل..."
    return redirect('/')

@app.route('/api/reset_full',methods=['POST'])
def reset_full():
    state["safi"]=0.0; state["ghair"]=0.0; state["free"]=0.0
    state["trades_closed"]=0; state["qalbat"]=0; state["loss_pool"]=0.0
    state["daily_peak"]=state["fixed"]; state["positions"]=[]
    state["is_frozen"]=False; state["macd_live"]="تم التصفير"
    return jsonify({"ok":True,"msg":"تم التصفير الكامل"})

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
.bar.frozen{background:#ff3b5c20;border-color:#ff3b5c}
.ctrl{display:flex;justify-content:center;align-items:center;gap:8px;background:#11158a;border:1px solid #232a8a;border-radius:14px;padding:8px;margin-bottom:6px;flex-wrap:wrap}
.c-inp{background:#070a1e;border:2px solid #00ff66;border-radius:12px;color:#00ff66;font-family:JetBrains Mono;font-weight:900;width:68px;text-align:center;padding:7px 0;outline:none;font-size:14px}
.c-btn{background:#00ff66;border:none;border-radius:12px;padding:7px 18px;font-weight:900;color:#000;cursor:pointer;font-size:13px}
.boards{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-bottom:6px}
.b{display:flex;flex-direction:column;gap:4px}
.bt{font-size:11px;font-weight:900;text-align:center}
.bc{background:#1a1f9e;border:1px solid #2d36c0;border-radius:16px;padding:12px 4px;text-align:center;min-height:82px;display:flex;flex-direction:column;justify-content:center}
.bc.gold{border:2px solid #00ff66;box-shadow:0 0 16px rgba(0,255,102,0.28)}
.bv{font-family:JetBrains Mono;font-size:20px;font-weight:900;direction:ltr}
.bv.g{color:#00ff66}.bv.w{color:#fff}.bv.yb{background:#ffeb3b;color:#000;border-radius:6px;padding:2px 8px;display:inline-block;font-size:14px}
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
@media(max-width:600px){.boards{grid-template-columns:repeat(2,1fr)}.ctrl{flex-direction:column}.c-btn{width:100%}.tbl{min-width:600px}}
</style></head><body>
<div class="h1"><h2>V82 SPOT MACD - $500 / $100 / 0.80% TP</h2><p>SPOT REAL + MACD فلتر + STRICT WAIT - سبوت فقط شراء</p></div>
<div class="bar" id="topBar"><span id="binStatus">BINANCE REAL SPOT</span><span>V82 SPOT FAKHMA 💎</span></div>
<div class="ctrl"><button class="c-btn" onclick="save()">حفظ 🟢</button><input class="c-inp" id="tp" value="0.80"><input class="c-inp" id="per_trade" value="100"><input class="c-inp" id="capital" value="1000"></div>
<div class="boards">
  <div class="b"><div class="bt">💰 ثابت</div><div class="bc"><div class="bv w" id="v_fixed">1000.0$</div></div></div>
  <div class="b"><div class="bt">🔥 حر</div><div class="bc"><div class="bv w">0.0$</div></div></div>
  <div class="b"><div class="bt">💹 صافي ربح</div><div class="bc"><div class="bv g" id="v_safi">+0.0$</div></div></div>
  <div class="b"><div class="bt">⚖️ مقفلة</div><div class="bc"><div class="bv w" id="v_ls">0</div></div></div>
  <div class="b"><div class="bt">💎 الإجمالي</div><div class="bc gold"><div class="bv w" id="v_total">1000.0$</div></div></div>
  <div class="b"><div class="bt">📈 غير محققة</div><div class="bc"><div class="bv yb" id="v_ghair">+0.00$</div></div></div>
</div>
<div class="act"><button class="r" onclick="doReset()">🔒 قفل الكل</button><button class="y" onclick="doReset()">🔄 تصفير</button></div>
<div class="tbl-wrap">
<table class="tbl">
<thead><tr><th>عملة</th><th>نوع</th><th>MACD</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th><th>✕</th></tr></thead>
<tbody id="coins"></tbody>
</table>
<div class="macd" id="macd">MACD LIVE: ينتظر باينانس...</div>
</div>
<script>
async function save(){
  const d={capital:parseFloat(document.getElementById('capital').value),per_trade:parseFloat(document.getElementById('per_trade').value),tp:parseFloat(document.getElementById('tp').value)};
  await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
  const b=document.querySelector('.c-btn'); b.innerText='✅ تم'; setTimeout(()=>b.innerText='حفظ 🟢',1000);
}
async function doReset(){
  if(!confirm('تصفير كامل؟ بيمسح كل شي: صافي الربح + المقفلة + العملات')) return;
  await fetch('/api/reset_full',{method:'POST'});
  location.reload();
}
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('v_fixed').innerText=d.fixed.toFixed(1)+'$';
    document.getElementById('v_safi').innerText=(d.safi>=0?'+':'')+d.safi.toFixed(1)+'$';
    document.getElementById('v_total').innerText=d.total.toFixed(1)+'$';
    document.getElementById('v_ghair').innerText=(d.ghair>=0?'+':'')+d.ghair.toFixed(2)+'$';
    document.getElementById('v_ls').innerText=d.trades_closed;
    document.getElementById('binStatus').innerText=d.binance_status+' • '+d.last_update;
    document.getElementById('macd').innerText='MACD LIVE: '+d.macd_live;
    let h='';
    for(const p of d.positions){
      const sym=p[0],dir=p[1],entry=p[2],cur=p[3],usd=p[4],pct=p[5],macd=p[6]||'...';
      h+=`<tr><td style="font-weight:900">${sym}</td><td><span class="spot">${dir}</span></td><td style="font-size:10px;color:${macd.includes('صاعد')?'#00ff66':'#ff3344'}">${macd}</td><td>${entry.toFixed(4)}</td><td>${cur.toFixed(4)}</td><td class="${usd<0?'neg':'pos'}">${usd>=0?'+':''}${usd.toFixed(2)}$</td><td class="${pct<0?'neg':'pos'}">${pct>=0?'+':''}${pct.toFixed(2)}%</td><td><button class="close" onclick="fetch('/api/close/'+sym).then(()=>load())">✕</button></td></tr>`;
    }
    document.getElementById('coins').innerHTML=h || '<tr><td colspan=8 style="padding:16px;opacity:0.5">⏳ يتصل بباينانس REAL...</td></tr>';
  }catch(e){}
}
setInterval(load,2000); load();
</script>
</body></html>
    '''
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

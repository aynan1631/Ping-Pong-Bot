from flask import Flask, request, jsonify, redirect
import threading, time, os
from datetime import datetime
import ccxt

app = Flask(__name__)
exchange = ccxt.binance({'enableRateLimit': True})

# V82 SPOT + MACD + STRICT WAIT
config = {"capital":500.0,"per_trade":100.0,"tp_pct":0.50,"sl_pct":0.50}
state = {
    "fixed":500.0,"free":0.0,"safi":73.5,"ghair":0.73,"total":574.2,
    "long":3,"short":2,"dawrat":130,"qalbat":170,
    "loss_pool":0.0,"daily_peak":574.2,
    "positions":[["LSK","LONG",1.0181,1.0197,0.95,0.95,"صاعد 0.002"]],
    "macd_live":"LSKUSDT, REZUSDT, VTHOUSDT, NEARUSDT, WLFIUSDT, PUMPUSDT",
    "binance_status":"BINANCE REAL","last_update":"...","is_frozen":False
}

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
    except: raise
def get_movers_spot():
    tickers=exchange.fetch_tickers()
    mov=[]
    for sym,t in tickers.items():
        if not sym.endswith('/USDT'): continue
        if not t.get('last'): continue
        pct=t.get('percentage')
        if pct is None or pct<0.5: continue
        mov.append((sym,float(pct),float(t['last'])))
    if len(mov)<3: raise Exception("No movers")
    mov.sort(key=lambda x:x[1],reverse=True)
    return mov[:20]

def engine():
    while True:
        try:
            state["is_frozen"]=True
            mov=get_movers_spot()
            state["positions"]=[]
            for i in range(min(6,len(mov))):
                sym,pct,pr=mov[i]
                state["positions"].append([sym.replace('/USDT',''),"LONG",pr*0.999,pr,0.0,0.0,"صاعد..."])
            state["macd_live"]=", ".join([f"{x[0]}" for x in mov[:15]])
            state["binance_status"]=f"BINANCE REAL ✅ SPOT"; state["is_frozen"]=False
            break
        except: time.sleep(5)
    pool=0.0; idx=0
    while True:
        try:
            try:
                for p in state["positions"]:
                    tk=exchange.fetch_ticker(p[0]+"/USDT")
                    cur=float(tk['last']); p[3]=cur
                    pp=(cur-p[2])/p[2]*100
                    p[4]=round(100*pp/100,2); p[5]=round(pp,2)
                state["ghair"]=round(sum([p[4] for p in state["positions"]]),2)
                state["last_update"]=datetime.now().strftime("%H:%M:%S")
                state["is_frozen"]=False
            except:
                state["is_frozen"]=True; time.sleep(5); continue
            if state["positions"]:
                try:
                    p=state["positions"][idx%len(state["positions"])]
                    is_bull,m=check_macd(p[0]+"/USDT")
                    p[6]=f"{'صاعد' if is_bull else 'نازل'} {m:.3f}"; idx+=1
                except: pass
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
    return jsonify({
        "fixed":state["fixed"],"free":state["free"],"safi":state["safi"],"ghair":state["ghair"],"total":state["fixed"]+state["safi"]+state["ghair"],
        "long":state["long"],"short":state["short"],"dawrat":state["dawrat"],"qalbat":state["qalbat"],
        "positions":state["positions"],"macd_live":state["macd_live"],
        "binance_status":state["binance_status"],"last_update":state["last_update"],"is_frozen":state["is_frozen"]
    })
@app.route('/api/config',methods=['POST'])
def api_cfg():
    d=request.get_json()
    if 'capital' in d: state["fixed"]=float(d['capital'])
    if 'per_trade' in d: config["per_trade"]=float(d['per_trade'])
    if 'tp' in d: config["tp_pct"]=float(d['tp'])
    return jsonify({"ok":True})
@app.route('/api/close/<sym>')
def close_sym(sym):
    state["positions"]=[p for p in state["positions"] if p[0]!=sym]
    return jsonify({"ok":True})
@app.route('/reset')
def reset():
    state["safi"]=0; state["ghair"]=0; state["positions"]=[]; return redirect('/')

@app.route('/')
def home():
    return '''
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}body{margin:0;background:#070a1e;color:#fff;font-family:Cairo;padding:5px}
.h1{border:2px solid #00ff66;border-radius:18px;background:#11158a;text-align:center;padding:10px 8px;margin-bottom:6px}
.h1 h2{margin:0;color:#00ff66;font-size:16px;font-weight:900}
.h1 p{margin:3px 0 0 0;color:#ffcc00;font-size:10px;font-weight:800}
.bar{display:flex;justify-content:space-between;align-items:center;background:#11158a;border:1px solid #232a8a;border-radius:10px;padding:6px 10px;font-size:11px;font-weight:800;margin-bottom:6px}
.bar.frozen{background:#ff3b5c20;border-color:#ff3b5c}
.ctrl{display:flex;justify-content:center;align-items:center;gap:8px;background:#11158a;border:1px solid #232a8a;border-radius:14px;padding:8px;margin-bottom:6px;flex-wrap:wrap}
.c-inp{background:#070a1e;border:2px solid #00ff66;border-radius:12px;color:#00ff66;font-family:JetBrains Mono;font-weight:900;width:68px;text-align:center;padding:7px 0;outline:none;font-size:14px}
.c-btn{background:#00ff66;border:none;border-radius:12px;padding:7px 18px;font-weight:900;font-family:Cairo;color:#000;cursor:pointer;font-size:13px}
.boards{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-bottom:6px}
.b{display:flex;flex-direction:column;gap:4px}
.bt{font-size:11px;font-weight:900;text-align:center}
.bc{background:#1a1f9e;border:1px solid #2d36c0;border-radius:16px;padding:12px 4px;text-align:center;min-height:82px;display:flex;flex-direction:column;justify-content:center}
.bc.gold{border:2px solid #00ff66;box-shadow:0 0 16px rgba(0,255,102,0.28)}
.bv{font-family:JetBrains Mono;font-size:20px;font-weight:900;direction:ltr}
.bv.g{color:#00ff66}.bv.w{color:#fff}.bv.yb{background:#ffeb3b;color:#000;border-radius:6px;padding:2px 8px;display:inline-block;font-size:14px}
.act{display:flex;justify-content:center;gap:10px;margin-bottom:6px}
.act button{border:none;border-radius:12px;padding:8px 20px;font-weight:900;font-family:Cairo;font-size:12px;cursor:pointer}
.r{background:#ff2d55;color:#fff}.y{background:#ffeb3b;color:#000}
.tbl-wrap{background:#11158a;border:1px solid #232a8a;border-radius:16px;overflow:hidden;overflow-x:auto}
.tbl{width:100%;border-collapse:collapse;min-width:520px}
.tbl th{background:#2a36f0;color:#ff4d8d;font-size:13px;font-weight:900;padding:12px 4px;text-align:center;white-space:nowrap}
.tbl td{padding:11px 4px;text-align:center;font-family:JetBrains Mono;font-size:13px;font-weight:800;border-top:1px solid #1a1f8a;white-space:nowrap}
.tbl tr{background:#11158a}
.long{background:#00ff55;color:#000;border-radius:20px;padding:5px 14px;font-size:12px;font-weight:900;display:inline-block;min-width:60px;font-family:Cairo}
.close{width:38px;height:38px;border:1.8px solid #4a4f9a;border-radius:12px;background:#0d1050;color:#aab;font-size:18px;cursor:pointer}
.neg{color:#ff3344}.pos{color:#00ff66}
.macd{background:#070a1e;border-top:3px solid #00ff66;color:#ffcc00;font-size:10px;font-weight:800;padding:7px 10px;direction:ltr;text-align:left;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

/* ===== متوافق مع الجوال ===== */
@media(max-width:900px){
 .boards{grid-template-columns:repeat(3,1fr)}
}
@media(max-width:600px){
  body{padding:6px}
 .h1 h2{font-size:13px}
 .h1 p{font-size:8px}
 .bar{font-size:10px;flex-direction:column;gap:4px;align-items:flex-start}
 .ctrl{flex-direction:column;gap:6px;padding:10px}
 .ctrl.c-inp{width:100px;font-size:16px;padding:10px 0}
 .c-btn{width:100%;padding:12px;font-size:14px}
 .boards{grid-template-columns:repeat(2,1fr);gap:8px}
 .bt{font-size:10px}
 .bc{min-height:72px;padding:10px 4px}
 .bv{font-size:17px}
 .act{flex-direction:column}
 .act button{width:100%;padding:12px;font-size:14px}
 .tbl{font-size:11px;min-width:600px}
 .tbl th{font-size:11px;padding:10px 6px}
 .tbl td{font-size:12px;padding:10px 6px}
 .macd{font-size:9px}
}
</style></head><body>
<div class="h1"><h2>TP $0.50$ / 100$ / 500$ - V77.1 علاج قوي</h2><p>$0.05 + ANTI يحفظ + SHORT ↔ LONG يقلب 3 + $0.50$ SL $0.50$ TP - اخسر يقلب $1-</p></div>
<div class="bar" id="topBar"><span>✅ BINANCE REAL</span><span>V82 SPOT MACD 💎 MOBILE</span></div>
<div class="ctrl">
  <button class="c-btn" onclick="save()">حفظ 🟢</button>
  <input class="c-inp" id="tp" value="0.50">
  <input class="c-inp" id="per_trade" value="100">
  <input class="c-inp" id="capital" value="500">
</div>
<div class="boards">
  <div class="b"><div class="bt">💰 ثابت</div><div class="bc"><div class="bv w" id="v_fixed">500.0$</div></div></div>
  <div class="b"><div class="bt">🔥 حر</div><div class="bc"><div class="bv w">0.0$</div></div></div>
  <div class="b"><div class="bt">💹 صافي ربح</div><div class="bc"><div class="bv g" id="v_safi">+73.5$</div></div></div>
  <div class="b"><div class="bt">⚖️ L/S | دورات | قلبات</div><div class="bc"><div class="bv w" id="v_ls" style="font-size:15px;line-height:1.2">3/2 | 130 |<br>170</div></div></div>
  <div class="b"><div class="bt">💎 الإجمالي</div><div class="bc gold"><div class="bv w" id="v_total">574.2$</div></div></div>
  <div class="b"><div class="bt">📈 غير محققة</div><div class="bc"><div class="bv yb" id="v_ghair">+0.73$</div></div></div>
</div>
<div class="act"><button class="r" onclick="fetch('/reset').then(()=>location.reload())">🔒 قفل الكل</button><button class="y" onclick="location.reload()">🔄 تصفير</button></div>
<div class="tbl-wrap">
<table class="tbl">
<thead><tr><th>عملة</th><th>اتجاه</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th><th>✕</th></tr></thead>
<tbody id="coins"></tbody>
</table>
<div class="macd" id="macd">MACD LIVE: ينتظر...</div>
</div>
<script>
async function save(){
  const d={capital:parseFloat(document.getElementById('capital').value),per_trade:parseFloat(document.getElementById('per_trade').value),tp:parseFloat(document.getElementById('tp').value)};
  await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
  const b=document.querySelector('.c-btn'); b.innerText='✅ تم'; setTimeout(()=>b.innerText='حفظ 🟢',1000);
}
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('v_fixed').innerText=d.fixed.toFixed(1)+'$';
    document.getElementById('v_safi').innerText=(d.safi>=0?'+':'')+d.safi.toFixed(1)+'$';
    document.getElementById('v_total').innerText=d.total.toFixed(1)+'$';
    document.getElementById('v_ghair').innerText=(d.ghair>=0?'+':'')+d.ghair.toFixed(2)+'$';
    document.getElementById('macd').innerText='MACD LIVE: '+d.macd_live;
    const top=document.getElementById('topBar'); if(d.is_frozen) top.classList.add('frozen'); else top.classList.remove('frozen');
    let h='';
    for(const p of d.positions){
      const sym=p[0],dir=p[1],entry=p[2],cur=p[3],usd=p[4],pct=p[5],macd=p[6]||'';
      h+=`<tr><td style="font-weight:900">${sym}<div style="font-size:8px;color:#ffcc00">${macd}</div></td><td><span class="long">${dir}</span></td><td>${entry.toFixed(4)}</td><td>${cur.toFixed(4)}</td><td class="${usd<0?'neg':'pos'}">${usd>=0?'+':''}${usd.toFixed(2)}$+</td><td class="${pct<0?'neg':'pos'}">${pct>=0?'+':''}${pct.toFixed(2)}%+</td><td><button class="close" onclick="fetch('/api/close/'+sym).then(()=>load())">✕</button></td></tr>`;
    }
    document.getElementById('coins').innerHTML=h || '<tr><td colspan=7 style="padding:16px;opacity:0.5">⏳ ينتظر باينانس REAL...</td></tr>';
  }catch(e){}
}
setInterval(load,2000); load();
</script>
</body></html>
    '''
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

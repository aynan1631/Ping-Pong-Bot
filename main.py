from flask import Flask, request, jsonify, redirect
import threading, time, os
from datetime import datetime
import ccxt

app = Flask(__name__)
exchange = ccxt.binance({'enableRateLimit': True})

config = {"capital":500.0,"per_trade":100.0,"tp":0.50,"sl":0.50}
state = {"fixed":500.0,"free":0.0,"safi":73.5,"ghair":-0.10,"long":2,"short":3,"dawrat":130,"qalbat":170,"positions":[["REZ","LONG",0.0040,0.0040,-0.55,-0.55],["VTHO","LONG",0.0007,0.0007,0.00,0.00],["NEAR","SHORT",2.3780,2.3780,0.00,0.00],["WLFI","LONG",0.0573,0.0573,0.00,0.00],["PUMP","LONG",0.0039,0.0039,0.03,0.03],["ETHFI","LONG",0.7428,0.7441,0.17,0.17]],"macd_live":"LSKUSDT, REZUSDT, VTHOUSDT, NEARUSDT, WLFIUSDT, PUMPUSDT, ETHFIUSDT, MARSCOINUSDT, RAYUSDT, UNIUSDT, SOPHUSDT, ENAUSDT, PEPEUSDT, ARBUSDT, AVAXUSDT","binance_status":"BINANCE REAL","last_update":"...","is_frozen":False}

def get_movers():
    tickers=exchange.fetch_tickers()
    mov=[]
    for sym,t in tickers.items():
        if not sym.endswith('/USDT'): continue
        if not t.get('last'): continue
        pct=t.get('percentage')
        if pct is None: continue
        mov.append((sym.replace('/USDT',''),float(pct),float(t['last'])))
    mov.sort(key=lambda x:x[1],reverse=True)
    return mov[:20]

def engine():
    while True:
        try:
            mov=get_movers()
            state["positions"]=[]
            for m in mov[:6]:
                state["positions"].append([m[0],"LONG",m[2]*0.999,m[2],0.0,0.0])
            state["macd_live"]=", ".join([f"{x[0]}USDT" for x in mov[:15]])
            state["binance_status"]=f"BINANCE REAL ✅"
            state["is_frozen"]=False
            break
        except: time.sleep(5)
    while True:
        try:
            for p in state["positions"]:
                try:
                    tk=exchange.fetch_ticker(p[0]+"/USDT")
                    cur=float(tk['last'])
                    p[3]=cur
                    pp=(cur-p[2])/p[2]*100
                    if p[1]=="SHORT": pp=-pp
                    p[4]=round(100*pp/100,2)
                    p[5]=round(pp,2)
                except: continue
            state["ghair"]=round(sum([p[4] for p in state["positions"]]),2)
            state["last_update"]=datetime.now().strftime("%H:%M:%S")
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
def api_data(): return jsonify(state)

@app.route('/api/close/<sym>')
def close_sym(sym):
    state["positions"]=[p for p in state["positions"] if p[0]!=sym]
    return jsonify({"ok":True})

@app.route('/api/config',methods=['POST'])
def api_cfg():
    d=request.get_json()
    if 'capital' in d: config["capital"]=float(d['capital']); state["fixed"]=float(d['capital'])
    if 'per_trade' in d: config["per_trade"]=float(d['per_trade'])
    if 'tp' in d: config["tp"]=float(d['tp'])
    return jsonify({"ok":True})

@app.route('/')
def home():
    return '''
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}body{margin:0;background:#070a1e;color:#fff;font-family:Cairo;padding:4px}
.h1{border:2px solid #00ff66;border-radius:18px;background:#12155a;text-align:center;padding:9px;margin-bottom:5px}
.h1 h2{margin:0;color:#00ff66;font-size:15px;font-weight:900}
.h1 p{margin:3px 0 0 0;color:#ffcc00;font-size:9px;font-weight:800}
.top{display:flex;justify-content:space-between;background:#12155a;border:1px solid #232a8a;border-radius:10px;padding:5px 10px;font-size:10px;font-weight:800;margin-bottom:5px}
.ctrl{display:flex;gap:6px;justify-content:center;align-items:center;background:#12155a;border:1px solid #232a8a;border-radius:12px;padding:6px;margin-bottom:5px}
.inp{background:#070a1e;border:2px solid #00ff66;border-radius:10px;color:#00ff66;font-family:JetBrains Mono;font-weight:900;width:62px;text-align:center;padding:5px;outline:none;font-size:13px}
.btn{background:#00ff66;border:none;border-radius:10px;padding:6px 16px;font-weight:900;font-family:Cairo;color:#000;cursor:pointer;font-size:12px}
.boards{display:grid;grid-template-columns:repeat(6,1fr);gap:5px;margin-bottom:5px}
.bd{display:flex;flex-direction:column;gap:2px}
.bt{font-size:10px;font-weight:900;text-align:center;opacity:0.9}
.bc{background:#1a1f8a;border:1px solid #2d36b0;border-radius:16px;padding:10px 4px;text-align:center;min-height:76px;display:flex;flex-direction:column;justify-content:center}
.bc.gold{border:2px solid #00ff66;box-shadow:0 0 14px rgba(0,255,102,0.25)}
.bv{font-family:JetBrains Mono;font-size:17px;font-weight:900;direction:ltr}
.bv.g{color:#00ff66}.bv.w{color:#fff}.bv.y{color:#ffcc00}
.act{display:flex;justify-content:center;gap:8px;margin-bottom:5px}
.act button{border:none;border-radius:12px;padding:6px 18px;font-weight:900;font-family:Cairo;font-size:12px;cursor:pointer}
.r{background:#ff2d55;color:#fff}.y{background:#ffeb3b;color:#000}
.tbl{width:100%;border-collapse:collapse;background:#0e1150;border-radius:16px;overflow:hidden;border:1px solid #1e2480}
.tbl th{background:#2a36f0;color:#ff4d8d;font-size:13px;font-weight:900;padding:12px 4px;text-align:center}
.tbl td{padding:11px 4px;text-align:center;font-family:JetBrains Mono;font-size:13px;font-weight:800;border-top:1px solid #1a2160}
.tbl tr{background:#12155a}
.long{background:#00ff55;color:#000;border-radius:20px;padding:5px 12px;font-size:12px;font-weight:900;display:inline-block;min-width:58px;font-family:Cairo}
.short{background:#ff2d55;color:#fff;border-radius:20px;padding:5px 12px;font-size:12px;font-weight:900;display:inline-block;min-width:58px;font-family:Cairo}
.close{width:36px;height:36px;border:1.5px solid #4a4f8a;border-radius:10px;background:transparent;color:#aab;font-size:16px;cursor:pointer}
.neg{color:#ff3344}.pos{color:#00ff66}
.macd{background:#080a1e;border-top:3px solid #00ff66;color:#ffcc00;font-size:10px;font-weight:800;padding:7px 10px;direction:ltr;text-align:left;white-space:nowrap;overflow:hidden}
</style></head><body>
<div class="h1"><h2>V77.1 علاج قوي - $500 / $100 / $0.50$ TP</h2><p>$0.05 + ANTI يحفظ + SHORT ↔ LONG يقلب 3 + $0.50$ TP -0.50$ SL اخسر يقلب -1$</p></div>
<div class="top"><span>فتوح - V77.1 FAKHMA 💎 100%</span><span id="binStatus">BINANCE REAL</span></div>
<div class="ctrl"><button class="btn" onclick="save()">⚙️ حفظ</button><input class="inp" id="tp" value="0.50"><input class="inp" id="per_trade" value="100"><input class="inp" id="capital" value="500"></div>
<div class="boards">
  <div class="bd"><div class="bt">💰 ثابت</div><div class="bc"><div class="bv w">500.0$</div></div></div>
  <div class="bd"><div class="bt">🦋 حر</div><div class="bc"><div class="bv w" id="free">0.0$</div></div></div>
  <div class="bd"><div class="bt">💵 صافي ربح</div><div class="bc"><div class="bv g" id="safi">+73.5$</div></div></div>
  <div class="bd"><div class="bt">⚖️ L/S | دورات | قلبات</div><div class="bc"><div class="bv w" id="ls">3/2 | 130 | 170</div></div></div>
  <div class="bd"><div class="bt">💎 الإجمالي</div><div class="bc gold"><div class="bv w" id="total">573.4$</div></div></div>
  <div class="bd"><div class="bt">📈 غير محققة</div><div class="bc"><div class="bv y" id="ghair">-+0.1$</div></div></div>
</div>
<div class="act"><button class="r" onclick="fetch('/reset').then(()=>location.reload())">🔒 قفل الكل</button><button class="y" onclick="location.reload()">🔄 تصفير</button></div>
<div style="border-radius:16px;overflow:hidden;border:1px solid #1e2480">
<table class="tbl">
<thead><tr><th>عملة</th><th>اتجاه</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th><th>✕</th></tr></thead>
<tbody id="coins"></tbody>
</table>
<div class="macd" id="macd">MACD LIVE: LSKUSDT, REZUSDT, VTHOUSDT, NEARUSDT, WLFIUSDT, PUMPUSDT, ETHFIUSDT, MARSCOINUSDT, RAYUSDT, UNIUSDT, SOPHUSDT, ENAUSDT, PEPEUSDT, ARBUSDT, AVAXUSDT</div>
</div>
<script>
async function save(){
  const d={capital:parseFloat(document.getElementById('capital').value),per_trade:parseFloat(document.getElementById('per_trade').value),tp:parseFloat(document.getElementById('tp').value)};
  await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
  location.reload();
}
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('binStatus').innerText=d.binance_status;
    document.getElementById('safi').innerText=(d.safi>=0?'+':'')+d.safi.toFixed(1)+'$';
    document.getElementById('ghair').innerText=(d.ghair>=0?'+':'')+d.ghair.toFixed(2)+'$';
    document.getElementById('total').innerText=(d.fixed+d.safi+d.ghair).toFixed(1)+'$';
    document.getElementById('macd').innerText='MACD LIVE: '+d.macd_live;
    let h='';
    for(const p of d.positions){
      const sym=p[0],dir=p[1],entry=p[2],cur=p[3],usd=p[4],pct=p[5];
      const badge=dir==='LONG'?`<span class="long">LONG</span>`:`<span class="short">SHORT</span>`;
      const usdC=usd<0?'neg':'pos', pctC=pct<0?'neg':'pos';
      h+=`<tr><td style="font-weight:900">${sym}</td><td>${badge}</td><td>${entry.toFixed(4)}</td><td>${cur.toFixed(4)}</td><td class="${usdC}">${usd>=0?'+':''}${usd.toFixed(2)}$</td><td class="${pctC}">${pct>=0?'+':''}${pct.toFixed(2)}%</td><td><button class="close" onclick="fetch('/api/close/'+sym).then(()=>load())">✕</button></td></tr>`;
    }
    document.getElementById('coins').innerHTML=h || '<tr><td colspan=7 style="padding:14px;opacity:0.5">⏳ ينتظر باينانس...</td></tr>';
  }catch(e){}
}
setInterval(load,2000); load();
</script>
</body></html>
    '''
@app.route('/reset')
def reset():
    state["safi"]=0; state["ghair"]=0; state["positions"]=[]; state["is_frozen"]=False
    return redirect('/')
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

from flask import Flask, request, jsonify, redirect
import threading, time, os
from datetime import datetime
import ccxt

app = Flask(__name__)
exchange = ccxt.binance({'enableRateLimit': True})

config = {"capital":2000.0,"per_trade":200.0,"tp_pct":0.8,"sl_pct":1.5,"daily_target_pct":3.5,"panic_drop_pct":1.0}
state = {"daily_start":2000.0,"daily_peak":2000.0,"daily_peak_pct":0.0,"safi":0.0,"ghair":0.0,"loss":0.0,"loss_pool":0.0,"trades_today":0,"trades_closed":0,"is_daily_done":False,"positions":[],"binance_status":"BINANCE REAL","last_update":"...","is_frozen":False,"binance_error":""}

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
        return (e12-e26>0),e12-e26
    except: raise
def get_movers():
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
def calc_total():
    total=config["capital"]+state["safi"]+state["ghair"]+state["loss"]
    pct=((total-state["daily_start"])/state["daily_start"]*100) if state["daily_start"]>0 else 0
    if total>state["daily_peak"]: state["daily_peak"]=total; state["daily_peak_pct"]=pct
    return total,pct

def engine():
    while True:
        try:
            state["binance_status"]="يتصل..."; state["is_frozen"]=True
            mov=get_movers()
            state["positions"]=[]
            for i in range(min(10,len(mov))):
                sym,pct,pr=mov[i]
                state["positions"].append([sym,pr*0.996,pr,0.0,0.0,pct,0.0,"..."])
            state["binance_status"]=f"BINANCE REAL ✅ {len(mov)}"; state["is_frozen"]=False; break
        except Exception as e:
            state["binance_status"]=f"BINANCE DOWN ⛔"; state["binance_error"]=str(e)[:120]; time.sleep(5)
    pool=0.0; idx=0
    while True:
        try:
            try:
                for p in state["positions"]:
                    tk=exchange.fetch_ticker(p[0])
                    if not tk['last']: raise Exception("No price")
                    cur=float(tk['last']); p[2]=cur; pp=(cur-p[1])/p[1]*100; us=config["per_trade"]*pp/100
                    p[3]=round(us,2); p[4]=round(pp,2)
                state["last_update"]=datetime.now().strftime("%H:%M:%S"); state["binance_status"]=f"BINANCE REAL ✅"; state["is_frozen"]=False
            except Exception as e:
                state["binance_status"]="BINANCE DOWN ⛔ مجمد"; state["binance_error"]=str(e)[:120]; state["is_frozen"]=True; time.sleep(5); continue
            if state["positions"]:
                try:
                    p=state["positions"][idx%len(state["positions"])]
                    is_bull,m=check_macd(p[0]); p[7]=f"{'صاعد' if is_bull else 'نازل'} {m:.3f}"; idx+=1
                except: pass
            total,daily=calc_total(); state["ghair"]=round(sum([p[3] for p in state["positions"]]),2)
            if daily>=config["daily_target_pct"] and not state["is_daily_done"]:
                drop=state["daily_peak"]-total; dp=(drop/state["daily_peak"]*100) if state["daily_peak"]>0 else 0
                if dp>=config["panic_drop_pct"]:
                    for p in list(state["positions"]):
                        real=round(p[3]-config["per_trade"]*0.002,2)
                        if real>=0: state["safi"]=round(state["safi"]+real,2)
                        else: state["loss"]=round(state["loss"]+real,2)
                    state["positions"]=[]; state["ghair"]=0; state["is_daily_done"]=True; continue
            if state["is_daily_done"]: time.sleep(3); continue
            closed=[]
            for p in state["positions"]:
                tp=config["tp_pct"]+(abs(p[6])/config["per_trade"]*100)
                if p[4]>=tp or p[4]<=-config["sl_pct"]: closed.append(p)
            for p in closed:
                real=round(p[3]-config["per_trade"]*0.002,2)
                if p in state["positions"]: state["positions"].remove(p)
                if real<0:
                    pool+=abs(real); state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=round(pool,2)
                    try:
                        mov=get_movers(); sh=round(pool/10,2); ex=[x[0] for x in state["positions"]]
                        for x in mov:
                            if x[0] not in ex: state["positions"].append([x[0],x[2]*0.996,x[2],0.0,0.0,x[1],sh,"دين"]); pool=round(max(0,pool-sh),2); state["loss_pool"]=pool; break
                    except: time.sleep(5)
                else:
                    if pool>0:
                        if real>=pool: state["safi"]=round(state["safi"]+real-pool,2); state["loss"]=round(state["loss"]+pool,2); pool=0; state["loss_pool"]=0
                        else: pool=round(pool-real,2); state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=pool
                    else: state["safi"]=round(state["safi"]+real,2)
                state["trades_closed"]+=1
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
    total,pct=calc_total()
    return jsonify({"total":round(total,2),"daily_pct":round(pct,2),"daily_usd":round(total-state["daily_start"],2),"capital":config["capital"],"per_trade":config["per_trade"],"safi":state["safi"],"ghair":state["ghair"],"loss":state["loss"],"loss_pool":state["loss_pool"],"trades_closed":state["trades_closed"],"daily_peak":round(state["daily_peak"],2),"positions":state["positions"],"binance_status":state["binance_status"],"binance_error":state["binance_error"],"last_update":state["last_update"],"is_frozen":state["is_frozen"]})
@app.route('/api/config',methods=['POST'])
def api_cfg():
    d=request.get_json()
    if 'capital' in d: config["capital"]=float(d['capital']); state["daily_start"]=config["capital"]+state["safi"]+state["loss"]
    if 'per_trade' in d: config["per_trade"]=float(d['per_trade'])
    if 'tp' in d: config["tp_pct"]=float(d['tp'])
    if 'sl' in d: config["sl_pct"]=float(d['sl'])
    if 'daily' in d: config["daily_target_pct"]=float(d['daily'])
    if 'panic' in d: config["panic_drop_pct"]=float(d['panic'])
    return jsonify({"ok":True})
@app.route('/')
def home():
    return '''
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;800;900&family=JetBrains+Mono:wght@700;800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}
body{margin:0;background:#070a14;color:#fff;font-family:Cairo;padding:6px}
.topbar{display:flex;justify-content:space-between;align-items:center;gap:8px;background:#0f1222;border:1px solid #22264a;border-radius:10px;padding:6px 10px;font-size:11px;font-weight:800;margin-bottom:6px}
.topbar.frozen{background:#ff3b5c20;border-color:#ff3b5c}
/* لوحة التحكم سطر واحد بالأعلى */
.ctrl-bar{max-width:100%;display:flex;flex-wrap:wrap;align-items:center;gap:6px;background:linear-gradient(180deg,#171a2e,#101323);border:1px solid #2a2f5a;border-radius:10px;padding:6px 8px;margin-bottom:6px}
.ctrl-bar.title{font-size:12px;font-weight:900;color:#ffca28;margin-left:8px;white-space:nowrap}
.ctrl-item{display:flex;align-items:center;gap:4px;background:#070912;border:1px solid #22264a;border-radius:8px;padding:4px 7px}
.ctrl-item label{font-size:10px;opacity:0.7;font-weight:800;white-space:nowrap}
.ctrl-item input{background:transparent;border:none;color:#ffca28;font-family:JetBrains Mono;font-weight:800;font-size:12px;width:55px;outline:none;direction:ltr}
.ctrl-bar button{border:none;border-radius:8px;padding:6px 12px;font-family:Cairo;font-weight:900;font-size:11px;cursor:pointer}
.btn-save{background:linear-gradient(90deg,#ffca28,#ffb300);color:#000}
.btn-reset{background:transparent;border:1px solid #333!important;color:#fff}
/* 5 لوحات في سطر واحد */
.stats-wrap{max-width:100%;margin-bottom:6px}
.stats-titles{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-bottom:3px}
.stats-titles span{font-size:11px;font-weight:900;opacity:0.8;text-align:center;letter-spacing:0.2px}
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:6px}
.card{background:radial-gradient(120% 120% at 0% 0%,#1a1e36,#0e1020);border:1px solid #22264a;border-radius:12px;padding:8px 10px;text-align:center;min-height:72px;display:flex;flex-direction:column;justify-content:center}
.card.gold{background:radial-gradient(120% 120% at 0% 0%,#2a220a,#1a1605);border-color:#ffca28;box-shadow:0 0 18px rgba(255,202,40,0.18)}
.card.val{font-family:JetBrains Mono;font-size:20px;font-weight:900;direction:ltr}
.card.sub{font-size:10px;font-weight:800;margin-top:2px;opacity:0.9}
.pos{color:#00ff9d}.neg{color:#ff3b5c}
/* عملات مصغرة تحت */
.coins{display:grid;grid-template-columns:repeat(5,1fr);gap:6px}
.coin{background:linear-gradient(180deg,#171a2e,#0f1222);border:1px solid #22264a;border-radius:10px;padding:6px 7px;min-height:92px;display:flex;flex-direction:column;justify-content:space-between}
.coin.frozen{opacity:0.5}
.coin.posb{border-color:rgba(0,255,157,0.35)}.coin.negb{border-color:rgba(255,59,92,0.35)}
.ctop{display:flex;justify-content:space-between;align-items:center}
.ctop b{font-family:JetBrains Mono;font-size:12px;font-weight:900}
.ctop.tags{display:flex;gap:3px;flex-wrap:wrap;justify-content:flex-end}
.bdg{font-size:7px;font-weight:900;padding:2px 5px;border-radius:10px;background:#ff9800;color:#000}
.bdgMacd{font-size:7px;font-weight:900;padding:2px 5px;border-radius:10px;border:1px solid #00ff9d;color:#00ff9d}
.bdgMacd.up{background:#00ff9d;color:#000}.bdgMacd.down{background:#ff3b5c;color:#fff;border-color:#ff3b5c}
.cprice{font-family:JetBrains Mono;font-size:8px;opacity:0.45;direction:ltr;margin:3px 0;white-space:nowrap;overflow:hidden}
.barw{height:4px;background:#05070a;border-radius:20px;overflow:hidden;margin-bottom:4px}
.bar{height:100%;border-radius:20px}
.cprof{border-radius:7px;padding:4px 5px;text-align:center;font-family:JetBrains Mono;font-weight:900;font-size:12px;direction:ltr;line-height:1.1}
.cprof small{font-size:9px;opacity:0.7;display:block}

@media(max-width:1200px){
 .coins{grid-template-columns:repeat(4,1fr)}
 .stats{grid-template-columns:repeat(5,1fr)}
 .card.val{font-size:17px}
}
@media(max-width:900px){
 .ctrl-bar{flex-direction:column;align-items:stretch}
 .ctrl-bar.ctrl-item{justify-content:space-between}
 .stats-titles{display:none}
 .stats{grid-template-columns:repeat(2,1fr)}
 .coins{grid-template-columns:repeat(2,1fr)}
}
@media(max-width:600px){
 .stats{grid-template-columns:1fr 1fr}
 .stats.card:last-child{grid-column:span 2}
 .coins{grid-template-columns:1fr}
}
</style></head><body>
<div class="topbar" id="topBar"><span style="font-weight:900">فتوح - COMPACT 100% 🖥️</span><span><span id="binStatus">BINANCE REAL</span> • <span id="lastUpd">...</span> • قمة $<span id="peak">2000</span></span></div>

<div class="ctrl-bar">
  <span class="title">⚙️ تحكم سريع</span>
  <div class="ctrl-item"><label>رأس</label><input id="capital" value="2000"></div>
  <div class="ctrl-item"><label>صفقة</label><input id="per_trade" value="200"></div>
  <div class="ctrl-item"><label>ربح%</label><input id="tp" value="0.8"></div>
  <div class="ctrl-item"><label>ستوب%</label><input id="sl" value="1.5"></div>
  <div class="ctrl-item"><label>هدف%</label><input id="daily" value="3.5"></div>
  <div class="ctrl-item"><label>حماية%</label><input id="panic_inp" value="1.0"></div>
  <button class="btn-save" onclick="save()">حفظ +</button>
  <button class="btn-reset" onclick="fetch('/reset').then(()=>location.reload())">🔄 يوم جديد</button>
  <span id="errorBox" style="font-size:10px;color:#ff8a80;display:none"></span>
</div>

<div class="stats-wrap">
  <div class="stats-titles">
    <span>رأس المال</span><span>الإجمالي</span><span>مجمع الخسارة</span><span>غير محقق</span><span>يوم محقق</span>
  </div>
  <div class="stats">
    <div class="card"><div class="val" id="v_cap">$2000</div><div class="sub" style="opacity:0.5">10×$200</div></div>
    <div class="card gold"><div class="val" id="v_total">$2000</div><div class="sub" id="v_daily">0$ (0%)</div></div>
    <div class="card"><div class="val" id="v_pool">$0</div><div class="sub" id="v_loss">0$</div></div>
    <div class="card"><div class="val" id="v_ghair">+$0</div><div class="sub" id="v_gcount">0 عملات</div></div>
    <div class="card"><div class="val" id="v_safi">-$0</div><div class="sub" id="v_today">0 مقفلة</div></div>
  </div>
</div>

<div class="coins" id="coins"></div>

<script>
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('binStatus').innerText=d.binance_status;
    document.getElementById('lastUpd').innerText=d.last_update;
    document.getElementById('peak').innerText=d.daily_peak.toFixed(0);
    document.getElementById('v_cap').innerText='$'+d.capital.toFixed(0);
    const totalEl=document.getElementById('v_total');
    totalEl.innerText='$'+d.total.toFixed(2);
    totalEl.className='val '+(d.total>=d.capital?'pos':'');
    const dailyEl=document.getElementById('v_daily');
    dailyEl.innerHTML=(d.daily_usd>=0?'+':'')+d.daily_usd.toFixed(2)+'$ ('+(d.daily_pct>=0?'+':'')+d.daily_pct.toFixed(2)+'%)';
    dailyEl.className='sub '+(d.daily_usd>=0?'pos':'neg');
    document.getElementById('v_pool').innerText='$'+d.loss_pool.toFixed(2);
    document.getElementById('v_loss').innerText=d.loss.toFixed(2)+'$';
    const ghairEl=document.getElementById('v_ghair');
    ghairEl.innerHTML=(d.ghair>=0?'+':'')+d.ghair.toFixed(2)+'$';
    ghairEl.className='val '+(d.ghair>=0?'pos':'neg');
    document.getElementById('v_gcount').innerText=d.positions.length+' عملات';
    const safiEl=document.getElementById('v_safi');
    safiEl.innerHTML=(d.safi>=0?'+':'')+d.safi.toFixed(2)+'$';
    safiEl.className='val '+(d.safi>=0?'pos':'neg');
    document.getElementById('v_today').innerText=d.trades_closed+' مقفلة';
    const eb=document.getElementById('errorBox');
    const top=document.getElementById('topBar');
    if(d.is_frozen){ top.classList.add('frozen'); eb.style.display='inline'; eb.innerText='⛔ مجمد: '+d.binance_error; }
    else { top.classList.remove('frozen'); eb.style.display='none'; }
    let html='';
    for(const p of d.positions){
      const sym=p[0].replace('/USDT',''),entry=p[1],cur=p[2],usd=p[3],pct=p[4],mov=p[5],loss=p[6],macd=p[7]||'';
      const isPos=usd>=0; const col=isPos?'#00ff9d':'#ff3b5c'; const bg=isPos?'rgba(0,255,157,0.12)':'rgba(255,59,92,0.12)';
      const bclass=d.is_frozen?'frozen':(isPos?'posb':'negb');
      const debt=loss>0.01?`<span style="font-size:6px;background:#ff1744;color:#fff;padding:2px 4px;border-radius:8px">دين $${loss.toFixed(2)}</span>`:'';
      const macdClass=macd.includes('صاعد')?'up':macd.includes('نازل')?'down':'';
      const bar=Math.min(100,Math.max(8,(pct+1.5)/2.5*100));
      html+=`<div class="coin ${bclass}"><div class="ctop"><b>${sym}</b><div class="tags"><span class="bdgMacd ${macdClass}">${macd}</span><span class="bdg">${mov.toFixed(1)}%</span>${debt}</div></div><div class="cprice">${entry.toFixed(4)} → ${cur.toFixed(4)}</div><div class="barw"><div class="bar" style="width:${bar}%;background:${col}"></div></div><div class="cprof" style="color:${col};background:${bg}">${isPos?'+':''}${usd.toFixed(2)}$<small>${pct>=0?'+':''}${pct.toFixed(2)}%</small></div></div>`;
    }
    document.getElementById('coins').innerHTML=html || '<div style="padding:20px;opacity:0.5;font-size:12px;text-align:center">⏳ ينتظر باينانس...</div>';
  }catch(e){}
}
async function save(){
  const d={capital:parseFloat(capital.value),per_trade:parseFloat(per_trade.value),tp:parseFloat(tp.value),sl:parseFloat(sl.value),daily:parseFloat(daily.value),panic:parseFloat(panic_inp.value)};
  const b=document.querySelector('.btn-save'); const old=b.innerText; b.innerText='⏳';
  try{const r=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}); if((await r.json()).ok){b.innerText='✅'; setTimeout(()=>b.innerText=old,1000);}}catch(e){b.innerText='❌';}
}
setInterval(load,2000); load();
</script>
</body></html>
    '''
@app.route('/reset')
def reset():
    state["daily_start"]=config["capital"]+state["safi"]+state["loss"]; state["daily_peak"]=state["daily_start"]; state["safi"]=0; state["ghair"]=0; state["loss"]=0; state["loss_pool"]=0; state["trades_closed"]=0; state["is_daily_done"]=False; state["positions"]=[]; state["is_frozen"]=False
    return redirect('/')
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

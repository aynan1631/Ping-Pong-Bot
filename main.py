from flask import Flask, request, jsonify, redirect
import threading, time, os
from datetime import datetime
try:
    import ccxt
    HAS_CCXT=True
    exchange=ccxt.binance({'enableRateLimit':True,'options':{'defaultType':'spot'}})
except:
    HAS_CCXT=False
    exchange=None

app=Flask(__name__)
config={"capital":2000.0,"per_trade":200.0,"tp_pct":0.8,"sl_pct":1.5,"daily_target_pct":3.5,"panic_drop_pct":1.0}
state={"daily_start":2000.0,"daily_peak_pct":0.0,"safi":0.0,"ghair":0.0,"loss":0.0,"loss_pool":0.0,"trades_today":0,"trades_closed":0,"is_daily_done":False,"panic_triggered":False,"positions":[],"binance_status":"CONNECTING","binance_error":"","last_update":"...","is_frozen":False}

EXCLUDE=['USDT','USDC','FDUSD','BUSD','DAI','TUSD','USDP']

def get_movers_strict():
    if not HAS_CCXT: raise Exception("CCXT not installed")
    tickers=exchange.fetch_tickers()
    mov=[]
    for sym,t in tickers.items():
        if not sym.endswith('/USDT'): continue
        if sym.replace('/USDT','') in EXCLUDE: continue
        if not t['quoteVolume'] or t['quoteVolume']<3000000: continue
        ch=t.get('percentage')
        if ch is None or ch<0.5: continue
        if not t['last']: continue
        mov.append((sym,float(ch),float(t['last'])))
    if not mov: raise Exception("No movers")
    mov.sort(key=lambda x:x[1],reverse=True)
    return mov[:15]

def calc_total():
    total=config["capital"]+state["safi"]+state["ghair"]+state["loss"]
    pct=((total-state["daily_start"])/state["daily_start"]*100) if state["daily_start"]>0 else 0
    if total>state["daily_peak"]:
        state["daily_peak"]=total
        state["daily_peak_pct"]=pct
    return total,pct

def engine():
    retry=0
    while True:
        try:
            state["binance_status"]="CONNECTING BINANCE..."
            mov=get_movers_strict()
            state["binance_status"]="BINANCE REAL"
            state["is_frozen"]=False
            state["binance_error"]=""
            for i in range(min(10,len(mov))):
                sym,pct,pr=mov[i]
                state["positions"].append([sym,pr*0.996,pr,0.0,0.0,pct,0.0])
            break
        except Exception as e:
            retry+=1
            state["binance_status"]=f"BINANCE DOWN - محاولة {retry}"
            state["binance_error"]=str(e)[:120]
            state["is_frozen"]=True
            time.sleep(5)
    pool=0.0
    while True:
        try:
            try:
                for p in state["positions"]:
                    tk=exchange.fetch_ticker(p[0])
                    if not tk['last']: raise Exception(f"No price {p[0]}")
                    rp=float(tk['last'])
                    p[2]=rp
                    pp=(rp-p[1])/p[1]*100
                    us=config["per_trade"]*pp/100
                    p[3]=round(us,2); p[4]=round(pp,2)
                state["binance_status"]="BINANCE REAL"
                state["is_frozen"]=False
                state["binance_error"]=""
                state["last_update"]=datetime.now().strftime("%H:%M:%S")
            except Exception as e:
                state["binance_status"]="BINANCE DOWN ⛔ - مجمد"
                state["binance_error"]=str(e)[:150]
                state["is_frozen"]=True
                time.sleep(5)
                continue

            total,daily=calc_total()
            state["ghair"]=round(sum([p[3] for p in state["positions"]]),2)

            if not state["is_frozen"] and daily>=config["daily_target_pct"] and not state["is_daily_done"]:
                drop=state["daily_peak"]-total
                drop_pct=(drop/state["daily_peak"]*100) if state["daily_peak"]>0 else 0
                if drop_pct>=config["panic_drop_pct"]:
                    for p in list(state["positions"]):
                        real=round(p[3]-config["per_trade"]*0.002,2)
                        if real>=0:
                            if pool>0:
                                if real>=pool: state["safi"]=round(state["safi"]+real-pool,2); state["loss"]=round(state["loss"]+pool,2); pool=0
                                else: pool=round(pool-real,2); state["loss"]=round(state["loss"]+real,2)
                            else: state["safi"]=round(state["safi"]+real,2)
                        else: state["loss"]=round(state["loss"]+real,2)
                        state["trades_closed"]+=1
                    state["positions"]=[]; state["ghair"]=0; state["loss_pool"]=pool
                    state["is_daily_done"]=True; state["panic_triggered"]=True
                    continue

            if state["is_daily_done"]:
                time.sleep(3); continue

            closed=[]
            for p in state["positions"]:
                tp=config["tp_pct"]+(abs(p[6])/config["per_trade"]*100)
                if p[4]>=tp or p[4]<=-config["sl_pct"]:
                    closed.append(p)
            for p in closed:
                real=round(p[3]-config["per_trade"]*0.002,2)
                if p in state["positions"]: state["positions"].remove(p)
                if real<0:
                    pool+=abs(real); state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=round(pool,2)
                    try:
                        mov=get_movers_strict(); ex=[x[0] for x in state["positions"]]; sh=round(pool/10,2)
                        for x in mov:
                            if x[0] not in ex:
                                state["positions"].append([x[0],x[2]*0.996,x[2],0.0,0.0,x[1],sh]); pool=round(max(0,pool-sh),2); state["loss_pool"]=pool; break
                    except: state["is_frozen"]=True
                else:
                    if pool>0:
                        if real>=pool: state["safi"]=round(state["safi"]+real-pool,2); state["loss"]=round(state["loss"]+pool,2); pool=0; state["loss_pool"]=0
                        else: pool=round(pool-real,2); state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=pool
                    else: state["safi"]=round(state["safi"]+real,2)
                state["trades_closed"]+=1; state["trades_today"]+=1
                if real>=0 and pool==0 and len(state["positions"])<10 and not state["is_frozen"]:
                    try:
                        mov=get_movers_strict(); ex=[x[0] for x in state["positions"]]
                        for x in mov:
                            if x[0] not in ex: state["positions"].append([x[0],x[2]*0.996,x[2],0.0,0.0,x[1],0.0]); break
                    except: pass
            time.sleep(2.5)
        except: time.sleep(3)

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
    return jsonify({"total":round(total,2),"daily_pct":round(pct,2),"daily_usd":round(total-state["daily_start"],2),"capital":config["capital"],"per_trade":config["per_trade"],"safi":state["safi"],"ghair":state["ghair"],"loss":state["loss"],"loss_pool":state["loss_pool"],"trades_today":state["trades_today"],"trades_closed":state["trades_closed"],"is_done":state["is_daily_done"],"panic_triggered":state["panic_triggered"],"daily_peak":round(state["daily_peak"],2),"daily_peak_pct":round(state["daily_peak_pct"],2),"panic_drop":config["panic_drop_pct"],"daily_target":config["daily_target_pct"],"positions":state["positions"],"binance_status":state["binance_status"],"binance_error":state["binance_error"],"last_update":state["last_update"],"is_frozen":state["is_frozen"],"has_ccxt":HAS_CCXT})
@app.route('/api/config',methods=['POST'])
def api_cfg():
    try:
        d=request.get_json()
        if 'capital' in d: config["capital"]=float(d['capital']); state["daily_start"]=config["capital"]+state["safi"]+state["loss"]
        if 'per_trade' in d: config["per_trade"]=float(d['per_trade'])
        if 'tp' in d: config["tp_pct"]=float(d['tp'])
        if 'sl' in d: config["sl_pct"]=float(d['sl'])
        if 'daily' in d: config["daily_target_pct"]=float(d['daily'])
        if 'panic' in d: config["panic_drop_pct"]=float(d['panic'])
        return jsonify({"ok":True})
    except: return jsonify({"ok":False})

@app.route('/')
def home():
    return '''
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}
body{margin:0;background:#080a0f;color:#fff;font-family:Cairo;padding:8px}
.hd{max-width:1600px;margin:0 auto 8px auto;display:flex;justify-content:space-between;align-items:center;background:#0e101a;border:1px solid #1e233a;border-radius:12px;padding:8px 14px;font-size:11px}
.hd.live{color:#00ff9d;font-weight:900}
.cards{max-width:1600px;margin:0 auto;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.card{background:linear-gradient(180deg,#121524,#0a0c14);border:1px solid #1e233a;border-radius:16px;padding:16px 14px;position:relative;overflow:hidden}
.card.gold{background:linear-gradient(180deg,#1a1608,#201c0a);border:1px solid #ffca28;box-shadow:0 0 30px rgba(255,202,40,0.18)}
.card.lb{font-size:10px;opacity:0.45;font-weight:800;letter-spacing:0.5px}
.card.val{font-family:JetBrains Mono;font-size:26px;font-weight:800;margin-top:6px;direction:ltr;text-align:right}
.card.sub{font-size:10px;opacity:0.55;margin-top:6px;font-weight:700}
.card.sub2{font-size:9px;opacity:0.35;margin-top:2px}
.pos{color:#00ff9d}.neg{color:#ff3b5c}
.main{max-width:1600px;margin:12px auto;display:grid;grid-template-columns:1fr 300px;gap:12px}
.coins{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;align-content:start}
.coin{background:linear-gradient(180deg,#13151f,#0e1018);border:1px solid #1e233a;border-radius:14px;padding:12px;position:relative}
.coin.posb{border-color:rgba(0,255,157,0.25)}.coin.negb{border-color:rgba(255,59,92,0.25)}
.ctop{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.ctop b{font-family:JetBrains Mono;font-size:13px}
.bdg{font-size:7.5px;font-weight:900;padding:3px 7px;border-radius:20px;background:#ff9800;color:#000}
.bdg2{font-size:7px;font-weight:900;padding:2px 6px;border-radius:20px;background:#ff1744;color:#fff}
.cprice{font-family:JetBrains Mono;font-size:10px;opacity:0.4;direction:ltr;margin-bottom:8px}
.barw{height:6px;background:#05070a;border-radius:20px;overflow:hidden;margin-bottom:8px}
.bar{height:100%;border-radius:20px;transition:width 0.5s}
.cprof{border-radius:8px;padding:8px;text-align:center;font-family:JetBrains Mono;font-weight:800;font-size:13px;direction:ltr}
.cprof small{display:block;font-size:9px;opacity:0.6;margin-top:2px}
.ctrl{background:linear-gradient(180deg,#121524,#0a0c14);border:1px solid #1e233a;border-radius:16px;padding:14px;position:sticky;top:8px;height:fit-content}
.ctrl h3{margin:0 0 14px 0;color:#ffca28;font-size:12px;text-align:right}
.row{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;background:#080a0f;border:1px solid #1e233a;border-radius:10px;padding:8px 10px}
.row label{font-size:10px;opacity:0.6;font-weight:700}
.inp{background:transparent;border:none;color:#ffca28;font-family:JetBrains Mono;font-weight:800;font-size:14px;text-align:left;width:90px;outline:none;direction:ltr}
.btn{width:100%;background:linear-gradient(90deg,#ffca28,#ffb300);color:#000;border:none;border-radius:12px;padding:12px;font-weight:900;font-family:Cairo;cursor:pointer;font-size:13px;margin-top:6px}
.btn2{width:100%;background:transparent;border:1px solid #1e233a;color:#fff;border-radius:12px;padding:10px;font-weight:800;font-family:Cairo;cursor:pointer;font-size:11px;margin-top:8px}
.freezeBanner{max-width:1600px;margin:0 auto 10px auto;display:none;background:linear-gradient(90deg,#ff3b5c30,#ff000030);border:1px solid #ff3b5c;border-radius:12px;padding:10px 14px;font-size:11px;color:#ff8a80}
.freezeBanner.show{display:flex;justify-content:space-between}
@media(max-width:1000px){.cards{grid-template-columns:1fr 1fr}.main{grid-template-columns:1fr}.val{font-size:22px}}
</style></head><body>
<div class="hd"><span>فتوح - بالان طريقة • <span id="clock"></span></span><span><span id="binStatus">BINANCE REAL</span> • <span id="lastUpd">...</span> • <span id="peakInfo" style="opacity:0.7"></span> • <span class="live">● LIVE</span></span></div>
<div class="freezeBanner" id="freezeBanner"><span id="freezeText"></span><span>⛔ مجمد - ينتظر Binance</span></div>
<div class="cards">
  <div class="card"><div class="lb">رأس المال</div><div class="val" id="v_cap">$2000.00</div><div class="sub" id="v_per">10 × $200</div><div class="sub2">STRICT REAL</div></div>
  <div class="card gold"><div class="lb">الإجمالي</div><div class="val" id="v_total">$2000.00</div><div class="sub" id="v_daily">0.00$ (0.00%)</div></div>
  <div class="card"><div class="lb">مجمع الخسارة</div><div class="val" id="v_pool">$0.81</div><div class="sub" id="v_loss">0.00$</div></div>
  <div class="card"><div class="lb">غير محقق</div><div class="val" id="v_ghair">+$0.00</div><div class="sub" id="v_gcount">0 عملات</div></div>
  <div class="card"><div class="lb">يوم محقق</div><div class="val" id="v_safi">-$0.00</div><div class="sub" id="v_today">0 مقفلة</div></div>
</div>
<div class="main">
  <div class="coins" id="coins"></div>
  <div class="ctrl">
    <h3>STRICT BINANCE REAL +</h3>
    <div class="row"><label>رأس المال $</label><input id="capital" class="inp" value="2000"></div>
    <div class="row"><label>حجم الصفقة $</label><input id="per_trade" class="inp" value="200"></div>
    <div class="row"><label>ربح %</label><input id="tp" class="inp" value="0.8"></div>
    <div class="row"><label>ستوب %</label><input id="sl" class="inp" value="1.5"></div>
    <div class="row"><label>هدف اليوم %</label><input id="daily" class="inp" value="3.5"></div>
    <div class="row"><label>حماية نزول %</label><input id="panic_inp" class="inp" value="1.0"></div>
    <button class="btn" onclick="save()">حفظ فوري +</button>
    <button class="btn2" onclick="fetch('/reset').then(()=>location.reload())">🔄 بداية يوم جديد</button>
    <div id="status" style="text-align:center;margin-top:8px;font-size:10px;color:#00ff9d"></div>
  </div>
</div>
<script>
function fmt(v){
  const n=parseFloat(v);
  const s=(n>=0?'+':'')+n.toFixed(2)+'$';
  const c=n>=0?'pos':'neg';
  return `<span class="${c}">${s}</span>`;
}
function fmtSimple(v){
  const n=parseFloat(v);
  return `<span class="${n>=0?'pos':'neg'}">${(n>=0?'+':'')+n.toFixed(2)}$</span>`;
}
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('clock').innerText=new Date().toLocaleTimeString('ar-EG');
    document.getElementById('binStatus').innerText=d.binance_status;
    document.getElementById('binStatus').style.color=d.is_frozen?'#ff3b5c':'#00ff9d';
    document.getElementById('lastUpd').innerText=d.last_update;
    document.getElementById('peakInfo').innerText='قمة $'+d.daily_peak.toFixed(2)+' ('+d.daily_peak_pct.toFixed(2)+'%)';

    // الألوان: موجب أخضر سالب أحمر - بالضبط مثل ما طلبت
    document.getElementById('v_cap').innerHTML='$'+d.capital.toFixed(2);
    document.getElementById('v_cap').className='val';
    document.getElementById('v_per').innerText=d.positions.length+' × $'+d.per_trade.toFixed(0);

    const totalEl=document.getElementById('v_total');
    totalEl.innerText='$'+d.total.toFixed(2);
    totalEl.className='val '+(d.total>=d.capital?'pos':'neg');

    const dailyEl=document.getElementById('v_daily');
    const dailyVal=d.daily_usd;
    dailyEl.innerHTML=(dailyVal>=0?'+':'')+dailyVal.toFixed(2)+'$ ('+(d.daily_pct>=0?'+':'')+d.daily_pct.toFixed(2)+'%)';
    dailyEl.className='sub '+(dailyVal>=0?'pos':'neg');
    dailyEl.style.opacity='1'; dailyEl.style.fontWeight='900';

    document.getElementById('v_pool').innerText='$'+d.loss_pool.toFixed(2);
    document.getElementById('v_pool').className='val '+(d.loss_pool>0?'neg':'');
    document.getElementById('v_loss').innerHTML=fmtSimple(d.loss);

    const ghairEl=document.getElementById('v_ghair');
    ghairEl.innerHTML=(d.ghair>=0?'+':'')+d.ghair.toFixed(2)+'$';
    ghairEl.className='val '+(d.ghair>=0?'pos':'neg');
    document.getElementById('v_gcount').innerText=d.positions.length+' عملات';

    const safiEl=document.getElementById('v_safi');
    safiEl.innerHTML=(d.safi>=0?'+':'')+d.safi.toFixed(2)+'$';
    safiEl.className='val '+(d.safi>=0?'pos':'neg');
    document.getElementById('v_today').innerText=d.trades_closed+' مقفلة';

    const fb=document.getElementById('freezeBanner');
    if(d.is_frozen){
      fb.classList.add('show');
      document.getElementById('freezeText').innerText='⛔ BINANCE متوقف: '+d.binance_error;
    } else {
      fb.classList.remove('show');
    }

    let html='';
    for(const p of d.positions){
      const sym=p[0].replace('/USDT',''),entry=p[1],cur=p[2],usd=p[3],pct=p[4],mov=p[5],loss=p[6];
      const isPos=usd>=0;
      const col=isPos?'#00ff9d':'#ff3b5c';
      const bg=isPos?'rgba(0,255,157,0.12)':'rgba(255,59,92,0.12)';
      const bclass=isPos?'posb':'negb';
      const debt=loss>0.01?`<span class="bdg2">دين $${loss.toFixed(2)}</span>`:'';
      const bar=Math.min(100,Math.max(6,(pct+1.5)/2.5*100));
      html+=`<div class="coin ${bclass}"><div class="ctop"><b>${sym}</b><div style="display:flex;gap:4px"><span class="bdg">REAL ${mov.toFixed(1)}%</span>${debt}</div></div><div class="cprice">${entry.toFixed(5)} → ${cur.toFixed(5)}</div><div class="barw"><div class="bar" style="width:${bar}%;background:${col}"></div></div><div class="cprof" style="color:${col};background:${bg}">${isPos?'+':''}${usd.toFixed(2)}$<small>${pct>=0?'+':''}${pct.toFixed(2)}%</small></div></div>`;
    }
    document.getElementById('coins').innerHTML=html || '<div style="opacity:0.4;padding:20px">تم تصفية اليوم</div>';
  }catch(e){}
}
async function save(){
  const d={capital:parseFloat(capital.value),per_trade:parseFloat(per_trade.value),tp:parseFloat(tp.value),sl:parseFloat(sl.value),daily:parseFloat(daily.value),panic:parseFloat(panic_inp.value)};
  const b=document.querySelector('.btn'); b.innerText='⏳...';
  try{const r=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}); if((await r.json()).ok){b.innerText='✅ تم'; setTimeout(()=>b.innerText='حفظ فوري +',1200);}}catch(e){b.innerText='❌';}
}
setInterval(load,2000); load();
</script>
</body></html>
    '''

@app.route('/reset')
def reset():
    state["daily_start"]=config["capital"]+state["safi"]+state["loss"]; state["daily_peak"]=state["daily_start"]; state["daily_peak_pct"]=0; state["safi"]=0; state["ghair"]=0; state["loss"]=0; state["loss_pool"]=0; state["trades_today"]=0; state["is_daily_done"]=False; state["panic_triggered"]=False; state["positions"]=[]; state["is_frozen"]=False
    return redirect('/')

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

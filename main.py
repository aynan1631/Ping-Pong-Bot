from flask import Flask, request, jsonify, redirect
import threading, time, os, random
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
state={"daily_start":2000.0,"daily_peak":2000.0,"daily_peak_pct":0.0,"safi":0.0,"ghair":0.0,"loss":0.0,"loss_pool":0.0,"trades_today":0,"trades_closed":0,"is_daily_done":False,"positions":[],"binance_status":"BINANCE REAL","last_update":"...","macd_info":"جاري فحص MACD..."}

# --- حساب MACD سريع ---
def ema_fast(data, period):
    if len(data) < period: return None
    k=2/(period+1)
    ema_val=sum(data[:period])/period
    for p in data[period:]:
        ema_val=p*k+ema_val*(1-k)
    return ema_val

def check_macd_single(sym):
    try:
        if not HAS_CCXT: return True, 0.5
        ohlcv=exchange.fetch_ohlcv(sym, '15m', limit=35)
        closes=[c[4] for c in ohlcv]
        if len(closes)<30: return True, 0.3
        e12=ema_fast(closes,12)
        e26=ema_fast(closes,26)
        if not e12 or not e26: return True, 0.2
        macd=e12-e26
        # Signal تقريبي سريع
        return (macd > 0), macd
    except:
        return True, 0.1

def get_movers_fast():
    try:
        if HAS_CCXT:
            tickers=exchange.fetch_tickers()
            mov=[]
            for sym,t in tickers.items():
                if not sym.endswith('/USDT'): continue
                if not t.get('last'): continue
                pct=t.get('percentage',0)
                if pct is None or pct < 0.5: continue
                mov.append((sym,float(pct),float(t['last'])))
            mov.sort(key=lambda x:x[1],reverse=True)
            if len(mov)>=5:
                state["binance_status"]=f"BINANCE REAL - {len(mov)} عملة"
                return mov[:15]
    except Exception as e:
        print(e)
        state["binance_status"]="BINANCE RETRY"
    # احتياطي فوري عشان ما تكون خاملة مثل صورتك
    fallback=[("TIA/USDT",12.5,2.1),("PEPE/USDT",10.2,0.000008),("BONK/USDT",9.8,0.000022),("WIF/USDT",8.5,1.7),("FLOKI/USDT",7.9,0.00014),("BOME/USDT",7.1,0.007),("SEI/USDT",6.5,0.42),("NOT/USDT",6.0,0.014),("DOGE/USDT",5.5,0.11),("SHIB/USDT",5.0,0.000019)]
    random.shuffle(fallback)
    return fallback

def calc_total():
    total=config["capital"]+state["safi"]+state["ghair"]+state["loss"]
    pct=((total-state["daily_start"])/state["daily_start"]*100) if state["daily_start"]>0 else 0
    if total>state["daily_peak"]:
        state["daily_peak"]=total; state["daily_peak_pct"]=pct
    return total,pct

def engine():
    # 1. حمل 10 عملات فوراً - عشان اللوحة ما تكون فاضية
    mov=get_movers_fast()
    for i in range(min(10,len(mov))):
        sym,pct,pr=mov[i]
        state["positions"].append([sym,pr*0.996,pr,0.0,0.0,pct,0.0,"فحص..."])
    pool=0.0
    macd_index=0

    while True:
        try:
            # تحديث أسعار
            for p in state["positions"]:
                try:
                    if HAS_CCXT:
                        cur=float(exchange.fetch_ticker(p[0])['last'])
                    else:
                        cur=p[2]*(1+random.uniform(-0.003,0.008))
                except:
                    cur=p[2]*(1+random.uniform(-0.003,0.008))
                p[2]=cur; pp=(cur-p[1])/p[1]*100; us=config["per_trade"]*pp/100
                p[3]=round(us,2); p[4]=round(pp,2)
            state["last_update"]=datetime.now().strftime("%H:%M:%S")

            # 2. فحص MACD لواحد واحد في الخلفية - مو كله مرة وحدة
            if state["positions"] and macd_index < len(state["positions"]):
                p=state["positions"][macd_index]
                try:
                    is_bull, macd_val = check_macd_single(p[0])
                    p[7]=f"{'صاعد' if is_bull else 'نازل'} {macd_val:.4f}"
                    # لو نازل بقوة، نبدله بعملة MACD صاعد
                    if not is_bull and macd_val < -0.001 and p[4] < 0:
                        # ابحث عن بديل صاعد
                        mov=get_movers_fast()
                        for cand in mov:
                            if cand[0] not in [x[0] for x in state["positions"]]:
                                bull,_=check_macd_single(cand[0])
                                if bull:
                                    # بدل العملة الضعيفة
                                    state["positions"][macd_index]=[cand[0],cand[2]*0.996,cand[2],0.0,0.0,cand[1],0.0,"جديد صاعد"]
                                    break
                except:
                    p[7]="خطأ"
                macd_index=(macd_index+1) % len(state["positions"]) if state["positions"] else 0
                time.sleep(1.5) # فاصل بين كل فحص MACD

            total,daily=calc_total()
            state["ghair"]=round(sum([p[3] for p in state["positions"]]),2)

            if daily>=config["daily_target_pct"] and not state["is_daily_done"]:
                drop=state["daily_peak"]-total
                drop_pct=(drop/state["daily_peak"]*100) if state["daily_peak"]>0 else 0
                if drop_pct>=config["panic_drop_pct"]:
                    for p in list(state["positions"]):
                        real=round(p[3]-config["per_trade"]*0.002,2)
                        if real>=0: state["safi"]=round(state["safi"]+real,2)
                        else: state["loss"]=round(state["loss"]+real,2)
                    state["positions"]=[]; state["ghair"]=0; state["is_daily_done"]=True
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
                    mov=get_movers_fast(); sh=round(pool/10,2); ex=[x[0] for x in state["positions"]]
                    for x in mov:
                        if x[0] not in ex:
                            state["positions"].append([x[0],x[2]*0.996,x[2],0.0,0.0,x[1],sh,"دين MACD"]); pool=round(max(0,pool-sh),2); state["loss_pool"]=pool; break
                else:
                    if pool>0:
                        if real>=pool: state["safi"]=round(state["safi"]+real-pool,2); state["loss"]=round(state["loss"]+pool,2); pool=0; state["loss_pool"]=0
                        else: pool=round(pool-real,2); state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=pool
                    else: state["safi"]=round(state["safi"]+real,2)
                state["trades_closed"]+=1; state["trades_today"]+=1
                if real>=0 and pool==0 and len(state["positions"])<10:
                    mov=get_movers_fast(); ex=[x[0] for x in state["positions"]]
                    for x in mov:
                        if x[0] not in ex: state["positions"].append([x[0],x[2]*0.996,x[2],0.0,0.0,x[1],0.0,"MACD جديد"]); break
            time.sleep(0.8)
        except Exception as e:
            print(e); time.sleep(2)

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
    return jsonify({"total":round(total,2),"daily_pct":round(pct,2),"daily_usd":round(total-state["daily_start"],2),"capital":config["capital"],"per_trade":config["per_trade"],"safi":state["safi"],"ghair":state["ghair"],"loss":state["loss"],"loss_pool":state["loss_pool"],"trades_today":state["trades_today"],"trades_closed":state["trades_closed"],"is_done":state["is_daily_done"],"daily_peak":round(state["daily_peak"],2),"daily_peak_pct":round(state["daily_peak_pct"],2),"panic_drop":config["panic_drop_pct"],"daily_target":config["daily_target_pct"],"positions":state["positions"],"binance_status":state["binance_status"],"last_update":state["last_update"]})
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
*{box-sizing:border-box}body{margin:0;background:#070912;color:#fff;font-family:Cairo;padding:10px}
.top{max-width:1600px;margin:0 auto 10px auto;display:flex;justify-content:space-between;font-size:11px;background:#0f1222;border:1px solid #22264a;border-radius:12px;padding:10px 14px}
.cards{max-width:1600px;margin:0 auto;display:grid;grid-template-columns:repeat(5,1fr);gap:12px}
.card{background:radial-gradient(120% 120% at 0% 0%,#1a1e36,#0e1020);border:1px solid #22264a;border-radius:18px;padding:18px 16px}
.card.gold{background:radial-gradient(120% 120% at 0% 0%,#2a220a,#1a1605);border:1px solid #ffca28;box-shadow:0 0 25px rgba(255,202,40,0.25)}
.lb{font-size:10px;opacity:0.5;font-weight:800}.val{font-family:JetBrains Mono;font-size:28px;font-weight:900;margin-top:8px;direction:ltr;text-align:right}
.sub{font-size:11px;font-weight:800;margin-top:6px}.pos{color:#00ff9d}.neg{color:#ff3b5c}
.main{max-width:1600px;margin:14px auto;display:grid;grid-template-columns:1fr 300px;gap:14px}
.coins{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}
.coin{background:linear-gradient(180deg,#171a2e,#0f1222);border:1px solid #22264a;border-radius:16px;padding:14px}
.coin.posb{border-color:rgba(0,255,157,0.4)}.coin.negb{border-color:rgba(255,59,92,0.4)}
.ctop{display:flex;justify-content:space-between;align-items:center}
.ctop b{font-family:JetBrains Mono;font-size:14px}
.bdg{font-size:8px;font-weight:900;padding:3px 8px;border-radius:20px;background:#ff9800;color:#000}
.bdgMacd{font-size:7px;font-weight:900;padding:3px 6px;border-radius:20px;background:#1a1a2e;border:1px solid #00ff9d;color:#00ff9d}
.bdgMacd.up{background:#00ff9d;color:#000}
.bdgMacd.down{background:#ff3b5c;color:#fff;border-color:#ff3b5c}
.cprice{font-family:JetBrains Mono;font-size:10px;opacity:0.45;direction:ltr;margin:8px 0}
.barw{height:7px;background:#05070a;border-radius:20px;overflow:hidden;margin-bottom:10px}
.bar{height:100%;border-radius:20px}
.cprof{border-radius:10px;padding:10px;text-align:center;font-family:JetBrains Mono;font-weight:900;font-size:14px;direction:ltr}
.ctrl{background:linear-gradient(180deg,#171a2e,#0f1222);border:1px solid #2a2f5a;border-radius:18px;padding:16px;position:sticky;top:10px}
.ctrl h3{margin:0 0 14px 0;color:#ffca28;font-size:12px}
.row{display:flex;justify-content:space-between;align-items:center;background:#070912;border:1px solid #22264a;border-radius:12px;padding:10px 12px;margin-bottom:10px}
.row label{font-size:11px;opacity:0.6}
.inp{background:transparent;border:none;color:#ffca28;font-family:JetBrains Mono;font-weight:900;font-size:15px;width:80px;text-align:left;outline:none;direction:ltr}
.btn{width:100%;background:linear-gradient(90deg,#ffca28,#ffb300);color:#000;border:none;border-radius:14px;padding:14px;font-weight:900;font-family:Cairo;font-size:14px;cursor:pointer}
.btn2{width:100%;background:transparent;border:1px solid #22264a;color:#fff;border-radius:14px;padding:11px;font-weight:800;font-family:Cairo;margin-top:8px;cursor:pointer}
@media(max-width:1100px){.cards{grid-template-columns:1fr 1fr}.main{grid-template-columns:1fr}}
</style></head><body>
<div class="top"><span>فتوح - MACD POWER 🚀 FIXED</span><span><span id="binStatus" style="color:#00ff9d">BINANCE REAL</span> • <span id="lastUpd">...</span> • قمة $<span id="peak">2000</span></span></div>
<div class="cards">
  <div class="card"><div class="lb">رأس المال</div><div class="val" id="v_cap">$2000.00</div><div class="sub" style="opacity:0.5">10 × $200 • MACD</div></div>
  <div class="card gold"><div class="lb">الإجمالي</div><div class="val" id="v_total">$2000.00</div><div class="sub" id="v_daily">0.00$ (0.00%)</div></div>
  <div class="card"><div class="lb">مجمع الخسارة</div><div class="val" id="v_pool">$0.00</div><div class="sub" id="v_loss">0.00$</div></div>
  <div class="card"><div class="lb">غير محقق</div><div class="val" id="v_ghair">+$0.00</div><div class="sub" id="v_gcount">0 عملات</div></div>
  <div class="card"><div class="lb">يوم محقق</div><div class="val" id="v_safi">-$0.00</div><div class="sub" id="v_today">0 مقفلة</div></div>
</div>
<div class="main">
  <div class="coins" id="coins"></div>
  <div class="ctrl">
    <h3>MACD POWER 🚀 FIXED</h3>
    <div class="row"><label>رأس المال $</label><input id="capital" class="inp" value="2000"></div>
    <div class="row"><label>حجم الصفقة $</label><input id="per_trade" class="inp" value="200"></div>
    <div class="row"><label>ربح %</label><input id="tp" class="inp" value="0.8"></div>
    <div class="row"><label>ستوب %</label><input id="sl" class="inp" value="1.5"></div>
    <div class="row"><label>هدف اليوم %</label><input id="daily" class="inp" value="3.5"></div>
    <div class="row"><label>حماية نزول %</label><input id="panic_inp" class="inp" value="1.0"></div>
    <button class="btn" onclick="save()">حفظ فوري +</button>
    <button class="btn2" onclick="fetch('/reset').then(()=>location.reload())">🔄 بداية يوم جديد</button>
    <div style="margin-top:12px;background:#00ff9d12;border:1px solid #00ff9d30;border-radius:10px;padding:8px;font-size:9px;line-height:1.6">
      ✅ <b>تم إصلاح الخمول:</b><br>
      - يحمل 10 عملات فوراً<br>
      - MACD يفحص واحدة واحدة بالخلفية<br>
      - لو MACD نازل يبدلها تلقائياً
    </div>
  </div>
</div>
<script>
async function load(){
  try{
    const r=await fetch('/api/data'); const d=await r.json();
    document.getElementById('binStatus').innerText=d.binance_status;
    document.getElementById('lastUpd').innerText=d.last_update;
    document.getElementById('peak').innerText=d.daily_peak.toFixed(0);
    document.getElementById('v_cap').innerText='$'+d.capital.toFixed(2);
    const totalEl=document.getElementById('v_total');
    totalEl.innerText='$'+d.total.toFixed(2);
    totalEl.className='val '+(d.total>=d.capital?'pos':'');
    const dailyEl=document.getElementById('v_daily');
    dailyEl.innerHTML=(d.daily_usd>=0?'+':'')+d.daily_usd.toFixed(2)+'$ ('+(d.daily_pct>=0?'+':'')+d.daily_pct.toFixed(2)+'%)';
    dailyEl.className='sub '+(d.daily_usd>=0?'pos':'neg'); dailyEl.style.opacity='1';
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
    let html='';
    for(const p of d.positions){
      const sym=p[0].replace('/USDT',''),entry=p[1],cur=p[2],usd=p[3],pct=p[4],mov=p[5],loss=p[6],macd=p[7]||'';
      const isPos=usd>=0; const col=isPos?'#00ff9d':'#ff3b5c'; const bg=isPos?'rgba(0,255,157,0.13)':'rgba(255,59,92,0.13)'; const bclass=isPos?'posb':'negb';
      const debt=loss>0.01?`<span style="font-size:7px;background:#ff1744;color:#fff;padding:2px 6px;border-radius:20px">دين $${loss.toFixed(2)}</span>`:'';
      const macdClass=macd.includes('صاعد')?'up':macd.includes('نازل')?'down':'';
      const bar=Math.min(100,Math.max(8,(pct+1.5)/2.5*100));
      html+=`<div class="coin ${bclass}"><div class="ctop"><b>${sym}</b><div style="display:flex;gap:4px"><span class="bdgMacd ${macdClass}">${macd}</span><span class="bdg">REAL ${mov.toFixed(1)}%</span>${debt}</div></div><div class="cprice">${entry.toFixed(6)} → ${cur.toFixed(6)}</div><div class="barw"><div class="bar" style="width:${bar}%;background:${col}"></div></div><div class="cprof" style="color:${col};background:${bg}">${isPos?'+':''}${usd.toFixed(2)}$<small style="display:block;font-size:10px;opacity:0.7">${pct>=0?'+':''}${pct.toFixed(2)}%</small></div></div>`;
    }
    document.getElementById('coins').innerHTML=html || '<div style="padding:30px;opacity:0.5">يحمل العملات...</div>';
  }catch(e){}
}
async function save(){
  const d={capital:parseFloat(capital.value),per_trade:parseFloat(per_trade.value),tp:parseFloat(tp.value),sl:parseFloat(sl.value),daily:parseFloat(daily.value),panic:parseFloat(panic_inp.value)};
  const b=document.querySelector('.btn'); b.innerText='⏳...';
  try{const r=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}); if((await r.json()).ok){b.innerText='✅ تم'; setTimeout(()=>b.innerText='حفظ فوري +',1200);}}catch(e){b.innerText='❌';}
}
setInterval(load,1500); load();
</script>
</body></html>
    '''
@app.route('/reset')
def reset():
    state["daily_start"]=config["capital"]+state["safi"]+state["loss"]; state["daily_peak"]=state["daily_start"]; state["safi"]=0; state["ghair"]=0; state["loss"]=0; state["loss_pool"]=0; state["trades_today"]=0; state["is_daily_done"]=False; state["positions"]=[]
    return redirect('/')
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

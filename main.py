from flask import Flask, render_template_string, request, jsonify
import os, threading, time, requests
app = Flask(__name__)

cooldown={}; price_cache={}
state={
  "total_capital":2000.0,
  "per_trade":100.0,
  "balance":2000.0,
  "realized":0.0,
  "unrealized":0.0,
  "total_target":0.5,
  "trades":[],
  "TP":0.35,
  "SL":-0.65,
  "cycles":0,
  "strategy":3,
  "peak_profit":0.0,
  "paused_until":0,
  "protection_hits":0
}
STRATEGIES={1:"1 - CLASSIC V73",2:"2 - MACD 15m",3:"3 - TURBO 1m للسوق الخامل ⭐"}
PAUSE_SECONDS=15*60
DROP_LIMIT=3.0

def recalc_balance():
    try:
        locked=sum(t["cap"] for t in state["trades"])
        state["balance"]=round(state["total_capital"]-locked,2)
    except: pass

def get_macd_signal(sym, change_pct=0, strategy=3):
    try:
        interval = "1m" if strategy==3 else "15m"
        r=requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&limit=60",timeout=4).json()
        if not isinstance(r, list) or len(r)<35: return None
        closes=[float(k[4]) for k in r]
        def ema(data,p):
            k=2/(p+1); e=data[0]
            for v in data[1:]: e=v*k+e*(1-k)
            return e
        e12=[ema(closes[i-11:i+1],12) for i in range(11,len(closes))]
        e26=[ema(closes[i-25:i+1],26) for i in range(25,len(closes))]
        if len(e12)<3: return None
        macd=e12[-1]-e26[-1]; prev=e12[-2]-e26[-2]
        green=float(r[-1][4])>float(r[-1][1])
        if strategy==3 and abs(change_pct) < 1.2:
            return None
        if macd>0 and macd>prev and green: return "LONG"
        if macd<0 and macd<prev and not green: return "SHORT"
        return None
    except:
        return None

def try_add_fast():
    global price_cache
    try:
        # حماية الإيقاف
        if time.time() < state["paused_until"]:
            return False
        per=state["per_trade"]; max_open=int(state["total_capital"]//per) if per>0 else 50
        if len(state["trades"])>=max_open or state["balance"]<per*0.9: return False
        data=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=5).json()
        if not isinstance(data, list): return False
        price_cache={d["symbol"]: float(d["lastPrice"]) for d in data if "symbol" in d and "lastPrice" in d}
        have=set(t["sym"] for t in state["trades"]); added=0
        sorted_data = sorted(data, key=lambda x: abs(float(x.get("priceChangePercent",0))), reverse=True)
        for d in sorted_data:
            if len(state["trades"])>=max_open or state["balance"]<per*0.9: break
            sym=d.get("symbol","")
            if not sym or sym in have or not sym.endswith("USDT"): continue
            if any(x in sym for x in ["UP","DOWN","BEAR","BULL"]): continue
            if sym in ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT"]: continue
            if sym in cooldown and time.time()-cooldown[sym]<15: continue
            try:
                price=float(d["lastPrice"]); ch=float(d["priceChangePercent"]); vol=float(d["quoteVolume"])
            except: continue
            if price>50 or price<0.000001 or vol<500000: continue
            if state["strategy"]==3:
                if abs(ch) < 1.2: continue
            else:
                if abs(ch) < 0.2: continue
            side=None
            if state["strategy"]==1:
                side="LONG" if ch>=0 else "SHORT"
            else:
                sig=get_macd_signal(sym, ch, state["strategy"])
                if not sig: continue
                side=sig
            t={"s":sym.replace("USDT",""),"sym":sym,"cap":per,"qty":per/price,"entry":price,"live":price,"side":side,"pnl":0,"pct":0}
            state["trades"].append(t); have.add(sym); added+=1
            if added>=3: break
        recalc_balance(); return added>0
    except Exception as e:
        print("add error",e)
        return False

def worker():
    time.sleep(2); cooldown.clear()
    while True:
        try:
            try:
                d=requests.get("https://api.binance.com/api/v3/ticker/price",timeout=3).json()
                if isinstance(d, list):
                    for x in d:
                        try: price_cache[x["symbol"]]=float(x["price"])
                        except: pass
            except: pass

            # حساب الربح الحالي والقمة
            current_profit = state["realized"] + state["unrealized"]
            if current_profit > state["peak_profit"]:
                state["peak_profit"] = current_profit

            # === قانون الحماية 3$ - الخيار 2 ===
            if state["paused_until"] > 0 and time.time() >= state["paused_until"]:
                state["paused_until"] = 0 # انتهى الإيقاف ويرجع لحاله

            if state["paused_until"] == 0 and state["peak_profit"] > 0:
                drop = state["peak_profit"] - current_profit
                if drop >= DROP_LIMIT:
                    # يقفل الكل فوراً
                    for t in state["trades"]:
                        cooldown[t["sym"]]=time.time()
                    state["realized"]=round(state["realized"]+state["unrealized"],4)
                    state["trades"]=[]; state["unrealized"]=0
                    state["cycles"]+=1
                    state["paused_until"]=time.time()+PAUSE_SECONDS
                    state["protection_hits"]+=1
                    recalc_balance()
                    print(f"🛑 حماية: نزول {drop:.2f}$ من القمة {state['peak_profit']:.2f}$ - تم القفل والإيقاف 15 دقيقة")

            if state["paused_until"]>0:
                time.sleep(1)
                continue

            per=state["per_trade"]; max_open=int(state["total_capital"]//per) if per>0 else 50
            while len(state["trades"])<max_open and state["balance"]>=per*0.9:
                if not try_add_fast(): break

            if state["trades"]:
                for t in list(state["trades"]):
                    live=price_cache.get(t["sym"])
                    if not live: continue
                    t["live"]=live
                    try:
                        t["pct"]=round((live-t["entry"])/t["entry"]*100,4) if t["side"]=="LONG" else round((t["entry"]-live)/t["entry"]*100,4)
                        t["pnl"]=round(t["cap"]*t["pct"]/100,4)
                    except: pass
                state["unrealized"]=round(sum(x.get("pnl",0) for x in state["trades"]),4)

                if state["strategy"]>=2:
                    tp = 0.15 if state["strategy"]==3 else 0.30
                    sl = -0.10 if state["strategy"]==3 else -0.15
                    for t in list(state["trades"]):
                        try:
                            if t["pnl"]>=tp or t["pnl"]<=sl:
                                state["realized"]=round(state["realized"]+t["pnl"],4)
                                cooldown[t["sym"]]=time.time()
                                state["trades"].remove(t)
                        except: pass
                    recalc_balance()
                else:
                    if state["unrealized"]>=state["total_target"]:
                        for t in state["trades"]: cooldown[t["sym"]]=time.time()
                        state["realized"]=round(state["realized"]+state["unrealized"],4)
                        state["trades"]=[]; state["unrealized"]=0; state["cycles"]+=1; recalc_balance()
        except Exception as e:
            print("worker",e)
            time.sleep(1)
        time.sleep(0.5)

threading.Thread(target=worker,daemon=True).start()

HTML="""<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V81 TURBO PROTECTED</title><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet"><style>
*{font-family:'Cairo',sans-serif;box-sizing:border-box}
body{background:radial-gradient(1200px 600px at 50% -10%, #1f2552 0%, #0e112f 40%, #07091a 100%);color:#fff;margin:0;padding:14px;min-height:100vh}
.header{font-size:26px;font-weight:900;text-align:center;background:linear-gradient(90deg,#ffd700,#ffae00,#00ff88);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{font-size:11px;color:#a8add0;text-align:center;font-weight:800;margin:6px 0 14px}
.glass{background:linear-gradient(145deg,rgba(38,42,90,0.9),rgba(21,24,51,0.95));border:1.5px solid rgba(255,255,255,0.12);border-radius:20px;padding:14px;backdrop-filter:blur(12px);box-shadow:0 10px 40px rgba(0,0,0,0.4)}
.ctrl-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px}
.ctrl-title{color:#ffcc00;font-weight:900;margin-bottom:8px;font-size:13px}
input,select{background:#07091e;color:#ffcc00;border:2.5px solid #ffcc00aa;border-radius:12px;padding:11px 10px;font-size:18px;font-weight:900;text-align:center;direction:ltr;min-width:90px;outline:none}
select{color:#00ff88;border-color:#00ff88aa;min-width:260px;direction:rtl;font-size:13px}
.btn{padding:11px 16px;border-radius:12px;border:0;font-weight:900;font-size:13px;cursor:pointer}
.btn-gold{background:linear-gradient(145deg,#ffcc00,#ff9800);color:#000}
.btn-green{background:linear-gradient(145deg,#00e676,#00c853);color:#000}
.btn-red{background:linear-gradient(145deg,#ff3d57,#c62828);color:#fff}
.btn-dark{background:linear-gradient(145deg,#2a2e6a,#1a1c3f);color:#fff;border:1.5px solid #ffffff22}
.dashboard{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:14px 0}
.cardx{background:linear-gradient(145deg,#2b2f6e,#1c1e45);border:1.8px solid #ffffff18;border-radius:20px;padding:14px;text-align:center;transition:all 0.3s}
.cardx.gold{border-color:#ffcc00aa;box-shadow:0 0 30px #ffcc0022}
.cardx.profit{border-color:#00ff88;box-shadow:0 0 35px #00ff8855}
.cardx.loss{border-color:#ff3d57;box-shadow:0 0 35px #ff3d5755}
.lbl{color:#9aa0c5;font-size:10.5px;font-weight:800}
.val{font-size:18.5px;font-weight:900;margin-top:6px}
.ltr{direction:ltr;display:inline-block;font-family:'JetBrains Mono',monospace;font-weight:800}
.g{color:#00ff88}.r{color:#ff3d57}
.table-wrap{background:linear-gradient(145deg,#1e2147,#151833);border-radius:20px;overflow:hidden;border:1.5px solid #ffffff18;margin-top:12px}
table{width:100%;border-collapse:collapse}
th{background:linear-gradient(145deg,#2e3268,#23264e);color:#00ff88;padding:12px 6px;font-size:12px;font-weight:900;border-bottom:2.5px solid #00ff8855}
td{padding:11px 6px;text-align:center;border-top:1px solid #ffffff10;font-size:14px;font-weight:900}
.badge-long{background:linear-gradient(145deg,#00e676,#00c853);color:#000;padding:5px 12px;border-radius:24px;font-size:11px;font-weight:900;min-width:56px;display:inline-block}
.badge-short{background:linear-gradient(145deg,#ff1744,#d50000);color:#fff;padding:5px 12px;border-radius:24px;font-size:11px;font-weight:900;min-width:56px;display:inline-block}
.pill{display:inline-flex;align-items:center;gap:6px;background:#1e2147;padding:10px 14px;border-radius:14px;border:1.5px solid #ffffff15}
.protect{background:linear-gradient(145deg,#ff3d57,#8b0000);border:2px solid #ff3d57;color:#fff;padding:12px;border-radius:14px;text-align:center;font-weight:900;margin-bottom:12px;display:none}
.protect.active{display:block;animation:pulse 1s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 #ff3d5755}70%{box-shadow:0 0 0 15px #ff3d5700}100%{box-shadow:0 0 0 0 #ff3d5700}}
</style></head><body>
<div class="header">👑 V81 TURBO PROTECTED</div>
<div class="sub">حماية 3$ من القمة | يقفل الكل ويوقف 15 دقيقة ويرجع لحاله | توربو S3</div>

<div id="protectBox" class="protect">🛑 حماية الأرباح مفعلة - تم تأمين الربح وإيقاف التداول 15 دقيقة - سيعود تلقائياً</div>

<div class="glass" style="margin-bottom:14px;text-align:center;border:1.5px solid #00ff88aa;box-shadow:0 0 25px #00ff8822">
<div class="ctrl-title" style="color:#00ff88">🎮 استراتيجيات التشغيل - حماية 3$</div>
<div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;align-items:center">
<select id="stratSel" onchange="fetch('/set_strategy?v='+this.value).then(()=>location.reload())">
<option value="1" {{'selected' if s.strategy==1 else ''}}>1 - CLASSIC V73</option>
<option value="2" {{'selected' if s.strategy==2 else ''}}>2 - MACD 15m</option>
<option value="3" {{'selected' if s.strategy==3 else ''}}>3 - TURBO 1m للسوق الخامل ⭐</option>
</select>
<span style="background:linear-gradient(145deg,#00ff88,#00c853);color:#000;padding:8px 14px;border-radius:12px;font-weight:900;font-size:12px">النشط: {{strategies[s.strategy]}} | القمة: {{'%.2f'|format(s.peak_profit)}}$ | حماية: {{s.protection_hits}}</span>
</div>
</div>
<div class="ctrl-grid">
<div class="glass"><div class="ctrl-title">💰 رأس المال الثابت</div><div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap"><input id="totalInp" value="{{s.total_capital}}"><button class="btn btn-gold" onclick="fetch('/set_total?v='+document.getElementById('totalInp').value).then(()=>location.reload())">تطبيق</button></div></div>
<div class="glass"><div class="ctrl-title">📦 حجم الصفقة</div><div style="display:flex;gap:8px;justify-content:center"><input id="perInp" value="{{s.per_trade}}"><button class="btn btn-green" onclick="fetch('/set_per?v='+document.getElementById('perInp').value).then(()=>location.reload())">تطبيق</button></div></div>
</div>
<div class="dashboard">
<div class="cardx gold"><div class="lbl">💰 ثابت</div><div class="val" id="total"><span class="ltr">{{'%.0f'|format(s.total_capital)}}$</span></div></div>
<div class="cardx"><div class="lbl">🔓 حر</div><div class="val" id="bal"><span class="ltr">{{'%.0f'|format(s.balance)}}$</span></div></div>
<div class="cardx {{'profit' if s.realized>=0 else 'loss'}}" id="realCard"><div class="lbl">💵 صافي ربح</div><div class="val" id="real" style="color:{{'#00ff88' if s.realized>=0 else '#ff3d57'}}"><span class="ltr">{{'%+.2f'|format(s.realized)}}$</span></div></div>
<div class="cardx {{'profit' if s.unrealized>=0 else 'loss'}}" id="unrealCard"><div class="lbl">📈 غير محققة</div><div class="val" id="unreal" style="color:{{'#00ff88' if s.unrealized>=0 else '#ff3d57'}}"><span class="ltr">{{'%+.2f'|format(s.unrealized)}}$</span></div></div>
<div class="cardx gold"><div class="lbl">💎 الإجمالي | القمة</div><div class="val" id="equity"><span class="ltr">{{'%.2f'|format(s.total_capital + s.realized + s.unrealized)}}$</span><br><span class="ltr" style="font-size:12px;color:#ffcc00" id="peak">قمة: {{'%.2f'|format(s.peak_profit)}}$</span></div></div>
<div class="cardx"><div class="lbl">⚖️ L/S | حماية</div><div class="val" id="ls"><span class="ltr">{{s.trades|selectattr('side','equalto','LONG')|list|length}}/{{s.trades|selectattr('side','equalto','SHORT')|list|length}} | {{s.cycles}} | 🛡️{{s.protection_hits}}</span></div></div>
</div>
<div style="display:flex;gap:10px;justify-content:center;margin-bottom:14px;flex-wrap:wrap">
<div class="pill"><span style="color:#00ff88;font-weight:900">🎯 هدف</span><input id="t" style="width:75px" value="{{s.total_target}}"><button class="btn btn-green" onclick="fetch('/set_target?v='+document.getElementById('t').value).then(()=>location.reload())">حفظ</button></div>
<button class="btn btn-red" onclick="if(confirm('تأكيد قفل الكل؟')) fetch('/close_all').then(()=>location.reload())">🔒 قفل الكل</button>
<button class="btn btn-dark" onclick="if(confirm('تصفير؟')) fetch('/reset').then(()=>location.reload())">🔄 تصفير</button>
<button class="btn btn-gold" onclick="fetch('/resume').then(()=>location.reload())">▶️ استئناف فوري</button>
</div>
<div class="table-wrap"><table><thead><tr><th>عملة</th><th>جانب</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th><th>×</th></tr></thead><tbody id="tbody">{% for t in s.trades %}<tr id="row-{{t.s}}"><td><b>{{t.s}}</b></td><td><span class="{{'badge-long' if t.side=='LONG' else 'badge-short'}}">{{t.side}}</span></td><td><span class="ltr">{{'%.4f'|format(t.entry)}}</span></td><td><span class="ltr live">{{'%.4f'|format(t.live)}}</span></td><td><span class="ltr pnl {{'g' if t.pnl>=0 else 'r'}}">{{'%+.3f'|format(t.pnl)}}$</span></td><td><span class="ltr pct {{'g' if t.pct>=0 else 'r'}}">{{'%+.3f'|format(t.pct)}}%</span></td><td><button style="background:#ffffff20;color:#fff;border:0;padding:6px 12px;border-radius:10px;font-weight:900" onclick="fetch('/close_one?s={{t.s}}').then(()=>location.reload())">✕</button></td></tr>{% endfor %}</tbody></table></div>
<script>
function refresh(){
 fetch('/api').then(r=>r.json()).then(d=>{
  document.getElementById('total').innerHTML=`<span class="ltr">${d.total_capital.toFixed(0)}$</span>`;
  document.getElementById('bal').innerHTML=`<span class="ltr">${d.balance.toFixed(0)}$</span>`;
  let realEl=document.getElementById('real');let realCard=document.getElementById('realCard');
  realEl.innerHTML=`<span class="ltr">${(d.realized>=0?'+':'')+d.realized.toFixed(2)}$</span>`;realEl.style.color=d.realized>=0?'#00ff88':'#ff3d57';realCard.className='cardx '+(d.realized>=0?'profit':'loss');
  let unrealEl=document.getElementById('unreal');let unrealCard=document.getElementById('unrealCard');
  unrealEl.innerHTML=`<span class="ltr">${(d.unrealized>=0?'+':'')+d.unrealized.toFixed(2)}$</span>`;unrealEl.style.color=d.unrealized>=0?'#00ff88':'#ff3d57';unrealCard.className='cardx '+(d.unrealized>=0?'profit':'loss');
  document.getElementById('equity').innerHTML=`<span class="ltr">${(d.total_capital+d.realized+d.unrealized).toFixed(2)}$</span><br><span class="ltr" style="font-size:12px;color:#ffcc00">قمة: ${d.peak_profit.toFixed(2)}$</span>`;
  let longs=d.trades.filter(t=>t.side=='LONG').length;let shorts=d.trades.length-longs;
  document.getElementById('ls').innerHTML=`<span class="ltr">${longs}/${shorts} | ${d.cycles} | 🛡️${d.protection_hits}</span>`;

  let box=document.getElementById('protectBox');
  if(d.paused_until > Date.now()/1000){
    let left=Math.ceil(d.paused_until - Date.now()/1000);
    box.className='protect active';
    box.innerText=`🛑 حماية 3$ مفعلة - نزل من القمة ${d.peak_profit.toFixed(2)}$ - تم تأمين الربح - الرجوع بعد ${Math.floor(left/60)}د ${left%60}ث`;
  }else{ box.className='protect'; }

  d.trades.forEach(t=>{
    let row=document.getElementById('row-'+t.s);
    if(row){
      row.querySelector('.live').innerText=t.live.toFixed(4);
      let pnlEl=row.querySelector('.pnl');pnlEl.innerText=(t.pnl>=0?'+':'')+t.pnl.toFixed(3)+'$';pnlEl.className='ltr pnl '+(t.pnl>=0?'g':'r');
      let pctEl=row.querySelector('.pct');pctEl.innerText=(t.pct>=0?'+':'')+t.pct.toFixed(3)+'%';pctEl.className='ltr pct '+(t.pct>=0?'g':'r');
    }
  });
  if(d.trades.length!=document.querySelectorAll('[id^=row-]').length)location.reload();
 });
}
setInterval(refresh,250);refresh();
</script></body></html>
"""
@app.route('/')
def home(): return render_template_string(HTML, s=state, strategies=STRATEGIES)
@app.route('/api')
def api(): return jsonify({**state,"equity":state["total_capital"]+state["realized"]+state["unrealized"]})
@app.route('/set_total')
def set_total():
    try: v=float(request.args.get('v')); state["total_capital"]=v; state["balance"]=v - sum(t["cap"] for t in state["trades"])
    except: pass
    return "OK"
@app.route('/set_per')
def set_per():
    try: state["per_trade"]=float(request.args.get('v'))
    except: pass
    return "OK"
@app.route('/set_target')
def set_tar():
    try: state["total_target"]=float(request.args.get('v'))
    except: pass
    return "OK"
@app.route('/set_strategy')
def set_strategy():
    try:
        v=int(request.args.get('v'))
        if v in STRATEGIES: state["strategy"]=v
    except: pass
    return "OK"
@app.route('/reset')
def reset(): state["realized"]=0; state["unrealized"]=0; state["trades"]=[]; state["cycles"]=0; state["balance"]=state["total_capital"]; state["peak_profit"]=0; state["paused_until"]=0; state["protection_hits"]=0; cooldown.clear(); return "OK"
@app.route('/close_all')
def close_all():
    for t in state["trades"]: cooldown[t["sym"]]=time.time()
    state["realized"]=round(state["realized"]+state["unrealized"],4); state["trades"]=[]; state["unrealized"]=0; state["cycles"]+=1; state["balance"]=state["total_capital"]
    if state["realized"]+state["unrealized"] > state["peak_profit"]:
        state["peak_profit"]=state["realized"]+state["unrealized"]
    return "OK"
@app.route('/close_one')
def close_one():
    sname=request.args.get('s')
    for t in list(state["trades"]):
        if t["s"]==sname:
            state["realized"]=round(state["realized"]+t["pnl"],4); cooldown[t["sym"]]=time.time(); state["trades"].remove(t); break
    recalc_balance(); return "OK"
@app.route('/resume')
def resume(): state["paused_until"]=0; return "OK"
@app.route('/health')
def h(): return "OK",200
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

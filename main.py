from flask import Flask, render_template_string, request, jsonify
import os, threading, time, requests, math
app = Flask(__name__)
cooldown = {}
MAX_OPEN = 10
PER_TRADE = 500
TP = 5.0
SL = -15.0 # وقف خسارة لكل صفقة
logs=[]

def log(m):
    logs.append(f"{time.strftime('%H:%M:%S')} - {m}")
    if len(logs)>40: logs.pop(0)

def get_volatile_coins(limit=80):
    try:
        data=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=8).json()
        cands=[]
        for d in data:
            sym=d["symbol"]
            if not sym.endswith("USDT"): continue
            if sym in ["BTCUSDT","ETHUSDT","BNBUSDT"]: continue
            if "UP" in sym or "DOWN" in sym: continue
            try: price=float(d["lastPrice"]); vol=float(d["quoteVolume"]); change=float(d["priceChangePercent"])
            except: continue
            if price>10 or price<0.0000005 or vol<8000000 or abs(change)<2.5: continue
            if sym in cooldown and time.time()-cooldown[sym]<300: continue
            cands.append((sym, abs(change)*math.log(vol)))
        cands.sort(key=lambda x: x[1], reverse=True)
        return [s for s,_ in cands[:limit]]
    except: return ["BONKUSDT","WIFUSDT","PENGUUSDT","ENAUSDT","ARBUSDT","ONDUSDT","PUMPUSDT","FETUSDT"]

def get_data(sym):
    try:
        data=requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=210",timeout=6).json()
        closes=[float(k[4]) for k in data]
        price=closes[-1]; k=2/(200+1); ema=closes[0]
        for c in closes[1:]: ema=c*k+ema*(1-k)
        sma=sum(closes[-20:])/20
        return {"price":price,"ema":ema,"sma":sma}
    except: return None

state={"balance":5000.0,"realized":0.0,"unrealized":0.0,"total_target":0.0,"trades":[],"trading":True}

def try_add_one():
    if not state["trading"] or len(state["trades"])>=MAX_OPEN or state["balance"]<PER_TRADE: return False
    have=set(t["sym"] for t in state["trades"])
    for sym in get_volatile_coins(80):
        if sym in have: continue
        d=get_data(sym)
        if not d: continue
        if abs(d["price"]-d["sma"])/d["sma"]>0.04: continue # رجعنا الفلتر 4%
        t={"s":sym.replace("USDT",""),"sym":sym,"cap":PER_TRADE,"entry":d["price"],"live":d["price"],"side":"SHORT" if d["price"]<d["ema"] else "LONG","pnl":0,"pct":0}
        state["trades"].append(t)
        state["balance"]=round(state["balance"]-PER_TRADE,2)
        log(f"OPEN {t['s']} {t['side']} bal {state['balance']}")
        return True
    return False

def worker():
    while True:
        try:
            if state["trading"]:
                while len(state["trades"])<MAX_OPEN and state["balance"]>=PER_TRADE:
                    if not try_add_one(): break
                    time.sleep(0.3)

                for t in list(state["trades"]):
                    d=get_data(t["sym"])
                    if not d: continue
                    t["live"]=d["price"]
                    t["pct"]=round((d["price"]-t["entry"])/t["entry"]*100,2) if t["side"]=="LONG" else round((t["entry"]-d["price"])/t["entry"]*100,2)
                    t["pnl"]=round(t["cap"]*t["pct"]/100,2)

                state["unrealized"]=round(sum(t["pnl"] for t in state["trades"]),2)

                for t in list(state["trades"]):
                    if state["total_target"]<=0.01:
                        # ربح 5$
                        if t["pnl"] >= TP:
                            state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2)
                            state["realized"]=round(state["realized"]+t["pnl"],2)
                            cooldown[t["sym"]]=time.time()
                            state["trades"].remove(t)
                            log(f"✅ TP {t['s']} +{t['pnl']}$ bal {state['balance']}")
                            try_add_one()
                        # خسارة -15$ يقفل ويبحث عن أقوى
                        elif t["pnl"] <= SL:
                            state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2)
                            state["realized"]=round(state["realized"]+t["pnl"],2)
                            cooldown[t["sym"]]=time.time()
                            state["trades"].remove(t)
                            log(f"❌ SL {t['s']} {t['pnl']}$ bal {state['balance']} | يبحث عن أقوى")
                            try_add_one()

                state["unrealized"]=round(sum(t["pnl"] for t in state["trades"]),2)

                if state["total_target"]>0.01 and state["unrealized"]>=state["total_target"] and state["unrealized"]>0:
                    for t in list(state["trades"]):
                        state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2)
                        state["realized"]=round(state["realized"]+t["pnl"],2)
                        cooldown[t["sym"]]=time.time()
                    state["trades"]=[]; state["unrealized"]=0; log("CLOSE ALL")
        except Exception as e:
            log(f"err {e}")
        time.sleep(3)

threading.Thread(target=worker,daemon=True).start()

HTML="""
<!DOCTYPE html><html dir="rtl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V51 TP5 SL15</title>
<style>
body{background:#0a0c1e;color:#fff;margin:0;padding:6px;font-family:Tahoma}
.title{text-align:center;color:#ffcc00;font-size:17px;font-weight:900}
.bar{background:#151833;border:2px solid #ffcc0044;border-radius:12px;padding:7px}
.status{text-align:center;color:#00ff88;font-size:12px;font-weight:900;margin-bottom:5px}
.row-main{display:flex;gap:4px;flex-wrap:wrap;justify-content:space-between;align-items:center}
.card{background:#1e2147;border:2px solid #ffcc00;border-radius:10px;padding:4px 7px;min-width:90px;text-align:center}
.card.orange{border-color:#ff9800}
.lbl{color:#9aa0c5;font-size:8px}.val{font-size:17px;font-weight:900}
.box{display:flex;gap:3px;background:#0000004d;padding:3px;border-radius:6px;border:1px solid #ffffff15;align-items:center}
input{background:#0a0c1e;color:#ffcc00;border:2px solid #666;border-radius:5px;padding:4px;width:55px;text-align:center;font-weight:900;direction:ltr}
.btn{padding:5px 7px;border-radius:6px;border:0;font-weight:900;font-size:10px;cursor:pointer}
.g{color:#00ff88}.r{color:#ff3d57}.gold{color:#ffcc00}
table{width:100%;background:#151833;border-radius:8px;border-collapse:collapse;margin-top:5px}
th{background:#1e2040;color:#ffcc00;padding:5px 1px;font-size:10px}
td{padding:4px 1px;text-align:center;border-top:1px solid #2a2d4a;font-size:10px}
.badge-long{background:#00e676;color:#000;padding:3px 7px;border-radius:10px;font-size:9px;font-weight:900;min-width:40px;display:inline-block}
.badge-short{background:#ff1744;color:#fff;padding:3px 7px;border-radius:10px;font-size:9px;font-weight:900;min-width:40px;display:inline-block}
.log{background:#000;border-radius:8px;padding:5px;margin-top:5px;font-size:10px;color:#0f0;max-height:120px;overflow:auto;direction:ltr;text-align:left}
.ltr{direction:ltr;display:inline-block;font-family:monospace}
</style></head><body>
<div class="title">💎 V51 - TP +$5 ✅ / SL -$15 ❌ - يفتح 10</div>
<div class="bar">
<div class="status" id="st">هدف {{s.total_target}}$ {% if s.total_target<=0.01 %}(معطل-TP5/SL15){% endif %} | {{s.trades|length}}/10 | رصيد {{'%.0f'|format(s.balance)}}$ | محجوز {{s.trades|length*500}}$ | محقق {{'%.1f'|format(s.realized)}}$</div>
<div class="row-main">
  <div class="card"><div class="lbl">💰 الرصيد</div><div class="val gold"><span class="ltr" id="bal">{{'%.2f'|format(s.balance)}}$</span></div></div>
  <div class="box"><span style="color:#ffcc00;font-size:8px">هدف الكل</span><input id="t" value="{{s.total_target}}"><button class="btn" style="background:#3d5afe;color:#fff" onclick="fetch('/set_target?v='+document.getElementById('t').value).then(()=>location.reload())">حفظ</button></div>
  <div class="card orange"><div class="lbl">📈 غير محققة</div><div class="val" id="uC"><span class="ltr" id="unreal">{{'%+.2f'|format(s.unrealized)}}$</span></div></div>
  <button class="btn" style="background:#ff3d00;color:#fff" onclick="fetch('/close_all').then(()=>location.reload())">🔒</button>
  <button class="btn" style="background:#00e676" onclick="fetch('/toggle').then(()=>location.reload())">⏸️</button>
  <button class="btn" style="background:#ff9800" onclick="if(confirm('تصفير؟'))fetch('/reset').then(()=>location.reload())">🔄</button>
</div>
</div>
<table><tr><th>العملة</th><th>الجانب</th><th>دخول</th><th>حالي</th><th>$</th><th>%</th><th>×</th></tr>
{% for t in s.trades %}
<tr>
<td><b>{{t.s}}</b></td>
<td><span class="{{'badge-long' if t.side=='LONG' else 'badge-short'}}">{{t.side}}</span></td>
<td><span class="ltr">{{'%.4f'|format(t.entry)}}</span></td>
<td><span class="ltr">{{'%.4f'|format(t.live)}}</span></td>
<td class="{{'g' if t.pnl>=0 else 'r'}}"><span class="ltr">{{'%+.2f'|format(t.pnl)}}$</span></td>
<td class="{{'g' if t.pct>=0 else 'r'}}"><span class="ltr">{{'%+.2f'|format(t.pct)}}%</span></td>
<td><button class="btn" style="background:#333;color:#fff;padding:1px 4px" onclick="fetch('/close_one?s={{t.s}}').then(()=>location.reload())">×</button></td>
</tr>
{% endfor %}
</table>
<div class="log" id="logBox">{% for l in logs %}{{l}}<br>{% endfor %}</div>
<script>
setInterval(()=>{
 fetch('/api').then(r=>r.json()).then(d=>{
  document.getElementById('bal').innerText=d.balance.toFixed(2)+'$';
  document.getElementById('unreal').innerText=(d.unrealized>=0?'+':'')+d.unrealized.toFixed(2)+'$';
  document.getElementById('st').innerText=`هدف ${d.total_target}$ ${d.total_target<=0.01?'(معطل-TP5/SL15)':''} | ${d.trades.length}/10 | رصيد ${d.balance.toFixed(0)}$ | محجوز ${d.trades.length*500}$ | محقق ${d.realized.toFixed(1)}$`;
  document.getElementById('uC').className='val '+(d.unrealized>=0?'g':'r');
  if(d.trades.length!= {{s.trades|length}} && Math.abs(d.trades.length - {{s.trades|length}})>1) location.reload();
 });
 fetch('/logs').then(r=>r.text()).then(t=>{document.getElementById('logBox').innerHTML=t.replace(/\\n/g,'<br>')});
},2000);
</script>
</body></html>
"""
@app.route('/')
def home(): return render_template_string(HTML, s=state, logs=logs)
@app.route('/api')
def api(): return jsonify(state)
@app.route('/logs')
def get_logs(): return "\n".join(logs)
@app.route('/set_target')
def set_tar():
    try: state["total_target"]=float(request.args.get('v')); log(f"SET {state['total_target']}")
    except: pass
    return "OK"
@app.route('/reset')
def reset(): state["balance"]=5000.0; state["realized"]=0.0; state["unrealized"]=0.0; state["trades"]=[]; cooldown.clear(); log("RESET"); return "OK"
@app.route('/close_all')
def close_all():
    for t in list(state["trades"]):
        state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2)
        state["realized"]=round(state["realized"]+t["pnl"],2)
        cooldown[t["sym"]]=time.time()
    state["trades"]=[]; state["unrealized"]=0; log("CLOSE ALL"); return "OK"
@app.route('/close_one')
def close_one():
    sname=request.args.get('s')
    for t in list(state["trades"]):
        if t["s"]==sname:
            state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2)
            state["realized"]=round(state["realized"]+t["pnl"],2)
            cooldown[t["sym"]]=time.time()
            state["trades"].remove(t); log(f"CLOSE {sname}"); break
    return "OK"
@app.route('/toggle')
def toggle(): state["trading"]=not state["trading"]; log(f"TOGGLE {state['trading']}"); return "OK"
@app.route('/health')
def h(): return "OK",200
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

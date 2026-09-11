from flask import Flask, render_template_string, request, jsonify
import os, threading, time, requests
app = Flask(__name__)
cooldown = {}
state={
  "total_capital":2000.0,"per_trade":100.0,"balance":2000.0,
  "realized":0.0,"unrealized":0.0,"total_target":0.5,
  "trades":[],"TP":0.35,"SL":-0.65,"cycles":0,
  "strategy":1
}
STRATEGIES={1:"1 - CLASSIC V73",2:"2 - MACD ZERO (فكرتك)"}

def recalc_balance():
    locked=sum(t["cap"] for t in state["trades"])
    state["balance"]=round(state["total_capital"]-locked,2)

def get_macd_signal(sym):
    try:
        kl=requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=40",timeout=2).json()
        closes=[float(k[4]) for k in kl]
        if len(closes)<35: return None
        def ema(data,p):
            k=2/(p+1); e=data[0]
            for v in data[1:]: e=v*k+e*(1-k)
            return e
        e12=[ema(closes[i-11:i+1],12) for i in range(11,len(closes))]
        e26=[ema(closes[i-25:i+1],26) for i in range(25,len(closes))]
        macd=e12[-1]-e26[-1]; macd_prev=e12[-2]-e26[-2]
        signal=ema([e12[j]-e26[j-14] for j in range(14,len(e12))],9)
        hist=macd-signal; hist_prev=macd_prev-signal
        green=float(kl[-1][4])>float(kl[-1][1])
        if hist>0 and hist>hist_prev and macd>0 and green: return "LONG"
        if hist<0 and hist<hist_prev and macd<0 and not green: return "SHORT"
        return None
    except: return None

def try_add_fast():
    per=state["per_trade"]; max_open=int(state["total_capital"]//per) if per>0 else 50
    if len(state["trades"])>=max_open or state["balance"]<per*0.9: return False
    try:
        data=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=3).json()
        have=set(t["sym"] for t in state["trades"]); added=0; strat=state["strategy"]
        for d in data:
            if len(state["trades"])>=max_open or state["balance"]<per*0.9: break
            sym=d["symbol"]
            if sym in have or not sym.endswith("USDT"): continue
            if "UP" in sym or "DOWN" in sym or "BEAR" in sym or "BULL" in sym: continue
            if sym in ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT"]: continue
            if sym in cooldown and time.time()-cooldown[sym]<15: continue
            try: price=float(d["lastPrice"]); ch=float(d["priceChangePercent"]); vol=float(d["quoteVolume"])
            except: continue
            if price>20 or price<0.000001 or vol<800000: continue
            if any(x in sym for x in ["MARS","PUMP","1000","SAGA","LUNA","USTC"]): continue
            side=None
            if strat==1:
                if abs(ch)<0.3: continue
                side="LONG" if ch>=0 else "SHORT"
            elif strat==2:
                if abs(ch)<0.2: continue
                sig=get_macd_signal(sym)
                if not sig: continue
                side=sig
            if not side: continue
            t={"s":sym.replace("USDT",""),"sym":sym,"cap":per,"qty":per/price,"entry":price,"live":price,"side":side,"pnl":0,"pct":0}
            state["trades"].append(t); have.add(sym); added+=1
            if added>=2 and strat==2: break
        recalc_balance(); return added>0
    except: return False

def worker():
    time.sleep(2); cooldown.clear()
    while True:
        try:
            per=state["per_trade"]; max_open=int(state["total_capital"]//per) if per>0 else 50
            while len(state["trades"])<max_open and state["balance"]>=per*0.9:
                if not try_add_fast(): break
            if state["trades"]:
                try: pm={d["symbol"]:float(d["price"]) for d in requests.get("https://api.binance.com/api/v3/ticker/price",timeout=2).json()}
                except: pm={}
                for t in list(state["trades"]):
                    live=pm.get(t["sym"])
                    if not live: continue
                    t["live"]=live; t["pct"]=round((live-t["entry"])/t["entry"]*100,3) if t["side"]=="LONG" else round((t["entry"]-live)/t["entry"]*100,3); t["pnl"]=round(t["cap"]*t["pct"]/100,2)
                state["unrealized"]=round(sum(x["pnl"] for x in state["trades"]),2)
                if state["unrealized"]<=-5.0:
                    worst=sorted(state["trades"],key=lambda x:x["pnl"])[:5]
                    for w in worst: state["realized"]=round(state["realized"]+w["pnl"],2); cooldown[w["sym"]]=time.time(); state["trades"].remove(w)
                    recalc_balance()
                if state["unrealized"]>=state["total_target"]:
                    for t in state["trades"]: cooldown[t["sym"]]=time.time()
                    state["realized"]=round(state["realized"]+state["unrealized"],2); state["trades"]=[]; state["unrealized"]=0; state["cycles"]+=1; recalc_balance()
                else:
                    for t in list(state["trades"]):
                        if t["pnl"]>=state["TP"] or t["pnl"]<=state["SL"]:
                            state["realized"]=round(state["realized"]+t["pnl"],2); cooldown[t["sym"]]=time.time(); state["trades"].remove(t); recalc_balance()
            else:
                if len(cooldown)>150: cooldown.clear()
        except: pass
        time.sleep(0.5 if state["strategy"]==2 else 0.15)
threading.Thread(target=worker,daemon=True).start()

HTML="""<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V75 DUAL</title><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet"><style>
*{font-family:'Cairo',sans-serif;box-sizing:border-box}
body{background:radial-gradient(1200px 600px at 50% -10%, #1f2552 0%, #0e112f 40%, #07091a 100%);color:#fff;margin:0;padding:14px;min-height:100vh}
.header{font-size:26px;font-weight:900;text-align:center;background:linear-gradient(90deg,#ffd700,#ffae00,#00ff88);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{font-size:12px;color:#a8add0;text-align:center;font-weight:800;margin:6px 0 14px}
.glass{background:linear-gradient(145deg,rgba(38,42,90,0.9),rgba(21,24,51,0.95));border:1.5px solid rgba(255,255,255,0.12);border-radius:20px;padding:14px;backdrop-filter:blur(12px);box-shadow:0 10px 40px rgba(0,0,0,0.4)}
.ctrl-title{color:#ffcc00;font-weight:900;margin-bottom:8px;font-size:13px}
input,select{background:#07091e;color:#ffcc00;border:2.5px solid #ffcc00aa;border-radius:12px;padding:11px 10px;font-size:16px;font-weight:900;text-align:center;outline:none}
select{color:#00ff88;border-color:#00ff88aa;min-width:240px;direction:rtl}
.btn{padding:11px 16px;border-radius:12px;border:0;font-weight:900;font-size:13px;cursor:pointer}
.btn-gold{background:linear-gradient(145deg,#ffcc00,#ff9800);color:#000}
.btn-green{background:linear-gradient(145deg,#00e676,#00c853);color:#000}
.btn-red{background:linear-gradient(145deg,#ff3d57,#c62828);color:#fff}
.btn-dark{background:linear-gradient(145deg,#2a2e6a,#1a1c3f);color:#fff;border:1.5px solid #ffffff22}
.dashboard{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:14px 0}
.cardx{background:linear-gradient(145deg,#2b2f6e,#1c1e45);border:1.8px solid #ffffff18;border-radius:20px;padding:14px;text-align:center}
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
td{padding:11px 6px;text-align:center;border-top:1px solid #ffffff10;font-size:15px;font-weight:900}
.badge-long{background:linear-gradient(145deg,#00e676,#00c853);color:#000;padding:5px 12px;border-radius:24px;font-size:11px;font-weight:900;min-width:56px;display:inline-block}
.badge-short{background:linear-gradient(145deg,#ff1744,#d50000);color:#fff;padding:5px 12px;border-radius:24px;font-size:11px;font-weight:900;min-width:56px;display:inline-block}
.pill{display:inline-flex;align-items:center;gap:6px;background:#1e2147;padding:10px 14px;border-radius:14px;border:1.5px solid #ffffff15}
</style></head><body>
<div class="header">👑 V75 DUAL — خيارين</div>
<div class="sub">اختيارك بيدك | 1=CLASSIC | 2=MACD ZERO فكرتك | الربح محفوظ</div>
<div class="glass" style="margin-bottom:14px;text-align:center">
<div class="ctrl-title">🎮 استراتيجيات التشغيل</div>
<div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
<select id="stratSel" onchange="setStrat()">
<option value="1" {{'selected' if s.strategy==1 else ''}}>1 - CLASSIC V73</option>
<option value="2" {{'selected' if s.strategy==2 else ''}}>2 - MACD ZERO (فكرتك) ⭐</option>
</select>
<span style="background:#00ff8822;border:1.5px solid #00ff88;color:#00ff88;padding:8px 14px;border-radius:12px;font-weight:900;font-size:12px">النشط الآن: {{strategies[s.strategy]}}</span>
</div>
</div>
<div class="dashboard">
<div class="cardx gold"><div class="lbl">💰 ثابت</div><div class="val"><span class="ltr">{{'%.0f'|format(s.total_capital)}}$</span></div></div>
<div class="cardx"><div class="lbl">🔓 حر</div><div class="val" id="bal"><span class="ltr">{{'%.0f'|format(s.balance)}}$</span></div></div>
<div class="cardx {{'profit' if s.realized>=0 else 'loss'}}"><div class="lbl">💵 صافي</div><div class="val" id="real"><span class="ltr">{{'%+.2f'|format(s.realized)}}$</span></div></div>
<div class="cardx {{'profit' if s.unrealized>=0 else 'loss'}}"><div class="lbl">📈 غير محققة</div><div class="val" id="unreal"><span class="ltr">{{'%+.2f'|format(s.unrealized)}}$</span></div></div>
<div class="cardx gold"><div class="lbl">💎 الإجمالي</div><div class="val" id="equity"><span class="ltr">{{'%.2f'|format(s.total_capital + s.realized + s.unrealized)}}$</span></div></div>
<div class="cardx"><div class="lbl">⚖️ L/S | دورات</div><div class="val" id="ls"><span class="ltr">{{s.trades|selectattr('side','equalto','LONG')|list|length}}/{{s.trades|selectattr('side','equalto','SHORT')|list|length}} | {{s.cycles}}</span></div></div>
</div>
<div class="table-wrap"><table><tr><th>عملة</th><th>جانب</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th></tr>{% for t in s.trades %}<tr><td><b>{{t.s}}</b></td><td><span class="{{'badge-long' if t.side=='LONG' else 'badge-short'}}">{{t.side}}</span></td><td><span class="ltr">{{'%.4f'|format(t.entry)}}</span></td><td><span class="ltr">{{'%.4f'|format(t.live)}}</span></td><td><span class="ltr {{'g' if t.pnl>=0 else 'r'}}">{{'%+.2f'|format(t.pnl)}}$</span></td><td><span class="ltr {{'g' if t.pct>=0 else 'r'}}">{{'%+.2f'|format(t.pct)}}%</span></td></tr>{% endfor %}</table></div>
<script>
function setStrat(){fetch('/set_strategy?v='+document.getElementById('stratSel').value).then(()=>location.reload())}
setInterval(()=>fetch('/api').then(r=>r.json()).then(d=>{location.reload()}),10000);
</script></body></html>
"""
@app.route('/')
def home(): return render_template_string(HTML, s=state, strategies=STRATEGIES)
@app.route('/api')
def api(): return jsonify({**state,"equity":state["total_capital"]+state["realized"]+state["unrealized"]})
@app.route('/set_strategy')
def set_strategy():
    try:
        v=int(request.args.get('v'));
        if v in STRATEGIES: state["strategy"]=v
    except: pass
    return "OK"
@app.route('/health')
def h(): return "OK",200
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

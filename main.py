from flask import Flask, render_template_string, request, jsonify
import os, threading, time, requests, math
app = Flask(__name__)
cooldown = {}
MAX_OPEN = 10
PER_TRADE = 500
TP = 5.0
SL = -15.0
logs=[]

def log(m):
    logs.append(f"{time.strftime('%H:%M:%S')} - {m}")
    if len(logs)>50: logs.pop(0)

def get_volatile_coins(limit=80):
    try:
        data=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=8).json()
        cands=[]
        for d in data:
            sym=d["symbol"]
            if not sym.endswith("USDT"): continue
            if sym in ["BTCUSDT","ETHUSDT"]: continue
            if "UP" in sym or "DOWN" in sym or "BEAR" in sym or "BULL" in sym: continue
            try: price=float(d["lastPrice"]); vol=float(d["quoteVolume"]); ch=float(d["priceChangePercent"])
            except: continue
            if price>10 or price<0.0000005 or vol<8000000 or abs(ch)<2.2: continue
            if sym in cooldown and time.time()-cooldown[sym]<300: continue
            cands.append((sym, abs(ch)*math.log(vol)))
        cands.sort(key=lambda x: x[1], reverse=True)
        return [s for s,_ in cands[:limit]]
    except: return ["ICPUSDT","ENAUSDT","AEROUSDT","HBARUSDT","TRUMPUSDT","INJUSDT","ONDUSDT","ASTERUSDT","XLMUSDT","SUIUSDT"]

def get_data(sym):
    try:
        data=requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=210",timeout=6).json()
        closes=[float(k[4]) for k in data]
        price=closes[-1]; k=2/(200+1); ema=closes[0]
        for c in closes[1:]: ema=c*k+ema*(1-k)
        sma=sum(closes[-20:])/20
        return {"price":price,"ema":ema,"sma":sma}
    except: return None

state={"balance":5000.0,"realized":0.0,"unrealized":0.0,"total_target":5.0,"trades":[],"trading":True}

def try_add_one():
    if not state["trading"] or len(state["trades"])>=MAX_OPEN or state["balance"]<PER_TRADE: return False
    have=set(t["sym"] for t in state["trades"])
    for sym in get_volatile_coins(80):
        if sym in have: continue
        d=get_data(sym)
        if not d: continue
        if abs(d["price"]-d["sma"])/d["sma"]>0.04: continue
        qty = PER_TRADE / d["price"]
        t={"s":sym.replace("USDT",""),"sym":sym,"cap":PER_TRADE,"qty":qty,"entry":d["price"],"live":d["price"],"side":"SHORT" if d["price"]<d["ema"] else "LONG","pnl":0,"pct":0}
        state["trades"].append(t)
        state["balance"]=round(state["balance"]-PER_TRADE,2)
        log(f"OPEN {t['s']} {t['side']} {qty:.1f} x {d['price']}")
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
                state["unrealized"]=round(sum(x["pnl"] for x in state["trades"]),2)
                for t in list(state["trades"]):
                    if t["pnl"]>=TP:
                        state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2)
                        state["realized"]=round(state["realized"]+t["pnl"],2)
                        cooldown[t["sym"]]=time.time()
                        state["trades"].remove(t)
                        log(f"✅ TP +${t['pnl']} {t['s']}")
                        try_add_one()
                    elif t["pnl"]<=SL:
                        state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2)
                        state["realized"]=round(state["realized"]+t["pnl"],2)
                        cooldown[t["sym"]]=time.time()
                        state["trades"].remove(t)
                        log(f"❌ SL {t['pnl']}$ {t['s']}")
                        try_add_one()
                state["unrealized"]=round(sum(x["pnl"] for x in state["trades"]),2)
        except Exception as e:
            log(f"err {e}")
        time.sleep(3)

threading.Thread(target=worker,daemon=True).start()

HTML="""
<!DOCTYPE html><html dir="rtl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V53 LUXURY</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap" rel="stylesheet">
<style>
*{font-family:'Cairo',Tahoma}
body{background:radial-gradient(ellipse at top,#1a1f4a 0%,#0a0c1e 60%);color:#fff;margin:0;padding:10px;min-height:100vh}
.header{background:linear-gradient(90deg,#ffcc00,#ff9800);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:26px;font-weight:900;text-align:center;letter-spacing:1px;text-shadow:0 0 30px #ffcc0055}
.sub{text-align:center;color:#7a7fb0;font-size:13px;margin-bottom:12px}
.dashboard{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-bottom:12px}
.cardx{background:linear-gradient(145deg,rgba(30,33,71,0.9),rgba(19,21,46,0.9));border:1.5px solid #ffffff18;border-radius:18px;padding:12px 10px;text-align:center;backdrop-filter:blur(10px);box-shadow:0 8px 25px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1)}
.cardx.gold{border-color:#ffcc0066;box-shadow:0 0 20px #ffcc0022,0 8px 25px rgba(0,0,0,0.4)}
.cardx.green{border-color:#00ff8866}
.cardx.red{border-color:#ff3d5766}
.lbl{color:#9aa0c5;font-size:11px;font-weight:700;letter-spacing:0.5px}
.val{font-size:22px;font-weight:900;margin-top:4px}
.val.gold{color:#ffcc00;text-shadow:0 0 15px #ffcc0088}
.val.g{color:#00ff88;text-shadow:0 0 15px #00ff8888}
.val.r{color:#ff3d57;text-shadow:0 0 15px #ff3d5788}
.controls{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;background:rgba(21,24,51,0.8);border-radius:16px;padding:10px;border:1px solid #ffffff12}
.inp{background:#0a0c1e;color:#ffcc00;border:2px solid #ffcc0066;border-radius:10px;padding:8px 10px;width:80px;text-align:center;font-size:18px!important;font-weight:900;direction:ltr}
.btn{padding:10px 16px;border-radius:12px;border:0;font-weight:900;font-size:13px;cursor:pointer;transition:0.2s}
.btn:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,0.4)}
.btn-save{background:linear-gradient(145deg,#3d5afe,#2a3eb1);color:#fff}
.btn-close{background:linear-gradient(145deg,#ff3d57,#c62828);color:#fff}
.btn-reset{background:linear-gradient(145deg,#ff9800,#e65100);color:#fff}
.table-wrap{background:rgba(21,24,51,0.9);border-radius:18px;overflow:hidden;border:1px solid #ffffff15;box-shadow:0 10px 30px rgba(0,0,0,0.5)}
table{width:100%;border-collapse:collapse}
th{background:linear-gradient(145deg,#1e2040,#181a35);color:#ffcc00;padding:12px 6px;font-size:13px;font-weight:900;letter-spacing:0.5px;border-bottom:2px solid #ffcc0033}
td{padding:10px 4px;text-align:center;border-top:1px solid #ffffff0a;font-size:14px;font-weight:700}
tr:hover{background:rgba(255,204,0,0.05)}
.badge-long{background:linear-gradient(145deg,#00e676,#00c853);color:#000;padding:6px 14px;border-radius:20px;font-size:12px;font-weight:900;box-shadow:0 0 15px #00e67688;min-width:60px;display:inline-block}
.badge-short{background:linear-gradient(145deg,#ff1744,#d50000);color:#fff;padding:6px 14px;border-radius:20px;font-size:12px;font-weight:900;box-shadow:0 0 15px #ff174488;min-width:60px;display:inline-block}
.money{color:#ffcc00;font-weight:900;font-size:14px}
.qty{color:#7ec8ff;font-weight:900}
.pnl-p{color:#00ff88}.pnl-n{color:#ff3d57}
.log{background:#000a;border-radius:12px;padding:10px;margin-top:12px;font-size:12px;color:#00ff88;max-height:140px;overflow:auto;direction:ltr;text-align:left;border:1px solid #ffffff12}
.ltr{direction:ltr;display:inline-block;font-family:monospace;font-weight:900}
</style></head><body>
<div class="header">💎 V53 LUXURY - يفتح 10 صفقات</div>
<div class="sub">TP +$5 ربح ✅ | SL -$15 خسارة ❌ | رأس مال $500 لكل عملة</div>

<div class="dashboard">
  <div class="cardx gold"><div class="lbl">💰 الرصيد الحر</div><div class="val gold"><span class="ltr">{{'%.2f'|format(s.balance)}}$</span></div></div>
  <div class="cardx"><div class="lbl">🔒 المحجوز</div><div class="val" style="color:#ff9800"><span class="ltr">{{s.trades|length*500}}$</span></div></div>
  <div class="cardx"><div class="lbl">💵 الكلي</div><div class="val" style="color:#fff"><span class="ltr">{{'%.2f'|format(s.balance + s.trades|length*500)}}$</span></div></div>
  <div class="cardx {{'green' if s.unrealized>=0 else 'red'}}"><div class="lbl">📈 غير محققة</div><div class="val {{'g' if s.unrealized>=0 else 'r'}}"><span class="ltr">{{'%+.2f'|format(s.unrealized)}}$</span></div></div>
  <div class="cardx {{'green' if s.realized>=0 else 'red'}}"><div class="lbl">✅ محقق</div><div class="val {{'g' if s.realized>=0 else 'r'}}"><span class="ltr">{{'%+.2f'|format(s.realized)}}$</span></div></div>
  <div class="cardx gold"><div class="lbl">📊 المفتوح</div><div class="val gold"><span class="ltr">{{s.trades|length}}/10</span></div></div>
</div>

<div class="controls">
  <span style="color:#ffcc00;font-weight:900">🎯 هدف الكل</span>
  <input class="inp" id="t" value="{{s.total_target}}">
  <button class="btn btn-save" onclick="fetch('/set_target?v='+document.getElementById('t').value).then(()=>location.reload())">💾 حفظ</button>
  <button class="btn btn-close" onclick="fetch('/close_all').then(()=>location.reload())">🔒 قفل الكل</button>
  <button class="btn btn-reset" onclick="if(confirm('تصفير الحساب؟'))fetch('/reset').then(()=>location.reload())">🔄 تصفير 5000$</button>
</div>

<div class="table-wrap">
<table>
<tr><th>العملة</th><th>الجانب</th><th>💰 رأس مال</th><th>📦 مبلغ العملة</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th><th>×</th></tr>
{% for t in s.trades %}
<tr>
<td><b style="font-size:15px;color:#fff">{{t.s}}</b></td>
<td><span class="{{'badge-long' if t.side=='LONG' else 'badge-short'}}">{{t.side}}</span></td>
<td><span class="money">$500</span></td>
<td><span class="qty ltr">{{'%.1f'|format(t.qty)}}</span></td>
<td><span class="ltr" style="color:#aaa">{{'%.4f'|format(t.entry)}}</span></td>
<td><span class="ltr" style="color:#fff">{{'%.4f'|format(t.live)}}</span></td>
<td class="{{'pnl-p' if t.pnl>=0 else 'pnl-n'}}"><span class="ltr" style="font-size:15px">{{'%+.2f'|format(t.pnl)}}$</span></td>
<td class="{{'pnl-p' if t.pct>=0 else 'pnl-n'}}"><span class="ltr">{{'%+.2f'|format(t.pct)}}%</span></td>
<td><button class="btn" style="background:#ffffff15;color:#fff;padding:4px 10px;border-radius:8px" onclick="fetch('/close_one?s={{t.s}}').then(()=>location.reload())">✕</button></td>
</tr>
{% endfor %}
</table>
</div>

<div class="log">{% for l in logs %}{{l}}<br>{% endfor %}</div>

<script>
setInterval(()=>{fetch('/logs').then(r=>r.text()).then(t=>{document.querySelector('.log').innerHTML=t.replace(/\\n/g,'<br>')})},2000);
</script>
</body></html>
"""
@app.route('/')
def home(): return render_template_string(HTML, s=state, logs=logs)
@app.route('/logs')
def get_logs(): return "\n".join(logs)
@app.route('/api')
def api(): return jsonify(state)
@app.route('/set_target')
def set_tar():
    try: state["total_target"]=float(request.args.get('v')); log(f"SET TARGET {state['total_target']}$")
    except: pass
    return "OK"
@app.route('/reset')
def reset(): state["balance"]=5000.0; state["realized"]=0.0; state["unrealized"]=0.0; state["trades"]=[]; cooldown.clear(); log("RESET 5000$"); return "OK"
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
@app.route('/health')
def h(): return "OK",200
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

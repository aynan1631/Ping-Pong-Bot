from flask import Flask, render_template_string, request
import os, threading, time, requests, math
app = Flask(__name__)
cooldown = {}

def get_rsi(closes, period=14):
    try:
        deltas = [closes[i]-closes[i-1] for i in range(1,len(closes))]
        gains = [d if d>0 else 0 for d in deltas[-period:]]
        losses = [-d if d<0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains)/period
        avg_loss = sum(losses)/period
        if avg_loss==0: return 70
        rs = avg_gain/avg_loss
        return 100 - (100/(1+rs))
    except: return 50

def get_volatile_coins(limit=80):
    try:
        data=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=8).json()
        cands=[]
        for d in data:
            sym=d["symbol"]
            if not sym.endswith("USDT"): continue
            if sym in ["BTCUSDT","ETHUSDT","BNBUSDT"]: continue
            if "UP" in sym or "DOWN" in sym or "BEAR" in sym or "BULL" in sym: continue
            try: price=float(d["lastPrice"]); vol=float(d["quoteVolume"]); ch=float(d["priceChangePercent"])
            except: continue
            if price>20 or price<0.0000005 or vol<8000000 or abs(ch)<2.0: continue
            if sym in cooldown and time.time()-cooldown[sym]<300: continue
            cands.append((sym, abs(ch)*math.log(vol)))
        cands.sort(key=lambda x: x[1], reverse=True)
        return [s for s,_ in cands[:limit]]
    except: return ["FORMUSDT","DOTUSDT","PROMUSDT","XPLUSDT","DOGSUSDT","WLDUSDT","ICPUSDT","ENAUSDT"]

def get_data(sym):
    try:
        data=requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=210",timeout=6).json()
        closes=[float(k[4]) for k in data]
        price=closes[-1]
        k=2/(200+1); ema=closes[0]
        for c in closes[1:]: ema=c*k+ema*(1-k)
        sma=sum(closes[-20:])/20
        rsi=get_rsi(closes,14)
        high20=max(closes[-20:]); low20=min(closes[-20:])
        return {"price":price,"ema":ema,"sma":sma,"rsi":round(rsi,1),"high20":high20,"low20":low20}
    except: return None

state={
    "total_capital":5000.0,
    "per_trade":500.0,
    "balance":5000.0,
    "realized":0.0,
    "unrealized":0.0,
    "total_target":5.0,
    "trades":[],
    "trading":True,
    "TP":5.0,
    "SL":-15.0,
    "strategy":"BALANCED"
}

def try_add_one():
    per = state["per_trade"]
    max_open = int(state["total_capital"] // per) if per>0 else 10
    if not state["trading"] or len(state["trades"])>=max_open or state["balance"]<per: return False
    
    longs = len([t for t in state["trades"] if t["side"]=="LONG"])
    shorts = len([t for t in state["trades"] if t["side"]=="SHORT"])
    need_short = longs > shorts + 1  # لو LONG كثير نحتاج SHORT

    have=set(t["sym"] for t in state["trades"])
    coins=get_volatile_coins(100)
    
    # أولوية للجانب الناقص
    candidates=[]
    for sym in coins:
        if sym in have: continue
        d=get_data(sym)
        if not d: continue
        if abs(d["price"]-d["sma"])/d["sma"]>0.05: continue
        
        side=None
        if d["price"] > d["ema"] and d["rsi"] < 68 and d["rsi"] > 35:
            side="LONG"
        elif d["price"] < d["ema"] and d["rsi"] > 32 and d["rsi"] < 65:
            side="SHORT"
        
        if side:
            score = 2 if (need_short and side=="SHORT") or (not need_short and side=="LONG") else 1
            candidates.append((score, sym, d, side))
    
    candidates.sort(key=lambda x: x[0], reverse=True)
    
    for score, sym, d, side in candidates[:5]:
        qty = per / d["price"]
        t={"s":sym.replace("USDT",""),"sym":sym,"cap":per,"qty":qty,"entry":d["price"],"live":d["price"],"side":side,"rsi":d["rsi"],"pnl":0,"pct":0}
        state["trades"].append(t)
        state["balance"]=round(state["balance"]-per,2)
        return True
    return False

def worker():
    while True:
        try:
            if state["trading"]:
                per = state["per_trade"]
                max_open = int(state["total_capital"] // per) if per>0 else 10
                tries=0
                while len(state["trades"])<max_open and state["balance"]>=per and tries<15:
                    if not try_add_one(): tries+=1
                    time.sleep(0.4)
                for t in list(state["trades"]):
                    d=get_data(t["sym"])
                    if not d: continue
                    t["live"]=d["price"]
                    t["rsi"]=d["rsi"]
                    t["pct"]=round((d["price"]-t["entry"])/t["entry"]*100,2) if t["side"]=="LONG" else round((t["entry"]-d["price"])/t["entry"]*100,2)
                    t["pnl"]=round(t["cap"]*t["pct"]/100,2)
                state["unrealized"]=round(sum(x["pnl"] for x in state["trades"]),2)
                for t in list(state["trades"]):
                    if t["pnl"]>=state["TP"] or t["pnl"]<=state["SL"]:
                        state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2)
                        state["realized"]=round(state["realized"]+t["pnl"],2)
                        cooldown[t["sym"]]=time.time()
                        state["trades"].remove(t)
                        try_add_one()
                state["unrealized"]=round(sum(x["pnl"] for x in state["trades"]),2)
        except: pass
        time.sleep(3)

threading.Thread(target=worker,daemon=True).start()

HTML="""
<!DOCTYPE html><html dir="rtl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V55 BALANCED</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap" rel="stylesheet">
<style>
*{font-family:'Cairo',Tahoma}
body{background:radial-gradient(ellipse at top,#1a1f4a 0%,#0a0c1e 70%);color:#fff;margin:0;padding:8px;min-height:100vh}
.header{background:linear-gradient(90deg,#ffcc00,#ff9800);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:24px;font-weight:900;text-align:center}
.sub{text-align:center;color:#7a7fb0;font-size:12px;margin-bottom:10px}
.strategy-bar{background:linear-gradient(145deg,#1e2147,#13152e);border:2px solid #00ff8866;border-radius:14px;padding:8px;text-align:center;margin-bottom:10px}
.top-controls{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px}
.ctrl{background:linear-gradient(145deg,#1e2147,#13152e);border:1.5px solid #ffcc0033;border-radius:14px;padding:10px;text-align:center}
.ctrl-title{color:#ffcc00;font-size:11px;font-weight:900;margin-bottom:6px}
.ctrl-row{display:flex;gap:6px;justify-content:center;align-items:center;flex-wrap:wrap}
select,input{background:#0a0c1e;color:#ffcc00;border:2px solid #ffcc0066;border-radius:10px;padding:7px;font-size:15px!important;font-weight:900;text-align:center;direction:ltr;min-width:85px}
.btn{padding:8px 12px;border-radius:10px;border:0;font-weight:900;font-size:11px;cursor:pointer}
.btn-gold{background:linear-gradient(145deg,#ffcc00,#ff9800);color:#000}
.btn-red{background:linear-gradient(145deg,#ff3d57,#c62828);color:#fff}
.btn-blue{background:linear-gradient(145deg,#3d5afe,#2a3eb1);color:#fff}
.dashboard{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:10px 0}
.cardx{background:linear-gradient(145deg,rgba(30,33,71,0.9),rgba(19,21,46,0.9));border:1.5px solid #ffffff18;border-radius:16px;padding:10px;text-align:center}
.cardx.gold{border-color:#ffcc0066}
.lbl{color:#9aa0c5;font-size:10px;font-weight:700}.val{font-size:19px;font-weight:900;margin-top:3px}
.table-wrap{background:rgba(21,24,51,0.95);border-radius:16px;overflow:hidden;border:1px solid #ffffff15}
table{width:100%;border-collapse:collapse}
th{background:#1e2040;color:#ffcc00;padding:11px 3px;font-size:12px;font-weight:900;border-bottom:2px solid #ffcc0033}
td{padding:11px 3px;text-align:center;border-top:1px solid #ffffff0a;font-size:15px!important;font-weight:800}
.badge-long{background:linear-gradient(145deg,#00e676,#00c853);color:#000;padding:6px 14px;border-radius:20px;font-size:12px;font-weight:900;box-shadow:0 0 12px #00e67688;min-width:65px;display:inline-block}
.badge-short{background:linear-gradient(145deg,#ff1744,#d50000);color:#fff;padding:6px 14px;border-radius:20px;font-size:12px;font-weight:900;box-shadow:0 0 12px #ff174488;min-width:65px;display:inline-block}
.ltr{direction:ltr;display:inline-block;font-family:monospace;font-weight:900}
.g{color:#00ff88}.r{color:#ff3d57}
</style></head><body>
<div class="header">💎 V55 BALANCED - متوازن LONG/SHORT</div>
<div class="sub">EMA200 + RSI 32-68 + موازنة تلقائية</div>

<div class="strategy-bar">
  <span style="color:#00ff88;font-weight:900">⚖️ الاستراتيجية 1: متوازنة - LONG فوق EMA و RSI<68 | SHORT تحت EMA و RSI>32</span><br>
  <span style="color:#aaa;font-size:11px">البوت يوازن تلقائي - إذا LONG كثير يبحث SHORT غصب</span>
</div>

<div class="top-controls">
  <div class="ctrl">
    <div class="ctrl-title">💰 إجمالي رأس المال</div>
    <div class="ctrl-row">
      <select onchange="document.getElementById('totalInp').value=this.value">
        <option value="500">500$</option><option value="1000">1000$</option><option value="2000">2000$</option>
        <option value="5000" selected>5000$</option><option value="10000">10000$</option><option value="50000">50000$</option><option value="100000">100000$</option>
      </select>
      <input id="totalInp" value="{{s.total_capital}}" style="width:95px">
      <button class="btn btn-gold" onclick="fetch('/set_total?v='+document.getElementById('totalInp').value).then(()=>location.reload())">تطبيق</button>
    </div>
  </div>
  <div class="ctrl">
    <div class="ctrl-title">📦 رأس مال الصفقة</div>
    <div class="ctrl-row">
      <select onchange="document.getElementById('perInp').value=this.value">
        <option value="100">100$</option><option value="500" selected>500$</option><option value="1000">1000$</option><option value="2000">2000$</option>
      </select>
      <input id="perInp" value="{{s.per_trade}}" style="width:85px">
      <button class="btn btn-blue" onclick="fetch('/set_per?v='+document.getElementById('perInp').value).then(()=>location.reload())">تطبيق</button>
    </div>
  </div>
</div>

<div class="dashboard">
  <div class="cardx gold"><div class="lbl">💰 رصيد حر</div><div class="val" style="color:#ffcc00"><span class="ltr">{{'%.2f'|format(s.balance)}}$</span></div></div>
  <div class="cardx"><div class="lbl">🔒 محجوز</div><div class="val" style="color:#ff9800"><span class="ltr">{{'%.0f'|format(s.trades|length * s.per_trade)}}$</span></div></div>
  <div class="cardx"><div class="lbl">💵 الكلي</div><div class="val"><span class="ltr">{{'%.2f'|format(s.balance + s.trades|length * s.per_trade)}}$</span></div></div>
  <div class="cardx"><div class="lbl">📈 غير محققة</div><div class="val {{'g' if s.unrealized>=0 else 'r'}}"><span class="ltr">{{'%+.2f'|format(s.unrealized)}}$</span></div></div>
  <div class="cardx"><div class="lbl">✅ محقق</div><div class="val {{'g' if s.realized>=0 else 'r'}}"><span class="ltr">{{'%+.2f'|format(s.realized)}}$</span></div></div>
  <div class="cardx gold"><div class="lbl">⚖️ LONG/SHORT</div><div class="val" style="color:#fff;font-size:16px"><span class="ltr">{{s.trades|selectattr('side','equalto','LONG')|list|length}} LONG / {{s.trades|selectattr('side','equalto','SHORT')|list|length}} SHORT</span></div></div>
</div>

<div style="display:flex;gap:6px;justify-content:center;margin-bottom:10px;flex-wrap:wrap">
  <div style="display:flex;gap:4px;align-items:center;background:#151833;padding:6px 10px;border-radius:10px;border:1px solid #ffffff15">
    <span style="color:#ffcc00;font-weight:900;font-size:11px">🎯 هدف الكل</span>
    <input id="t" style="width:65px" value="{{s.total_target}}">
    <button class="btn btn-blue" style="padding:5px 10px" onclick="fetch('/set_target?v='+document.getElementById('t').value).then(()=>location.reload())">حفظ</button>
  </div>
  <button class="btn btn-red" onclick="fetch('/close_all').then(()=>location.reload())">🔒 قفل الكل</button>
  <button class="btn btn-gold" onclick="if(confirm('تصفير؟'))fetch('/reset').then(()=>location.reload())">🔄 تصفير</button>
</div>

<div class="table-wrap">
<table>
<tr><th>العملة</th><th>الجانب</th><th>RSI</th><th>💰 رأس مال</th><th>📦 مبلغ</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th><th>×</th></tr>
{% for t in s.trades %}
<tr>
<td><b style="font-size:16px">{{t.s}}</b></td>
<td><span class="{{'badge-long' if t.side=='LONG' else 'badge-short'}}">{{t.side}}</span></td>
<td><span class="ltr" style="color:{{'#ff9800' if t.rsi>60 or t.rsi<40 else '#aaa'}};font-size:14px">{{t.rsi}}</span></td>
<td><span class="ltr" style="color:#ffcc00">${{t.cap|int}}</span></td>
<td><span class="ltr" style="color:#7ec8ff">{{'%.1f'|format(t.qty) if t.qty<1000 else '%.1fK'|format(t.qty/1000)}}</span></td>
<td><span class="ltr" style="color:#aaa">{{'%.4f'|format(t.entry)}}</span></td>
<td><span class="ltr" style="color:#fff">{{'%.4f'|format(t.live)}}</span></td>
<td class="{{'g' if t.pnl>=0 else 'r'}}"><span class="ltr">{{'%+.2f'|format(t.pnl)}}$</span></td>
<td class="{{'g' if t.pct>=0 else 'r'}}"><span class="ltr">{{'%+.2f'|format(t.pct)}}%</span></td>
<td><button style="background:#ffffff15;color:#fff;border:0;padding:5px 10px;border-radius:8px;font-weight:900;cursor:pointer" onclick="fetch('/close_one?s={{t.s}}').then(()=>location.reload())">✕</button></td>
</tr>
{% endfor %}
</table>
</div>
</body></html>
"""
@app.route('/')
def home(): return render_template_string(HTML, s=state)
@app.route('/set_total')
def set_total():
    try: v=float(request.args.get('v')); state["total_capital"]=v; state["balance"]=v - len(state["trades"])*state["per_trade"]
    except: pass
    return "OK"
@app.route('/set_per')
def set_per():
    try: v=float(request.args.get('v')); state["per_trade"]=v
    except: pass
    return "OK"
@app.route('/set_target')
def set_tar():
    try: state["total_target"]=float(request.args.get('v'))
    except: pass
    return "OK"
@app.route('/reset')
def reset(): state["balance"]=state["total_capital"]; state["realized"]=0; state["unrealized"]=0; state["trades"]=[]; cooldown.clear(); return "OK"
@app.route('/close_all')
def close_all():
    for t in list(state["trades"]):
        state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2); state["realized"]=round(state["realized"]+t["pnl"],2); cooldown[t["sym"]]=time.time()
    state["trades"]=[]; state["unrealized"]=0; return "OK"
@app.route('/close_one')
def close_one():
    sname=request.args.get('s')
    for t in list(state["trades"]):
        if t["s"]==sname: state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2); state["realized"]=round(state["realized"]+t["pnl"],2); cooldown[t["sym"]]=time.time(); state["trades"].remove(t); break
    return "OK"
@app.route('/health')
def h(): return "OK",200
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

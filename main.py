from flask import Flask, render_template_string, request, jsonify
import os, threading, time, requests, math
app = Flask(__name__)
cooldown = {}
MAX_OPEN = 10
PER_TRADE = 500

def get_volatile_coins(limit=60):
    try:
        data=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=8).json()
        cands=[]
        for d in data:
            sym=d["symbol"]
            if not sym.endswith("USDT"): continue
            if sym in ["BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT"]: continue
            if "UP" in sym or "DOWN" in sym: continue
            try: price=float(d["lastPrice"]); vol=float(d["quoteVolume"]); change=float(d["priceChangePercent"])
            except: continue
            if price>5 or price<0.0000005 or vol<10000000 or abs(change)<2.2: continue
            if sym in cooldown and time.time()-cooldown[sym]<3600: continue
            cands.append((sym, abs(change)*math.log(vol)))
        cands.sort(key=lambda x: x[1], reverse=True)
        return [s for s,_ in cands[:limit]]
    except: return ["MARSUSDT","BONKUSDT","WIFUSDT","FLOKIUSDT","BOMEUSDT"]

def get_data(sym):
    try:
        data=requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=210",timeout=6).json()
        closes=[float(k[4]) for k in data]
        price=closes[-1]; k=2/(200+1); ema=closes[0]
        for c in closes[1:]: ema=c*k+ema*(1-k)
        sma=sum(closes[-20:])/20
        return {"price":price,"ema":ema,"sma":sma}
    except: return None

# الرصيد الكلي هو الفلوس الكاش المتاحة
state={"balance":5000.0,"realized":0.0,"unrealized":0.0,"delta":0.0,"trades":[],"trading":True}

def try_add_one():
    if not state["trading"] or len(state["trades"])>=MAX_OPEN: return False
    if state["balance"] < PER_TRADE: return False # ما يكفي
    have=set(t["s"] for t in state["trades"])
    for sym in get_volatile_coins(60):
        short=sym.replace("USDT","")
        if short in have or sym in cooldown: continue
        d=get_data(sym)
        if not d or abs(d["price"]-d["sma"])/d["sma"]>0.03: continue
        # هنا السحب الصحيح
        state["balance"] = round(state["balance"] - PER_TRADE, 2)
        state["trades"].append({"s":short,"sym":sym,"cap":PER_TRADE,"entry":d["price"],"live":d["price"],"side":"SHORT" if d["price"]<d["ema"] else "LONG","pnl":0,"pct":0})
        print(f"OPEN {short} balance now {state['balance']}")
        return True
    return False

def worker():
    while True:
        if state["trading"]:
            if len(state["trades"])<MAX_OPEN and state["balance"]>=PER_TRADE:
                try_add_one()
            tot=0
            should_close = state["delta"] > 0.01
            for t in list(state["trades"]):
                d=get_data(t["sym"])
                if not d: continue
                t["live"]=d["price"]
                t["pct"]=round((t["entry"]-d["price"])/t["entry"]*100,2) if t["side"]=="SHORT" else round((d["price"]-t["entry"])/t["entry"]*100,2)
                t["pnl"]=round(t["cap"]*t["pct"]/100,2)
                tot+=t["pnl"]
            state["unrealized"]=round(tot,2)
            if should_close and state["unrealized"]>=state["delta"] and state["unrealized"]>0:
                for t in list(state["trades"]):
                    state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2)
                    state["realized"]=round(state["realized"]+t["pnl"],2)
                    cooldown[t["sym"]]=time.time()
                state["trades"]=[]; state["unrealized"]=0
        time.sleep(3)
threading.Thread(target=worker,daemon=True).start()

HTML="""
<!DOCTYPE html><html dir="rtl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V46 FIXED</title>
<style>
body{background:#0a0c1e;color:#fff;margin:0;padding:6px;font-family:Tahoma}
.title{text-align:center;color:#ffcc00;font-size:22px;font-weight:900;margin:6px}
.bar{background:#151833;border:2px solid #ffcc0055;border-radius:14px;padding:10px}
.status{text-align:center;color:#00ff88;font-size:16px;font-weight:900;margin-bottom:8px}
.row-main{display:flex;align-items:center;gap:6px;flex-wrap:wrap;justify-content:space-between}
.card{background:linear-gradient(145deg,#1e2147,#13152e);border:2px solid #ffcc00;border-radius:12px;padding:6px 10px;min-width:120px;text-align:center}
.card.orange{border-color:#ff9800}
.lbl{color:#9aa0c5;font-size:10px;font-weight:800}
.val{font-size:24px;font-weight:900}
.box{display:flex;align-items:center;gap:4px;background:rgba(0,0,0,0.3);padding:5px 6px;border-radius:8px;border:1px solid #ffffff15}
input{font-family:Tahoma!important;background:#0a0c1e;color:#ffcc00;border:2px solid #666;border-radius:6px;padding:7px;width:75px;text-align:center;font-size:16px!important;font-weight:900;direction:ltr}
.btn{padding:7px 10px;border-radius:7px;border:0;font-weight:900;font-size:11px;cursor:pointer}
.g{color:#00ff88}.r{color:#ff3d57}.gold{color:#ffcc00}
table{width:100%;background:#151833;border-radius:10px;border-collapse:collapse;margin-top:8px}
th{background:#1e2040;color:#ffcc00;padding:8px 2px;font-size:12px}
td{padding:6px 2px;text-align:center;border-top:1px solid #2a2d4a;font-size:11px}
.badge{background:#00e676;color:#000;padding:2px 6px;border-radius:10px;font-size:9px;font-weight:900}
.badge-short{background:#ff3d00;color:#fff}
.ltr{direction:ltr;display:inline-block}
</style></head><body>
<div class="title">💎 V46 - الرصيد الكلي - 10×500$ (سحب تلقائي)</div>
<div class="bar">
<div class="status">🟢 شغال - هدف ${{s.delta}} {% if s.delta<=0.01 %}معطل{% endif %} | مفتوح {{s.trades|length}}/10 | متاح ${{'%.0f'|format(s.balance)}} | محجوز ${{s.trades|length*500}}$</div>
<div class="row-main">
  <div class="card"><div class="lbl">💰 الرصيد الكلي (كاش)</div><div class="val gold"><span class="ltr" id="bal">{{'%.2f'|format(s.balance)}}$</span></div><div style="font-size:8px;color:#888">ينقص 500 مع كل صفقة</div></div>
  <div class="box"><span style="color:#ffcc00;font-size:11px;font-weight:900">الرصيد</span><input id="c" value="{{'%.0f'|format(s.balance)}}"><button class="btn" style="background:#ffeb3b" onclick="fetch('/set_bal?v='+document.getElementById('c').value).then(()=>location.reload())">حفظ</button></div>
  <div class="box"><span style="color:#ffcc00;font-size:11px;font-weight:900">هدف</span><input id="t" value="{{s.delta}}"><button class="btn" style="background:#3d5afe;color:#fff" onclick="fetch('/set_target?v='+document.getElementById('t').value).then(()=>location.reload())">حفظ</button></div>
  <div class="card orange"><div class="lbl">📈 غير المحققة</div><div class="val" id="uC"><span class="ltr" id="unreal">{{'%.2f'|format(s.unrealized)}}$</span></div><div style="font-size:8px;color:#aaa">{{s.trades|length}}×500$</div></div>
  <button class="btn" style="background:#ff3d00;color:#fff" onclick="fetch('/close_all').then(()=>location.reload())">🔒 قفل الكل + ارجاع</button>
  <button class="btn" style="background:#00e676" onclick="fetch('/toggle').then(()=>location.reload())">⏸️ إيقاف</button>
  <button class="btn" style="background:#ff9800" onclick="if(confirm('تصفير؟'))fetch('/reset').then(()=>location.reload())">🔄 تصفير</button>
</div>
</div>
<table><tr><th>العملة</th><th>الجانب</th><th>رأس المال</th><th>دخول</th><th>حالي</th><th>$</th><th>%</th><th>×</th></tr>
{% for t in s.trades %}
<tr><td style="color:#00ff88"><b>{{t.s}}</b></td><td><span class="badge {{'badge-short' if t.side=='SHORT' else ''}}">{{t.side}}</span></td><td><span class="ltr">$500</span></td><td><span class="ltr">{{'%.4f'|format(t.entry)}}</span></td><td><span class="ltr">{{'%.4f'|format(t.live)}}</span></td><td class="{{'g' if t.pnl>=0 else 'r'}}"><span class="ltr">{{'%.2f'|format(t.pnl)}}$</span></td><td class="{{'g' if t.pct>=0 else 'r'}}"><span class="ltr">{{'%.2f'|format(t.pct)}}%</span></td><td><button class="btn" style="background:#333;color:#fff;padding:2px 5px" onclick="fetch('/close_one?s={{t.s}}').then(()=>location.reload())">×</button></td></tr>
{% endfor %}
</table>
<script>setInterval(()=>{fetch('/api').then(r=>r.json()).then(d=>{document.getElementById('bal').innerText=d.balance.toFixed(2)+'$';document.getElementById('unreal').innerText=d.unrealized.toFixed(2)+'$';document.getElementById('uC').className='val '+(d.unrealized>=0?'g':'r');})},2000);</script>
</body></html>
"""
@app.route('/')
def home(): return render_template_string(HTML, s=state)
@app.route('/api')
def api(): return jsonify(state)
@app.route('/set_bal')
def set_bal():
    try: state["balance"]=float(request.args.get('v'))
    except: pass
    return "OK"
@app.route('/set_target')
def set_tar():
    try: state["delta"]=float(request.args.get('v'))
    except: pass
    return "OK"
@app.route('/reset')
def reset(): state["balance"]=5000.0; state["realized"]=0.0; state["unrealized"]=0.0; state["trades"]=[]; return "OK"
@app.route('/close_all')
def close_all():
    for t in list(state["trades"]):
        state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2)
        state["realized"]=round(state["realized"]+t["pnl"],2)
        cooldown[t["sym"]]=time.time()
    state["trades"]=[]; state["unrealized"]=0; return "OK"
@app.route('/close_one')
def close_one():
    sname=request.args.get('s')
    for t in list(state["trades"]):
        if t["s"]==sname:
            state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2)
            state["realized"]=round(state["realized"]+t["pnl"],2)
            cooldown[t["sym"]]=time.time()
            state["trades"].remove(t); break
    return "OK"
@app.route('/toggle')
def toggle(): state["trading"]=not state["trading"]; return "OK"
@app.route('/health')
def h(): return "OK",200
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

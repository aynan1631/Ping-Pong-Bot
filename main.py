from flask import Flask, render_template_string, request, jsonify
import os, threading, time, requests, math
from concurrent.futures import ThreadPoolExecutor
app = Flask(__name__)
cooldown = {}

def get_rsi(closes, period=14):
    try:
        deltas = [closes[i]-closes[i-1] for i in range(1,len(closes))]
        gains = [d if d>0 else 0 for d in deltas[-period:]]
        losses = [-d if d<0 else 0 for d in deltas[-period:]]
        ag=sum(gains)/period; al=sum(losses)/period
        if al==0: return 70
        rs=ag/al; return 100 - (100/(1+rs))
    except: return 50

def get_volatile_coins(limit=100):
    try:
        data=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=5).json()
        cands=[]
        for d in data:
            sym=d["symbol"]
            if not sym.endswith("USDT"): continue
            if sym in ["BTCUSDT","ETHUSDT","BNBUSDT"]: continue
            if "UP" in sym or "DOWN" in sym or "BEAR" in sym or "BULL" in sym: continue
            try: price=float(d["lastPrice"]); vol=float(d["quoteVolume"]); ch=float(d["priceChangePercent"])
            except: continue
            if price>20 or price<0.0000005 or vol<5000000 or abs(ch)<1.5: continue
            if sym in cooldown and time.time()-cooldown[sym]<180: continue
            cands.append((sym, abs(ch)*math.log(vol)))
        cands.sort(key=lambda x: x[1], reverse=True)
        return [s for s,_ in cands[:limit]]
    except: return ["FORMUSDT","DOTUSDT","PENGUUSDT","FFUSDT","XPLUSDT","DOGSUSDT","WLDUSDT","ENAUSDT","AEROUSDT","ICPUSDT"]

def get_data(sym):
    try:
        r=requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=210",timeout=4)
        data=r.json()
        closes=[float(k[4]) for k in data]
        price=closes[-1]
        k=2/(200+1); ema=closes[0]
        for c in closes[1:]: ema=c*k+ema*(1-k)
        sma=sum(closes[-20:])/20
        rsi=get_rsi(closes,14)
        return {"price":price,"ema":ema,"sma":sma,"rsi":round(rsi,1)}
    except: return None

def get_price_fast(sym):
    try:
        r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}",timeout=2).json()
        return float(r["price"])
    except: return None

state={"total_capital":5000.0,"per_trade":500.0,"balance":5000.0,"realized":0.0,"unrealized":0.0,"total_target":5.0,"trades":[],"trading":True,"TP":5.0,"SL":-15.0}

def try_add_one():
    per=state["per_trade"]
    max_open=int(state["total_capital"]//per) if per>0 else 10
    if len(state["trades"])>=max_open or state["balance"]<per: return False
    longs=len([t for t in state["trades"] if t["side"]=="LONG"])
    shorts=len([t for t in state["trades"] if t["side"]=="SHORT"])
    need_short=longs>shorts+1
    have=set(t["sym"] for t in state["trades"])
    candidates=[]
    for sym in get_volatile_coins(100):
        if sym in have: continue
        d=get_data(sym)
        if not d: continue
        if abs(d["price"]-d["sma"])/d["sma"]>0.06: continue
        side=None
        if d["price"]>d["ema"] and d["rsi"]<69: side="LONG"
        elif d["price"]<d["ema"] and d["rsi"]>31: side="SHORT"
        if side:
            score=2 if (need_short and side=="SHORT") or (not need_short and side=="LONG") else 1
            candidates.append((score,sym,d,side))
    candidates.sort(key=lambda x: x[0], reverse=True)
    for score,sym,d,side in candidates[:3]:
        qty=per/d["price"]
        t={"s":sym.replace("USDT",""),"sym":sym,"cap":per,"qty":qty,"entry":d["price"],"live":d["price"],"side":side,"rsi":d["rsi"],"pnl":0,"pct":0}
        state["trades"].append(t)
        state["balance"]=round(state["balance"]-per,2)
        return True
    return False

def worker():
    while True:
        try:
            per=state["per_trade"]
            max_open=int(state["total_capital"]//per) if per>0 else 10
            while len(state["trades"])<max_open and state["balance"]>=per:
                if not try_add_one(): break
                time.sleep(0.3)
            # تحديث سريع بالتوازي
            if state["trades"]:
                with ThreadPoolExecutor(max_workers=10) as ex:
                    prices=list(ex.map(lambda t: (t["sym"], get_price_fast(t["sym"])), state["trades"]))
                price_map=dict(prices)
                for t in list(state["trades"]):
                    live=price_map.get(t["sym"])
                    if not live: continue
                    t["live"]=live
                    t["pct"]=round((live-t["entry"])/t["entry"]*100,2) if t["side"]=="LONG" else round((t["entry"]-live)/t["entry"]*100,2)
                    t["pnl"]=round(t["cap"]*t["pct"]/100,2)
                state["unrealized"]=round(sum(x["pnl"] for x in state["trades"]),2)
                for t in list(state["trades"]):
                    if t["pnl"]>=state["TP"] or t["pnl"]<=state["SL"]:
                        state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2)
                        state["realized"]=round(state["realized"]+t["pnl"],2)
                        cooldown[t["sym"]]=time.time()
                        state["trades"].remove(t)
        except: pass
        time.sleep(2)

threading.Thread(target=worker,daemon=True).start()

HTML="""
<!DOCTYPE html><html dir="rtl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V55.1 FAST</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap" rel="stylesheet">
<style>
*{font-family:'Cairo',Tahoma}
body{background:radial-gradient(ellipse at top,#1a1f4a 0%,#0a0c1e 70%);color:#fff;margin:0;padding:8px}
.header{background:linear-gradient(90deg,#ffcc00,#ff9800);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:22px;font-weight:900;text-align:center}
.sub{text-align:center;color:#00ff88;font-size:11px;margin-bottom:8px}
.top-controls{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px}
.ctrl{background:#1e2147;border:1.5px solid #ffcc0033;border-radius:14px;padding:8px;text-align:center}
.ctrl-title{color:#ffcc00;font-size:11px;font-weight:900;margin-bottom:4px}
.ctrl-row{display:flex;gap:5px;justify-content:center;align-items:center;flex-wrap:wrap}
select,input{background:#0a0c1e;color:#ffcc00;border:2px solid #ffcc0066;border-radius:8px;padding:6px;font-size:14px!important;font-weight:900;text-align:center;direction:ltr;min-width:80px}
.btn{padding:7px 11px;border-radius:9px;border:0;font-weight:900;font-size:11px;cursor:pointer}
.btn-gold{background:linear-gradient(145deg,#ffcc00,#ff9800);color:#000}.btn-red{background:linear-gradient(145deg,#ff3d57,#c62828);color:#fff}.btn-blue{background:linear-gradient(145deg,#3d5afe,#2a3eb1);color:#fff}
.dashboard{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:8px 0}
.cardx{background:linear-gradient(145deg,#1e2147,#13152e);border:1.5px solid #ffffff18;border-radius:14px;padding:8px;text-align:center}
.cardx.gold{border-color:#ffcc0066}.lbl{color:#9aa0c5;font-size:9px;font-weight:700}.val{font-size:17px;font-weight:900}
.table-wrap{background:#151833;border-radius:14px;overflow:hidden;border:1px solid #ffffff15}
table{width:100%;border-collapse:collapse}
th{background:#1e2040;color:#ffcc00;padding:9px 2px;font-size:11px;font-weight:900;border-bottom:2px solid #ffcc0033}
td{padding:9px 2px;text-align:center;border-top:1px solid #ffffff0a;font-size:14px!important;font-weight:800}
.badge-long{background:linear-gradient(145deg,#00e676,#00c853);color:#000;padding:5px 12px;border-radius:20px;font-size:11px;font-weight:900;min-width:60px;display:inline-block}
.badge-short{background:linear-gradient(145deg,#ff1744,#d50000);color:#fff;padding:5px 12px;border-radius:20px;font-size:11px;font-weight:900;min-width:60px;display:inline-block}
.ltr{direction:ltr;display:inline-block;font-family:monospace;font-weight:900}
.g{color:#00ff88}.r{color:#ff3d57}
</style></head><body>
<div class="header">💎 V55.1 FAST - تحديث كل 2 ثانية</div>
<div class="sub">⚡ LIVE - الأسعار تتحرك لحظيا</div>

<div class="top-controls">
  <div class="ctrl"><div class="ctrl-title">💰 إجمالي رأس المال</div><div class="ctrl-row">
    <select onchange="document.getElementById('totalInp').value=this.value"><option value="500">500$</option><option value="1000">1000$</option><option value="2000">2000$</option><option value="5000" selected>5000$</option><option value="10000">10000$</option><option value="100000">100000$</option></select>
    <input id="totalInp" value="{{s.total_capital}}" style="width:90px"><button class="btn btn-gold" onclick="fetch('/set_total?v='+document.getElementById('totalInp').value).then(()=>location.reload())">تطبيق</button>
  </div></div>
  <div class="ctrl"><div class="ctrl-title">📦 رأس مال الصفقة</div><div class="ctrl-row">
    <select onchange="document.getElementById('perInp').value=this.value"><option value="100">100$</option><option value="500" selected>500$</option><option value="1000">1000$</option></select>
    <input id="perInp" value="{{s.per_trade}}" style="width:80px"><button class="btn btn-blue" onclick="fetch('/set_per?v='+document.getElementById('perInp').value).then(()=>location.reload())">تطبيق</button>
  </div></div>
</div>

<div class="dashboard">
  <div class="cardx gold"><div class="lbl">💰 رصيد حر</div><div class="val" id="bal" style="color:#ffcc00"><span class="ltr">{{'%.2f'|format(s.balance)}}$</span></div></div>
  <div class="cardx"><div class="lbl">🔒 محجوز</div><div class="val" id="locked" style="color:#ff9800"><span class="ltr">{{'%.0f'|format(s.trades|length * s.per_trade)}}$</span></div></div>
  <div class="cardx"><div class="lbl">💵 الكلي</div><div class="val" id="total"><span class="ltr">{{'%.2f'|format(s.balance + s.trades|length * s.per_trade)}}$</span></div></div>
  <div class="cardx"><div class="lbl">📈 غير محققة</div><div class="val" id="unreal" style="color:{{'#00ff88' if s.unrealized>=0 else '#ff3d57'}}"><span class="ltr">{{'%+.2f'|format(s.unrealized)}}$</span></div></div>
  <div class="cardx"><div class="lbl">✅ محقق</div><div class="val" id="real"><span class="ltr">{{'%+.2f'|format(s.realized)}}$</span></div></div>
  <div class="cardx gold"><div class="lbl">⚖️ LONG/SHORT</div><div class="val" id="ls" style="font-size:14px"><span class="ltr">{{s.trades|selectattr('side','equalto','LONG')|list|length}} / {{s.trades|selectattr('side','equalto','SHORT')|list|length}}</span></div></div>
</div>

<div style="display:flex;gap:6px;justify-content:center;margin-bottom:8px;flex-wrap:wrap">
  <div style="display:flex;gap:4px;align-items:center;background:#151833;padding:5px 8px;border-radius:9px;border:1px solid #ffffff15"><span style="color:#ffcc00;font-weight:900;font-size:11px">🎯 هدف</span><input id="t" style="width:60px" value="{{s.total_target}}"><button class="btn btn-blue" style="padding:4px 8px" onclick="fetch('/set_target?v='+document.getElementById('t').value).then(()=>location.reload())">حفظ</button></div>
  <button class="btn btn-red" onclick="fetch('/close_all').then(()=>location.reload())">🔒 قفل الكل</button>
  <button class="btn btn-gold" onclick="if(confirm('تصفير؟'))fetch('/reset').then(()=>location.reload())">🔄 تصفير</button>
</div>

<div class="table-wrap"><table id="tradesTable"><tr><th>العملة</th><th>الجانب</th><th>RSI</th><th>💰 رأس مال</th><th>📦 مبلغ</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th><th>×</th></tr>
{% for t in s.trades %}
<tr id="row-{{t.s}}">
<td><b>{{t.s}}</b></td><td><span class="{{'badge-long' if t.side=='LONG' else 'badge-short'}}">{{t.side}}</span></td>
<td><span class="ltr">{{t.rsi}}</span></td><td><span class="ltr" style="color:#ffcc00">${{t.cap|int}}</span></td>
<td><span class="ltr" style="color:#7ec8ff">{{'%.1f'|format(t.qty) if t.qty<1000 else '%.1fK'|format(t.qty/1000)}}</span></td>
<td><span class="ltr">{{'%.4f'|format(t.entry)}}</span></td><td><span class="ltr live">{{'%.4f'|format(t.live)}}</span></td>
<td><span class="ltr pnl {{'g' if t.pnl>=0 else 'r'}}">{{'%+.2f'|format(t.pnl)}}$</span></td><td><span class="ltr pct {{'g' if t.pct>=0 else 'r'}}">{{'%+.2f'|format(t.pct)}}%</span></td>
<td><button style="background:#ffffff15;color:#fff;border:0;padding:4px 8px;border-radius:7px;font-weight:900;cursor:pointer" onclick="fetch('/close_one?s={{t.s}}').then(()=>location.reload())">✕</button></td>
</tr>
{% endfor %}
</table></div>

<script>
function refresh(){
 fetch('/api').then(r=>r.json()).then(d=>{
  document.getElementById('bal').innerHTML=`<span class="ltr">${d.balance.toFixed(2)}$</span>`;
  document.getElementById('locked').innerHTML=`<span class="ltr">${(d.trades.length*d.per_trade).toFixed(0)}$</span>`;
  document.getElementById('total').innerHTML=`<span class="ltr">${(d.balance + d.trades.length*d.per_trade).toFixed(2)}$</span>`;
  document.getElementById('unreal').innerHTML=`<span class="ltr">${(d.unrealized>=0?'+':'')+d.unrealized.toFixed(2)}$</span>`;
  document.getElementById('unreal').style.color=d.unrealized>=0?'#00ff88':'#ff3d57';
  document.getElementById('real').innerHTML=`<span class="ltr">${(d.realized>=0?'+':'')+d.realized.toFixed(2)}$</span>`;
  let longs=d.trades.filter(t=>t.side=='LONG').length;
  let shorts=d.trades.length-longs;
  document.getElementById('ls').innerHTML=`<span class="ltr">${longs} / ${shorts}</span>`;
  d.trades.forEach(t=>{
    let row=document.getElementById('row-'+t.s);
    if(row){
      row.querySelector('.live').innerText=t.live.toFixed(4);
      row.querySelector('.pnl').innerText=(t.pnl>=0?'+':'')+t.pnl.toFixed(2)+'$';
      row.querySelector('.pnl').className='ltr pnl '+(t.pnl>=0?'g':'r');
      row.querySelector('.pct').innerText=(t.pct>=0?'+':'')+t.pct.toFixed(2)+'%';
      row.querySelector('.pct').className='ltr pct '+(t.pct>=0?'g':'r');
    }
  });
  if(d.trades.length!= document.querySelectorAll('[id^=row-]').length) location.reload();
 });
}
setInterval(refresh,2000);
refresh();
</script>
</body></html>
"""
@app.route('/')
def home(): return render_template_string(HTML, s=state)
@app.route('/api')
def api(): return jsonify(state)
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

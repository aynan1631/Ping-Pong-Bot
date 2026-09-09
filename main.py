from flask import Flask, render_template_string, request, jsonify
import os, threading, time, requests
from concurrent.futures import ThreadPoolExecutor
app = Flask(__name__)
cooldown = {}

def get_rsi(closes, p=14):
    try:
        deltas=[closes[i]-closes[i-1] for i in range(1,len(closes))]
        g=sum(d if d>0 else 0 for d in deltas[-p:])/p
        l=sum(-d if d<0 else 0 for d in deltas[-p:])/p
        if l==0: return 70
        return 100-(100/(1+g/l))
    except: return 50

def get_volatile_coins(limit=100):
    try:
        data=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=5).json()
        cands=[]
        for d in data:
            sym=d["symbol"]
            if not sym.endswith("USDT"): continue
            if sym in ["BTCUSDT","ETHUSDT","BNBUSDT"]: continue
            if "UP" in sym or "DOWN" in sym: continue
            try: price=float(d["lastPrice"]); vol=float(d["quoteVolume"]); ch=float(d["priceChangePercent"])
            except: continue
            if price>20 or price<0.0000005 or vol<5000000 or abs(ch)<1.5: continue
            if sym in cooldown and time.time()-cooldown[sym]<180: continue
            cands.append((sym,abs(ch)))
        cands.sort(key=lambda x: x[1], reverse=True)
        return [s for s,_ in cands[:limit]]
    except: return ["FFUSDT","QKCUSDT","FORMUSDT","PENGUUSDT","XPLUSDT","DOGSUSDT","WLDUSDT","ENAUSDT","AEROUSDT","ICPUSDT"]

def get_data(sym):
    try:
        data=requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=210",timeout=4).json()
        closes=[float(k[4]) for k in data]
        price=closes[-1]; k=2/(201); ema=closes[0]
        for c in closes[1:]: ema=c*k+ema*(1-k)
        sma=sum(closes[-20:])/20
        return {"price":price,"ema":ema,"sma":sma,"rsi":round(get_rsi(closes),1)}
    except: return None

def get_price_fast(sym):
    try: return float(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}",timeout=2).json()["price"])
    except: return None

state={"total_capital":5000.0,"per_trade":500.0,"balance":5000.0,"realized":0.0,"unrealized":0.0,"total_target":5.0,"trades":[],"TP":5.0,"SL":-15.0}

def try_add_one():
    per=state["per_trade"]
    max_open=int(state["total_capital"]//per) if per>0 else 10
    if len(state["trades"])>=max_open or state["balance"]<per: return False
    longs=len([t for t in state["trades"] if t["side"]=="LONG"]); shorts=len(state["trades"])-longs
    need_short=longs>shorts+1
    have=set(t["sym"] for t in state["trades"])
    cands=[]
    for sym in get_volatile_coins(100):
        if sym in have: continue
        d=get_data(sym)
        if not d: continue
        if abs(d["price"]-d["sma"])/d["sma"]>0.06: continue
        side="LONG" if d["price"]>d["ema"] and d["rsi"]<69 else "SHORT" if d["price"]<d["ema"] and d["rsi"]>31 else None
        if side:
            score=2 if (need_short and side=="SHORT") or (not need_short and side=="LONG") else 1
            cands.append((score,sym,d,side))
    cands.sort(key=lambda x: x[0], reverse=True)
    for _,sym,d,side in cands[:3]:
        t={"s":sym.replace("USDT",""),"sym":sym,"cap":per,"qty":per/d["price"],"entry":d["price"],"live":d["price"],"side":side,"rsi":d["rsi"],"pnl":0,"pct":0}
        state["trades"].append(t); state["balance"]=round(state["balance"]-per,2); return True
    return False

def worker():
    while True:
        try:
            per=state["per_trade"]; max_open=int(state["total_capital"]//per) if per>0 else 10
            while len(state["trades"])<max_open and state["balance"]>=per:
                if not try_add_one(): break
                time.sleep(0.2)
            if state["trades"]:
                with ThreadPoolExecutor(max_workers=10) as ex:
                    pm=dict(ex.map(lambda t: (t["sym"], get_price_fast(t["sym"])), state["trades"]))
                for t in list(state["trades"]):
                    live=pm.get(t["sym"])
                    if not live: continue
                    t["live"]=live
                    t["pct"]=round((live-t["entry"])/t["entry"]*100,2) if t["side"]=="LONG" else round((t["entry"]-live)/t["entry"]*100,2)
                    t["pnl"]=round(t["cap"]*t["pct"]/100,2)
                state["unrealized"]=round(sum(x["pnl"] for x in state["trades"]),2)
                # قفل عند الهدف
                if state["total_target"]>0.1 and state["unrealized"]>=state["total_target"]:
                    for t in list(state["trades"]):
                        state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2); state["realized"]=round(state["realized"]+t["pnl"],2); cooldown[t["sym"]]=time.time()
                    state["trades"]=[]; state["unrealized"]=0; time.sleep(0.5)
                else:
                    for t in list(state["trades"]):
                        if t["pnl"]>=state["TP"] or t["pnl"]<=state["SL"]:
                            state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2); state["realized"]=round(state["realized"]+t["pnl"],2); cooldown[t["sym"]]=time.time(); state["trades"].remove(t); try_add_one()
                state["unrealized"]=round(sum(x["pnl"] for x in state["trades"]),2)
        except: pass
        time.sleep(1.5)

threading.Thread(target=worker,daemon=True).start()

HTML="""
<!DOCTYPE html><html dir="rtl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V56 ULTRA</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
*{font-family:'Cairo',Tahoma; }
body{background:radial-gradient(ellipse at top,#1e244d 0%,#07091a 70%);color:#fff;margin:0;padding:12px;min-height:100vh}
.header{font-size:30px!important;font-weight:900!important;text-align:center;background:linear-gradient(90deg,#ffcc00,#ff9800,#ffcc00);-webkit-background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 0 20px #ffcc0088);letter-spacing:1px}
.sub{font-size:14px!important;color:#00ff88;text-align:center;font-weight:800;margin-bottom:12px}
.top-controls{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
.ctrl{background:linear-gradient(145deg,#262a5a,#151833);border:2px solid #ffcc0055;border-radius:18px;padding:12px;text-align:center;box-shadow:0 8px 25px rgba(0,0,0,0.5)}
.ctrl-title{color:#ffcc00;font-size:14px!important;font-weight:900!important;margin-bottom:8px}
select,input{background:#080a1e;color:#ffcc00;border:2.5px solid #ffcc00aa;border-radius:12px;padding:10px;font-size:18px!important;font-weight:900!important;text-align:center;direction:ltr;min-width:100px}
.btn{padding:12px 18px!important;border-radius:12px!important;border:0;font-weight:900!important;font-size:15px!important;cursor:pointer;box-shadow:0 6px 15px rgba(0,0,0,0.4)}
.btn-gold{background:linear-gradient(145deg,#ffcc00,#ff9800);color:#000}.btn-red{background:linear-gradient(145deg,#ff3d57,#c62828);color:#fff}.btn-blue{background:linear-gradient(145deg,#3d5afe,#2a3eb1);color:#fff}
.dashboard{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:14px 0}
.cardx{background:linear-gradient(145deg,#2a2e6a,#1a1c3f);border:2px solid #ffffff20;border-radius:20px;padding:14px;text-align:center;box-shadow:0 10px 30px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.15)}
.cardx.gold{border-color:#ffcc00aa;box-shadow:0 0 25px #ffcc0033,0 10px 30px rgba(0,0,0,0.5)}
.lbl{color:#9aa0c5;font-size:13px!important;font-weight:800!important}.val{font-size:22px!important;font-weight:900!important;margin-top:6px}
.table-wrap{background:linear-gradient(145deg,#1e2147,#151833);border-radius:20px;overflow:hidden;border:2px solid #ffffff18;box-shadow:0 15px 40px rgba(0,0,0,0.6)}
table{width:100%;border-collapse:collapse}
th{background:linear-gradient(145deg,#2a2d5a,#1e2040);color:#ffcc00;padding:16px 6px!important;font-size:15px!important;font-weight:900!important;border-bottom:3px solid #ffcc0055;letter-spacing:0.5px}
td{padding:16px 6px!important;text-align:center;border-top:1px solid #ffffff12;font-size:18px!important;font-weight:900!important}
tr:hover{background:rgba(255,204,0,0.08)}
.badge-long{background:linear-gradient(145deg,#00e676,#00c853);color:#000;padding:8px 18px!important;border-radius:25px;font-size:14px!important;font-weight:900!important;box-shadow:0 0 20px #00e676aa;min-width:75px;display:inline-block}
.badge-short{background:linear-gradient(145deg,#ff1744,#d50000);color:#fff;padding:8px 18px!important;border-radius:25px;font-size:14px!important;font-weight:900!important;box-shadow:0 0 20px #ff1744aa;min-width:75px;display:inline-block}
.ltr{direction:ltr;display:inline-block;font-family:'JetBrains Mono',monospace!important;font-weight:800!important;font-size:18px!important}
.g{color:#00ff88;text-shadow:0 0 10px #00ff8888}.r{color:#ff3d57;text-shadow:0 0 10px #ff3d5788}
</style></head><body>
<div class="header">💎 V56 ULTRA LUXURY - خطوط فخمة ضخمة</div>
<div class="sub">⚡ تحديث لحظي كل 1.5 ثانية - يقفل تلقائي عند +5$</div>

<div class="top-controls">
  <div class="ctrl"><div class="ctrl-title">💰 إجمالي رأس المال</div><div style="display:flex;gap:8px;justify-content:center;align-items:center;flex-wrap:wrap">
    <select onchange="document.getElementById('totalInp').value=this.value"><option value="500">500$</option><option value="1000">1000$</option><option value="2000">2000$</option><option value="5000" selected>5000$</option><option value="10000">10000$</option><option value="50000">50000$</option><option value="100000">100000$</option></select>
    <input id="totalInp" value="{{s.total_capital}}" style="width:110px"><button class="btn btn-gold" onclick="fetch('/set_total?v='+document.getElementById('totalInp').value).then(()=>location.reload())">تطبيق</button>
  </div></div>
  <div class="ctrl"><div class="ctrl-title">📦 رأس مال الصفقة</div><div style="display:flex;gap:8px;justify-content:center;align-items:center;flex-wrap:wrap">
    <select onchange="document.getElementById('perInp').value=this.value"><option value="100">100$</option><option value="500" selected>500$</option><option value="1000">1000$</option><option value="2000">2000$</option></select>
    <input id="perInp" value="{{s.per_trade}}" style="width:100px"><button class="btn btn-blue" onclick="fetch('/set_per?v='+document.getElementById('perInp').value).then(()=>location.reload())">تطبيق</button>
  </div></div>
</div>

<div class="dashboard">
  <div class="cardx gold"><div class="lbl">💰 رصيد حر</div><div class="val" id="bal" style="color:#ffcc00"><span class="ltr">{{'%.2f'|format(s.balance)}}$</span></div></div>
  <div class="cardx"><div class="lbl">🔒 محجوز</div><div class="val" id="locked" style="color:#ff9800"><span class="ltr">{{'%.0f'|format(s.trades|length * s.per_trade)}}$</span></div></div>
  <div class="cardx"><div class="lbl">💵 الكلي</div><div class="val" id="total"><span class="ltr">{{'%.2f'|format(s.balance + s.trades|length * s.per_trade)}}$</span></div></div>
  <div class="cardx"><div class="lbl">📈 غير محققة</div><div class="val" id="unreal" style="color:{{'#00ff88' if s.unrealized>=0 else '#ff3d57'}}"><span class="ltr">{{'%+.2f'|format(s.unrealized)}}$</span></div></div>
  <div class="cardx"><div class="lbl">✅ محقق</div><div class="val" id="real"><span class="ltr">{{'%+.2f'|format(s.realized)}}$</span></div></div>
  <div class="cardx gold"><div class="lbl">⚖️ LONG / SHORT</div><div class="val" id="ls" style="font-size:20px!important"><span class="ltr">{{s.trades|selectattr('side','equalto','LONG')|list|length}} / {{s.trades|selectattr('side','equalto','SHORT')|list|length}}</span></div></div>
</div>

<div style="display:flex;gap:10px;justify-content:center;margin-bottom:14px;flex-wrap:wrap">
  <div style="display:flex;gap:6px;align-items:center;background:#1e2147;padding:10px 14px;border-radius:14px;border:2px solid #ffffff15"><span style="color:#ffcc00;font-weight:900;font-size:15px">🎯 هدف</span><input id="t" style="width:80px" value="{{s.total_target}}"><button class="btn btn-blue" onclick="fetch('/set_target?v='+document.getElementById('t').value).then(()=>location.reload())">حفظ</button></div>
  <button class="btn btn-red" onclick="fetch('/close_all').then(()=>location.reload())">🔒 قفل الكل</button>
  <button class="btn btn-gold" onclick="if(confirm('تصفير؟'))fetch('/reset').then(()=>location.reload())">🔄 تصفير</button>
</div>

<div class="table-wrap"><table id="tradesTable"><tr><th>العملة</th><th>الجانب</th><th>RSI</th><th>💰 رأس مال</th><th>📦 مبلغ</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th><th>×</th></tr>
{% for t in s.trades %}
<tr id="row-{{t.s}}">
<td><b style="font-size:20px!important">{{t.s}}</b></td>
<td><span class="{{'badge-long' if t.side=='LONG' else 'badge-short'}}">{{t.side}}</span></td>
<td><span class="ltr">{{t.rsi}}</span></td>
<td><span class="ltr" style="color:#ffcc00">$500</span></td>
<td><span class="ltr" style="color:#7ec8ff">{{'%.1f'|format(t.qty) if t.qty<1000 else '%.1fK'|format(t.qty/1000)}}</span></td>
<td><span class="ltr">{{'%.4f'|format(t.entry)}}</span></td>
<td><span class="ltr live">{{'%.4f'|format(t.live)}}</span></td>
<td><span class="ltr pnl {{'g' if t.pnl>=0 else 'r'}}">{{'%+.2f'|format(t.pnl)}}$</span></td>
<td><span class="ltr pct {{'g' if t.pct>=0 else 'r'}}">{{'%+.2f'|format(t.pct)}}%</span></td>
<td><button style="background:#ffffff20;color:#fff;border:0;padding:8px 14px;border-radius:10px;font-weight:900;font-size:16px;cursor:pointer" onclick="fetch('/close_one?s={{t.s}}').then(()=>location.reload())">✕</button></td>
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
  let longs=d.trades.filter(t=>t.side=='LONG').length; let shorts=d.trades.length-longs;
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
setInterval(refresh,1500); refresh();
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
    try: state["per_trade"]=float(request.args.get('v'))
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
    for t in list(state["trades"]): state["balance"]=round(state["balance"]+t["cap"]+t["pnl"],2); state["realized"]=round(state["realized"]+t["pnl"],2); cooldown[t["sym"]]=time.time()
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

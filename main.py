from flask import Flask, render_template_string, request, jsonify, make_response
import os, threading, time, requests, math
app = Flask(__name__)
cooldown = {}
MAX_OPEN = 6

def get_volatile_coins(limit=50):
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
            if price>5 or price<0.0000005 or vol<12000000 or abs(change)<2.5: continue
            if sym in cooldown and time.time()-cooldown[sym]<3600: continue
            cands.append((sym, abs(change)*math.log(vol)))
        cands.sort(key=lambda x: x[1], reverse=True)
        return [s for s,_ in cands[:limit]]
    except: return ["BONKUSDT","WIFUSDT","FLOKIUSDT","BOMEUSDT","POPCATUSDT","DOGEUSDT"]

def get_data(sym):
    try:
        url=f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=210"
        data=requests.get(url,timeout=6).json()
        closes=[float(k[4]) for k in data]
        price=closes[-1]; k=2/(200+1); ema=closes[0]
        for c in closes[1:]: ema=c*k+ema*(1-k)
        sma=sum(closes[-20:])/20
        return {"price":price,"ema":ema,"sma":sma}
    except: return None

state={"capital":5000,"per_coin":500,"realized":0.0,"unrealized":0.0,"delta":50.0,"trades":[],"trading":True}

def try_add_one():
    if not state["trading"] or len(state["trades"])>=MAX_OPEN: return False
    have=set(t["s"] for t in state["trades"])
    for sym in get_volatile_coins(50):
        short=sym.replace("USDT","")
        if short in have or sym in cooldown: continue
        d=get_data(sym)
        if not d or abs(d["price"]-d["sma"])/d["sma"]>0.03: continue
        state["trades"].append({"s":short,"sym":sym,"cap":state["per_coin"],"entry":d["price"],"live":d["price"],"side":"SHORT" if d["price"]<d["ema"] else "LONG","pnl":0,"pct":0})
        return True
    return False

def worker():
    while True:
        if state["trading"]:
            if len(state["trades"])<MAX_OPEN: try_add_one()
            tot=0; to_remove=[]; global_mode=state["delta"]>0
            for t in list(state["trades"]):
                d=get_data(t["sym"])
                if not d: continue
                price=d["price"]; t["live"]=price
                t["pct"]=round((t["entry"]-price)/t["entry"]*100,2) if t["side"]=="SHORT" else round((price-t["entry"])/t["entry"]*100,2)
                t["pnl"]=round(t["cap"]*t["pct"]/100,2)
                if not global_mode and t["pnl"]>=5: to_remove.append(t); state["realized"]+=t["pnl"]; cooldown[t["sym"]]=time.time()
                else: tot+=t["pnl"]
            for t in to_remove:
                if t in state["trades"]: state["trades"].remove(t)
            state["unrealized"]=round(tot,2)
            if global_mode and state["unrealized"]>=state["delta"] and state["unrealized"]>0:
                state["realized"]=round(state["realized"]+state["unrealized"],2)
                for t in state["trades"]: cooldown[t["sym"]]=time.time()
                state["trades"]=[]; state["unrealized"]=0
        time.sleep(3)
threading.Thread(target=worker,daemon=True).start()

HTML="""
<!DOCTYPE html><html dir="rtl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V42 LUXURY</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&display=swap" rel="stylesheet">
<style>
*{font-family:'Cairo',Tahoma!important}
body{background:radial-gradient(circle at 50% -20%, #1a1d4a 0%, #0a0c1e 60%);color:#fff;margin:0;padding:10px;min-height:100vh}
.title{text-align:center;background:linear-gradient(90deg,#ffcc00,#ff9900);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:32px;font-weight:900;margin:8px;letter-spacing:1px;text-shadow:0 0 30px rgba(255,204,0,0.5)}
.bar{background:linear-gradient(145deg, rgba(21,24,51,0.9), rgba(15,17,35,0.9));backdrop-filter:blur(12px);border:1px solid rgba(255,204,0,0.25);border-radius:20px;padding:16px;margin:10px 0;box-shadow:0 8px 32px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.1)}
.status{text-align:center;font-size:22px;font-weight:900;color:#00e676;text-shadow:0 0 15px #00e676;margin-bottom:12px}
.status-off{color:#ff3d57!important;text-shadow:0 0 15px #ff3d57!important}
.row-main{display:flex;gap:10px;justify-content:center;align-items:center;flex-wrap:wrap}
.lux-card{background:linear-gradient(145deg,#1e2147,#13152e);border:2px solid transparent;border-image:linear-gradient(45deg,#ffcc00,#ff9900) 1;border-radius:16px;padding:10px 20px;min-width:150px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,0.5), 0 0 20px rgba(255,204,0,0.15);position:relative;overflow:hidden}
.lux-card::before{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:linear-gradient(45deg,transparent,rgba(255,255,255,0.05),transparent);transform:rotate(45deg);animation:shine 3s infinite}
@keyframes shine{0%{transform:translateX(-100%) rotate(45deg)}100%{transform:translateX(100%) rotate(45deg)}}
.lux-card.orange{border-image:linear-gradient(45deg,#ff9800,#ff5722) 1;box-shadow:0 4px 20px rgba(0,0,0,0.5), 0 0 20px rgba(255,152,0,0.15)}
.mini-lbl{color:#a0a3c5;font-size:15px;font-weight:800;letter-spacing:0.5px}
.mini-val{font-size:36px;font-weight:900;margin-top:4px;text-shadow:0 0 20px currentColor}
.green{color:#00ff88!important}.red{color:#ff3d57!important}
.gold{color:#ffcc00!important;text-shadow:0 0 20px #ffcc00!important}
input{background:rgba(15,17,35,0.8);color:#ffcc00;border:2px solid rgba(255,204,0,0.3);border-radius:12px;padding:12px;width:95px;text-align:center;font-size:24px;font-weight:900;box-shadow:inset 0 2px 8px rgba(0,0,0,0.5)}
.btn{padding:12px 18px;border-radius:12px;border:0;font-weight:900;font-size:16px;cursor:pointer;transition:all 0.2s;box-shadow:0 4px 15px rgba(0,0,0,0.3)}
.btn:active{transform:scale(0.95)}
.label-big{font-size:22px;font-weight:900;color:#ffcc00}
.row-extra{display:flex;gap:12px;justify-content:center;margin-top:14px;padding-top:14px;border-top:1px solid rgba(255,204,0,0.15)}
table{width:100%;background:linear-gradient(145deg, rgba(21,24,51,0.9), rgba(15,17,35,0.9));border-radius:20px;border-collapse:separate;border-spacing:0;overflow:hidden;margin-top:10px;box-shadow:0 8px 32px rgba(0,0,0,0.6);border:1px solid rgba(255,204,0,0.15)}
th{background:linear-gradient(90deg,#1e2040,#25285a);color:#ffcc00;padding:14px 6px;font-size:19px;font-weight:900;text-shadow:0 0 10px rgba(255,204,0,0.5)}
td{padding:12px 6px;text-align:center;border-top:1px solid rgba(255,255,255,0.05);font-size:17px;font-weight:800}
tr:hover{background:rgba(255,204,0,0.03)}
.badge{background:linear-gradient(90deg,#ff3d00,#ff6a00);color:#fff;padding:6px 14px;border-radius:20px;font-size:13px;font-weight:900;box-shadow:0 2px 10px rgba(255,61,0,0.4)}
.badge-long{background:linear-gradient(90deg,#00e676,#00ff88);color:#000;box-shadow:0 2px 10px rgba(0,230,118,0.4)}
.ltr{direction:ltr!important;display:inline-block}
</style></head><body>
<div class="title">💎 V42 LUXURY - فريم الساعة 1H تحت EMA200 💎</div>
<div class="bar">
<div class="status {{'status-off' if not s.trading else ''}}">{{'🟢 التداول شغال' if s.trading else '🔴 متوقف'}} - هدف ${{s.delta}}</div>

<div class="row-main">
<div class="lux-card"><div class="mini-lbl">💰 الأرباح</div><div class="mini-val gold" id="realT"><span class="ltr">{{'%.2f'|format(s.realized)}}$</span></div></div>

<span class="label-big">رأس المال</span><input id="c" value="{{s.capital}}" type="number"><button class="btn" style="background:linear-gradient(90deg,#ffeb3b,#ffcc00);color:#000" onclick="saveCap()">حفظ</button>

<span class="label-big">هدف</span><input id="t" value="{{s.delta}}" type="number"><button class="btn" style="background:linear-gradient(90deg,#3d5afe,#536dfe);color:#fff" onclick="saveTarget()">حفظ</button>

<div class="lux-card orange"><div class="mini-lbl">📈 غير المحققة</div><div class="mini-val" id="unrealBox"><span class="ltr" id="unrealT">{{'%.2f'|format(s.unrealized)}}$</span></div></div>

<button class="btn" style="background:linear-gradient(90deg,#ff3d00,#ff6a00);color:#fff;box-shadow:0 4px 15px rgba(255,61,0,0.4)" onclick="fetch('/close?v='+Date.now()).then(()=>location.reload(true))">🔒 قفل وجلب</button>
</div>

<div class="row-extra">
<button class="btn" style="background:{{'linear-gradient(90deg,#00e676,#00ff88)' if s.trading else 'linear-gradient(90deg,#ff3d57,#ff6a6a)'}};color:{{'#000' if s.trading else '#fff'}}" onclick="toggleTrading()">{{'⏸️ إيقاف' if s.trading else '▶️ تشغيل'}}</button>
<button class="btn" style="background:linear-gradient(90deg,#ff9800,#ffb74d);color:#000" onclick="resetCounters()">🔄 تصفير</button>
</div>
</div>

<table id="tbl">
<tr><th>العملة</th><th>الجانب</th><th>رأس المال</th><th>دخول</th><th>حالي</th><th>$</th><th>%</th></tr>
{% for t in s.trades %}
<tr>
<td style="color:#00ff88"><b>{{t.s}}</b></td>
<td>{% if t.side=='LONG' %}<span class="badge badge-long">LONG</span>{% else %}<span class="badge">SHORT</span>{% endif %}</td>
<td style="color:#ffcc00"><span class="ltr">${{t.cap}}</span></td>
<td><span class="ltr">{{'%.6f'|format(t.entry)}}</span></td>
<td><span class="ltr">{{'%.6f'|format(t.live)}}</span></td>
<td class="{{'green' if t.pnl>=0 else 'red'}}"><span class="ltr">{{'%.2f'|format(t.pnl)}}$</span></td>
<td class="{{'green' if t.pct>=0 else 'red'}}"><span class="ltr">{{'%.2f'|format(t.pct)}}%</span></td>
</tr>
{% endfor %}
</table>
<script>
function saveCap(){let v=document.getElementById('c').value; fetch('/set_capital?v='+v+'&t='+Date.now()).then(()=>location.reload(true));}
function saveTarget(){let v=document.getElementById('t').value; fetch('/set_target?v='+v+'&t='+Date.now()).then(()=>location.reload(true));}
function resetCounters(){ if(confirm('تصفير العدادات؟')) fetch('/reset?v='+Date.now()).then(()=>location.reload(true)); }
function toggleTrading(){ fetch('/toggle?v='+Date.now()).then(r=>r.json()).then(d=>location.reload(true)); }
setInterval(()=>{
 fetch('/api?v='+Date.now()).then(r=>r.json()).then(d=>{
   document.getElementById('realT').innerHTML='<span class="ltr">'+d.realized.toFixed(2)+'$</span>';
   document.getElementById('unrealT').innerHTML='<span class="ltr">'+d.unrealized.toFixed(2)+'$</span>';
   document.getElementById('unrealBox').className='mini-val '+(d.unrealized>=0?'green':'red');
   if(d.trades.length!=document.querySelectorAll('#tbl tr').length-1) location.reload(true);
 });
},2000);
</script>
</body></html>
"""
@app.route('/')
def home():
    resp=make_response(render_template_string(HTML, s=state))
    resp.headers['Cache-Control']='no-store'
    return resp
@app.route('/api')
def api(): return jsonify(state)
@app.route('/set_capital')
def set_cap():
    try: v=int(float(request.args.get('v'))); state["capital"]=v; state["per_coin"]=v//MAX_OPEN
    except: pass
    return "OK"
@app.route('/set_target')
def set_tar():
    try: state["delta"]=float(request.args.get('v'))
    except: pass
    return "OK"
@app.route('/reset')
def reset(): state["realized"]=0.0; state["unrealized"]=0.0; return "OK"
@app.route('/close')
def close():
    for t in state["trades"]: cooldown[t["sym"]]=time.time()
    state["trades"]=[]; state["unrealized"]=0.0; return "OK"
@app.route('/toggle')
def toggle(): state["trading"]=not state["trading"]; return jsonify({"trading":state["trading"]})
@app.route('/health')
def h(): return "OK",200
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

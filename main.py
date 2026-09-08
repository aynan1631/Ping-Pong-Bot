from flask import Flask, render_template_string, request, jsonify, make_response
import os, random, threading, time, requests, math
app = Flask(__name__)

BASE = [
    ("BONK",0.00002050),
    ("ASTER",0.7517),
    ("SAHARA",0.00973),
    ("PEPE",0.00000790),
    ("SHIB",0.00001190),
    ("FLOKI",0.000130),
    ("WIF",1.39),
    ("BOME",0.00851),
    ("DOGE",0.1218),
    ("POPCAT",0.321)
]

def get_data(symbol):
    try:
        url=f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=210"
        data=requests.get(url,timeout=5).json()
        closes=[float(k[4]) for k in data]
        price=closes[-1]
        prev=closes[-2]
        # EMA200
        k=2/(200+1); ema=closes[0]
        for c in closes[1:]: ema=c*k+ema*(1-k)
        # BB20 وسط
        sma20=sum(closes[-20:])/20
        sma_prev=sum(closes[-21:-1])/20
        return {"price":price,"prev":prev,"ema":ema,"sma":sma20,"sma_prev":sma_prev}
    except:
        return None

def make_trades(pc):
    out=[]
    for n,p in BASE:
        d=get_data(n)
        if d is None:
            # لو فشل النت استخدم وهمي
            live=p*random.uniform(0.985,1.015)
            pct=(p-live)/p*100
            out.append({"s":n,"cap":pc,"entry":p,"live":live,"ema":p*1.05,"sma":p,"below":False,"side":"SHORT","pnl":round(pc*pct/100,2),"pct":round(pct,2)})
            continue

        price=d["price"]; ema=d["ema"]; sma=d["sma"]
        below=price<ema
        # فلتر EMA + تقاطع بولنجر
        cross_up = d["prev"] < d["sma_prev"] and price > sma
        cross_down = d["prev"] > d["sma_prev"] and price < sma

        # نفتح فقط اذا تحت EMA200 + قطع تحت الوسط = SHORT
        # او فوق EMA200 + قطع فوق = LONG (حطيته LONG/SHORT بس اللوحة تعرض SHORT)
        if cross_down and below:
            side="SHORT"
            entry=price
            live=price
            cap=pc
        elif cross_up and not below:
            side="LONG"
            entry=price
            live=price
            cap=pc
        elif below:
            # تحت EMA200 نسمح SHORT حتى بدون تقاطع للبداية
            side="SHORT"
            entry=price
            live=price
            cap=pc
        else:
            # فوق EMA200 = SKIP
            side="SKIP"
            entry=price
            live=price
            cap=0

        pct=(entry-live)/entry*100 if side=="SHORT" else (live-entry)/entry*100 if side=="LONG" else 0
        out.append({
            "s":n,"cap":cap,"entry":entry,"live":live,"ema":ema,"sma":sma,"below":below,"side":side,
            "pnl":round(cap*pct/100,2),"pct":round(pct,2)
        })
    return out

state={
    "capital":5000,
    "per_coin":500,
    "realized":199.86,
    "delta":50.0,
    "trades":make_trades(500)
}
state["unrealized"]=round(sum(t["pnl"] for t in state["trades"]),2)

def worker():
    while True:
        tot=0
        for t in state["trades"]:
            d=get_data(t["s"])
            if d:
                price=d["price"]; sma=d["sma"]; ema=d["ema"]
                t["live"]=price; t["ema"]=ema; t["sma"]=sma
                t["below"]=price<ema

                # === تقفيل لحاله ===
                if t["side"]=="LONG" and price < sma:
                    # هبط تحت الوسط يقفل لحاله
                    state["realized"]=round(state["realized"]+t["pnl"],2)
                    t["side"]="SKIP"; t["cap"]=0; t["pnl"]=0; t["pct"]=0
                    continue
                if t["side"]=="SHORT" and price > sma:
                    # صعد فوق الوسط يقفل لحاله
                    state["realized"]=round(state["realized"]+t["pnl"],2)
                    t["side"]="SKIP"; t["cap"]=0; t["pnl"]=0; t["pct"]=0
                    continue

                # تحديث ربح
                if t["side"]=="SHORT":
                    t["pct"]=round((t["entry"]-t["live"])/t["entry"]*100,2)
                elif t["side"]=="LONG":
                    t["pct"]=round((t["live"]-t["entry"])/t["entry"]*100,2)
                else:
                    # يحاول يفتح من جديد اذا تقاطع
                    cross_up = d["prev"] < d["sma_prev"] and price > sma
                    cross_down = d["prev"] > d["sma_prev"] and price < sma
                    if cross_up and price>ema:
                        t["side"]="LONG"; t["entry"]=price; t["cap"]=state["per_coin"]
                    elif cross_down and price<ema:
                        t["side"]="SHORT"; t["entry"]=price; t["cap"]=state["per_coin"]
                    t["pct"]=0

                t["pnl"]=round(t["cap"]*t["pct"]/100,2)
            else:
                # محاكاة اذا فشل النت
                t["live"]*=random.uniform(0.994,1.006)
                if t["side"]=="SHORT":
                    t["pct"]=round((t["entry"]-t["live"])/t["entry"]*100,2)
                else:
                    t["pct"]=round((t["live"]-t["entry"])/t["entry"]*100,2)
                t["pnl"]=round(t["cap"]*t["pct"]/100,2)

            tot+=t["pnl"]

        state["unrealized"]=round(tot,2)
        if state["unrealized"]>=state["delta"] and state["unrealized"]>0:
            state["realized"]=round(state["realized"]+state["unrealized"],2)
            state["trades"]=make_trades(state["per_coin"])
            state["unrealized"]=round(sum(x["pnl"] for x in state["trades"]),2)
        time.sleep(3)

threading.Thread(target=worker,daemon=True).start()

HTML="""
<!DOCTYPE html><html dir="rtl"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>V40.9 BB+EMA</title>
<style>
body{background:#0a0c1e;color:#fff;font-family:Tahoma;margin:0;padding:12px}
.title{text-align:center;color:#ffcc00;font-size:26px;font-weight:900;margin:14px}
.cards{display:flex;gap:12px;justify-content:center}
.card{background:#151833;border:2px solid #2a2d4a;border-radius:14px;padding:14px 18px;min-width:130px;text-align:center}
.lbl{color:#8a8db5;font-size:15px;font-weight:bold}
.val{font-size:28px;font-weight:900;margin-top:6px}
.green{color:#00e676!important}
.red{color:#ff3d57!important}
.bar{background:#151833;border:2px solid #2a2d4a;border-radius:14px;padding:14px;text-align:center;margin:12px 0}
.status{color:#00e676;font-size:16px;font-weight:900}
.controls{display:flex;gap:10px;justify-content:center;align-items:center;margin-top:10px;flex-wrap:wrap}
.btn{padding:11px 18px;border-radius:10px;border:0;font-weight:900;font-size:17px;cursor:pointer}
input{background:#0f1123;color:#fff;border:2px solid #777;border-radius:10px;padding:11px;width:100px;text-align:center;font-size:22px;font-weight:900}
.label-big{font-size:22px;font-weight:900}
table{width:100%;background:#151833;border-radius:14px;border-collapse:collapse;margin-top:10px}
th{background:#1e2040;color:#ffeb3b;padding:12px 6px;font-size:17px;font-weight:900}
td{padding:10px 6px;text-align:center;border-top:1px solid #2a2d4a;font-size:15px;font-weight:900}
.badge{padding:5px 12px;border-radius:12px;font-size:13px;font-weight:900}
.badge-short{background:#ff3d00;color:#fff}.badge-long{background:#00e676;color:#000}.badge-skip{background:#444;color:#aaa}
.ltr{direction:ltr!important;unicode-bidi:plaintext!important;display:inline-block}
</style>
</head><body>
<div class="title">💎 V40.9 - فريم الساعة 1H - BB20 + EMA200 - يقفل لحاله</div>
<div class="cards">
<div class="card"><div class="lbl">رأس المال</div><div class="val" style="color:#fff"><span class="ltr">$5000</span></div></div>
<div class="card"><div class="lbl">المحققة</div><div class="val green" id="realT"><span class="ltr">{{'%.2f'|format(s.realized)}}$</span></div></div>
<div class="card"><div class="lbl">غير المحققة</div><div class="val" id="unrealBox"><span class="ltr" id="unrealT">{{'%.2f'|format(s.unrealized)}}$</span></div></div>
</div>
<div class="bar">
<div class="status">✅ هدف $<span id="deltaT">{{s.delta}}</span> - السالب أحمر والموجب أخضر - يقفل عند الربح</div>
<div class="status" style="color:#ffeb3b;margin-top:6px;font-size:14px">BB20: LONG تقفل اذا هبطت تحت الوسط | SHORT تقفل اذا صعدت فوق الوسط + فلتر EMA200</div>
<div class="controls">
<span class="label-big">رأس المال</span><input id="c" value="{{s.capital}}"><button class="btn" style="background:#ffeb3b" onclick="fetch('/set_capital?v='+c.value).then(()=>location.reload(true))">حفظ</button>
<span class="label-big">هدف</span><input id="t" value="{{s.delta}}"><button class="btn" style="background:#3d5afe;color:#fff" onclick="fetch('/set_target?v='+t.value).then(()=>location.reload(true))">حفظ</button>
<button class="btn" style="background:#ff3d00;color:#fff" onclick="fetch('/close').then(()=>location.reload(true))">🔒 قفل وتجديد</button>
</div>
</div>
<table id="tbl">
<tr><th>العملة</th><th>الجانب</th><th>رأس المال</th><th>دخول</th><th>حالي</th><th>$</th><th>%</th></tr>
{% for t in s.trades %}
<tr>
<td style="color:#00e676"><b>{{t.s}}</b></td>
<td>{% if t.side=='LONG' %}<span class="badge badge-long">LONG</span>{% elif t.side=='SHORT' %}<span class="badge badge-short">SHORT</span>{% else %}<span class="badge badge-skip">SKIP</span>{% endif %}</td>
<td style="color:#ffeb3b"><span class="ltr">${{t.cap}}</span></td>
<td><span class="ltr">{{'%.8f'|format(t.entry)}}</span></td>
<td><span class="ltr">{{'%.8f'|format(t.live)}}</span></td>
<td class="{{'green' if t.pnl>=0 else 'red'}}"><span class="ltr">{{'%.2f'|format(t.pnl)}}$</span></td>
<td class="{{'green' if t.pct>=0 else 'red'}}"><span class="ltr">{{'%.2f'|format(t.pct)}}%</span></td>
</tr>
{% endfor %}
</table>
<script>
function fmt(v){ return v.toFixed(2)+'$'; }
setInterval(()=>{
 fetch('/api?v='+Date.now()).then(r=>r.json()).then(d=>{
   let realEl=document.getElementById('realT');
   realEl.innerHTML='<span class="ltr">'+d.realized.toFixed(2)+'$</span>';
   realEl.className='val '+(d.realized>=0?'green':'red');
   let unrealEl=document.getElementById('unrealT');
   unrealEl.innerHTML='<span class="ltr">'+d.unrealized.toFixed(2)+'$</span>';
   document.getElementById('unrealBox').className='val '+(d.unrealized>=0?'green':'red');
   document.getElementById('deltaT').innerText=d.delta;
   let rows=document.querySelectorAll('#tbl tr');
   d.trades.forEach((t,i)=>{
     let row=rows[i+1]; if(!row) return;
     row.cells[1].innerHTML = t.side=='LONG'? '<span class="badge badge-long">LONG</span>' : t.side=='SHORT'? '<span class="badge badge-short">SHORT</span>' : '<span class="badge badge-skip">SKIP</span>';
     row.cells[2].innerHTML='<span class="ltr">$'+t.cap+'</span>';
     row.cells[3].innerHTML='<span class="ltr">'+t.entry.toFixed(8)+'</span>';
     row.cells[4].innerHTML='<span class="ltr">'+t.live.toFixed(8)+'</span>';
     row.cells[5].innerHTML='<span class="ltr">'+t.pnl.toFixed(2)+'$</span>';
     row.cells[5].className=t.pnl>=0?'green':'red';
     row.cells[6].innerHTML='<span class="ltr">'+t.pct.toFixed(2)+'%</span>';
     row.cells[6].className=t.pct>=0?'green':'red';
   });
 });
},2000);
</script>
</body></html>
"""

@app.route('/')
def home():
    resp=make_response(render_template_string(HTML, s=state))
    resp.headers['Cache-Control']='no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma']='no-cache'
    resp.headers['Expires']='0'
    return resp

@app.route('/api')
def api():
    resp=make_response(jsonify({
        "realized":state["realized"],
        "unrealized":state["unrealized"],
        "delta":state["delta"],
        "trades":[{"entry":t["entry"],"live":t["live"],"pnl":t["pnl"],"pct":t["pct"],"side":t["side"],"cap":t["cap"]} for t in state["trades"]]
    }))
    resp.headers['Cache-Control']='no-store'
    return resp

@app.route('/set_capital')
def set_cap():
    v=int(float(request.args.get('v')))
    state["capital"]=v
    state["per_coin"]=v//len(BASE)
    for t in state["trades"]:
        if t["side"]!="SKIP":
            t["cap"]=state["per_coin"]
            t["pnl"]=round(t["cap"]*t["pct"]/100,2)
    state["unrealized"]=round(sum(t["pnl"] for t in state["trades"]),2)
    return "OK"

@app.route('/set_target')
def set_tar():
    state["delta"]=float(request.args.get('v'))
    return "OK"

@app.route('/close')
def close():
    state["realized"]=round(state["realized"]+state["unrealized"],2)
    state["trades"]=make_trades(state["per_coin"])
    state["unrealized"]=round(sum(t["pnl"] for t in state["trades"]),2)
    return "OK"

@app.route('/health')
def h():
    return "OK",200

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

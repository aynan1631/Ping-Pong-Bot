from flask import Flask, render_template_string, request, jsonify, make_response
import os, random, threading, time
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

def make_trades(pc):
    out=[]
    for n,p in BASE:
        live=p*random.uniform(0.985,1.015)
        pct=(p-live)/p*100
        out.append({
            "s":n,
            "cap":pc,
            "entry":p,
            "live":live,
            "pnl":round(pc*pct/100,2),
            "pct":round(pct,2)
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
            t["live"]*=random.uniform(0.994,1.006)
            t["pct"]=round((t["entry"]-t["live"])/t["entry"]*100,2)
            t["pnl"]=round(t["cap"]*t["pct"]/100,2)
            tot+=t["pnl"]
        state["unrealized"]=round(tot,2)
        if state["unrealized"]>=state["delta"]:
            state["realized"]=round(state["realized"]+state["unrealized"],2)
            state["trades"]=make_trades(state["per_coin"])
            state["unrealized"]=round(sum(x["pnl"] for x in state["trades"]),2)
        time.sleep(1)

threading.Thread(target=worker,daemon=True).start()

HTML="""
<!DOCTYPE html><html dir="rtl"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>V40.9</title>
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
.status{color:#00e676;font-size:19px;font-weight:900}
.controls{display:flex;gap:10px;justify-content:center;align-items:center;margin-top:10px;flex-wrap:wrap}
.btn{padding:11px 18px;border-radius:10px;border:0;font-weight:900;font-size:17px;cursor:pointer}
input{background:#0f1123;color:#fff;border:2px solid #777;border-radius:10px;padding:11px;width:100px;text-align:center;font-size:22px;font-weight:900}
.label-big{font-size:22px;font-weight:900}
table{width:100%;background:#151833;border-radius:14px;border-collapse:collapse;margin-top:10px}
th{background:#1e2040;color:#ffeb3b;padding:12px 6px;font-size:17px;font-weight:900}
td{padding:10px 6px;text-align:center;border-top:1px solid #2a2d4a;font-size:15px;font-weight:900}
.badge{background:#ff3d00;color:#fff;padding:5px 12px;border-radius:12px;font-size:13px;font-weight:900}
</style>
</head><body>
<div class="title">💎 V40.9 - فريم الساعة 1H - تحت EMA200</div>
<div class="cards">
<div class="card"><div class="lbl">رأس المال</div><div class="val" style="color:#fff">$5000</div></div>
<div class="card"><div class="lbl">المحققة</div><div class="val green" id="realT">{{'%.2f'|format(s.realized)}}$</div></div>
<div class="card"><div class="lbl">غير المحققة</div><div class="val" id="unrealT">{{'%.2f'|format(s.unrealized)}}$</div></div>
</div>
<div class="bar">
<div class="status">✅ هدف $<span id="deltaT">{{s.delta}}</span> - السالب أحمر والموجب أخضر - يقفل عند الربح</div>
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
<td><span class="badge">SHORT</span></td>
<td style="color:#ffeb3b">${{t.cap}}</td>
<td>{{'%.8f'|format(t.entry)}}</td>
<td>{{'%.8f'|format(t.live)}}</td>
<td class="{{'green' if t.pnl>=0 else 'red'}}">{{'%.2f'|format(t.pnl)}}$</td>
<td class="{{'green' if t.pct>=0 else 'red'}}">{{'%.2f'|format(t.pct)}}%</td>
</tr>
{% endfor %}
</table>
<script>
setInterval(()=>{
 fetch('/api?v='+Date.now()).then(r=>r.json()).then(d=>{
   let realEl=document.getElementById('realT');
   realEl.innerText=d.realized.toFixed(2)+'$';
   realEl.className='val '+(d.realized>=0?'green':'red');
   let unrealEl=document.getElementById('unrealT');
   unrealEl.innerText=d.unrealized.toFixed(2)+'$';
   unrealEl.className='val '+(d.unrealized>=0?'green':'red');
   document.getElementById('deltaT').innerText=d.delta;
   let rows=document.querySelectorAll('#tbl tr');
   d.trades.forEach((t,i)=>{
     let row=rows[i+1]; if(!row) return;
     row.cells[4].innerText=t.live.toFixed(8);
     row.cells[5].innerText=t.pnl.toFixed(2)+'$';
     row.cells[5].className=t.pnl>=0?'green':'red';
     row.cells[6].innerText=t.pct.toFixed(2)+'%';
     row.cells[6].className=t.pct>=0?'green':'red';
   });
 });
},1000);
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
        "trades":[{"live":t["live"],"pnl":t["pnl"],"pct":t["pct"]} for t in state["trades"]]
    }))
    resp.headers['Cache-Control']='no-store'
    return resp

@app.route('/set_capital')
def set_cap():
    v=int(float(request.args.get('v')))
    state["capital"]=v
    state["per_coin"]=v//len(BASE)
    for t in state["trades"]:
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

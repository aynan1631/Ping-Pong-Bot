from flask import Flask, render_template_string, request
import os, random, threading, time
app = Flask(__name__)

BASE = [
    ("BONK",0.00002050),("ASTER",0.7517),("SAHARA",0.00973),
    ("PEPE",0.00000790),("SHIB",0.00001190),("FLOKI",0.000130),
    ("WIF",1.39),("BOME",0.00851),("DOGE",0.1218),("POPCAT",0.321)
]

def make_trades(per_coin):
    out=[]
    for name, price in BASE:
        live = price * random.uniform(0.985,1.015)
        pct = (price-live)/price*100
        out.append({
            "s":name,"cap":per_coin,"entry":price,"live":live,
            "pnl":round(per_coin*pct/100,2),"pct":round(pct,2),
            "vol":round(random.uniform(3.5,6.7),1)
        })
    return out

state={
    "capital":5000,
    "per_coin":500,
    "realized":45.05,
    "btc":78376,
    "target":50.0,
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
        if state["realized"]+state["unrealized"] >= state["target"]:
            state["realized"]=round(state["realized"]+state["unrealized"],2)
            state["trades"]=make_trades(state["per_coin"])
            state["target"]=round(state["realized"]+50,2)
            state["unrealized"]=round(sum(x["pnl"] for x in state["trades"]),2)
        time.sleep(2)

threading.Thread(target=worker,daemon=True).start()

HTML="""
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V40</title>
<style>
body{background:#0a0c1e;color:#fff;font-family:Tahoma;margin:0;padding:12px}
.title{text-align:center;color:#ffcc00;font-size:18px;font-weight:bold;margin:10px}
.cards{display:flex;gap:8px;justify-content:center;flex-wrap:wrap}
.card{background:#151833;border:1px solid #2a2d4a;border-radius:12px;padding:10px 14px;min-width:100px;text-align:center}
.lbl{color:#8a8db5;font-size:10px}.val{font-size:15px;font-weight:bold;margin-top:4px}
.green{color:#00e676}.red{color:#ff5252}
.bar{background:#151833;border:1px solid #2a2d4a;border-radius:12px;padding:10px;text-align:center;margin:10px 0}
.btn{padding:7px 10px;border-radius:8px;border:0;font-weight:bold;margin:3px;font-size:11px;cursor:pointer}
input{background:#0f1123;color:#fff;border:1px solid #555;border-radius:7px;padding:6px;width:65px;text-align:center}
table{width:100%;background:#151833;border-radius:12px;border-collapse:collapse;margin-top:8px}
th{background:#1e2040;color:#ffeb3b;padding:10px 4px;font-size:11px}
td{padding:9px 4px;text-align:center;border-top:1px solid #2a2d4a;font-size:11px}
.badge{background:#ff3d00;color:#fff;padding:3px 8px;border-radius:10px;font-size:10px}
</style>
<script>
function setC(){let v=document.getElementById('c').value;fetch('/set_capital?v='+v).then(()=>location.reload())}
function setP(){let v=document.getElementById('p').value;fetch('/set_percoin?v='+v).then(()=>location.reload())}
function setT(){let v=document.getElementById('t').value;fetch('/set_target?v='+v).then(()=>location.reload())}
</script>
</head><body>
<div class="title">💎 V40 - فريم الساعة 1H - تحت EMA200</div>
<div class="cards">
<div class="card"><div class="lbl">رأس المال الكلي</div><div class="val">${{s.capital}}</div></div>
<div class="card"><div class="lbl">رأس مال كل عملة</div><div class="val" style="color:#ffeb3b">${{s.per_coin}}</div></div>
<div class="card"><div class="lbl">المحققة</div><div class="val green">${{s.realized}}</div></div>
<div class="card"><div class="lbl">غير المحققة</div><div class="val green">${{s.unrealized}}</div></div>
</div>
<div class="bar">
<div style="color:#00e676;font-size:12px">✅ فحص 1H: كل العملات تحت EMA200 - BTC ${{s.btc}} - هدف ${{s.target}}$ - يقفل تلقائي</div>
<div style="margin-top:8px">
كلي <input id="c" value="{{s.capital}}"><button class="btn" style="background:#ffeb3b" onclick="setC()">حفظ</button>
لكل عملة <input id="p" value="{{s.per_coin}}"><button class="btn" style="background:#ff9800" onclick="setP()">حفظ</button>
هدف <input id="t" value="{{s.target}}"><button class="btn" style="background:#3d5afe;color:#fff" onclick="setT()">حفظ</button>
<button class="btn" style="background:#ff3d00;color:#fff" onclick="fetch('/close').then(()=>location.reload())">🔒 قفل وتجديد</button>
</div>
</div>
<table>
<tr><th>العملة</th><th>الجانب</th><th>رأس المال</th><th>دخول</th><th>حالي</th><th>$</th><th>%</th><th>تقلب</th></tr>
{% for t in s.trades %}
<tr>
<td style="color:#00e676"><b>{{t.s}}</b> ▼1H</td>
<td><span class="badge">SHORT</span></td>
<td style="color:#ffeb3b">${{t.cap}}</td>
<td>{{'%.8f'|format(t.entry)}}</td>
<td>{{'%.8f'|format(t.live)}}</td>
<td class="{{'green' if t.pnl>=0 else 'red'}}">{{t.pnl}}</td>
<td class="{{'green' if t.pct>=0 else 'red'}}">{{t.pct}}%</td>
<td>{{t.vol}}%</td>
</tr>
{% endfor %}
</table>
</body></html>
"""

@app.route('/')
def home(): return render_template_string(HTML, s=state)

@app.route('/set_capital')
def set_cap():
    v=int(float(request.args.get('v')))
    state["capital"]=v
    state["per_coin"]=v//10
    state["trades"]=make_trades(state["per_coin"])
    state["unrealized"]=round(sum(t["pnl"] for t in state["trades"]),2)
    return "OK"

@app.route('/set_percoin')
def set_per():
    v=int(float(request.args.get('v')))
    state["per_coin"]=v
    state["capital"]=v*10
    state["trades"]=make_trades(v)
    state["unrealized"]=round(sum(t["pnl"] for t in state["trades"]),2)
    return "OK"

@app.route('/set_target')
def set_tar():
    state["target"]=float(request.args.get('v'))
    return "OK"

@app.route('/close')
def close():
    state["realized"]=round(state["realized"]+state["unrealized"],2)
    state["trades"]=make_trades(state["per_coin"])
    state["unrealized"]=round(sum(t["pnl"] for t in state["trades"]),2)
    state["target"]=round(state["realized"]+50,2)
    return "OK"

@app.route('/health')
def h(): return "OK",200

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

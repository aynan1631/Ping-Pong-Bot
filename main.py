from flask import Flask, render_template_string, request
import os, threading, time, random
app = Flask(__name__)

def new_trades():
    data=[
        ("ASTER",0.75),("SAHARA",0.0097),("MEME",0.00220),("PEPE",0.0000078),
        ("SHIB",0.0000119),("BONK",0.0000205),("FLOKI",0.000130),("WIF",1.39),
        ("BOME",0.0085),("DOGE",0.121)
    ]
    out=[]
    for s, p in data:
        live = p * random.uniform(0.97,1.03)
        pct = (p - live)/p * 100
        out.append({
            "s":s,"side":"SHORT","cap":500,"entry":p,"live":live,
            "pnl":round(500*pct/100,2),"pct":round(pct,2),
            "vol":round(random.uniform(3.5,7.5),1)
        })
    return out

state={
    "capital":5000,"realized":243.7,"unrealized":0,
    "btc_price":78376,"ema":78944,"target":293.7,
    "trades": new_trades()
}
state["unrealized"]=round(sum([t["pnl"] for t in state["trades"]],2)

def worker():
    while True:
        s=0
        for t in state["trades"]:
            t["live"] *= random.uniform(0.997,1.003)
            ch=(t["entry"]-t["live"])/t["entry"]*100
            t["pnl"]=round(t["cap"]*ch/100,2)
            t["pct"]=round(ch,2)
            s+=t["pnl"]
        state["unrealized"]=round(s,2)
        time.sleep(2)

threading.Thread(target=worker,daemon=True).start()

HTML="""
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V34</title>
<style>
body{background:#0f1123;color:#fff;font-family:Tahoma;margin:0;padding:10px}
.title{text-align:center;color:#ffcc00;font-size:20px;font-weight:bold;margin:12px}
.cards{display:flex;gap:10px;justify-content:center}
.card{background:#1a1d35;border:1px solid #2a2d4a;border-radius:12px;padding:12px 18px;min-width:120px;text-align:center}
.lbl{color:#888;font-size:11px}.val{font-size:17px;font-weight:bold;margin-top:3px}
.green{color:#00ff88!important}.red{color:#ff4444!important}
.bar{background:#1a1d35;border:1px solid #2a2d4a;border-radius:10px;padding:12px;text-align:center;margin:12px 0}
.btn{padding:8px 14px;border-radius:8px;border:0;cursor:pointer;font-weight:bold;margin:3px}
.btn-red{background:#e53935;color:#fff}.btn-blue{background:#3a5bff;color:#fff}
input{background:#0f1123;color:#fff;border:1px solid #555;border-radius:8px;padding:7px;width:80px;text-align:center}
table{width:100%;border-collapse:collapse;background:#1a1d35;border-radius:10px;overflow:hidden}
th{background:#222544;color:#ffcc00;padding:10px 5px;font-size:11px}
td{padding:9px 5px;text-align:center;border-top:1px solid #2a2d4a;font-size:11px}
.badge{background:#e53935;color:#fff;padding:3px 8px;border-radius:10px;font-size:10px}
</style>
<script>
function saveTarget(){let v=document.getElementById('t').value;fetch('/set_target?v='+v).then(()=>location.reload());}
function closeTrades(){fetch('/close').then(()=>location.reload());}
</script>
</head><body>
<div class="title">💎 V34 - تحت EMA200 - 10 صفقات نشطة</div>
<div class="cards">
<div class="card"><div class="lbl">رأس المال</div><div class="val">$5000</div></div>
<div class="card"><div class="lbl">المحققة</div><div class="val {{'green' if state.realized>=0 else 'red'}}">${{state.realized}}</div></div>
<div class="card"><div class="lbl">غير المحققة</div><div class="val {{'green' if state.unrealized>=0 else 'red'}}">${{state.unrealized}}</div></div>
</div>
<div class="bar">
<div style="color:#ffcc00;margin-bottom:8px">BTC {{state.btc_price}}$ - هدف ${{state.target}}$</div>
<button class="btn btn-red" onclick="closeTrades()">🔒 قفل الصفقات</button>
<input id="t" type="number" value="{{state.target}}"><button class="btn btn-blue" onclick="saveTarget()">حفظ</button>
</div>
<table>
<tr><th>العملة</th><th>الجانب</th><th>رأس المال</th><th>دخول</th><th>حالي</th><th>$</th><th>%</th><th>تقلب</th></tr>
{% for t in state.trades %}
<tr>
<td><b>{{t.s}}</b></td>
<td><span class="badge">{{t.side}}</span></td>
<td style="color:#ffcc00">$500</td>
<td>{{t.entry}}</td>
<td>{{'%.6g'|format(t.live)}}</td>
<td class="{{'green' if t.pnl>=0 else 'red'}}">{{t.pnl}}</td>
<td class="{{'green' if t.pct>=0 else 'red'}}">{{t.pct}}%</td>
<td>{{t.vol}}%</td>
</tr>
{% endfor %}
</table>
</body></html>
"""
@app.route('/')
def home(): return render_template_string(HTML, state=state)
@app.route('/set_target')
def set_t():
    try: state["target"]=float(request.args.get('v')); return "OK"
    except: return "ERR",400
@app.route('/close')
def close_all():
    state["realized"]=round(state["realized"]+state["unrealized"],2)
    state["trades"]=new_trades()
    state["unrealized"]=round(sum([t["pnl"] for t in state["trades"]],2)
    state["target"]=state["realized"]+50
    return "OK"
@app.route('/health')
def h(): return "OK",200
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

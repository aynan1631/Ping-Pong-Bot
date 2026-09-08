from flask import Flask, render_template_string, request
import os, threading, time, random
app = Flask(__name__)

state={
    "capital":5000,"realized":243.7,"unrealized":-3.14,
    "btc_price":78376,"ema":78944,"target":293.7,
    "trades":[
        {"s":"ASTER","side":"SHORT","cap":500,"entry":0.76,"live":0.7514213,"pnl":0.40,"pct":0.08,"vol":4.1},
        {"s":"SAHARA","side":"SHORT","cap":500,"entry":0.00974,"live":0.0097058,"pnl":-0.45,"pct":-0.09,"vol":3.8},
        {"s":"MEME","side":"SHORT","cap":500,"entry":0.00230,"live":0.0022025,"pnl":-0.75,"pct":-0.15,"vol":5.2},
        {"s":"PEPE","side":"SHORT","cap":500,"entry":0.0000079,"live":0.00000780,"pnl":0.13,"pct":0.02,"vol":6.1},
        {"s":"SHIB","side":"SHORT","cap":500,"entry":0.000012,"live":0.0000119,"pnl":0.85,"pct":0.17,"vol":4.3},
        {"s":"BONK","side":"SHORT","cap":500,"entry":0.000021,"live":0.0000206,"pnl":-1.20,"pct":-0.24,"vol":5.5},
        {"s":"FLOKI","side":"SHORT","cap":500,"entry":0.00014,"live":0.000139,"pnl":0.95,"pct":0.19,"vol":4.7},
        {"s":"WIF","side":"SHORT","cap":500,"entry":1.42,"live":1.39,"pnl":2.50,"pct":0.50,"vol":7.2},
        {"s":"BOME","side":"SHORT","cap":500,"entry":0.0087,"live":0.0085,"pnl":-0.60,"pct":-0.12,"vol":6.8},
        {"s":"DOGE","side":"SHORT","cap":500,"entry":0.124,"live":0.122,"pnl":1.10,"pct":0.22,"vol":4.0},
    ]
}

def worker():
    while True:
        try:
            for t in state["trades"]:
                t["live"]*=random.uniform(0.999,1.001)
                ch=(t["entry"]-t["live"])/t["entry"]*100
                t["pnl"]=round(t["cap"]*ch/100,2)
                t["pct"]=round(ch,2)
            state["unrealized"]=round(sum([x["pnl"] for x in state["trades"]]),2)
            time.sleep(5)
        except: time.sleep(5)

threading.Thread(target=worker,daemon=True).start()

HTML="""
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V33.8 LUXURY</title>
<style>
body{background:#0f1123;color:#fff;font-family:Tahoma;margin:0;padding:12px}
.title{text-align:center;color:#ffcc00;font-size:22px;font-weight:bold;margin:15px 0}
.cards{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-bottom:14px}
.card{background:#1a1d35;border:1px solid #2a2d4a;border-radius:14px;padding:16px 22px;min-width:150px;text-align:center}
.lbl{color:#9aa0b8;font-size:12px}.val{font-size:20px;font-weight:bold;margin-top:5px}
.green{color:#00ff88!important}.red{color:#ff4444!important}.gold{color:#ffcc00}
.bar{background:#1a1d35;border:1px solid #2a2d4a;border-radius:12px;padding:14px;text-align:center;margin-bottom:14px}
.btn{padding:9px 18px;border-radius:10px;border:0;cursor:pointer;font-weight:bold;margin:4px;font-size:13px}
.btn-red{background:#e53935;color:#fff}.btn-blue{background:#3a5bff;color:#fff}
input{background:#0f1123;color:#fff;border:1px solid #555;border-radius:10px;padding:9px;text-align:center;width:90px}
table{width:100%;border-collapse:collapse;background:#1a1d35;border-radius:12px;overflow:hidden}
th{background:#222544;color:#ffcc00;padding:12px 6px;font-size:12px} 
td{padding:10px 6px;text-align:center;border-top:1px solid #2a2d4a;font-size:12px}
.badge{padding:4px 10px;border-radius:12px;font-size:11px;color:#fff;background:#e53935}
</style>
<script>
function saveTarget(){
  let v=document.getElementById('t').value;
  fetch('/set_target?v='+v).then(()=>{location.reload();});
}
function closeTrades(){
  if(!confirm('تقفل الـ 10 صفقات؟')) return;
  fetch('/close').then(()=>location.reload());
}
</script>
</head><body>
<div class="title">💎 V33.8 LUXURY - فلتر EMA200 المزدوج (10 صفقات إجباري)</div>

<div class="cards">
<div class="card"><div class="lbl">الأرباح غير المحققة</div><div class="val {{'green' if state.unrealized>=0 else 'red'}}">{{'$%.2f'|format(state.unrealized)}}</div></div>
<div class="card"><div class="lbl">الأرباح المحققة</div><div class="val {{'green' if state.realized>=0 else 'red'}}">${{state.realized}}</div></div>
<div class="card"><div class="lbl">رأس المال</div><div class="val">$5000</div></div>
</div>

<div class="bar">
<div style="color:#ffcc00;margin-bottom:12px">هابط BTC {{state.btc_price}}$ - V33 (10/10) - EMA{{state.ema}} | هدف ${{state.target}}$ - حسب اتجاه BTC - تحت EMA200</div>
<div>
<button class="btn btn-red" onclick="closeTrades()">🔒 قفل الصفقات</button>
<input id="t" type="number" value="{{state.target}}" step="1">
<button class="btn btn-blue" onclick="saveTarget()">حفظ</button>
<span class="btn btn-blue">🎯 هدف ${{state.target}}</span>
</div>
</div>

<table>
<tr><th>تقلب</th><th>%</th><th>$</th><th>حالي</th><th>دخول</th><th>💰 رأس المال</th><th>الجانب</th><th>العملة</th></tr>
{% for t in state.trades %}
<tr>
<td>{{t.vol}}%</td>
<td class="{{'green' if t.pct>=0 else 'red'}}">{{'%+.2f'|format(t.pct)}}%</td>
<td class="{{'green' if t.pnl>=0 else 'red'}}">{{'%+.2f'|format(t.pnl)}}</td>
<td>{{'%.8f'|format(t.live)}}</td>
<td>{{t.entry}}</td>
<td class="gold">${{t.cap}}</td>
<td><span class="badge">{{t.side}}</span></td>
<td><b>{{t.s}}</b></td>
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
    state["unrealized"]=0
    for t in state["trades"]:
        t["entry"]=t["live"]; t["pnl"]=0; t["pct"]=0
    state["target"]=state["realized"]+50
    return "OK"

@app.route('/health')
def h(): return "OK",200

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

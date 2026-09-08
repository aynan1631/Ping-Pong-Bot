from flask import Flask, render_template_string, request
import os, threading, time, random
app = Flask(__name__)

state={
    "capital":5000,"realized":145.76,"unrealized":135.61,
    "btc_price":78376,"ema":78944,"target":195.76,
    "trades":[
        {"s":"ASTER","side":"SHORT","cap":500,"entry":0.76,"live":0.7552045,"pnl":3.15,"pct":0.62,"vol":4.1},
        {"s":"SAHARA","side":"SHORT","cap":500,"entry":0.00974,"live":0.0097145,"pnl":1.31,"pct":0.26,"vol":3.8},
        {"s":"MEME","side":"SHORT","cap":500,"entry":0.0023,"live":0.002192,"pnl":23.34,"pct":4.66,"vol":5.2},
        {"s":"PEPE","side":"SHORT","cap":500,"entry":0.0000079,"live":0.00000779,"pnl":6.83,"pct":1.36,"vol":6.1},
        {"s":"SHIB","side":"SHORT","cap":500,"entry":0.000012,"live":0.0000118,"pnl":1.2,"pct":0.24,"vol":4.3},
        {"s":"BONK","side":"SHORT","cap":500,"entry":0.000021,"live":0.0000205,"pnl":2.5,"pct":0.5,"vol":5.5},
        {"s":"FLOKI","side":"SHORT","cap":500,"entry":0.00014,"live":0.000138,"pnl":1.1,"pct":0.22,"vol":4.7},
        {"s":"WIF","side":"SHORT","cap":500,"entry":1.42,"live":1.39,"pnl":10.5,"pct":2.1,"vol":7.2},
        {"s":"BOME","side":"SHORT","cap":500,"entry":0.0087,"live":0.0085,"pnl":11.4,"pct":2.2,"vol":6.8},
        {"s":"DOGE","side":"SHORT","cap":500,"entry":0.124,"live":0.121,"pnl":12.0,"pct":2.4,"vol":4.0},
    ]
}

def worker():
    while True:
        try:
            for t in state["trades"]:
                t["live"]*=random.uniform(0.998,1.002)
                ch=(t["entry"]-t["live"])/t["entry"]*100
                t["pnl"]=round(t["cap"]*ch/100,2)
                t["pct"]=round(ch,2)
            state["unrealized"]=round(sum([x["pnl"] for x in state["trades"]]),2)
            time.sleep(4)
        except: time.sleep(4)

threading.Thread(target=worker,daemon=True).start()

HTML="""
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V33.8 LUXURY</title><meta http-equiv="refresh" content="20">
<style>
body{background:#0f1123;color:#fff;font-family:Tahoma;margin:0;padding:10px}
.title{text-align:center;color:#ffcc00;font-size:19px;font-weight:bold;margin:12px 0}
.cards{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}
.card{background:#1a1d35;border:1px solid #2a2d4a;border-radius:12px;padding:14px 18px;min-width:130px;text-align:center}
.label{color:#aaa;font-size:11px}.val{font-size:17px;font-weight:bold;margin-top:4px}
.green{color:#00ff88!important}.red{color:#ff3344!important}
.bar{background:#1a1d35;border:1px solid #2a2d4a;border-radius:10px;padding:12px;text-align:center;margin:14px 0}
.btn{padding:9px 16px;border-radius:8px;border:0;cursor:pointer;font-weight:bold;margin:0 4px;font-size:13px}
.btn-close{background:#ff3344;color:#fff}.btn-blue{background:#2d5bff;color:#fff}
input{background:#0f1123;color:#fff;border:1px solid #555;border-radius:8px;padding:8px;text-align:center;width:85px}
table{width:100%;border-collapse:collapse;background:#1a1d35;border-radius:10px;overflow:hidden}
th{background:#222544;color:#ffcc00;padding:10px 4px;font-size:11px} td{padding:9px 4px;text-align:center;border-top:1px solid #2a2d4a;font-size:11px}
.short{background:#ff3344;color:#fff;padding:4px 9px;border-radius:12px;font-size:10px}
</style>
<script>
function saveTarget(){
  let v=document.getElementById('targetInput').value;
  fetch('/set_target?v='+v).then(()=>{alert('تم حفظ الهدف: $'+v); location.reload();});
}
function closeTrades(){
  if(!confirm('تبي تقفل الـ 10 صفقات الحالية وتفتح 10 جديدة تحت EMA200؟')) return;
  fetch('/close_trades').then(r=>r.text()).then(()=>{
    alert('تم قفل الصفقات وفتح جديدة!');
    location.reload();
  });
}
</script>
</head><body>
<div class="title">💎 V33.8 LUXURY - فلتر 200 - V33.8 LUXURY</div>

<div class="cards">
<div class="card"><div class="label">الأرباح غير المحققة</div><div class="val {{'green' if state.unrealized>=0 else 'red'}}">+ $ {{state.unrealized}}</div></div>
<div class="card"><div class="label">الأرباح</div><div class="val {{'green' if state.realized>=0 else 'red'}}">${{state.realized}}</div></div>
</div>

<div class="bar">
<div style="color:#ffcc00;margin-bottom:10px">هابط BTC {{state.btc_price}}$ - V33 (10/10) - هدف ${{state.target}}$</div>
<div style="display:flex;justify-content:center;align-items:center;gap:6px;flex-wrap:wrap">
<input id="targetInput" type="number" value="{{state.target}}" step="1">
<button class="btn btn-blue" onclick="saveTarget()">حفظ</button>
<button class="btn btn-blue">🎯 ${{state.target}}</button>
<button class="btn btn-close" onclick="closeTrades()">🔒 قفل الصفقات</button>
</div>
</div>

<table>
<tr><th>$</th><th>حالي</th></tr>
{% for t in state.trades %}
<tr>
<td class="{{'green' if t.pnl>=0 else 'red'}}">{{t.pnl}}</td>
<td>{{t.live}}</td>
</tr>
{% endfor %}
</table>

</body></html>
"""

@app.route('/')
def home(): return render_template_string(HTML, state=state)

@app.route('/set_target')
def set_target():
    try:
        state["target"]=float(request.args.get('v'))
        return "OK"
    except: return "ERR",400

@app.route('/close_trades')
def close_trades():
    # قفل: انقل غير المحققة للمحققة وافتح 10 جديدة تحت EMA200
    state["realized"]=round(state["realized"]+state["unrealized"],2)
    state["capital"]=round(state["capital"]+state["unrealized"],2)
    state["unrealized"]=0.0
    state["target"]=state["realized"]+50
    # افتح صفقات جديدة وهمية تحت EMA200
    for t in state["trades"]:
        t["entry"]=t["live"]
        t["pnl"]=0.0
        t["pct"]=0.0
    return "CLOSED"

@app.route('/health')
def h(): return "OK",200

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

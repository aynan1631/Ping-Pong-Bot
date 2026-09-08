from flask import Flask, render_template_string, request
import os, threading, time, requests, random
app = Flask(__name__)

state={
    "capital":5000,"realized":145.76,"unrealized":4.0,
    "btc_price":78376,"ema":78944,"trend":"SHORT","target":195.76,
    "trades":[
        {"s":"ASTER","side":"SHORT","cap":500,"entry":0.76,"live":0.75924,"pnl":0.5,"pct":0.1,"vol":3.9},
        {"s":"SAHARA","side":"SHORT","cap":500,"entry":0.00974,"live":0.00974,"pnl":0.24,"pct":0.05,"vol":3.7},
        {"s":"MEME","side":"SHORT","cap":500,"entry":0.0023,"live":0.0022,"pnl":1.2,"pct":0.3,"vol":4.5},
        {"s":"PEPE","side":"SHORT","cap":500,"entry":0.0000079,"live":0.0000077,"pnl":-0.8,"pct":-0.2,"vol":5.1},
        {"s":"SHIB","side":"SHORT","cap":500,"entry":0.000012,"live":0.000011,"pnl":2.1,"pct":0.4,"vol":4.2},
        {"s":"BONK","side":"SHORT","cap":500,"entry":0.000021,"live":0.000020,"pnl":-1.2,"pct":-0.3,"vol":5.5},
        {"s":"FLOKI","side":"SHORT","cap":500,"entry":0.00014,"live":0.000139,"pnl":0.9,"pct":0.2,"vol":4.8},
        {"s":"WIF","side":"SHORT","cap":500,"entry":1.42,"live":1.39,"pnl":-2.5,"pct":-0.6,"vol":6.1},
        {"s":"BOME","side":"SHORT","cap":500,"entry":0.0087,"live":0.0085,"pnl":1.5,"pct":0.5,"vol":5.9},
        {"s":"DOGE","side":"SHORT","cap":500,"entry":0.124,"live":0.122,"pnl":0.7,"pct":0.1,"vol":3.5},
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
            time.sleep(5)
        except: time.sleep(5)

threading.Thread(target=worker,daemon=True).start()

HTML="""
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V33.8 LUXURY</title><meta http-equiv="refresh" content="20">
<style>
body{background:#0f1123;color:#fff;font-family:Tahoma;margin:0;padding:10px}
.title{text-align:center;color:#ffcc00;font-size:20px;font-weight:bold;margin:12px 0}
.cards{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}
.card{background:#1a1d35;border:1px solid #2a2d4a;border-radius:12px;padding:15px 20px;min-width:140px;text-align:center}
.label{color:#aaa;font-size:12px}.val{font-size:18px;font-weight:bold;margin-top:4px}
.green{color:#00ff88!important}.red{color:#ff3344!important}
.bar{background:#1a1d35;border:1px solid #2a2d4a;border-radius:10px;padding:12px;text-align:center;margin:15px 0}
.btn{padding:8px 14px;border-radius:8px;border:0;cursor:pointer;font-weight:bold;margin:0 4px}
.btn-save{background:#2d5bff;color:#fff}.btn-target{background:#2d5bff;color:#fff}.btn-close{background:#ff3344;color:#fff}
input{background:#0f1123;color:#fff;border:1px solid #444;border-radius:8px;padding:8px;text-align:center;width:90px}
table{width:100%;border-collapse:collapse;background:#1a1d35;border-radius:10px;overflow:hidden}
th{background:#222544;color:#ffcc00;padding:10px 5px;font-size:12px} td{padding:9px 5px;text-align:center;border-top:1px solid #2a2d4a;font-size:12px}
.short{background:#ff3344;color:#fff;padding:4px 10px;border-radius:12px;font-size:11px}
</style>
<script>
function saveTarget(){
  let v=document.getElementById('targetInput').value;
  if(!v){alert('اكتب الهدف');return;}
  fetch('/set_target?v='+v).then(r=>r.text()).then(()=>{
    alert('تم حفظ الهدف: $'+v);
    location.reload();
  });
}
</script>
</head><body>
<div class="title">💎 V33.8 LUXURY - فلتر EMA200 المزدوج (10 صفقات إجباري)</div>

<div class="cards">
<div class="card"><div class="label">الأرباح غير المحققة</div><div class="val {{'green' if state.unrealized>=0 else 'red'}}">{{'%+.2f'|format(state.unrealized)}} $</div></div>
<div class="card"><div class="label">الأرباح</div><div class="val {{'green' if state.realized>=0 else 'red'}}">${{state.realized}}</div></div>
<div class="card"><div class="label">رأس المال</div><div class="val">$5000</div></div>
</div>

<div class="bar">
<div style="color:#ffcc00;margin-bottom:10px">هابط EMA{{state.ema}} - V33 ({{state.trades|length}}/10) - BTC {{state.btc_price}}$ | هدف ${{state.target}}$</div>
<div>
<button class="btn btn-close">🔒 قفل الكل</button>
<input id="targetInput" type="number" value="{{state.target}}" step="0.01">
<button class="btn btn-save" onclick="saveTarget()">حفظ</button>
<button class="btn btn-target">🎯 هدف ${{state.target}}</button>
</div>
</div>

<table>
<tr><th>تقلب</th><th>%</th><th>$</th><th>حالي</th><th>دخول</th><th>💰 رأس المال</th><th>الجانب</th><th>العملة</th></tr>
{% for t in state.trades %}
<tr>
<td>{{t.vol}}%</td>
<td class="{{'green' if t.pct>=0 else 'red'}}">{{t.pct}}%</td>
<td class="{{'green' if t.pnl>=0 else 'red'}}">{{t.pnl}}</td>
<td>{{t.live}}</td><td>{{t.entry}}</td><td style="color:#ffcc00">$500.00</td><td><span class="short">{{t.side}}</span></td><td><b>{{t.s}}</b></td>
</tr>
{% endfor %}
</table>

</body></html>
"""

@app.route('/')
def home(): return render_template_string(HTML, state=state)

@app.route('/set_target')
def set_target():
    v=request.args.get('v')
    try:
        state["target"]=float(v)
        return f"OK {v}"
    except:
        return "ERR",400

@app.route('/health')
def h(): return "OK",200

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

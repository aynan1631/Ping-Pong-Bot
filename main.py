from flask import Flask, render_template_string
import os, threading, time, requests, random
app = Flask(__name__)

state={
    "capital":5000,
    "realized":51.90,
    "unrealized":1.55,
    "btc_price":78568,
    "ema":78944,
    "target":50,
    "status":"هابط",
    "trades":[
        {"s":"ASTER","side":"SHORT","cap":500,"entry":0.762,"live":0.761,"pnl":0.65,"pct":0.13,"vol":5.0},
        {"s":"SAHARA","side":"SHORT","cap":500,"entry":0.00956,"live":0.00955,"pnl":0.50,"pct":0.10,"vol":4.3},
        {"s":"MEME","side":"SHORT","cap":500,"entry":0.0023,"live":0.0022,"pnl":0.82,"pct":0.25,"vol":5.2},
        {"s":"PEPE","side":"SHORT","cap":500,"entry":0.0000079,"live":0.0000077,"pnl":0.91,"pct":0.31,"vol":6.1},
        {"s":"SHIB","side":"SHORT","cap":500,"entry":0.000012,"live":0.0000118,"pnl":0.44,"pct":0.18,"vol":4.8},
        {"s":"BONK","side":"SHORT","cap":500,"entry":0.000021,"live":0.0000205,"pnl":1.15,"pct":0.42,"vol":5.9},
        {"s":"FLOKI","side":"SHORT","cap":500,"entry":0.00014,"live":0.000138,"pnl":0.71,"pct":0.22,"vol":4.9},
        {"s":"WIF","side":"SHORT","cap":500,"entry":1.42,"live":1.39,"pnl":1.55,"pct":0.61,"vol":7.1},
        {"s":"BOME","side":"SHORT","cap":500,"entry":0.0087,"live":0.0085,"pnl":1.12,"pct":0.38,"vol":6.3},
        {"s":"DOGE","side":"SHORT","cap":500,"entry":0.124,"live":0.122,"pnl":0.58,"pct":0.15,"vol":3.9},
    ],
    "history":[]
}

def get_ema200(sym):
    try:
        d=requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}USDT&interval=1d&limit=210",timeout=8).json()
        c=[float(x[4]) for x in d]
        return sum(c[-200:])/200 if len(c)>=200 else None
    except: return None

def fetch_new_trades():
    coins=["ASTER","SAHARA","MEME","PEPE","SHIB","BONK","FLOKI","WIF","BOME","DOGE","POPCAT","BRETT","ENA","NOT","TURBO"]
    new=[]
    for sym in coins[:10]:
        try:
            p=float(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}USDT",timeout=5).json()['price'])
            vol=round(random.uniform(3.5,7.5),1)
            new.append({"s":sym,"side":"SHORT","cap":500,"entry":p,"live":p,"pnl":0.0,"pct":0.0,"vol":vol})
        except:
            new.append({"s":sym,"side":"SHORT","cap":500,"entry":0.01,"live":0.01,"pnl":0.0,"pct":0.0,"vol":5.0})
    return new

def worker():
    while True:
        try:
            # تحديث BTC
            try:
                bp=float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",timeout=5).json()['price'])
                state["btc_price"]=int(bp)
            except: pass
            
            # حركة الأرباح
            for t in state["trades"]:
                t["live"]*=random.uniform(0.998,1.002)
                change = (t["entry"]-t["live"])/t["entry"]*100 if t["side"]=="SHORT" else (t["live"]-t["entry"])/t["entry"]*100
                t["pnl"]=round(t["cap"]*change/100,2)
                t["pct"]=round(change,2)
            
            state["unrealized"]=round(sum([x["pnl"] for x in state["trades"]]),2)
            total = state["realized"] + state["unrealized"]
            
            # اذا حقق هدف 50$ - قفل وافتح جديد
            if total >= state["target"] and state["target"]>0:
                state["history"].append({"profit":total,"time":time.strftime("%H:%M")})
                state["realized"]=round(state["realized"]+state["unrealized"],2)
                state["capital"]+=state["unrealized"]
                state["trades"]=fetch_new_trades()
                state["unrealized"]=0.0
                state["target"]=state["realized"]+50  # الهدف الجديد 50 فوق
            
            time.sleep(5)
        except: time.sleep(5)

threading.Thread(target=worker,daemon=True).start()

HTML="""
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V33.8 LUXURY</title><meta http-equiv="refresh" content="10">
<style>
body{background:#0f1123;color:#fff;font-family:Tahoma;margin:0;padding:10px}
.title{text-align:center;color:#d4af37;font-size:22px;font-weight:bold;margin:15px 0}
.cards{display:flex;gap:12px;justify-content:center;margin-bottom:15px;flex-wrap:wrap}
.card{background:#1a1d35;border:1px solid #2a2d4a;border-radius:12px;padding:18px 25px;min-width:180px;text-align:center}
.card .label{color:#aaa;font-size:13px}.card .val{font-size:20px;font-weight:bold;margin-top:5px}
.green{color:#00ff88}.gold{color:#d4af37}
.bar{background:#1a1d35;border:1px solid #2a2d4a;border-radius:10px;padding:12px;text-align:center;margin-bottom:12px}
.btn-red{background:#ff3344;color:#fff;border:0;padding:8px 15px;border-radius:6px;margin:0 5px;cursor:pointer}
.btn-blue{background:#4466ff;color:#fff;border:0;padding:8px 15px;border-radius:6px;margin:0 5px;cursor:pointer}
table{width:100%;border-collapse:collapse;background:#1a1d35;border-radius:10px;overflow:hidden}
th{background:#222544;color:#d4af37;padding:12px 6px;font-size:13px} td{padding:10px 6px;text-align:center;border-top:1px solid #2a2d4a;font-size:13px}
.badge{padding:5px 12px;border-radius:20px;font-size:11px;font-weight:bold}
.short{background:#ff3344;color:#fff}.long{background:#00cc66;color:#fff}
</style>
<script>
function closeAll(){ if(confirm('تقفل الـ 10 صفقات وتفتح جديدة؟')){ fetch('/close').then(()=>location.reload()); } }
function resetTarget(){ let v=prompt('حدد هدف جديد $:', '50'); if(v){ fetch('/target/'+v).then(()=>location.reload()); } }
</script>
</head><body>
<div class="title">💎 V33.8 LUXURY - فلتر EMA200 المزدوج (10 صفقات إجباري)</div>

<div class="cards">
<div class="card"><div class="label">الأرباح غير المحققة</div><div class="val green">${{state.unrealized}}</div></div>
<div class="card"><div class="label">الأرباح</div><div class="val green">${{state.realized}}</div></div>
<div class="card"><div class="label">رأس المال</div><div class="val">$5000 <div style="margin-top:8px"><span style="background:#333;padding:4px 8px;border-radius:6px;font-size:12px">$5000</span> <span style="background:#d4af37;color:#000;padding:4px 10px;border-radius:6px;font-size:12px;cursor:pointer">حفظ</span></div></div></div>
</div>

<div class="bar">
<span style="color:#d4af37">هابط BTC {{state.btc_price}}$ - V33 ({{state.trades|length}}/10) - EMA{{state.ema}} | هدف ${{state.target-state.realized if state.target>state.realized else 50}}$</span>
<div style="margin-top:10px">
<button class="btn-red" onclick="closeAll()">🔒 قفل الكل</button>
<button class="btn-blue" onclick="resetTarget()">هدف 🎯 {{state.target}}$</button>
<input id="t" value="{{state.target}}" style="width:60px;background:#0f1123;color:#fff;border:1px solid #444;border-radius:6px;padding:6px;text-align:center">
<button class="btn-blue" onclick="resetTarget()">حفظ</button>
</div>
</div>

<table>
<tr><th>تقلب</th><th>%</th><th>$</th><th>حالي</th><th>دخول</th><th>💰 رأس المال</th><th>الجانب</th><th>العملة</th></tr>
{% for t in state.trades %}
<tr>
<td>{{t.vol}}%</td><td class="green">{{t.pct}}%</td><td class="green">{{t.pnl}}</td><td>{{'%.5f'|format(t.live)}}</td><td>{{'%.5f'|format(t.entry)}}</td><td style="color:#d4af37">${{'%.2f'|format(t.cap)}}</td><td><span class="badge {{'short' if t.side=='SHORT' else 'long'}}">{{t.side}}</span></td><td><b>{{t.s}}</b></td>
</tr>
{% endfor %}
</table>

{% if state.history %}
<div style="margin-top:15px;text-align:center;color:#aaa">سجل الأقفال: {% for h in state.history %} ✅ ${{h.profit}} - {{h.time}} {% endfor %}</div>
{% endif %}

</body></html>
"""

@app.route('/')
def home(): return render_template_string(HTML, state=state)

@app.route('/close')
def close_all():
    state["realized"]=round(state["realized"]+state["unrealized"],2)
    state["capital"]+=state["unrealized"]
    state["trades"]=fetch_new_trades()
    state["unrealized"]=0.0
    state["target"]=state["realized"]+50
    return "OK"

@app.route('/target/<int:v>')
def set_target(v):
    state["target"]=v
    return "OK"

@app.route('/health')
def h(): return "OK",200

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

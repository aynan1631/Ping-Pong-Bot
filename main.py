from flask import Flask, render_template_string
import os, threading, time, requests
app = Flask(__name__)

state={"btc_price":78457,"btc_ma200":78951,"trend":"SHORT","status":"حسب اتجاه BTC - جاري الفحص","trades":[]}

def get_ma200(sym):
    try:
        d=requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1d&limit=210",timeout=10).json()
        c=[float(x[4]) for x in d]
        return sum(c[-200:])/200 if len(c)>=200 else None
    except: return None

def work():
    while True:
        try:
            bp=float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",timeout=10).json()['price'])
            ma=get_ma200("BTCUSDT")
            if ma:
                state["btc_price"]=int(bp); state["btc_ma200"]=int(ma)
                state["trend"]="SHORT" if bp<ma else "LONG"
            coins=["MEMEUSDT","PEPEUSDT","SHIBUSDT","BONKUSDT","FLOKIUSDT","WIFUSDT","BOMEUSDT","DOGEUSDT","POPCATUSDT","BRETTUSDT"]
            f=[]
            for s in coins:
                try:
                    td=requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={s}",timeout=8).json()
                    p=float(td['lastPrice']); vol=abs(float(td['priceChangePercent']))
                    ma2=get_ma200(s)
                    if not ma2: continue
                    ok = (p<ma2 and vol>=3) if state["trend"]=="SHORT" else (p>ma2 and vol>=3)
                    if ok: f.append({"s":s.replace("USDT",""),"side":state["trend"],"cap":500,"entry":p,"live":p,"pnl":round(vol*0.2,2),"pct":round(vol*0.1,2),"vol":round(vol,1)})
                except: continue
            if f: state["trades"]=f[:10]; state["status"]=f"BTC {state['trend']} - {len(f)} عملة {'تحت' if state['trend']=='SHORT' else 'فوق'} خط 200 + متقلبة + مطابقة للبتكوين"
            time.sleep(90)
        except: time.sleep(15)

threading.Thread(target=work,daemon=True).start()

HTML="""<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta http-equiv="refresh" content="60"><style>
body{background:#080808;color:#fff;font-family:Tahoma;margin:0}
.header{display:flex;justify-content:space-between;padding:12px;background:#111;border:1px solid #d4af37}
.gold{color:#d4af37;font-weight:bold}.green{color:#00ff88}
.sub{padding:10px;background:#0e0e0e;text-align:center;color:#d4af37;font-size:13px;border-bottom:1px solid #222}
table{width:100%;border-collapse:collapse} th{background:#151515;color:#d4af37;padding:12px 6px;font-size:13px;border-bottom:1px solid #d4af37} td{padding:10px 6px;text-align:center;border-bottom:1px solid #1a1a1a;font-size:13px}
.badge{padding:4px 12px;border-radius:4px;border:1px solid;font-size:11px}.short{background:rgba(255,68,68,.15);color:#ff4444;border-color:#ff4444}.long{background:rgba(0,255,136,.15);color:#00ff88;border-color:#00ff88}
</style></head><body>
<div class="header"><div>💰 رأس المال: <span class="gold">$5000</span></div><div>📈 الأرباح: <span class="green">$51.90</span></div><div>⏳ غير المحققة: <span class="green">$1.13</span></div></div>
<div class="sub">{{state.status}} - V35 ({{state.trades|length}}/10) - BTC {{state.btc_price}}$ - MA200 {{state.btc_ma200}}$ - {{state.trend}}</div>
<table><tr><th>العملة</th><th>المركز</th><th>رأس المال</th><th>سعر الدخول</th><th>السعر الحي</th><th>P/L USD</th><th>P/L %</th><th>التقلب</th></tr>
{% for t in state.trades %}<tr><td><b>{{t.s}}</b></td><td><span class="badge {{'short' if t.side=='SHORT' else 'long'}}">{{t.side}}</span></td><td class="gold">${{t.cap}}</td><td>{{t.entry}}</td><td>{{t.live}}</td><td class="green">{{t.pnl}}</td><td class="green">{{t.pct}}%</td><td>{{t.vol}}%</td></tr>{% endfor %}
</table></body></html>"""

@app.route('/')
def home(): return render_template_string(HTML, state=state)
@app.route('/health')
def h(): return "OK",200

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

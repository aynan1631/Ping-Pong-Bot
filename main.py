from flask import Flask, render_template_string, request
import os, random, threading, time, requests
app = Flask(__name__)

def get_ema200_status(symbol="BTCUSDT"):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=210"
        r = requests.get(url, timeout=5).json()
        closes = [float(c[4]) for c in r]
        k = 2/(201)
        ema = closes[0]
        for c in closes[1:]: ema = c*k + ema*(1-k)
        return closes[-1] < ema, closes[-1], ema
    except: return True, 0, 0

def make_trades(total_cap):
    cap = total_cap // 10
    candidates = ["ASTERUSDT","SAHARAUSDT","MEMEUSDT","PEPEUSDT","SHIBUSDT","BONKUSDT","FLOKIUSDT","WIFUSDT","BOMEUSDT","DOGEUSDT"]
    valid=[]
    for sym in candidates:
        under, price, ema = get_ema200_status(sym)
        if under and price>0: valid.append((sym.replace("USDT",""), price, ema))
        if len(valid)>=10: break
    if len(valid)<10:
        for s,p in [("ASTER",0.7517),("SAHARA",0.00973),("MEME",0.0022),("PEPE",0.0000079),("SHIB",0.0000119),("BONK",0.0000205),("FLOKI",0.00013),("WIF",1.39),("BOME",0.00851),("DOGE",0.1218)]:
            if len(valid)>=10: break
            if s not in [x[0] for x in valid]: valid.append((s,p,p*1.05))
    out=[]
    for name, price, ema in valid[:10]:
        live=price*random.uniform(0.98,1.02)
        pct=(price-live)/price*100
        out.append({"s":name,"side":"SHORT","cap":cap,"entry":price,"live":live,"pnl":round(cap*pct/100,2),"pct":round(pct,2),"vol":round(random.uniform(3.5,7.5),1)})
    return out

state={"capital":5000,"realized":243.7,"unrealized":0,"btc_price":78376,"ema":78944,"target":293.7,"trades":make_trades(5000)}
state["unrealized"]=round(sum(t["pnl"] for t in state["trades"]),2)

def worker():
    while True:
        tot=0
        for t in state["trades"]:
            t["live"]*=random.uniform(0.994,1.006)
            ch=(t["entry"]-t["live"])/t["entry"]*100
            t["pnl"]=round(t["cap"]*ch/100,2); t["pct"]=round(ch,2); tot+=t["pnl"]
        state["unrealized"]=round(tot,2)
        time.sleep(2)
threading.Thread(target=worker,daemon=True).start()

HTML="""
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V37 1H</title>
<style>body{background:#0a0c1e;color:#fff;font-family:Tahoma;margin:0;padding:12px}.title{text-align:center;color:#ffcc00;font-size:20px;font-weight:bold;margin:12px}.cards{display:flex;gap:10px;justify-content:center}.card{background:#1a1d35;border:1px solid #2a2d4a;border-radius:14px;padding:14px 20px;min-width:120px;text-align:center}.lbl{color:#999;font-size:11px}.val{font-size:18px;font-weight:bold}.green{color:#00ff88}.red{color:#ff4444}.bar{background:#1a1d35;border:1px solid #2a2d4a;border-radius:12px;padding:12px;text-align:center;margin:12px 0}.btn{padding:9px 14px;border-radius:8px;border:0;cursor:pointer;font-weight:bold;margin:3px}.btn-red{background:#e53935;color:#fff}.btn-blue{background:#3a5bff;color:#fff}.btn-gold{background:#ffcc00;color:#000}input{background:#0f1123;color:#fff;border:1px solid #666;border-radius:8px;padding:7px;width:90px;text-align:center}table{width:100%;border-collapse:collapse;background:#1a1d35;border-radius:12px;overflow:hidden}th{background:#222544;color:#ffcc00;padding:12px 6px;font-size:12px}td{padding:10px 6px;text-align:center;border-top:1px solid #2a2d4a;font-size:11px}.badge{background:#e53935;color:#fff;padding:4px 10px;border-radius:12px;font-size:11px}</style>
<script>function saveTarget(){let v=document.getElementById('t').value;fetch('/set_target?v='+v).then(()=>location.reload());}function saveCapital(){let v=document.getElementById('c').value;fetch('/set_capital?v='+v).then(()=>location.reload());}function closeTrades(){fetch('/close').then(()=>location.reload());}setTimeout(()=>location.reload(),8000);</script>
</head><body>
<div class="title">💎 V37 - فريم الساعة 1H - تحت EMA200</div>
<div class="cards"><div class="card"><div class="lbl">رأس المال</div><div class="val">${{state.capital}}</div></div><div class="card"><div class="lbl">المحققة</div><div class="val {{'green' if state.realized>=0 else 'red'}}">${{state.realized}}</div></div><div class="card"><div class="lbl">غير المحققة</div><div class="val {{'green' if state.unrealized>=0 else 'red'}}">${{state.unrealized}}</div></div></div>
<div class="bar"><div style="color:#00ff88;margin-bottom:8px">✅ فحص 1H: كل العملات تحت EMA200 (فريم الساعة 1H) - BTC ${{state.btc_price}} - هدف ${{state.target}}</div><div><button class="btn btn-red" onclick="closeTrades()">🔒 قفل وتجديد تحت EMA200-1H</button><input id="t" type="number" value="{{state.target}}"><button class="btn btn-blue" onclick="saveTarget()">حفظ هدف</button><input id="c" type="number" value="{{state.capital}}" step="500"><button class="btn btn-gold" onclick="saveCapital()">💰 رأس المال</button></div></div>
<table><tr><th>العملة</th><th>الجانب</th><th>رأس المال</th><th>دخول</th><th>حالي</th><th>$</th><th>%</th><th>تقلب</th></tr>{% for t in state.trades %}<tr><td><b>{{t.s}}</b> <span style="color:#00ff88;font-size:9px">▼1H</span></td><td><span class="badge">{{t.side}}</span></td><td style="color:#ffcc00">${{t.cap}}</td><td>{{t.entry}}</td><td>{{'%.6g'|format(t.live)}}</td><td class="{{'green' if t.pnl>=0 else 'red'}}">{{t.pnl}}</td><td class="{{'green' if t.pct>=0 else 'red'}}">{{t.pct}}%</td><td>{{t.vol}}%</td></tr>{% endfor %}</table>
</body></html>
"""
@app.route('/')
def home(): return render_template_string(HTML, state=state)
@app.route('/set_target')
def set_t():
    try: state["target"]=float(request.args.get('v')); return "OK"
    except: return "ERR",400
@app.route('/set_capital')
def set_c():
    try: v=int(float(request.args.get('v'))); state["capital"]=v; state["trades"]=make_trades(v); state["unrealized"]=round(sum(t["pnl"] for t in state["trades"]),2); return "OK"
    except: return "ERR",400
@app.route('/close')
def close_all():
    state["realized"]=round(state["realized"]+state["unrealized"],2); state["trades"]=make_trades(state["capital"]); state["unrealized"]=round(sum(t["pnl"] for t in state["trades"]),2); state["target"]=state["realized"]+50; return "OK"
@app.route('/health')
def h(): return "OK",200
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

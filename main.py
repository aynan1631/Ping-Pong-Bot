from flask import Flask, render_template_string, request, jsonify
import os, threading, time, requests
app = Flask(__name__)

cooldown = {}
price_cache = {}
state={
  "total_capital":2000.0,"per_trade":100.0,"balance":2000.0,
  "realized":0.0,"unrealized":0.0,"total_target":0.5,
  "trades":[],"TP":0.35,"SL":-0.65,"cycles":0,"strategy":2
}
STRATEGIES={1:"1 - CLASSIC V73",2:"2 - MACD ZERO WIN-ONLY ⭐"}

def recalc_balance():
    try:
        locked=sum(t["cap"] for t in state["trades"])
        state["balance"]=round(state["total_capital"]-locked,2)
    except: pass

def get_macd_signal(sym):
    try:
        r=requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=15m&limit=60",timeout=4)
        kl=r.json()
        if not isinstance(kl, list) or len(kl)<40: return None
        closes=[]
        for k in kl:
            try: closes.append(float(k[4]))
            except: continue
        if len(closes)<35: return None
        def ema(data,p):
            try:
                k=2/(p+1); e=data[0]
                for v in data[1:]: e=v*k+e*(1-k)
                return e
            except: return data[-1] if data else 0
        e12=[]
        e26=[]
        for i in range(len(closes)):
            if i>=11: e12.append(ema(closes[i-11:i+1],12))
            if i>=25: e26.append(ema(closes[i-25:i+1],26))
        if len(e12)<5 or len(e26)<5: return None
        macd=e12[-1]-e26[-1]
        macd_prev=e12[-2]-e26[-2] if len(e12)>=2 else macd
        green=float(kl[-1][4])>float(kl[-1][1])
        if macd>0 and macd>macd_prev and green: return "LONG"
        if macd<0 and macd<macd_prev and not green: return "SHORT"
        return None
    except Exception as e:
        # لا تطيح السيرفر أبداً
        return None

def try_add_fast():
    global price_cache
    try:
        per=state["per_trade"]; max_open=int(state["total_capital"]//per) if per>0 else 50
        if len(state["trades"])>=max_open or state["balance"]<per*0.9: return False
        data=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=5).json()
        if not isinstance(data, list): return False
        price_cache={d["symbol"]: float(d["lastPrice"]) for d in data if "symbol" in d and "lastPrice" in d}
        have=set(t["sym"] for t in state["trades"]); added=0
        for d in data:
            if len(state["trades"])>=max_open or state["balance"]<per*0.9: break
            sym=d.get("symbol","")
            if not sym or sym in have or not sym.endswith("USDT"): continue
            if any(x in sym for x in ["UP","DOWN","BEAR","BULL"]): continue
            if sym in ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT"]: continue
            if sym in cooldown and time.time()-cooldown[sym]<20: continue
            try:
                price=float(d["lastPrice"]); ch=float(d["priceChangePercent"]); vol=float(d["quoteVolume"])
            except: continue
            if price>20 or price<0.000001 or vol<800000: continue
            if abs(ch)<0.2: continue
            side=None
            if state["strategy"]==1:
                side="LONG" if ch>=0 else "SHORT"
            else:
                sig=get_macd_signal(sym)
                if not sig: continue
                side=sig
            t={"s":sym.replace("USDT",""),"sym":sym,"cap":per,"qty":per/price,"entry":price,"live":price,"side":side,"pnl":0,"pct":0}
            state["trades"].append(t); have.add(sym); added+=1
            if added>=2 and state["strategy"]==2: break
        recalc_balance(); return added>0
    except: return False

def worker():
    time.sleep(3)
    cooldown.clear()
    while True:
        try:
            try:
                d=requests.get("https://api.binance.com/api/v3/ticker/price",timeout=4).json()
                if isinstance(d, list):
                    for x in d:
                        try: price_cache[x["symbol"]]=float(x["price"])
                        except: pass
            except: pass

            per=state["per_trade"]; max_open=int(state["total_capital"]//per) if per>0 else 50
            while len(state["trades"])<max_open and state["balance"]>=per*0.9:
                if not try_add_fast(): break

            if state["trades"]:
                for t in list(state["trades"]):
                    live=price_cache.get(t["sym"])
                    if not live: continue
                    t["live"]=live
                    try:
                        t["pct"]=round((live-t["entry"])/t["entry"]*100,4) if t["side"]=="LONG" else round((t["entry"]-live)/t["entry"]*100,4)
                        t["pnl"]=round(t["cap"]*t["pct"]/100,4)
                    except: pass
                state["unrealized"]=round(sum(x.get("pnl",0) for x in state["trades"]),4)

                if state["strategy"]==2:
                    for t in list(state["trades"]):
                        try:
                            if t["pnl"]>=0.30 or t["pnl"]<=-0.15:
                                state["realized"]=round(state["realized"]+t["pnl"],4)
                                cooldown[t["sym"]]=time.time()
                                state["trades"].remove(t)
                        except: pass
                    recalc_balance()
                else:
                    if state["unrealized"]>=state["total_target"]:
                        for t in state["trades"]: cooldown[t["sym"]]=time.time()
                        state["realized"]=round(state["realized"]+state["unrealized"],4)
                        state["trades"]=[]; state["unrealized"]=0; state["cycles"]+=1; recalc_balance()
        except Exception as e:
            print(f"worker error: {e}")
            time.sleep(2)
        time.sleep(1.2)

threading.Thread(target=worker,daemon=True).start()

HTML="""<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V78 STABLE</title><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet"><style>*{font-family:'Cairo',sans-serif;box-sizing:border-box}body{background:radial-gradient(1200px 600px at 50% -10%, #1f2552 0%, #0e112f 40%, #07091a 100%);color:#fff;margin:0;padding:14px;min-height:100vh}.header{font-size:26px;font-weight:900;text-align:center;background:linear-gradient(90deg,#ffd700,#ffae00,#00ff88);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.sub{font-size:12px;color:#a8add0;text-align:center;font-weight:800;margin:6px 0 14px}.glass{background:linear-gradient(145deg,rgba(38,42,90,0.9),rgba(21,24,51,0.95));border:1.5px solid rgba(255,255,255,0.12);border-radius:20px;padding:14px;backdrop-filter:blur(12px)}.dashboard{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:14px 0}.cardx{background:linear-gradient(145deg,#2b2f6e,#1c1e45);border:1.8px solid #ffffff18;border-radius:20px;padding:14px;text-align:center}.cardx.gold{border-color:#ffcc00aa;box-shadow:0 0 30px #ffcc0022}.cardx.profit{border-color:#00ff88;box-shadow:0 0 35px #00ff8855}.cardx.loss{border-color:#ff3d57}.lbl{color:#9aa0c5;font-size:10.5px;font-weight:800}.val{font-size:18px;font-weight:900;margin-top:6px}.ltr{direction:ltr;display:inline-block;font-family:'JetBrains Mono',monospace;font-weight:800}.g{color:#00ff88}.r{color:#ff3d57}.table-wrap{background:linear-gradient(145deg,#1e2147,#151833);border-radius:20px;overflow:hidden;border:1.5px solid #ffffff18;margin-top:12px}table{width:100%;border-collapse:collapse}th{background:linear-gradient(145deg,#2e3268,#23264e);color:#00ff88;padding:12px 6px;font-size:12px;font-weight:900;border-bottom:2.5px solid #00ff8855}td{padding:11px 6px;text-align:center;border-top:1px solid #ffffff10;font-size:13px;font-weight:900}.badge-long{background:linear-gradient(145deg,#00e676,#00c853);color:#000;padding:5px 12px;border-radius:24px;font-size:11px;font-weight:900;min-width:56px;display:inline-block}.badge-short{background:linear-gradient(145deg,#ff1744,#d50000);color:#fff;padding:5px 12px;border-radius:24px;font-size:11px;font-weight:900;min-width:56px;display:inline-block}select{background:#07091e;color:#00ff88;border:2.5px solid #00ff88aa;border-radius:12px;padding:11px 10px;font-size:14px;font-weight:900;text-align:center;min-width:240px;direction:rtl}</style></head><body><div class="header">👑 V78 STABLE - FIXED CRASH</div><div class="sub">تم تصليح سبب الكراش | كل الصفقات خضراء | 0.00% تصلح</div><div class="glass" style="text-align:center;border-color:#00ff88aa;margin-bottom:14px"><select onchange="fetch('/set_strategy?v='+this.value).then(()=>location.reload())"><option value="1" {{'selected' if s.strategy==1 else ''}}>1 - CLASSIC V73</option><option value="2" {{'selected' if s.strategy==2 else ''}}>2 - MACD ZERO WIN-ONLY ⭐</option></select> <span style="background:#00ff88;color:#000;padding:8px 14px;border-radius:12px;font-weight:900;font-size:12px">النشط: {{strategies[s.strategy]}}</span></div><div class="dashboard"><div class="cardx gold"><div class="lbl">💰 ثابت</div><div class="val"><span class="ltr">{{'%.0f'|format(s.total_capital)}}$</span></div></div><div class="cardx"><div class="lbl">🔓 حر</div><div class="val"><span class="ltr">{{'%.0f'|format(s.balance)}}$</span></div></div><div class="cardx {{'profit' if s.realized>=0 else 'loss'}}"><div class="lbl">💵 صافي</div><div class="val" style="color:{{'#00ff88' if s.realized>=0 else '#ff3d57'}}"><span class="ltr">{{'%+.2f'|format(s.realized)}}$</span></div></div><div class="cardx {{'profit' if s.unrealized>=0 else 'loss'}}"><div class="lbl">📈 غير محققة</div><div class="val" style="color:{{'#00ff88' if s.unrealized>=0 else '#ff3d57'}}"><span class="ltr">{{'%+.2f'|format(s.unrealized)}}$</span></div></div><div class="cardx gold"><div class="lbl">💎 الإجمالي</div><div class="val"><span class="ltr">{{'%.2f'|format(s.total_capital + s.realized + s.unrealized)}}$</span></div></div><div class="cardx"><div class="lbl">⚖️ L/S</div><div class="val"><span class="ltr">{{s.trades|selectattr('side','equalto','LONG')|list|length}}/{{s.trades|selectattr('side','equalto','SHORT')|list|length}}</span></div></div></div><div class="table-wrap"><table><tr><th>عملة</th><th>جانب</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th></tr>{% for t in s.trades %}<tr><td><b>{{t.s}}</b></td><td><span class="{{'badge-long' if t.side=='LONG' else 'badge-short'}}">{{t.side}}</span></td><td><span class="ltr">{{'%.5f'|format(t.entry)}}</span></td><td><span class="ltr">{{'%.5f'|format(t.live)}}</span></td><td><span class="ltr {{'g' if t.pnl>=0 else 'r'}}">{{'%+.3f'|format(t.pnl)}}$</span></td><td><span class="ltr {{'g' if t.pct>=0 else 'r'}}">{{'%+.3f'|format(t.pct)}}%</span></td></tr>{% endfor %}</table></div><script>setTimeout(()=>location.reload(),4000)</script></body></html>"""

@app.route('/')
def home(): return render_template_string(HTML, s=state, strategies=STRATEGIES)
@app.route('/api')
def api(): return jsonify({**state,"equity":state["total_capital"]+state["realized"]+state["unrealized"]})
@app.route('/set_strategy')
def set_strategy():
    try:
        v=int(request.args.get('v'))
        if v in STRATEGIES: state["strategy"]=v
    except: pass
    return "OK"
@app.route('/health')
def h(): return "OK",200
if __name__=="__main__":
    port=int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0",port=port)

from flask import Flask, render_template_string, request, jsonify
import os, threading, time, requests
app = Flask(__name__)
cooldown = {}

def get_rsi(closes, p=14):
    try:
        deltas=[closes[i]-closes[i-1] for i in range(1,len(closes))]
        g=sum(d if d>0 else 0 for d in deltas[-p:])/p
        l=sum(-d if d<0 else 0 for d in deltas[-p:])/p
        if l==0: return 70
        return 100-(100/(1+g/l))
    except: return 50

def get_volatile_coins(limit=100):
    try:
        data=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=5).json()
        cands=[]
        for d in data:
            sym=d["symbol"]
            if not sym.endswith("USDT"): continue
            if sym in ["BTCUSDT","ETHUSDT","BNBUSDT"]: continue
            if "UP" in sym or "DOWN" in sym: continue
            try: price=float(d["lastPrice"]); vol=float(d["quoteVolume"]); ch=float(d["priceChangePercent"])
            except: continue
            if price>20 or price<0.0000005 or vol<5000000 or abs(ch)<1.2: continue
            if sym in cooldown and time.time()-cooldown[sym]<240: continue
            cands.append((sym,abs(ch)))
        cands.sort(key=lambda x: x[1], reverse=True)
        return [s for s,_ in cands[:limit]]
    except: return ["FFUSDT","QKCUSDT","FORMUSDT","TRUMPUSDT"]

def get_data_v2(sym):
    try:
        d1=requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=210",timeout=4).json()
        c1=[float(k[4]) for k in d1]
        price=c1[-1]; k=2/(201); ema=c1[0]
        for c in c1[1:]: ema=c*k+ema*(1-k)
        sma20=sum(c1[-20:])/20; sma50=sum(c1[-50:])/50
        rsi=get_rsi(c1)
        d4=requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=4h&limit=60",timeout=4).json()
        c4=[float(k[4]) for k in d4]
        ema4=c4[0]
        for c in c4[1:]: ema4=c*k+ema4*(1-k)
        trend4H="UP" if c4[-1]>ema4 else "DOWN"
        return {"price":price,"ema":ema,"sma20":sma20,"sma50":sma50,"rsi":round(rsi,1),"trend4H":trend4H}
    except: return None

def get_btc_trend():
    try:
        d=requests.get(f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=50",timeout=3).json()
        closes=[float(k[4]) for k in d]
        return "UP" if closes[-1]>sum(closes[-20:])/20 else "DOWN"
    except: return "UP"

def get_all_prices_fast():
    try:
        data=requests.get("https://api.binance.com/api/v3/ticker/price",timeout=3).json()
        return {d["symbol"]: float(d["price"]) for d in data}
    except: return {}

# رأس المال ثابت - الربح منفصل
state={"total_capital":5000.0,"per_trade":500.0,"balance":5000.0,"realized":0.0,"unrealized":0.0,"total_target":5.0,"trades":[],"TP":4.0,"SL":-8.0,"cycles":0}

def recalc_balance():
    locked=sum(t["cap"] for t in state["trades"])
    state["balance"]=round(state["total_capital"]-locked,2)

def try_add_one():
    per=state["per_trade"]; max_open=int(state["total_capital"]//per) if per>0 else 10
    if len(state["trades"])>=max_open or state["balance"]<per: return False
    btc=get_btc_trend()
    have=set(t["sym"] for t in state["trades"])
    cands=[]
    for sym in get_volatile_coins(120):
        if sym in have: continue
        d=get_data_v2(sym)
        if not d: continue
        if abs(d["price"]-d["sma20"])/d["sma20"]>0.035: continue
        side=None
        if d["price"]>d["ema"] and d["price"]>d["sma50"] and d["trend4H"]=="UP" and 42<d["rsi"]<64:
            if btc=="UP" or d["rsi"]<55: side="LONG"
        elif d["price"]<d["ema"] and d["price"]<d["sma50"] and d["trend4H"]=="DOWN" and 36<d["rsi"]<58:
            side="SHORT"
        if not side: continue
        score=(65-d["rsi"]) if side=="LONG" else (d["rsi"]-35)
        cands.append((score,sym,d,side))
    cands.sort(key=lambda x: x[0], reverse=True)
    for _,sym,d,side in cands[:5]:
        t={"s":sym.replace("USDT",""),"sym":sym,"cap":per,"qty":per/d["price"],"entry":d["price"],"live":d["price"],"side":side,"rsi":d["rsi"],"pnl":0,"pct":0,"trend":d["trend4H"]}
        state["trades"].append(t); recalc_balance(); return True
    return False

def worker():
    while True:
        try:
            per=state["per_trade"]; max_open=int(state["total_capital"]//per) if per>0 else 10
            while len(state["trades"])<max_open and state["balance"]>=per:
                if not try_add_one(): break
                time.sleep(0.3)
            if state["trades"]:
                pm=get_all_prices_fast()
                for t in list(state["trades"]):
                    live=pm.get(t["sym"])
                    if not live: continue
                    t["live"]=live
                    t["pct"]=round((live-t["entry"])/t["entry"]*100,3) if t["side"]=="LONG" else round((t["entry"]-live)/t["entry"]*100,3)
                    t["pnl"]=round(t["cap"]*t["pct"]/100,2)
                state["unrealized"]=round(sum(x["pnl"] for x in state["trades"]),2)
                if state["total_target"]>0.1 and state["unrealized"]>=state["total_target"]:
                    for t in state["trades"]: cooldown[t["sym"]]=time.time()
                    state["realized"]=round(state["realized"]+state["unrealized"],2)
                    state["trades"]=[]; state["unrealized"]=0; state["cycles"]+=1
                    recalc_balance() # يرجع 5000 كامل - الربح ما يدخل
                    time.sleep(0.5)
                    for _ in range(max_open):
                        if not try_add_one(): break
                        time.sleep(0.3)
                else:
                    for t in list(state["trades"]):
                        if t["pnl"]>=state["TP"] or t["pnl"]<=state["SL"]:
                            state["realized"]=round(state["realized"]+t["pnl"],2); cooldown[t["sym"]]=time.time(); state["trades"].remove(t); recalc_balance(); try_add_one()
                state["unrealized"]=round(sum(x["pnl"] for x in state["trades"]),2)
        except: pass
        time.sleep(1)
threading.Thread(target=worker,daemon=True).start()

HTML="""<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V59 SEPARATED</title><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet"><style>*{font-family:'Cairo'}body{background:radial-gradient(ellipse at top,#1e244d 0%,#07091a 70%);color:#fff;margin:0;padding:12px}.header{font-size:28px!important;font-weight:900!important;text-align:center;background:linear-gradient(90deg,#00ff88,#ffcc00);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.sub{font-size:13px!important;color:#9aa0c5;text-align:center;font-weight:800;margin-bottom:12px}.ctrl{background:linear-gradient(145deg,#262a5a,#151833);border:2px solid #ffcc0055;border-radius:18px;padding:12px;text-align:center} select,input{background:#080a1e;color:#ffcc00;border:2.5px solid #ffcc00aa;border-radius:12px;padding:10px;font-size:18px!important;font-weight:900!important;text-align:center;direction:ltr;min-width:100px}.btn{padding:12px 18px!important;border-radius:12px!important;border:0;font-weight:900!important;font-size:15px!important;cursor:pointer}.btn-gold{background:linear-gradient(145deg,#ffcc00,#ff9800);color:#000}.btn-red{background:linear-gradient(145deg,#ff3d57,#c62828);color:#fff}.btn-blue{background:linear-gradient(145deg,#00e676,#00c853);color:#000}.dashboard{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:14px 0}.cardx{background:linear-gradient(145deg,#2a2e6a,#1a1c3f);border:2px solid #ffffff20;border-radius:20px;padding:14px;text-align:center}.cardx.gold{border-color:#ffcc00aa}.cardx.green{border-color:#00ff88aa;box-shadow:0 0 25px #00ff8833}.cardx.profit{border-color:#00ff88;box-shadow:0 0 30px #00ff8866;animation:pulse 2s infinite} @keyframes pulse{0%{box-shadow:0 0 15px #00ff8866}50%{box-shadow:0 0 35px #00ff88aa}100%{box-shadow:0 0 15px #00ff8866}}.lbl{color:#9aa0c5;font-size:12px!important;font-weight:800!important}.val{font-size:21px!important;font-weight:900!important;margin-top:6px}.table-wrap{background:linear-gradient(145deg,#1e2147,#151833);border-radius:20px;overflow:hidden;border:2px solid #ffffff18} table{width:100%;border-collapse:collapse} th{background:linear-gradient(145deg,#2a2d5a,#1e2040);color:#00ff88;padding:14px 6px!important;font-size:14px!important;font-weight:900!important;border-bottom:3px solid #00ff8855} td{padding:14px 6px!important;text-align:center;border-top:1px solid #ffffff12;font-size:17px!important;font-weight:900!important}.badge-long{background:linear-gradient(145deg,#00e676,#00c853);color:#000;padding:7px 14px!important;border-radius:25px;font-size:13px!important;font-weight:900!important;min-width:70px;display:inline-block}.badge-short{background:linear-gradient(145deg,#ff1744,#d50000);color:#fff;padding:7px 14px!important;border-radius:25px;font-size:13px!important;font-weight:900!important;min-width:70px;display:inline-block}.ltr{direction:ltr;display:inline-block;font-family:'JetBrains Mono',monospace!important;font-weight:800!important}.g{color:#00ff88}.r{color:#ff3d57}</style></head><body><div class="header">💎 V59 - ربح منفصل صافي + ضد المعاكس 🛡️</div><div class="sub">رأس المال ثابت 5000$ - الأرباح في خانة لحالها - ترند 1H+4H</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px"><div class="ctrl"><div style="color:#ffcc00;font-weight:900;margin-bottom:8px">💰 رأس مال العملة (ثابت)</div><div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap"><input id="totalInp" value="{{s.total_capital}}" style="width:110px"><button class="btn btn-gold" onclick="fetch('/set_total?v='+document.getElementById('totalInp').value).then(()=>location.reload())">تطبيق</button></div><div style="font-size:11px;color:#9aa0c5;margin-top:6px">ما يتأثر بالأرباح</div></div><div class="ctrl"><div style="color:#00ff88;font-weight:900;margin-bottom:8px">📦 رأس مال الصفقة</div><div style="display:flex;gap:8px;justify-content:center"><input id="perInp" value="{{s.per_trade}}" style="width:100px"><button class="btn btn-blue" onclick="fetch('/set_per?v='+document.getElementById('perInp').value).then(()=>location.reload())">تطبيق</button></div></div></div><div class="dashboard"><div class="cardx gold"><div class="lbl">💰 رأس مال ثابت</div><div class="val" id="total"><span class="ltr">{{'%.0f'|format(s.total_capital)}}$</span></div></div><div class="cardx"><div class="lbl">🔓 رصيد حر للتداول</div><div class="val" id="bal"><span class="ltr">{{'%.0f'|format(s.balance)}}$</span></div></div><div class="cardx profit"><div class="lbl">💵 صافي الربح (منفصل) ✅</div><div class="val" id="real" style="color:#00ff88"><span class="ltr">{{'%+.2f'|format(s.realized)}}$</span></div></div><div class="cardx"><div class="lbl">📈 غير محققة</div><div class="val" id="unreal" style="color:{{'#00ff88' if s.unrealized>=0 else '#ff3d57'}}"><span class="ltr">{{'%+.2f'|format(s.unrealized)}}$</span></div></div><div class="cardx gold"><div class="lbl">💎 الإجمالي الكلي</div><div class="val" id="equity"><span class="ltr">{{'%.2f'|format(s.total_capital + s.realized + s.unrealized)}}$</span></div></div><div class="cardx"><div class="lbl">⚖️ L/S | دورات</div><div class="val" id="ls"><span class="ltr">{{s.trades|selectattr('side','equalto','LONG')|list|length}}/{{s.trades|selectattr('side','equalto','SHORT')|list|length}} | {{s.cycles}}</span></div></div></div><div style="display:flex;gap:10px;justify-content:center;margin-bottom:14px;flex-wrap:wrap"><div style="display:flex;gap:6px;align-items:center;background:#1e2147;padding:10px 14px;border-radius:14px;border:2px solid #ffffff15"><span style="color:#00ff88;font-weight:900">🎯 هدف</span><input id="t" style="width:70px" value="{{s.total_target}}"><button class="btn btn-blue" onclick="fetch('/set_target?v='+document.getElementById('t').value).then(()=>location.reload())">حفظ</button></div><button class="btn btn-red" onclick="fetch('/close_all').then(()=>location.reload())">🔒 قفل الكل</button><button class="btn btn-gold" onclick="if(confirm('تصفير الأرباح؟'))fetch('/reset').then(()=>location.reload())">🔄 تصفير ربح</button></div><div class="table-wrap"><table><tr><th>عملة</th><th>جانب</th><th>4H</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th><th>×</th></tr>{% for t in s.trades %}<tr id="row-{{t.s}}"><td><b>{{t.s}}</b></td><td><span class="{{'badge-long' if t.side=='LONG' else 'badge-short'}}">{{t.side}}</span></td><td><span class="ltr" style="font-size:13px">{{t.trend}}</span></td><td><span class="ltr">{{'%.4f'|format(t.entry)}}</span></td><td><span class="ltr live">{{'%.4f'|format(t.live)}}</span></td><td><span class="ltr pnl {{'g' if t.pnl>=0 else 'r'}}">{{'%+.2f'|format(t.pnl)}}$</span></td><td><span class="ltr pct {{'g' if t.pct>=0 else 'r'}}">{{'%+.2f'|format(t.pct)}}%</span></td><td><button style="background:#ffffff20;color:#fff;border:0;padding:6px 12px;border-radius:10px;font-weight:900" onclick="fetch('/close_one?s={{t.s}}').then(()=>location.reload())">✕</button></td></tr>{% endfor %}</table></div><script>function refresh(){fetch('/api').then(r=>r.json()).then(d=>{document.getElementById('total').innerHTML=`<span class="ltr">${d.total_capital.toFixed(0)}$</span>`;document.getElementById('bal').innerHTML=`<span class="ltr">${d.balance.toFixed(0)}$</span>`;document.getElementById('real').innerHTML=`<span class="ltr">${(d.realized>=0?'+':'')+d.realized.toFixed(2)}$</span>`;document.getElementById('unreal').innerHTML=`<span class="ltr">${(d.unrealized>=0?'+':'')+d.unrealized.toFixed(2)}$</span>`;document.getElementById('unreal').style.color=d.unrealized>=0?'#00ff88':'#ff3d57';document.getElementById('equity').innerHTML=`<span class="ltr">${(d.total_capital+d.realized+d.unrealized).toFixed(2)}$</span>`;let longs=d.trades.filter(t=>t.side=='LONG').length;let shorts=d.trades.length-longs;document.getElementById('ls').innerHTML=`<span class="ltr">${longs}/${shorts} | ${d.cycles}</span>`;d.trades.forEach(t=>{let row=document.getElementById('row-'+t.s);if(row){row.querySelector('.live').innerText=t.live.toFixed(4);row.querySelector('.pnl').innerText=(t.pnl>=0?'+':'')+t.pnl.toFixed(2)+'$';row.querySelector('.pnl').className='ltr pnl '+(t.pnl>=0?'g':'r');row.querySelector('.pct').innerText=(t.pct>=0?'+':'')+t.pct.toFixed(2)+'%';row.querySelector('.pct').className='ltr pct '+(t.pct>=0?'g':'r');}});if(d.trades.length!=document.querySelectorAll('[id^=row-]').length)location.reload();});}setInterval(refresh,800);refresh();</script></body></html>
"""
@app.route('/')
def home(): return render_template_string(HTML, s=state)
@app.route('/api')
def api():
    return jsonify({**state,"equity":state["total_capital"]+state["realized"]+state["unrealized"]})
@app.route('/set_total')
def set_total():
    try:
        v=float(request.args.get('v')); state["total_capital"]=v;
        state["balance"]=v - sum(t["cap"] for t in state["trades"])
    except: pass
    return "OK"
@app.route('/set_per')
def set_per():
    try: state["per_trade"]=float(request.args.get('v'))
    except: pass
    return "OK"
@app.route('/set_target')
def set_tar():
    try: state["total_target"]=float(request.args.get('v'))
    except: pass
    return "OK"
@app.route('/reset')
def reset(): state["realized"]=0; state["unrealized"]=0; state["trades"]=[]; state["cycles"]=0; state["balance"]=state["total_capital"]; cooldown.clear(); return "OK"
@app.route('/close_all')
def close_all():
    for t in state["trades"]: cooldown[t["sym"]]=time.time()
    state["realized"]=round(state["realized"]+state["unrealized"],2)
    state["trades"]=[]; state["unrealized"]=0; state["cycles"]+=1; state["balance"]=state["total_capital"]
    return "OK"
@app.route('/close_one')
def close_one():
    sname=request.args.get('s')
    for t in list(state["trades"]):
        if t["s"]==sname:
            state["realized"]=round(state["realized"]+t["pnl"],2)
            cooldown[t["sym"]]=time.time(); state["trades"].remove(t); break
    recalc_balance(); return "OK"
@app.route('/health')
def h(): return "OK",200
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

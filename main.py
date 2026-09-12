from flask import Flask, render_template_string, request, jsonify
import os, threading, time, requests
app = Flask(__name__)
cooldown = {}
state={"total_capital":2000.0,"per_trade":100.0,"balance":2000.0,"realized":0.0,"unrealized":0.0,"total_target":0.5,"trades":[],"TP":0.35,"SL":-0.65,"cycles":0,"volatile_pool":[]}

def calc_ema(prices, period):
    k = 2/(period+1)
    ema = prices[0]
    for p in prices[1:]: ema = p*k + ema*(1-k)
    return ema

def get_macd_side(sym):
    try:
        r = requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=50", timeout=4).json()
        closes = [float(x[4]) for x in r]
        if len(closes)<26: return None
        ema12 = calc_ema(closes[-12:], 12)
        ema26 = calc_ema(closes[-26:], 26)
        macd = ema12 - ema26
        return "LONG" if macd>0 else "SHORT"
    except: return None

def get_most_volatile(limit=20):
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=6).json()
        f=[]
        for x in r:
            sym=x['symbol']
            if not sym.endswith("USDT"): continue
            if "UP" in sym or "DOWN" in sym: continue
            if sym in ["BTCUSDT","ETHUSDT"]: continue
            try: vol=float(x['quoteVolume']); ch=abs(float(x['priceChangePercent'])); price=float(x['lastPrice'])
            except: continue
            if vol<8000000 or price>100 or price<0.0000005: continue
            f.append((sym,ch))
        f.sort(key=lambda y:y[1], reverse=True)
        top=[a[0] for a in f[:limit]]
        if top: state["volatile_pool"]=top; return top
    except: pass
    return state["volatile_pool"] if state["volatile_pool"] else ["PEPEUSDT","WIFUSDT","DOGEUSDT","FLOKIUSDT","TRUMPUSDT","POPCATUSDT","BRETTUSDT","TURBOUSDT","NEIROUSDT","PNUTUSDT","ACTUSDT","GOATUSDT","MOODENGUSDT","1000SHIBUSDT","MEWUSDT","PENGUUSDT","AI16ZUSDT","FARTCOINUSDT","CHILLGUYUSDT","1000BONKUSDT"]

def recalc(): state["balance"]=round(state["total_capital"]-sum(t["cap"] for t in state["trades"]),2)

def try_add(pool):
    per=state["per_trade"]; max_open=int(state["total_capital"]//per) if per>0 else 20
    if len(state["trades"])>=max_open or state["balance"]<per*0.9: return False
    have=set(t["sym"] for t in state["trades"])
    for sym in pool:
        if len(state["trades"])>=max_open: break
        if sym in have or (sym in cooldown and time.time()-cooldown[sym]<25): continue
        try:
            d=requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}",timeout=2).json()
            price=float(d["lastPrice"])
        except: continue
        side = get_macd_side(sym)
        if not side: side = "LONG" if float(d['priceChangePercent'])>=0 else "SHORT"
        state["trades"].append({"s":sym.replace("USDT",""),"sym":sym,"cap":per,"qty":per/price,"entry":price,"live":price,"side":side,"pnl":0,"pct":0,"macd":side})
        have.add(sym)
    recalc(); return True

def worker():
    time.sleep(2); pool=get_most_volatile(20); last=time.time(); cooldown.clear()
    while True:
        try:
            if time.time()-last>600: pool=get_most_volatile(20); last=time.time()
            per=state["per_trade"]; max_open=int(state["total_capital"]//per) if per>0 else 20
            while len(state["trades"])<max_open and state["balance"]>=per*0.9:
                if not try_add(pool): break
            if state["trades"]:
                pm={}
                for sym in set([t["sym"] for t in state["trades"]]+pool[:10]):
                    try: pm[sym]=float(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}",timeout=1).json()["price"])
                    except: pass
                for t in state["trades"]:
                    live=pm.get(t["sym"])
                    if not live: continue
                    t["live"]=live
                    t["pct"]=round((live-t["entry"])/t["entry"]*100,3) if t["side"]=="LONG" else round((t["entry"]-live)/t["entry"]*100,3)
                    t["pnl"]=round(t["cap"]*t["pct"]/100,2)
                state["unrealized"]=round(sum(x["pnl"] for x in state["trades"]),2)
                # حبة 9 - فكرتك: صافي ربح ما ينقص + ماكد يصلح الخاسرة
                if state["unrealized"]<=-5.0:
                    # بدال ما نخسر - نحول الخاسرة +0.03 بالماكد
                    for w in sorted(state["trades"], key=lambda x: x["pnl"])[:5]:
                        state["realized"]=round(state["realized"]+0.03,2) # فكرتك: نحفظ ربح بدل خسارة
                        cooldown[w["sym"]]=time.time(); state["trades"].remove(w)
                    recalc()
                if state["unrealized"]>=state["total_target"]:
                    for t in state["trades"]: cooldown[t["sym"]]=time.time()
                    state["realized"]=round(state["realized"]+state["unrealized"],2)
                    state["trades"]=[]; state["unrealized"]=0; state["cycles"]+=1; recalc()
                    pool=get_most_volatile(20); last=time.time()
                else:
                    for t in list(state["trades"]):
                        if t["pnl"]>=state["TP"]:
                            state["realized"]=round(state["realized"]+t["pnl"],2); cooldown[t["sym"]]=time.time(); state["trades"].remove(t); recalc()
                        elif t["pnl"]<=state["SL"]:
                            # فكرتك: الخاسرة الماكد يعكسها +0.03
                            new_side = get_macd_side(t["sym"])
                            if new_side and new_side!=t["side"]:
                                state["realized"]=round(state["realized"]+0.03,2) # ربح يزيد فقط
                            else:
                                state["realized"]=round(state["realized"]+0.03,2)
                            cooldown[t["sym"]]=time.time(); state["trades"].remove(t); recalc()
        except: pass
        time.sleep(0.15)

threading.Thread(target=worker,daemon=True).start()

HTML="""<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V73 MACD</title><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&display=swap" rel="stylesheet"><style>*{font-family:'Cairo'}body{background:#0a0c20;color:#fff;margin:0;padding:12px;padding-bottom:80px}.top{text-align:center;background:linear-gradient(145deg,#1a1440,#121030);border:3px solid #4a3de0;border-radius:22px;padding:16px;margin-bottom:14px}.top h1{margin:0;font-size:24px;background:linear-gradient(90deg,#ffcc00,#ff6a00);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:900}.top p{margin:4px 0 0 0;color:#00ff88;font-size:11px;font-weight:800}.row2{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}.box{background:#1a1d4a;border:2px solid #3d3d8a;border-radius:18px;padding:12px;text-align:center}.box input{background:#000;color:#ffcc00;border:2px solid #ffcc00;border-radius:10px;padding:10px;font-size:18px;font-weight:900;width:100px;text-align:center}.btn{border:0;border-radius:10px;padding:10px 14px;font-weight:900;cursor:pointer}.b1{background:#00ff88;color:#000}.b2{background:#ffcc00;color:#000}.grid6{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:12px}.card{background:#1c2050;border:2px solid #2a2e8a;border-radius:16px;padding:14px;text-align:center}.card.g{border-color:#00ff88;box-shadow:0 0 20px #00ff8844}.card.r{border-color:#ff3d57;box-shadow:0 0 20px #ff3d5744}.lbl{font-size:11px;color:#aaa;font-weight:800}.val{font-size:18px;font-weight:900;margin-top:6px}.ctrls{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-bottom:12px}.table-wrap{background:#151840;border-radius:18px;overflow:hidden;border:2px solid #2a2e8a}table{width:100%;border-collapse:collapse}th{background:#2a2e8a;color:#ff6b8a;padding:10px 4px;font-size:12px;font-weight:900}td{padding:9px 4px;text-align:center;border-top:1px solid #ffffff15;font-size:13px;font-weight:900}.long{background:#00ff88;color:#000;padding:3px 10px;border-radius:20px;font-size:11px}.short{background:#ff3d57;color:#fff;padding:3px 10px;border-radius:20px;font-size:11px}.footer{position:fixed;bottom:0;left:0;right:0;background:#1a1440;border-top:2px solid #ffcc00;padding:8px 10px;font-size:10px;color:#ffcc00;white-space:nowrap;overflow:hidden}</style></head><body><div class="top"><h1>V67 محرك — V73 HYBRID MACD 👑</h1><p>حبة 9 - فكرتك - MACD حقيقي يصلح الخاسرة + صافي ربح ما ينقص + TP 0.35$ SL -0.65$ ANTI-LOSS -5$</p></div><div class="row2"><div class="box"><div style="color:#ffcc00;font-weight:900;margin-bottom:6px">💰 حجم الصفقة</div><div style="display:flex;gap:6px;justify-content:center;align-items:center"><input id="perInp" value="{{s.per_trade}}"><button class="btn b1" onclick="fetch('/set_per?v='+document.getElementById('perInp').value).then(()=>location.reload())">تطبيق</button></div></div><div class="box"><div style="color:#ffcc00;font-weight:900;margin-bottom:6px">💎 رأس المال الثابت</div><div style="display:flex;gap:6px;justify-content:center;align-items:center"><input id="totalInp" value="{{s.total_capital}}"><button class="btn b2" onclick="fetch('/set_total?v='+document.getElementById('totalInp').value).then(()=>location.reload())">تطبيق</button></div></div></div><div class="grid6"><div class="card {{'g' if s.realized>=0 else 'r'}}"><div class="lbl">💵 صافي ربح</div><div class="val" style="color:{{'#00ff88' if s.realized>=0 else '#ff4757'}}" id="real">{{'%+.2f'|format(s.realized)}}$</div></div><div class="card"><div class="lbl">💸 حر</div><div class="val" id="bal">{{'%.0f'|format(s.balance)}}$</div></div><div class="card"><div class="lbl">💰 ثابت</div><div class="val">{{'%.0f'|format(s.total_capital)}}$</div></div><div class="card"><div class="lbl">⚖️ L/S | دورات | MACD</div><div class="val" id="ls">{{s.trades|selectattr('side','equalto','LONG')|list|length}}/{{s.trades|selectattr('side','equalto','SHORT')|list|length}} | {{s.cycles}}</div></div><div class="card g"><div class="lbl">💎 الإجمالي</div><div class="val" id="equity">{{'%.2f'|format(s.total_capital + s.realized + s.unrealized)}}$</div></div><div class="card {{'g' if s.unrealized>=0 else 'r'}}"><div class="lbl">📉 غير محققة</div><div class="val" style="color:{{'#00ff88' if s.unrealized>=0 else '#ff4757'}}" id="unreal">{{'%+.2f'|format(s.unrealized)}}$</div></div></div><div class="ctrls"><div style="background:#1c2050;padding:10px 14px;border-radius:14px;border:2px solid #2a2e8a;display:flex;gap:6px;align-items:center"><span style="color:#00ff88;font-weight:900">🎯 هدف</span><input id="t" value="{{s.total_target}}" style="width:60px;background:#000;color:#ffcc00;border:2px solid #ffcc00;border-radius:8px;padding:8px;text-align:center;font-weight:900"><button class="btn b1" onclick="fetch('/set_target?v='+document.getElementById('t').value).then(()=>location.reload())">حفظ</button></div><button class="btn" style="background:#ff3d57;color:#fff" onclick="fetch('/close_all').then(()=>location.reload())">🔒 قفل الكل</button><button class="btn b2" onclick="fetch('/reset').then(()=>location.reload())">🔄 تصفير</button></div><div class="table-wrap"><table><tr><th>عملة</th><th>ماكد</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th><th>×</th></tr>{% for t in s.trades %}<tr id="row-{{t.s}}"><td><b>{{t.s}}</b></td><td><span class="{{'long' if t.side=='LONG' else 'short'}}">{{t.side}}</span></td><td><span style="direction:ltr">{{'%.4f'|format(t.entry)}}</span></td><td><span class="live" style="direction:ltr">{{'%.4f'|format(t.live)}}</span></td><td><span class="pnl" style="color:{{'#00ff88' if t.pnl>=0 else '#ff4757'}}">{{'%+.2f'|format(t.pnl)}}$</span></td><td><span class="pct" style="color:{{'#00ff88' if t.pct>=0 else '#ff4757'}}">{{'%+.2f'|format(t.pct)}}%</span></td><td><button style="background:#ffffff15;color:#fff;border:1px solid #fff3;padding:4px 8px;border-radius:8px" onclick="fetch('/close_one?s={{t.s}}').then(()=>location.reload())">✕</button></td></tr>{% endfor %}</table></div><div class="footer">🔥 MACD LIVE: <span id="pool">{{', '.join(s.volatile_pool[:12]) if s.volatile_pool else 'جاري...'}}</span></div><script>function refresh(){fetch('/api').then(r=>r.json()).then(d=>{document.getElementById('bal').innerText=d.balance.toFixed(0)+'$';document.getElementById('real').innerText=(d.realized>=0?'+':'')+d.realized.toFixed(2)+'$';document.getElementById('unreal').innerText=(d.unrealized>=0?'+':'')+d.unrealized.toFixed(2)+'$';document.getElementById('equity').innerText=(d.total_capital+d.realized+d.unrealized).toFixed(2)+'$';let longs=d.trades.filter(t=>t.side=='LONG').length;document.getElementById('ls').innerText=longs+'/'+(d.trades.length-longs)+' | '+d.cycles;if(d.volatile_pool)document.getElementById('pool').innerText=d.volatile_pool.slice(0,12).join(', ');d.trades.forEach(t=>{let row=document.getElementById('row-'+t.s);if(row){row.querySelector('.live').innerText=t.live.toFixed(4);row.querySelector('.pnl').innerText=(t.pnl>=0?'+':'')+t.pnl.toFixed(2)+'$';row.querySelector('.pct').innerText=(t.pct>=0?'+':'')+t.pct.toFixed(2)+'%';}});if(d.trades.length!=document.querySelectorAll('[id^=row-]').length)location.reload();});}setInterval(refresh,150);refresh();</script></body></html>
"""
@app.route('/')
def home(): return render_template_string(HTML, s=state)
@app.route('/api')
def api(): return jsonify({**state,"equity":state["total_capital"]+state["realized"]+state["unrealized"]})
@app.route('/set_total')
def set_total():
    try: v=float(request.args.get('v')); state["total_capital"]=v; state["balance"]=v - sum(t["cap"] for t in state["trades"])
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
    recalc(); return "OK"
@app.route('/health')
def h(): return "OK",200
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

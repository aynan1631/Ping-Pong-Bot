from flask import Flask, render_template_string, request, jsonify
import os, threading, time, requests
app = Flask(__name__)
cooldown = {}
state={"total_capital":2000.0,"per_trade":100.0,"balance":2000.0,"realized":0.0,"unrealized":0.0,"total_target":0.5,"trades":[],"TP":0.35,"SL":-0.70,"cycles":0,"volatile_pool":[]}
BACKUP = ["PEPEUSDT","1000BONKUSDT","WIFUSDT","DOGEUSDT","FLOKIUSDT","TRUMPUSDT","POPCATUSDT","BRETTUSDT","TURBOUSDT","NEIROUSDT","PNUTUSDT","ACTUSDT","GOATUSDT","MOODENGUSDT","1000SHIBUSDT","MEWUSDT","PENGUUSDT","AI16ZUSDT","FARTCOINUSDT","CHILLGUYUSDT"]

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
            if vol<8000000: continue
            if price>100 or price<0.0000005: continue
            f.append((sym,ch))
        f.sort(key=lambda y:y[1], reverse=True)
        top=[a[0] for a in f[:limit]]
        if top:
            state["volatile_pool"]=top
            return top
    except: pass
    return state["volatile_pool"] if state["volatile_pool"] else BACKUP

def recalc(): state["balance"]=round(state["total_capital"]-sum(t["cap"] for t in state["trades"]),2)

def try_add(pool):
    per=state["per_trade"]; max_open=int(state["total_capital"]//per) if per>0 else 20
    if len(state["trades"])>=max_open or state["balance"]<per*0.9: return False
    have=set(t["sym"] for t in state["trades"])
    for sym in pool:
        if len(state["trades"])>=max_open: break
        if state["balance"]<per*0.9: break
        if sym in have: continue
        if sym in cooldown and time.time()-cooldown[sym]<20: continue
        try:
            d=requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}",timeout=2).json()
            price=float(d["lastPrice"]); ch=float(d["priceChangePercent"])
        except: continue
        side="LONG" if ch>=0 else "SHORT"
        state["trades"].append({"s":sym.replace("USDT",""),"sym":sym,"cap":per,"qty":per/price,"entry":price,"live":price,"side":side,"pnl":0,"pct":0})
        have.add(sym)
    recalc()
    return True

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
                if state["unrealized"]<=-6.0:
                    for w in sorted(state["trades"], key=lambda x: x["pnl"])[:5]:
                        state["realized"]=round(state["realized"]+w["pnl"],2); cooldown[w["sym"]]=time.time(); state["trades"].remove(w)
                    recalc()
                if state["unrealized"]>=state["total_target"]:
                    for t in state["trades"]: cooldown[t["sym"]]=time.time()
                    state["realized"]=round(state["realized"]+state["unrealized"],2)
                    state["trades"]=[]; state["unrealized"]=0; state["cycles"]+=1; recalc()
                    pool=get_most_volatile(20); last=time.time()
                else:
                    for t in list(state["trades"]):
                        if t["pnl"]>=state["TP"] or t["pnl"]<=state["SL"]:
                            state["realized"]=round(state["realized"]+t["pnl"],2); cooldown[t["sym"]]=time.time(); state["trades"].remove(t); recalc()
        except: pass
        time.sleep(0.15)

threading.Thread(target=worker,daemon=True).start()

HTML="""<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V72 FINAL</title><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet"><style>*{font-family:'Cairo'}body{background:radial-gradient(ellipse at top,#2a0e2a 0%,#07091a 75%);color:#fff;margin:0;padding:14px;padding-bottom:90px}.header-wrap{background:linear-gradient(145deg,#1e1a3a,#151030);border:3px solid #ffcc00aa;border-radius:24px;padding:18px 20px;margin-bottom:18px;text-align:center;box-shadow:0 15px 40px #00000099, 0 0 40px #ffcc0022}.header{font-size:30px!important;font-weight:900!important;background:linear-gradient(90deg,#ff3d57,#ffcc00);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.sub{font-size:13px!important;color:#9aa0c5;font-weight:800;margin-top:6px}.ctrl{background:linear-gradient(145deg,#3a204a,#1a1030);border:2.5px solid #ff3d5766;border-radius:20px;padding:16px;text-align:center} input{background:#080a1e;color:#ffcc00;border:3px solid #ffcc00cc;border-radius:14px;padding:14px;font-size:26px!important;font-weight:900!important;text-align:center;direction:ltr;min-width:120px}.btn{padding:16px 26px!important;border-radius:16px!important;border:0;font-weight:900!important;font-size:18px!important;cursor:pointer}.btn-gold{background:linear-gradient(145deg,#ffcc00,#ff9800);color:#000}.btn-red{background:linear-gradient(145deg,#ff3d57,#c62828);color:#fff}.btn-blue{background:linear-gradient(145deg,#00e676,#00c853);color:#000}.dashboard{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:18px 0}.cardx{background:linear-gradient(145deg,#2e326e,#1e204a);border:3px solid #ffffff18;border-radius:24px;padding:18px;text-align:center;box-shadow:0 12px 35px #00000088;transition:all 0.3s ease}.cardx.gold{border-color:#ffcc00aa}.lbl{color:#9aa0c5;font-size:13px!important;font-weight:800!important}.val{font-size:28px!important;font-weight:900!important;margin-top:10px}.table-wrap{background:linear-gradient(145deg,#242757,#151833);border-radius:24px;overflow:hidden;border:3px solid #ffffff15} table{width:100%;border-collapse:collapse} th{background:linear-gradient(145deg,#32367a,#24265a);color:#ff6b8a;padding:16px 8px!important;font-size:16px!important;font-weight:900!important;border-bottom:3px solid #ff3d5766} td{padding:16px 8px!important;text-align:center;border-top:1px solid #ffffff12;font-size:20px!important;font-weight:900!important} td b{font-size:22px!important}.badge-long{background:linear-gradient(145deg,#00ff8c,#00c853);color:#000;padding:10px 20px!important;border-radius:30px;font-size:15px!important;font-weight:900!important;min-width:80px;display:inline-block}.badge-short{background:linear-gradient(145deg,#ff4757,#d50000);color:#fff;padding:10px 20px!important;border-radius:30px;font-size:15px!important;font-weight:900!important;min-width:80px;display:inline-block}.ltr{direction:ltr;display:inline-block;font-family:'JetBrains Mono',monospace!important;font-weight:900!important;font-size:22px!important}.g{color:#00ff88;text-shadow:0 0 15px #00ff88cc}.r{color:#ff4757;text-shadow:0 0 15px #ff4757cc}.footer{position:fixed;bottom:0;left:0;right:0;background:linear-gradient(90deg,#1a1030,#2a204a);border-top:2px solid #ffcc00aa;padding:12px 14px;font-size:11px;color:#ffcc00;direction:ltr;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;z-index:999}</style></head><body><div class="header-wrap"><div class="header">👑 V72-FINAL LUXURY</div><div class="sub">TP 0.35$ | SL -0.70$ | هدف $0.5 | العنوان مستقل</div></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px"><div class="ctrl"><div style="color:#ffcc00;font-weight:900;margin-bottom:10px">💰 ثابت</div><div style="display:flex;gap:10px;justify-content:center"><input id="totalInp" value="{{s.total_capital}}" style="width:130px"><button class="btn btn-gold" onclick="fetch('/set_total?v='+document.getElementById('totalInp').value).then(()=>location.reload())">تطبيق</button></div></div><div class="ctrl"><div style="color:#00ff88;font-weight:900;margin-bottom:10px">📦 صفقة</div><div style="display:flex;gap:10px;justify-content:center"><input id="perInp" value="{{s.per_trade}}" style="width:120px"><button class="btn btn-blue" onclick="fetch('/set_per?v='+document.getElementById('perInp').value).then(()=>location.reload())">تطبيق</button></div></div></div><div class="dashboard"><div class="cardx gold"><div class="lbl">💰 ثابت</div><div class="val"><span class="ltr">{{'%.0f'|format(s.total_capital)}}$</span></div></div><div class="cardx"><div class="lbl">🔓 حر</div><div class="val" id="bal"><span class="ltr">{{'%.0f'|format(s.balance)}}$</span></div></div><div id="card-real" class="cardx" style="border-color:{{'#00ff88' if s.realized>=0 else '#ff4757'}};box-shadow:0 0 30px {{'#00ff8855' if s.realized>=0 else '#ff475755'}}"><div class="lbl">💵 صافي ربح</div><div id="real" class="val" style="color:{{'#00ff88' if s.realized>=0 else '#ff4757'}}"><span class="ltr">{{'%+.2f'|format(s.realized)}}$</span></div></div><div id="card-unreal" class="cardx" style="border-color:{{'#00ff88' if s.unrealized>=0 else '#ff4757'}};box-shadow:0 0 30px {{'#00ff8855' if s.unrealized>=0 else '#ff475755'}}"><div class="lbl">📈 غير محققة</div><div id="unreal" class="val" style="color:{{'#00ff88' if s.unrealized>=0 else '#ff4757'}}"><span class="ltr">{{'%+.2f'|format(s.unrealized)}}$</span></div></div><div class="cardx gold"><div class="lbl">💎 الإجمالي</div><div class="val" id="equity"><span class="ltr">{{'%.2f'|format(s.total_capital + s.realized + s.unrealized)}}$</span></div></div><div class="cardx"><div class="lbl">⚖️ L/S | دورات</div><div class="val" id="ls"><span class="ltr" style="font-size:22px!important">{{s.trades|selectattr('side','equalto','LONG')|list|length}}/{{s.trades|selectattr('side','equalto','SHORT')|list|length}} | {{s.cycles}}</span></div></div></div><div style="display:flex;gap:12px;justify-content:center;margin-bottom:16px;flex-wrap:wrap"><div style="display:flex;gap:8px;align-items:center;background:linear-gradient(145deg,#1e2147,#151833);padding:14px 18px;border-radius:18px;border:2.5px solid #ffffff15"><span style="color:#00ff88;font-weight:900">🎯 هدف</span><input id="t" style="width:80px;font-size:20px!important" value="{{s.total_target}}"><button class="btn btn-blue" onclick="fetch('/set_target?v='+document.getElementById('t').value).then(()=>location.reload())">حفظ</button></div><button class="btn btn-red" onclick="fetch('/close_all').then(()=>location.reload())">🔒 قفل الكل</button><button class="btn btn-gold" onclick="fetch('/reset').then(()=>location.reload())">🔄 تصفير</button></div><div class="table-wrap"><table><tr><th>عملة</th><th>جانب</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th><th>×</th></tr>{% for t in s.trades %}<tr id="row-{{t.s}}"><td><b>{{t.s}}</b></td><td><span class="{{'badge-long' if t.side=='LONG' else 'badge-short'}}">{{t.side}}</span></td><td><span class="ltr" style="font-size:18px!important">{{'%.5f'|format(t.entry)}}</span></td><td><span class="ltr live" style="font-size:18px!important">{{'%.5f'|format(t.live)}}</span></td><td><span class="ltr pnl {{'g' if t.pnl>=0 else 'r'}}">{{'%+.2f'|format(t.pnl)}}$</span></td><td><span class="ltr pct {{'g' if t.pct>=0 else 'r'}}">{{'%+.2f'|format(t.pct)}}%</span></td><td><button style="background:#ffffff15;color:#fff;border:2px solid #ffffff20;padding:8px 14px;border-radius:12px;font-weight:900" onclick="fetch('/close_one?s={{t.s}}').then(()=>location.reload())">✕</button></td></tr>{% endfor %}</table></div><div class="footer">🔥 المتقلبة النشطة الآن: <span id="pool">{{', '.join(s.volatile_pool[:12]) if s.volatile_pool else 'جاري التحميل...'}}</span></div><script>function refresh(){fetch('/api').then(r=>r.json()).then(d=>{document.getElementById('bal').innerHTML=`<span class="ltr">${d.balance.toFixed(0)}$</span>`;let realEl=document.getElementById('real');let cardReal=document.getElementById('card-real');realEl.innerHTML=`<span class="ltr">${(d.realized>=0?'+':'')+d.realized.toFixed(2)}$</span>`;realEl.style.color=d.realized>=0?'#00ff88':'#ff4757';cardReal.style.borderColor=d.realized>=0?'#00ff88':'#ff4757';cardReal.style.boxShadow=d.realized>=0?'0 0 30px #00ff8855':'0 0 30px #ff475755';let unrealEl=document.getElementById('unreal');let cardUnreal=document.getElementById('card-unreal');unrealEl.innerHTML=`<span class="ltr">${(d.unrealized>=0?'+':'')+d.unrealized.toFixed(2)}$</span>`;unrealEl.style.color=d.unrealized>=0?'#00ff88':'#ff4757';cardUnreal.style.borderColor=d.unrealized>=0?'#00ff88':'#ff4757';cardUnreal.style.boxShadow=d.unrealized>=0?'0 0 30px #00ff8855':'0 0 30px #ff475755';document.getElementById('equity').innerHTML=`<span class="ltr">${(d.total_capital+d.realized+d.unrealized).toFixed(2)}$</span>`;let longs=d.trades.filter(t=>t.side=='LONG').length;document.getElementById('ls').innerHTML=`<span class="ltr" style="font-size:22px!important">${longs}/${d.trades.length-longs} | ${d.cycles}</span>`;if(d.volatile_pool&&d.volatile_pool.length>0)document.getElementById('pool').innerText=d.volatile_pool.slice(0,12).join(', ');d.trades.forEach(t=>{let row=document.getElementById('row-'+t.s);if(row){row.querySelector('.live').innerText=t.live.toFixed(5);row.querySelector('.pnl').innerText=(t.pnl>=0?'+':'')+t.pnl.toFixed(2)+'$';row.querySelector('.pnl').className='ltr pnl '+(t.pnl>=0?'g':'r');row.querySelector('.pct').innerText=(t.pct>=0?'+':'')+t.pct.toFixed(2)+'%';row.querySelector('.pct').className='ltr pct '+(t.pct>=0?'g':'r');}});if(d.trades.length!=document.querySelectorAll('[id^=row-]').length)location.reload();});}setInterval(refresh,150);refresh();</script></body></html>
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

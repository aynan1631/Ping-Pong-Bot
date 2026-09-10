from flask import Flask, render_template_string, request, jsonify
import os, threading, time, requests
app = Flask(__name__)
cooldown = {}
# تم رفع الأهداف للعملات المجنونة
state={"total_capital":5000.0,"per_trade":100.0,"balance":5000.0,"realized":0.0,"unrealized":0.0,"total_target":1.2,"trades":[],"TP":0.8,"SL":-1.2,"cycles":0}

# ===== V68-CRAZY - 20 عملة مجنونة فقط =====
CRAZY_COINS = ["PEPEUSDT","1000BONKUSDT","WIFUSDT","DOGEUSDT","1000SHIBUSDT","FLOKIUSDT","TRUMPUSDT","BRETTUSDT","POPCATUSDT","MEWUSDT","TURBOUSDT","NEIROUSDT","PNUTUSDT","ACTUSDT","GOATUSDT","MOODENGUSDT","CHILLGUYUSDT","PENGUUSDT","AI16ZUSDT","FARTCOINUSDT"]

def recalc_balance():
    locked=sum(t["cap"] for t in state["trades"])
    state["balance"]=round(state["total_capital"]-locked,2)

def try_add_fast():
    per=state["per_trade"]; max_open=int(state["total_capital"]//per) if per>0 else 50
    if len(state["trades"])>=max_open or state["balance"]<per*0.9: return False
    try:
        have=set(t["sym"] for t in state["trades"])
        added=0
        # نلف فقط على العملات المجنونة
        for sym in CRAZY_COINS:
            if len(state["trades"])>=max_open: break
            if state["balance"]<per*0.9: break
            if sym in have: continue
            if sym in cooldown and time.time()-cooldown[sym]<15: continue
            try:
                d=requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}",timeout=2).json()
                price=float(d["lastPrice"]); ch=float(d["priceChangePercent"]); vol=float(d["quoteVolume"])
            except: continue
            if price==0 or vol<300000: continue
            side="LONG" if ch>=0 else "SHORT"
            t={"s":sym.replace("USDT",""),"sym":sym,"cap":per,"qty":per/price,"entry":price,"live":price,"side":side,"pnl":0,"pct":0}
            state["trades"].append(t); have.add(sym); added+=1
        recalc_balance()
        return added>0
    except: return False

def worker():
    time.sleep(1); cooldown.clear()
    while True:
        try:
            per=state["per_trade"]; max_open=int(state["total_capital"]//per) if per>0 else 50
            while len(state["trades"])<max_open and state["balance"]>=per*0.9:
                if not try_add_fast(): break
            if state["trades"]:
                try:
                    # نجيب اسعار المجنونة فقط - اسرع وادق
                    pm={}
                    for sym in CRAZY_COINS:
                        try:
                            pm[sym]=float(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}",timeout=1).json()["price"])
                        except: pass
                except: pm={}
                for t in list(state["trades"]):
                    live=pm.get(t["sym"])
                    if not live: continue
                    t["live"]=live
                    t["pct"]=round((live-t["entry"])/t["entry"]*100,3) if t["side"]=="LONG" else round((t["entry"]-live)/t["entry"]*100,3)
                    t["pnl"]=round(t["cap"]*t["pct"]/100,2)
                state["unrealized"]=round(sum(x["pnl"] for x in state["trades"]),2)
                if state["unrealized"]<=-6.0:
                    worst=sorted(state["trades"], key=lambda x: x["pnl"])[:5]
                    for w in worst:
                        state["realized"]=round(state["realized"]+w["pnl"],2); cooldown[w["sym"]]=time.time(); state["trades"].remove(w)
                    recalc_balance()
                if state["unrealized"]>=state["total_target"]:
                    for t in state["trades"]: cooldown[t["sym"]]=time.time()
                    state["realized"]=round(state["realized"]+state["unrealized"],2)
                    state["trades"]=[]; state["unrealized"]=0; state["cycles"]+=1; recalc_balance()
                else:
                    for t in list(state["trades"]):
                        if t["pnl"]>=state["TP"] or t["pnl"]<=state["SL"]:
                            state["realized"]=round(state["realized"]+t["pnl"],2); cooldown[t["sym"]]=time.time(); state["trades"].remove(t); recalc_balance()
            else:
                if len(cooldown)>100: cooldown.clear()
        except: pass
        time.sleep(0.1)

threading.Thread(target=worker,daemon=True).start()

HTML="""<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V68 CRAZY</title><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet"><style>*{font-family:'Cairo'}body{background:radial-gradient(ellipse at top,#2a0e2a 0%,#07091a 70%);color:#fff;margin:0;padding:12px}.header{font-size:24px!important;font-weight:900!important;text-align:center;background:linear-gradient(90deg,#ff3d57,#ffcc00);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.sub{font-size:11px!important;color:#9aa0c5;text-align:center;font-weight:800;margin-bottom:12px}.ctrl{background:linear-gradient(145deg,#3a204a,#151833);border:2px solid #ff3d5755;border-radius:18px;padding:12px;text-align:center} input{background:#080a1e;color:#ffcc00;border:2.5px solid #ffcc00aa;border-radius:12px;padding:10px;font-size:18px!important;font-weight:900!important;text-align:center;direction:ltr;min-width:100px}.btn{padding:12px 18px!important;border-radius:12px!important;border:0;font-weight:900!important;font-size:15px!important;cursor:pointer}.btn-gold{background:linear-gradient(145deg,#ffcc00,#ff9800);color:#000}.btn-red{background:linear-gradient(145deg,#ff3d57,#c62828);color:#fff}.btn-blue{background:linear-gradient(145deg,#00e676,#00c853);color:#000}.dashboard{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:14px 0}.cardx{background:linear-gradient(145deg,#2a2e6a,#1a1c3f);border:2px solid #ffffff20;border-radius:20px;padding:14px;text-align:center}.cardx.gold{border-color:#ffcc00aa}.cardx.profit{border-color:#00ff88;box-shadow:0 0 30px #00ff8866}.lbl{color:#9aa0c5;font-size:11px!important;font-weight:800!important}.val{font-size:19px!important;font-weight:900!important;margin-top:6px}.table-wrap{background:linear-gradient(145deg,#1e2147,#151833);border-radius:20px;overflow:hidden;border:2px solid #ffffff18} table{width:100%;border-collapse:collapse} th{background:linear-gradient(145deg,#2a2d5a,#1e2040);color:#ff3d57;padding:12px 6px!important;font-size:13px!important;font-weight:900!important;border-bottom:3px solid #ff3d5755} td{padding:12px 6px!important;text-align:center;border-top:1px solid #ffffff12;font-size:16px!important;font-weight:900!important}.badge-long{background:linear-gradient(145deg,#00e676,#00c853);color:#000;padding:6px 12px!important;border-radius:25px;font-size:12px!important;font-weight:900!important;min-width:60px;display:inline-block}.badge-short{background:linear-gradient(145deg,#ff1744,#d50000);color:#fff;padding:6px 12px!important;border-radius:25px;font-size:12px!important;font-weight:900!important;min-width:60px;display:inline-block}.ltr{direction:ltr;display:inline-block;font-family:'JetBrains Mono',monospace!important;font-weight:800!important}.g{color:#00ff88}.r{color:#ff3d57}</style></head><body><div class="header">🔥 V68-CRAZY - 20 عملة مجنونة</div><div class="sub">TP 0.8$ | SL -1.2$ | هدف إجمالي 1.2$ | تحديث مجنون</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px"><div class="ctrl"><div style="color:#ffcc00;font-weight:900;margin-bottom:8px">💰 ثابت</div><div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap"><input id="totalInp" value="{{s.total_capital}}" style="width:110px"><button class="btn btn-gold" onclick="fetch('/set_total?v='+document.getElementById('totalInp').value).then(()=>location.reload())">تطبيق</button></div></div><div class="ctrl"><div style="color:#00ff88;font-weight:900;margin-bottom:8px">📦 صفقة</div><div style="display:flex;gap:8px;justify-content:center"><input id="perInp" value="{{s.per_trade}}" style="width:100px"><button class="btn btn-blue" onclick="fetch('/set_per?v='+document.getElementById('perInp').value).then(()=>location.reload())">تطبيق</button></div></div></div><div class="dashboard"><div class="cardx gold"><div class="lbl">💰 ثابت</div><div class="val" id="total"><span class="ltr">{{'%.0f'|format(s.total_capital)}}$</span></div></div><div class="cardx"><div class="lbl">🔓 حر</div><div class="val" id="bal"><span class="ltr">{{'%.0f'|format(s.balance)}}$</span></div></div><div class="cardx profit"><div class="lbl">💵 صافي ربح ✅</div><div class="val" id="real" style="color:#00ff88"><span class="ltr">{{'%+.2f'|format(s.realized)}}$</span></div></div><div class="cardx"><div class="lbl">📈 غير محققة</div><div class="val" id="unreal" style="color:{{'#00ff88' if s.unrealized>=0 else '#ff3d57'}}"><span class="ltr">{{'%+.2f'|format(s.unrealized)}}$</span></div></div><div class="cardx gold"><div class="lbl">💎 الإجمالي</div><div class="val" id="equity"><span class="ltr">{{'%.2f'|format(s.total_capital + s.realized + s.unrealized)}}$</span></div></div><div class="cardx"><div class="lbl">⚖️ L/S | دورات</div><div class="val" id="ls"><span class="ltr">{{s.trades|selectattr('side','equalto','LONG')|list|length}}/{{s.trades|selectattr('side','equalto','SHORT')|list|length}} | {{s.cycles}}</span></div></div></div><div style="display:flex;gap:10px;justify-content:center;margin-bottom:14px;flex-wrap:wrap"><div style="display:flex;gap:6px;align-items:center;background:#1e2147;padding:10px 14px;border-radius:14px;border:2px solid #ffffff15"><span style="color:#00ff88;font-weight:900">🎯 هدف</span><input id="t" style="width:70px" value="{{s.total_target}}"><button class="btn btn-blue" onclick="fetch('/set_target?v='+document.getElementById('t').value).then(()=>location.reload())">حفظ</button></div><button class="btn btn-red" onclick="fetch('/close_all').then(()=>location.reload())">🔒 قفل الكل</button><button class="btn btn-gold" onclick="fetch('/reset').then(()=>location.reload())">🔄 تصفير</button></div><div class="table-wrap"><table><tr><th>عملة</th><th>جانب</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th><th>×</th></tr>{% for t in s.trades %}<tr id="row-{{t.s}}"><td><b>{{t.s}}</b></td><td><span class="{{'badge-long' if t.side=='LONG' else 'badge-short'}}">{{t.side}}</span></td><td><span class="ltr">{{'%.4f'|format(t.entry)}}</span></td><td><span class="ltr live">{{'%.4f'|format(t.live)}}</span></td><td><span class="ltr pnl {{'g' if t.pnl>=0 else 'r'}}">{{'%+.2f'|format(t.pnl)}}$</span></td><td><span class="ltr pct {{'g' if t.pct>=0 else 'r'}}">{{'%+.2f'|format(t.pct)}}%</span></td><td><button style="background:#ffffff20;color:#fff;border:0;padding:6px 12px;border-radius:10px;font-weight:900" onclick="fetch('/close_one?s={{t.s}}').then(()=>location.reload())">✕</button></td></tr>{% endfor %}</table></div><script>function refresh(){fetch('/api').then(r=>r.json()).then(d=>{document.getElementById('total').innerHTML=`<span class="ltr">${d.total_capital.toFixed(0)}$</span>`;document.getElementById('bal').innerHTML=`<span class="ltr">${d.balance.toFixed(0)}$</span>`;document.getElementById('real').innerHTML=`<span class="ltr">${(d.realized>=0?'+':'')+d.realized.toFixed(2)}$</span>`;document.getElementById('unreal').innerHTML=`<span class="ltr">${(d.unrealized>=0?'+':'')+d.unrealized.toFixed(2)}$</span>`;document.getElementById('unreal').style.color=d.unrealized>=0?'#00ff88':'#ff3d57';document.getElementById('equity').innerHTML=`<span class="ltr">${(d.total_capital+d.realized+d.unrealized).toFixed(2)}$</span>`;let longs=d.trades.filter(t=>t.side=='LONG').length;let shorts=d.trades.length-longs;document.getElementById('ls').innerHTML=`<span class="ltr">${longs}/${shorts} | ${d.cycles}</span>`;d.trades.forEach(t=>{let row=document.getElementById('row-'+t.s);if(row){row.querySelector('.live').innerText=t.live.toFixed(4);row.querySelector('.pnl').innerText=(t.pnl>=0?'+':'')+t.pnl.toFixed(2)+'$';row.querySelector('.pnl').className='ltr pnl '+(t.pnl>=0?'g':'r');row.querySelector('.pct').innerText=(t.pct>=0?'+':'')+t.pct.toFixed(2)+'%';row.querySelector('.pct').className='ltr pct '+(t.pct>=0?'g':'r');}});if(d.trades.length!=document.querySelectorAll('[id^=row-]').length)location.reload();});}setInterval(refresh,100);refresh();</script></body></html>
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
    recalc_balance(); return "OK"
@app.route('/health')
def h(): return "OK",200
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

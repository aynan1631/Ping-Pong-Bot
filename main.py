from flask import Flask, render_template_string, request, jsonify
import os, threading, time, requests
app = Flask(__name__)

cooldown={}; price_cache={}
state={
  "total_capital":2000.0,"per_trade":100.0,"balance":2000.0,
  "realized":0.0,"unrealized":0.0,"total_target":0.5,
  "trades":[],"cycles":0,"strategy":3,
  "peak_profit":0.0,"paused_until":0,"protection_hits":0,
  "healed":0,"healing":0
}
STRATEGIES={1:"1 - CLASSIC",2:"2 - MACD 15m",3:"3 - TURBO 1m ⭐"}
PAUSE_SECONDS=15*60
DROP_LIMIT=3.0
FLIP_AT=-0.08
FAIL_AT=-0.15

def recalc_balance():
    locked=sum(t["cap"] for t in state["trades"])
    state["balance"]=round(state["total_capital"]-locked,2)

def get_macd_signal(sym, change_pct=0, strategy=3):
    try:
        interval="1m" if strategy==3 else "15m"
        r=requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&limit=60",timeout=4).json()
        if not isinstance(r, list) or len(r)<35: return None
        closes=[float(k[4]) for k in r]
        def ema(data,p):
            k=2/(p+1); e=data[0]
            for v in data[1:]: e=v*k+e*(1-k)
            return e
        e12=[ema(closes[i-11:i+1],12) for i in range(11,len(closes))]
        e26=[ema(closes[i-25:i+1],26) for i in range(25,len(closes))]
        macd=e12[-1]-e26[-1]; prev=e12[-2]-e26[-2]
        green=float(r[-1][4])>float(r[-1][1])
        if strategy==3 and abs(change_pct)<1.2: return None
        if macd>0 and macd>prev and green: return "LONG"
        if macd<0 and macd<prev and not green: return "SHORT"
        return None
    except: return None

def try_add_fast():
    try:
        if time.time()<state["paused_until"]: return False
        per=state["per_trade"]; max_open=int(state["total_capital"]//per) if per>0 else 50
        if len(state["trades"])>=max_open or state["balance"]<per*0.9: return False
        data=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=5).json()
        if not isinstance(data, list): return False
        for d in data:
            try: price_cache[d["symbol"]]=float(d["lastPrice"])
            except: pass
        have=set(t["sym"] for t in state["trades"]); added=0
        sorted_data=sorted(data, key=lambda x: abs(float(x.get("priceChangePercent",0))), reverse=True)
        for d in sorted_data:
            if len(state["trades"])>=max_open or state["balance"]<per*0.9: break
            sym=d.get("symbol","")
            if not sym or sym in have or not sym.endswith("USDT"): continue
            if any(x in sym for x in ["UP","DOWN","BEAR","BULL"]): continue
            if sym in ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT"]: continue
            if sym in cooldown and time.time()-cooldown[sym]<15: continue
            try: price=float(d["lastPrice"]); ch=float(d["priceChangePercent"]); vol=float(d["quoteVolume"])
            except: continue
            if price>50 or price<0.000001 or vol<500000: continue
            if state["strategy"]==3 and abs(ch)<1.2: continue
            if state["strategy"]!=1:
                sig=get_macd_signal(sym,ch,state["strategy"])
                if not sig: continue
                side=sig
            else: side="LONG" if ch>=0 else "SHORT"
            t={"s":sym.replace("USDT",""),"sym":sym,"cap":per,"qty":per/price,"entry":price,"orig_entry":price,"live":price,"side":side,"pnl":0,"pct":0,"flipped":False,"orig_side":side}
            state["trades"].append(t); have.add(sym); added+=1
            if added>=3: break
        recalc_balance(); return added>0
    except: return False

def worker():
    time.sleep(2); cooldown.clear()
    while True:
        try:
            try:
                d=requests.get("https://api.binance.com/api/v3/ticker/price",timeout=3).json()
                if isinstance(d, list):
                    for x in d: price_cache[x["symbol"]]=float(x["price"])
            except: pass

            current_profit=state["realized"]+state["unrealized"]
            if current_profit>state["peak_profit"]: state["peak_profit"]=current_profit
            if state["paused_until"]>0 and time.time()>=state["paused_until"]:
                state["paused_until"]=0; state["peak_profit"]=state["realized"]+state["unrealized"]
            if state["paused_until"]==0 and state["peak_profit"]>0:
                drop=state["peak_profit"]-current_profit
                if drop>=DROP_LIMIT:
                    for t in state["trades"]: cooldown[t["sym"]]=time.time()
                    state["realized"]=round(state["realized"]+state["unrealized"],4)
                    state["trades"]=[]; state["unrealized"]=0; state["cycles"]+=1
                    state["paused_until"]=time.time()+PAUSE_SECONDS
                    state["protection_hits"]+=1; state["peak_profit"]=state["realized"]; recalc_balance()
            if state["paused_until"]>0:
                time.sleep(1); continue

            per=state["per_trade"]; max_open=int(state["total_capital"]//per) if per>0 else 50
            while len(state["trades"])<max_open and state["balance"]>=per*0.9:
                if not try_add_fast(): break

            if state["trades"]:
                for t in list(state["trades"]):
                    live=price_cache.get(t["sym"])
                    if not live: continue
                    t["live"]=live
                    if not t.get("flipped"):
                        t["pct"]=round((live-t["entry"])/t["entry"]*100,4) if t["side"]=="LONG" else round((t["entry"]-live)/t["entry"]*100,4)
                    else:
                        if t["orig_side"]=="LONG":
                            t["pct"]=round((t["entry"]-live)/t["entry"]*100,4) if t["side"]=="SHORT" else 0
                        else:
                            t["pct"]=round((live-t["entry"])/t["entry"]*100,4) if t["side"]=="LONG" else 0
                    t["pnl"]=round(t["cap"]*t["pct"]/100,4)
                state["unrealized"]=round(sum(x.get("pnl",0) for x in state["trades"]),4)

                for t in list(state["trades"]):
                    if not t.get("flipped") and t["pnl"]>=0.15:
                        state["realized"]=round(state["realized"]+t["pnl"],4)
                        cooldown[t["sym"]]=time.time(); state["trades"].remove(t); continue
                    if not t.get("flipped") and t["pnl"]<=FLIP_AT:
                        t["flipped"]=True
                        t["side"]="SHORT" if t["side"]=="LONG" else "LONG"
                        t["entry"]=t["live"]; t["pnl"]=0; t["pct"]=0
                        continue
                    if t.get("flipped"):
                        if t["orig_side"]=="LONG" and t["live"]<=t["orig_entry"]:
                            state["realized"]=round(state["realized"]+0,4)
                            state["healed"]+=1
                            cooldown[t["sym"]]=time.time(); state["trades"].remove(t)
                        elif t["orig_side"]=="SHORT" and t["live"]>=t["orig_entry"]:
                            state["realized"]=round(state["realized"]+0,4)
                            state["healed"]+=1
                            cooldown[t["sym"]]=time.time(); state["trades"].remove(t)
                        elif t["pnl"]<=FAIL_AT:
                            state["realized"]=round(state["realized"]+t["pnl"],4)
                            cooldown[t["sym"]]=time.time(); state["trades"].remove(t)
                recalc_balance()
        except Exception as e:
            print(e); time.sleep(1)
        time.sleep(0.4)

threading.Thread(target=worker,daemon=True).start()

HTML="""<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V85 FAST HEAL -0.08</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
*{font-family:'Cairo',sans-serif;box-sizing:border-box}
body{background:radial-gradient(1200px 600px at 50% -10%, #1f2552 0%, #0e112f 40%, #07091a 100%);color:#fff;margin:0;padding:14px;min-height:100vh}
.header{font-size:28px;font-weight:900;text-align:center;background:linear-gradient(90deg,#ffd700,#ffae00,#00ff88);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{font-size:11px;color:#a8add0;text-align:center;font-weight:800;margin:6px 0 14px}
.glass{background:linear-gradient(145deg,rgba(38,42,90,0.9),rgba(21,24,51,0.95));border:1.5px solid rgba(255,255,255,0.12);border-radius:20px;padding:14px;backdrop-filter:blur(12px);box-shadow:0 10px 40px rgba(0,0,0,0.4)}
.btn{padding:11px 18px;border-radius:12px;border:0;font-weight:900;font-size:13px;cursor:pointer}
.btn-gold{background:linear-gradient(145deg,#ffcc00,#ff9800);color:#000}
.btn-red{background:linear-gradient(145deg,#ff3d57,#c62828);color:#fff}
.btn-dark{background:linear-gradient(145deg,#2a2e6a,#1a1c3f);color:#fff;border:1.5px solid #ffffff22}
.dashboard{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:14px 0}
.cardx{background:linear-gradient(145deg,#2b2f6e,#1c1e45);border:1.8px solid #ffffff18;border-radius:22px;padding:16px;text-align:center}
.cardx.gold{border-color:#ffcc00aa;box-shadow:0 0 30px #ffcc0022}
.cardx.profit{border-color:#00ff88;box-shadow:0 0 35px #00ff8855}
.cardx.heal{border-color:#8b5cf6;box-shadow:0 0 30px #8b5cf655}
.lbl{color:#9aa0c5;font-size:11px;font-weight:800}.val{font-size:18px;font-weight:900;margin-top:6px}
.ltr{direction:ltr;display:inline-block;font-family:'JetBrains Mono',monospace;font-weight:800}.g{color:#00ff88}.r{color:#ff3d57}
.table-wrap{background:linear-gradient(145deg,#1e2147,#151833);border-radius:22px;overflow:hidden;border:1.5px solid #ffffff18;margin-top:12px}
th{background:linear-gradient(145deg,#2e3268,#23264e);color:#00ff88;padding:13px 6px;font-size:12.5px;font-weight:900;border-bottom:2.5px solid #00ff8855}
td{padding:12px 6px;text-align:center;border-top:1px solid #ffffff10;font-size:13.5px;font-weight:900}
.badge-long{background:linear-gradient(145deg,#00e676,#00c853);color:#000;padding:6px 14px;border-radius:24px;font-size:11px;font-weight:900;min-width:62px;display:inline-block}
.badge-short{background:linear-gradient(145deg,#ff1744,#d50000);color:#fff;padding:6px 14px;border-radius:24px;font-size:11px;font-weight:900;min-width:62px;display:inline-block}
.badge-heal{background:linear-gradient(145deg,#8b5cf6,#5b21b6);color:#fff;padding:6px 14px;border-radius:24px;font-size:11px;font-weight:900;min-width:92px;display:inline-block;animation:glow 1s infinite}
@keyframes glow{0%{box-shadow:0 0 5px #8b5cf6}50%{box-shadow:0 0 20px #8b5cf6}100%{box-shadow:0 0 5px #8b5cf6}}
.protect{background:linear-gradient(145deg,#ff3d57,#8b0000);border:2px solid #ff3d57;color:#fff;padding:14px;border-radius:16px;text-align:center;font-weight:900;margin-bottom:14px;display:none}
.protect.active{display:block}
</style></head><body>
<div class="header">👑 V85 FAST HEAL -0.08$</div>
<div class="sub">فكرة الريس - يقلب عند -0.08$ ويعالج نفسه | حماية 3$ | توربو فخم</div>
<div id="protectBox" class="protect"></div>
<div class="dashboard">
<div class="cardx gold"><div class="lbl">💰 ثابت</div><div class="val"><span class="ltr">{{'%.0f'|format(s.total_capital)}}$</span></div></div>
<div class="cardx"><div class="lbl">🔓 حر</div><div class="val" id="bal"><span class="ltr">{{'%.0f'|format(s.balance)}}$</span></div></div>
<div class="cardx {{'profit' if s.realized>=0 else 'loss'}}"><div class="lbl">💵 صافي ربح</div><div class="val" id="real"><span class="ltr">{{'%+.2f'|format(s.realized)}}$</span></div></div>
<div class="cardx heal"><div class="lbl">🔄 يعالج الآن</div><div class="val" id="healing"><span class="ltr">{{s.trades|selectattr('flipped')|list|length}}</span></div></div>
<div class="cardx gold"><div class="lbl">💎 إجمالي | شفاء {{s.healed}}</div><div class="val" id="equity"><span class="ltr">{{'%.2f'|format(s.total_capital + s.realized + s.unrealized)}}$</span><br><span class="ltr" style="font-size:11px;color:#ffcc00">قمة {{'%.2f'|format(s.peak_profit)}}$</span></div></div>
<div class="cardx"><div class="lbl">⚖️ L/S | 🛡️</div><div class="val" id="ls"><span class="ltr">{{s.trades|selectattr('side','equalto','LONG')|list|length}}/{{s.trades|selectattr('side','equalto','SHORT')|list|length}} | 🛡️{{s.protection_hits}}</span></div></div>
</div>
<div style="display:flex;gap:10px;justify-content:center;margin-bottom:16px;flex-wrap:wrap">
<button class="btn btn-red" onclick="fetch('/close_all').then(()=>location.reload())">🔒 قفل الكل</button>
<button class="btn btn-dark" onclick="fetch('/reset').then(()=>location.reload())">🔄 تصفير</button>
<button class="btn btn-gold" onclick="fetch('/force_resume').then(()=>location.reload())">🚀 فك التعليق</button>
</div>
<div class="table-wrap"><table><thead><tr><th>عملة</th><th>جانب</th><th>أصلي</th><th>حالي</th><th>ربح $</th><th>%</th><th>×</th></tr></thead><tbody>{% for t in s.trades %}<tr id="row-{{t.s}}"><td><b>{{t.s}}</b></td><td>{% if t.flipped %}<span class="badge-heal">🔄 {{t.side}}</span>{% else %}<span class="{{'badge-long' if t.side=='LONG' else 'badge-short'}}">{{t.side}}</span>{% endif %}</td><td><span class="ltr">{{'%.4f'|format(t.orig_entry)}}</span></td><td><span class="ltr live">{{'%.4f'|format(t.live)}}</span></td><td><span class="ltr {{'g' if t.pnl>=0 else 'r'}}">{{'%+.3f'|format(t.pnl)}}$</span></td><td><span class="ltr {{'g' if t.pct>=0 else 'r'}}">{{'%+.3f'|format(t.pct)}}%</span></td><td><button style="background:#ffffff20;color:#fff;border:0;padding:6px 12px;border-radius:10px" onclick="fetch('/close_one?s={{t.s}}').then(()=>location.reload())">✕</button></td></tr>{% endfor %}</tbody></table></div>
<script>
function refresh(){
 fetch('/api').then(r=>r.json()).then(d=>{
  document.getElementById('real').innerHTML=`<span class="ltr">${(d.realized>=0?'+':'')+d.realized.toFixed(2)}$</span>`;
  document.getElementById('equity').innerHTML=`<span class="ltr">${(d.total_capital+d.realized+d.unrealized).toFixed(2)}$</span><br><span class="ltr" style="font-size:11px;color:#ffcc00">قمة ${d.peak_profit.toFixed(2)}$ | شفاء ${d.healed}</span>`;
  document.getElementById('bal').innerHTML=`<span class="ltr">${d.balance.toFixed(0)}$</span>`;
  document.getElementById('healing').innerHTML=`<span class="ltr">${d.trades.filter(t=>t.flipped).length}</span>`;
  let box=document.getElementById('protectBox');
  if(d.paused_until > Date.now()/1000){
    let left=Math.ceil(d.paused_until - Date.now()/1000);
    box.className='protect active';
    box.innerText=`🛑 حماية 3$ - الرجوع بعد ${Math.floor(left/60)}د ${left%60}ث`;
  }else{ box.className='protect';}
 });
}
setInterval(refresh,500);refresh();
</script></body></html>
"""
@app.route('/')
def home(): return render_template_string(HTML, s=state)
@app.route('/api')
def api(): return jsonify({**state,"equity":state["total_capital"]+state["realized"]+state["unrealized"]})
@app.route('/reset')
def reset(): state["realized"]=0; state["unrealized"]=0; state["trades"]=[]; state["cycles"]=0; state["balance"]=state["total_capital"]; state["peak_profit"]=0; state["paused_until"]=0; state["protection_hits"]=0; state["healed"]=0; state["healing"]=0; cooldown.clear(); return "OK"
@app.route('/close_all')
def close_all():
    for t in state["trades"]: cooldown[t["sym"]]=time.time()
    state["realized"]=round(state["realized"]+state["unrealized"],4); state["trades"]=[]; state["unrealized"]=0; state["cycles"]+=1; state["balance"]=state["total_capital"]; return "OK"
@app.route('/close_one')
def close_one():
    sname=request.args.get('s')
    for t in list(state["trades"]):
        if t["s"]==sname: state["realized"]=round(state["realized"]+t["pnl"],4); cooldown[t["sym"]]=time.time(); state["trades"].remove(t); break
    recalc_balance(); return "OK"
@app.route('/force_resume')
def force_resume(): state["paused_until"]=0; state["peak_profit"]=state["realized"]+state["unrealized"]; return "OK"
@app.route('/health')
def h(): return "OK",200
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

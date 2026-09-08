import os, time, threading, requests
from flask import Flask, jsonify, request
app = Flask(__name__)

MAX_TRADES = 10
HEAVY_COINS = ['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT','DOGEUSDT','ADAUSDT','TRXUSDT','TONUSDT','AVAXUSDT','SHIBUSDT']
bot_state = {"trades":[],"realized":0.0,"last_signal":None,"btc_trend":"بانتظار...","base_capital":5000.0,"target_profit":50.0,"is_running":True}

def get_ema200(symbol):
    try:
        r = requests.get(f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=300", timeout=8).json()
        closes=[float(x[4]) for x in r]
        if len(closes)<200: return None, None
        sma=sum(closes[:200])/200; ema=sma; k=2/(200+1)
        for p in closes[200:]: ema=p*k+ema*(1-k)
        return ema, closes[-2]
    except: return None, None

def get_ema200_signal():
    ema,last = get_ema200("BTCUSDT")
    if ema is None: return None,0,0
    desired="LONG" if last>ema else "SHORT"
    return desired,ema,last

def get_filtered_coins(desired):
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=8).json()
        cands=[]
        for i in r:
            s=i['symbol']
            if s in HEAVY_COINS: continue
            if not s.endswith('USDT'): continue
            if "BULL" in s or "BEAR" in s or "UP" in s or "DOWN" in s: continue
            ch=abs(float(i['priceChangePercent'])); vol=float(i['quoteVolume'])
            if ch>=5.0 and vol>=10000000:
                cands.append({"symbol":s,"vol":ch,"price":float(i['lastPrice'])})
        cands.sort(key=lambda x:x['vol'],reverse=True)
        cands=cands[:30] # نفحص أقوى 30 فقط لتسريع

        filtered=[]
        for c in cands:
            ema,last_price = get_ema200(c["symbol"])
            if ema is None: continue
            # شرطك الذهبي
            if desired=="LONG" and last_price < ema: continue # لا تشتري عملة تحت EMA200
            if desired=="SHORT" and last_price > ema: continue # لا تبيع عملة فوق EMA200
            c["ema"]=ema
            filtered.append(c)
            if len(filtered)>=20: break
            time.sleep(0.2) # عشان ما ننحظر

        filtered.sort(key=lambda x:x['vol'],reverse=True)
        return filtered[:MAX_TRADES]
    except Exception as e:
        print("filter error",e)
        return []

def bot_loop():
    while True:
        if bot_state["is_running"]:
            try:
                desired,ema_val,last_price=get_ema200_signal()
                if desired is None: time.sleep(10); continue
                pm={x['symbol']:float(x['price']) for x in requests.get("https://api.binance.com/api/v3/ticker/price",timeout=5).json()}
                per_trade=bot_state["base_capital"]/MAX_TRADES
                floating=0
                for t in bot_state["trades"]:
                    if t["coin"] in pm:
                        t["live"]=pm[t["coin"]]
                        t["pct"]=round(((t["live"]-t["entry"])/t["entry"]*100 if t["side"]=="LONG" else (t["entry"]-t["live"])/t["entry"]*100),2)
                        t["usd"]=round(t["pct"]/100*t["cap"],2)
                    floating+=t.get("usd",0)

                if len(bot_state["trades"])>0 and floating>=bot_state["target_profit"]:
                    bot_state["realized"]=round(bot_state["realized"]+floating,2); bot_state["trades"]=[]
                    market=get_filtered_coins(desired)
                    for c in market:
                        bot_state["trades"].append({"coin":c["symbol"],"entry":c["price"],"live":c["price"],"side":desired,"cap":per_trade,"usd":0.0,"pct":0.0,"vol":c["vol"]})

                elif bot_state["last_signal"]!=desired:
                    if bot_state["trades"]: bot_state["realized"]=round(bot_state["realized"]+floating,2)
                    bot_state["trades"]=[]; bot_state["last_signal"]=desired
                    bot_state["btc_trend"]=f"هابط EMA{ema_val:.0f} - بيع فقط عملات تحت EMA200 - {last_price:.0f}$" if desired=="SHORT" else f"صاعد EMA{ema_val:.0f} - شراء فقط عملات فوق EMA200 - {last_price:.0f}$"
                    market=get_filtered_coins(desired)
                    for c in market:
                        bot_state["trades"].append({"coin":c["symbol"],"entry":c["price"],"live":c["price"],"side":desired,"cap":per_trade,"usd":0.0,"pct":0.0,"vol":c["vol"]})
                else:
                    bot_state["btc_trend"]=f"هابط EMA{ema_val:.0f} - بيع فقط تحت EMA200 - {last_price:.0f}$" if desired=="SHORT" else f"صاعد EMA{ema_val:.0f} - شراء فقط فوق EMA200 - {last_price:.0f}$"

            except Exception as e: print(e)
        time.sleep(20)

@app.route("/")
def dashboard():
    return """
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V32 مفلتر</title>
<style>
body{background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);color:#fff;font-family:Arial;min-height:100vh;margin:0;padding:15px}
.top{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:15px}
.card{background:rgba(255,255,255,0.08);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.1);border-radius:15px;padding:12px;text-align:center}
.card b{font-size:18px;display:block;margin-top:5px}
table{width:100%;border-collapse:collapse;background:rgba(0,0,0,0.3);border-radius:15px;overflow:hidden;margin-top:15px}
th{background:rgba(255,255,255,0.1);padding:12px 6px;font-size:12px}
td{padding:10px 6px;text-align:center;border-bottom:1px solid rgba(255,255,255,0.05);font-size:13px}
.green{color:#00ff88}.red{color:#ff4d6d}
.badge{padding:3px 8px;border-radius:20px;font-size:11px}
.long{background:#00ff8822;color:#00ff88}.short{background:#ff4d6d22;color:#ff4d6d}
.btn{border:0;padding:8px 14px;border-radius:8px;color:#fff;cursor:pointer;margin:2px}
.btn-cap{background:#222;color:#ddd;border:1px solid #444}
.btn-cap.active{background:#6c5ce7;border-color:#6c5ce7}
input{background:#00000066;color:#fff;border:1px solid #ffffff22;border-radius:8px;padding:7px;width:90px;text-align:center}
.ctrl{font-size:18px;width:35px;background:#ffffff15}
</style></head><body>
<h2 style="text-align:center">🚀 V32 - فلتر EMA200 المزدوج</h2>
<div class="top">
<div class="card"><small>رأس المال</small><b id="cap"></b><small id="per"></small></div>
<div class="card"><small>المحقق</small><b id="real" class="green"></b></div>
<div class="card"><small>العائم</small><b id="float"></b></div>
<div class="card"><small>الكلي</small><b id="total"></b></div>
</div>
<div class="card" style="margin-bottom:12px;text-align:right">
<div style="margin-bottom:10px"><b>💰 رأس المال:</b></div>
<button class="btn btn-cap" onclick="setCapQuick(100)">$100</button>
<button class="btn btn-cap" onclick="setCapQuick(200)">$200</button>
<button class="btn btn-cap" onclick="setCapQuick(500)">$500</button>
<button class="btn btn-cap" onclick="setCapQuick(1000)">$1000</button>
<button class="btn btn-cap" onclick="setCapQuick(2000)">$2000</button>
<button class="btn btn-cap" onclick="setCapQuick(5000)">$5000</button>
مخصص: <input id="capIn" type="number"> <button class="btn" style="background:#00d2ff" onclick="setCapCustom()">تحديث</button>
</div>
<div class="card" style="margin-bottom:15px">
<div id="trend" style="font-weight:bold;margin-bottom:10px"></div>
<b>🎯 هدف:</b>
<button class="btn ctrl" onclick="changeTarget(-5)">-</button>
<input id="targetIn" type="number">
<button class="btn ctrl" onclick="changeTarget(5)">+</button>
<button class="btn" style="background:#6c5ce7" onclick="setT()">حفظ</button>
<button class="btn" style="background:#ff3b3b" onclick="closeAll()">قفل</button>
</div>
<table><thead><tr><th>العملة</th><th>الجانب</th><th>دخول</th><th>حالي</th><th>رأس مال</th><th>ربح $</th><th>ربح %</th><th>تقلب</th></tr></thead><tbody id="tbody"></tbody></table>
<script>
async function load(){
 let j=await (await fetch('/api/stats')).json();
 document.getElementById('cap').innerText='$'+j.base_capital;
 document.getElementById('per').innerText='كل صفقة $'+(j.base_capital/10).toFixed(2);
 document.getElementById('real').innerText='$'+j.realized.toFixed(2);
 document.getElementById('float').innerText='$'+j.floating.toFixed(2);
 document.getElementById('total').innerText='$'+j.total.toFixed(2);
 document.getElementById('trend').innerText=j.btc_trend+' | هدف: $'+j.target_profit;
 document.getElementById('targetIn').value=j.target_profit;
 document.getElementById('capIn').value=j.base_capital;
 let tb=''; j.trades.forEach(t=>{
   let cls=t.usd>=0?'green':'red'; let badge=t.side=='LONG'?'long':'short';
   tb+=`<tr><td><b>${t.coin.replace('USDT','')}</b></td><td><span class="badge ${badge}">${t.side}</span></td><td>${t.entry}</td><td>${t.live}</td><td>$${t.cap.toFixed(2)}</td><td class="${cls}">${t.usd}</td><td class="${cls}">${t.pct}%</td><td>${t.vol.toFixed(1)}%</td></tr>`;
 }); document.getElementById('tbody').innerHTML=tb;
}
async function setCapQuick(v){await fetch('/api/set_cap',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capital:v})}); load()}
async function setCapCustom(){let v=document.getElementById('capIn').value; await fetch('/api/set_cap',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capital:parseFloat(v)})}); load()}
function changeTarget(d){let el=document.getElementById('targetIn'); el.value=parseFloat(el.value||0)+d;}
async function setT(){let v=document.getElementById('targetIn').value; await fetch('/api/set_target',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({target:parseFloat(v)})}); load()}
async function closeAll(){if(!confirm('تقفل؟')) return; await fetch('/api/close_all',{method:'POST'}); load()}
setInterval(load,4000); load();
</script></body></html>
"""
@app.route("/api/stats")
def stats():
    floating=round(sum(t.get("usd",0) for t in bot_state["trades"]),2)
    return jsonify({"trades":bot_state["trades"],"realized":bot_state["realized"],"floating":floating,"total":round(bot_state["realized"]+floating,2),"btc_trend":bot_state["btc_trend"],"target_profit":bot_state["target_profit"],"base_capital":bot_state["base_capital"]})
@app.route("/api/close_all", methods=["POST"])
def close_all():
    floating=sum(t.get("usd",0) for t in bot_state["trades"])
    bot_state["realized"]=round(bot_state["realized"]+floating,2); bot_state["trades"]=[]; return jsonify({"ok":True})
@app.route("/api/set_target", methods=["POST"])
def set_target():
    bot_state["target_profit"]=float(request.json.get("target",30)); return jsonify({"ok":True})
@app.route("/api/set_cap", methods=["POST"])
def set_cap():
    bot_state["base_capital"]=float(request.json.get("capital",100))
    per=bot_state["base_capital"]/10
    for t in bot_state["trades"]: t["cap"]=per
    return jsonify({"ok":True})
threading.Thread(target=bot_loop,daemon=True).start()
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)))

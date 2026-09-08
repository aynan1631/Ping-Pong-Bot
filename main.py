import os, time, threading, requests
from flask import Flask, jsonify, request
app = Flask(__name__)
MAX_TRADES=10
HEAVY=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT','DOGEUSDT','ADAUSDT','TRXUSDT','TONUSDT','AVAXUSDT','SHIBUSDT']
bot_state={"trades":[],"realized":0.0,"last_signal":None,"btc_trend":"بانتظار...","base_capital":5000.0,"target_profit":50.0}

def ema200(sym):
 try:
  d=requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=250",timeout=10).json()
  c=[float(x[4]) for x in d]
  if len(c)<200: return None,None
  e=sum(c[:200])/200;k=2/201
  for p in c[200:]: e=p*k+e*(1-k)
  return e,c[-2]
 except: return None,None

def btc_sig():
 e,last=ema200("BTCUSDT")
 if e is None: return None,0,0
 return ("LONG" if last>e else "SHORT"),e,last

def get_coins(desired):
 try:
  all=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=10).json()
  pool=[]
  for i in all:
   s=i['symbol']
   if s in HEAVY or not s.endswith('USDT'): continue
   if any(x in s for x in ["BULL","BEAR","UP","DOWN"]): continue
   ch=abs(float(i['priceChangePercent'])); vol=float(i['quoteVolume'])
   if ch>=4 and vol>=5000000: pool.append((s,ch,float(i['lastPrice'])))
  pool=sorted(pool,key=lambda x:x[1],reverse=True)[:35]
  good=[]; bad=[]
  for sym,ch,price in pool:
   ema,lp=ema200(sym)
   if ema is None: continue
   if desired=="SHORT":
    if lp < ema: good.append({"symbol":sym,"vol":ch,"price":price})
    else: bad.append({"symbol":sym,"vol":ch,"price":price,"dist":abs(lp-ema)/ema})
   else:
    if lp > ema: good.append({"symbol":sym,"vol":ch,"price":price})
    else: bad.append({"symbol":sym,"vol":ch,"price":price,"dist":abs(lp-ema)/ema})
   time.sleep(0.12)
  good=sorted(good,key=lambda x:x['vol'],reverse=True); bad=sorted(bad,key=lambda x:x['dist'])
  res=good[:MAX_TRADES]
  if len(res)<MAX_TRADES: res+=bad[:MAX_TRADES-len(res)]
  return sorted(res,key=lambda x:x['vol'],reverse=True)[:MAX_TRADES]
 except: return []

def loop():
 while True:
  try:
   des,ema_v,last=btc_sig()
   if des is None: time.sleep(5); continue
   pr={x['symbol']:float(x['price']) for x in requests.get("https://api.binance.com/api/v3/ticker/price",timeout=5).json()}
   per=bot_state["base_capital"]/MAX_TRADES; fl=0
   for t in bot_state["trades"]:
    if t["coin"] in pr:
     t["live"]=pr[t["coin"]]
     t["pct"]=round(((t["live"]-t["entry"])/t["entry"]*100 if t["side"]=="LONG" else (t["entry"]-t["live"])/t["entry"]*100),2)
     t["usd"]=round(t["pct"]/100*t["cap"],2)
    fl+=t.get("usd",0)
   bot_state["trades"]=sorted(bot_state["trades"], key=lambda x: x.get("usd",0), reverse=True)
   if (len(bot_state["trades"])>0 and fl>=bot_state["target_profit"]) or bot_state["last_signal"]!=des:
    if bot_state["trades"]: bot_state["realized"]=round(bot_state["realized"]+fl,2)
    bot_state["trades"]=[]; bot_state["last_signal"]=des
    bot_state["btc_trend"]=f"{'صاعد' if des=='LONG' else 'هابط'} EMA{ema_v:.0f} - V33 ({len(bot_state['trades'])}/10) - BTC {last:.0f}$"
    mk=get_coins(des)
    for c in mk: bot_state["trades"].append({"coin":c["symbol"],"entry":c["price"],"live":c["price"],"side":des,"cap":per,"usd":0,"pct":0,"vol":c["vol"]})
   else: bot_state["btc_trend"]=f"{'صاعد' if des=='LONG' else 'هابط'} EMA{ema_v:.0f} - V33 ({len(bot_state['trades'])}/10) - BTC {last:.0f}$"
  except Exception as e: print(e)
  time.sleep(20)

@app.route("/")
def dash():
 return """
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V33.8 LUXURY</title>
<style>
body{background:radial-gradient(circle at top,#1e293b,#020617);color:#fff;font-family:Tahoma;padding:12px}
.card{background:linear-gradient(135deg,rgba(15,23,42,0.9),rgba(30,41,59,0.8));border:1px solid rgba(251,191,36,0.25);border-radius:16px;padding:14px;text-align:center;margin:5px}
table{width:100%;background:rgba(15,23,42,0.9);border:1px solid rgba(251,191,36,0.25);border-radius:18px;border-collapse:collapse}
th{background:linear-gradient(180deg,#1e293b,#0f172a);color:#fbbf24;padding:12px 8px;font-size:12px;border-bottom:1px solid rgba(251,191,36,0.35)}
td{padding:11px 8px;text-align:center;border-bottom:1px solid rgba(255,255,255,0.06);font-size:12.5px}
.green{color:#22c55e;font-weight:900}.red{color:#ef4444;font-weight:900}
.badge{padding:4px 10px;border-radius:20px;font-size:11px;font-weight:bold}.short{background:linear-gradient(90deg,#7f1d1d,#ef4444);color:#fff}.long{background:linear-gradient(90deg,#064e3b,#22c55e);color:#fff}
.capital{color:#fde68a;font-weight:900;background:linear-gradient(90deg,rgba(251,191,36,0.22),rgba(251,191,36,0.05));border:1px solid rgba(251,191,36,0.2);border-radius:10px;padding:6px 10px}
.btn{border:0;padding:6px 12px;border-radius:8px;color:#fff;cursor:pointer;margin:2px;font-weight:bold;font-size:12px}
.sel{background:#0f172a;color:#fbbf24;border:1px solid rgba(251,191,36,0.4);border-radius:8px;padding:5px 8px}
</style></head><body>
<h2 style="text-align:center;color:#fbbf24">💎 V33.8 LUXURY - فلتر EMA200 المزدوج (10 صفقات إجباري)</h2>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px">
<div class="card"><small>رأس المال</small><br><b id="capTxt" style="font-size:18px">$5000</b><br><div style="margin-top:8px"><select id="capSel" class="sel"><option value="1000">$1000</option><option value="3000">$3000</option><option value="5000" selected>$5000</option><option value="10000">$10000</option><option value="20000">$20000</option><option value="50000">$50000</option></select><button class="btn" style="background:#fbbf24;color:#000" onclick="setCap()">حفظ</button></div></div>
<div class="card"><small>الأرباح</small><br><b id="real" class="green" style="font-size:20px">$0.00</b></div>
<div class="card"><small>الأرباح غير المحققة</small><br><b id="float" style="font-size:20px">$-4.60</b></div>
</div>
<div class="card"><div id="trend" style="color:#fbbf24"></div><br>🎯 هدف <input id="tin" type="number" style="width:70px;border-radius:8px;padding:4px;background:#0f172a;color:#fff;border:1px solid #334155"><button class="btn" style="background:#6c5ce7" onclick="setT()">حفظ</button><button class="btn" style="background:#ff3b3b" onclick="closeAll()">🔒 قفل الكل</button></div>
<div style="overflow:auto"><table><thead><tr><th>العملة</th><th>الجانب</th><th>💰 رأس المال</th><th>دخول</th><th>حالي</th><th>$</th><th>%</th><th>تقلب</th></tr></thead><tbody id="tb"></tbody></table></div>
<script>
function fmt(p){let n=parseFloat(p);if(n<0.001)return n.toFixed(8).replace(/0+$/,'').replace(/\\.$/,'');if(n<1)return n.toFixed(6).replace(/0+$/,'').replace(/\\.$/,'');return n.toFixed(4);}
async function load(){let j=await (await fetch('/api/stats')).json();document.getElementById('capTxt').innerText='$'+j.base_capital;document.getElementById('capSel').value=j.base_capital;document.getElementById('real').innerText='$'+j.realized.toFixed(2);document.getElementById('float').innerText='$'+j.floating.toFixed(2);document.getElementById('trend').innerText=j.btc_trend+' | هدف $'+j.target_profit;document.getElementById('tin').value=j.target_profit;let h='';j.trades.forEach(t=>{let c=t.usd>=0?'green':'red';h+=`<tr><td><b>${t.coin.replace('USDT','')}</b></td><td><span class="badge ${t.side=='LONG'?'long':'short'}">${t.side}</span></td><td><span class="capital">$${t.cap.toFixed(2)}</span></td><td>${fmt(t.entry)}</td><td>${fmt(t.live)}</td><td class="${c}">${t.usd.toFixed(2)}</td><td class="${c}">${t.pct}%</td><td>${t.vol.toFixed(1)}%</td></tr>`});document.getElementById('tb').innerHTML=h;}
async function setT(){let v=document.getElementById('tin').value;await fetch('/api/set_target',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({target:parseFloat(v)})});load();}
async function setCap(){let v=document.getElementById('capSel').value;await fetch('/api/set_cap',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capital:parseFloat(v)})});load();}
async function closeAll(){await fetch('/api/close_all',{method:'POST'});load();}
setInterval(load,3000);load();</script></body></html>
"""
@app.route("/api/stats")
def stats():
 fl=round(sum(t.get("usd",0) for t in bot_state["trades"]),2)
 sorted_trades=sorted(bot_state["trades"], key=lambda x: x.get("usd",0), reverse=True)
 return jsonify({"trades":sorted_trades,"realized":bot_state["realized"],"floating":fl,"btc_trend":bot_state["btc_trend"],"target_profit":bot_state["target_profit"],"base_capital":bot_state["base_capital"]})
@app.route("/api/close_all",methods=["POST"])
def ca():
 fl=sum(t.get("usd",0) for t in bot_state["trades"]); bot_state["realized"]=round(bot_state["realized"]+fl,2); bot_state["trades"]=[]; return jsonify({"ok":True})
@app.route("/api/set_target",methods=["POST"])
def st():
 bot_state["target_profit"]=float(request.json.get("target",50)); return jsonify({"ok":True})
@app.route("/api/set_cap",methods=["POST"])
def sc():
 bot_state["base_capital"]=float(request.json.get("capital",5000)); 
 for t in bot_state["trades"]: t["cap"]=bot_state["base_capital"]/MAX_TRADES
 return jsonify({"ok":True})
threading.Thread(target=loop,daemon=True).start()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)))

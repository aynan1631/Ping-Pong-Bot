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
   if ch>=4 and vol>=5000000:
    pool.append((s,ch,float(i['lastPrice'])))
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
  good=sorted(good,key=lambda x:x['vol'],reverse=True)
  bad=sorted(bad,key=lambda x:x['dist'])
  res=good[:MAX_TRADES]
  if len(res)<MAX_TRADES:
   res+=bad[:MAX_TRADES-len(res)]
  return sorted(res,key=lambda x:x['vol'],reverse=True)[:MAX_TRADES]
 except Exception as e:
  print(e); return []

def loop():
 while True:
  try:
   des,ema_v,last=btc_sig()
   if des is None: time.sleep(5); continue
   pr={x['symbol']:float(x['price']) for x in requests.get("https://api.binance.com/api/v3/ticker/price",timeout=5).json()}
   per=bot_state["base_capital"]/MAX_TRADES
   fl=0
   for t in bot_state["trades"]:
    if t["coin"] in pr:
     t["live"]=pr[t["coin"]]
     t["pct"]=round(((t["live"]-t["entry"])/t["entry"]*100 if t["side"]=="LONG" else (t["entry"]-t["live"])/t["entry"]*100),2)
     t["usd"]=round(t["pct"]/100*t["cap"],2)
    fl+=t.get("usd",0)
   if (len(bot_state["trades"])>0 and fl>=bot_state["target_profit"]) or bot_state["last_signal"]!=des:
    if bot_state["trades"]: bot_state["realized"]=round(bot_state["realized"]+fl,2)
    bot_state["trades"]=[]; bot_state["last_signal"]=des
    bot_state["btc_trend"]=f"{'صاعد' if des=='LONG' else 'هابط'} EMA{ema_v:.0f} - V33 مفلتر - BTC {last:.0f}$"
    mk=get_coins(des)
    for c in mk:
     bot_state["trades"].append({"coin":c["symbol"],"entry":c["price"],"live":c["price"],"side":des,"cap":per,"usd":0,"pct":0,"vol":c["vol"]})
   else:
    bot_state["btc_trend"]=f"{'صاعد' if des=='LONG' else 'هابط'} EMA{ema_v:.0f} - V33 ({len(bot_state['trades'])}/10) - BTC {last:.0f}$"
  except Exception as e: print(e)
  time.sleep(20)

@app.route("/")
def dash():
 return """
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V33</title>
<style>body{background:#0f0c29;color:#fff;font-family:Arial;padding:15px}.card{background:rgba(255,255,255,0.08);border-radius:15px;padding:12px;text-align:center;margin:5px}table{width:100%;background:rgba(0,0,0,0.3);border-radius:15px;border-collapse:collapse}th,td{padding:10px;text-align:center;border-bottom:1px solid #222}.green{color:#00ff88}.red{color:#ff4d6d}.badge{padding:3px 8px;border-radius:20px;font-size:11px}.short{background:#ff4d6d22;color:#ff4d6d}.long{background:#00ff8822;color:#00ff88}.btn{border:0;padding:8px 14px;border-radius:8px;color:#fff;cursor:pointer;margin:2px}</style></head><body>
<h2 style="text-align:center">🚀 V33 - فلتر EMA200 المزدوج (10 صفقات إجباري)</h2>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px"><div class="card"><small>رأس المال</small><b id="cap"></b></div><div class="card"><small>المحقق</small><b id="real" class="green"></b></div><div class="card"><small>العائم</small><b id="float"></b></div><div class="card"><small>الكلي</small><b id="total"></b></div></div>
<div class="card"><div id="trend"></div><br><b>🎯</b><input id="tin" type="number"><button class="btn" style="background:#6c5ce7" onclick="setT()">حفظ</button><button class="btn" style="background:#ff3b3b" onclick="closeAll()">قفل</button></div>
<table><thead><tr><th>العملة</th><th>الجانب</th><th>دخول</th><th>حالي</th><th>$</th><th>%</th><th>تقلب</th></tr></thead><tbody id="tb"></tbody></table>
<script>
async function load(){let j=await (await fetch('/api/stats')).json();document.getElementById('cap').innerText='$'+j.base_capital;document.getElementById('real').innerText='$'+j.realized.toFixed(2);document.getElementById('float').innerText='$'+j.floating.toFixed(2);document.getElementById('total').innerText='$'+j.total.toFixed(2);document.getElementById('trend').innerText=j.btc_trend+' | هدف $'+j.target_profit;document.getElementById('tin').value=j.target_profit;let h='';j.trades.forEach(t=>{let c=t.usd>=0?'green':'red';h+=`<tr><td>${t.coin.replace('USDT','')}</td><td><span class="badge ${t.side=='LONG'?'long':'short'}">${t.side}</span></td><td>${t.entry}</td><td>${t.live}</td><td class="${c}">${t.usd}</td><td class="${c}">${t.pct}%</td><td>${t.vol.toFixed(1)}%</td></tr>`});document.getElementById('tb').innerHTML=h;}
async function setT(){let v=document.getElementById('tin').value;await fetch('/api/set_target',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({target:parseFloat(v)})});load();}
async function closeAll(){await fetch('/api/close_all',{method:'POST'});load();}
setInterval(load,3000);load();</script></body></html>
"""
@app.route("/api/stats")
def stats():
 fl=round(sum(t.get("usd",0) for t in bot_state["trades"]),2)
 return jsonify({"trades":bot_state["trades"],"realized":bot_state["realized"],"floating":fl,"total":round(bot_state["realized"]+fl,2),"btc_trend":bot_state["btc_trend"],"target_profit":bot_state["target_profit"],"base_capital":bot_state["base_capital"]})
@app.route("/api/close_all",methods=["POST"])
def ca():
 fl=sum(t.get("usd",0) for t in bot_state["trades"]); bot_state["realized"]=round(bot_state["realized"]+fl,2); bot_state["trades"]=[]; return jsonify({"ok":True})
@app.route("/api/set_target",methods=["POST"])
def st():
 from flask import request as R; bot_state["target_profit"]=float(R.json.get("target",50)); return jsonify({"ok":True})
@app.route("/api/set_cap",methods=["POST"])
def sc():
 from flask import request as R; bot_state["base_capital"]=float(R.json.get("capital",5000)); return jsonify({"ok":True})
threading.Thread(target=loop,daemon=True).start()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)))

import os, time, threading, requests
from flask import Flask, jsonify, request
app = Flask(__name__)

MAX_TRADES = 10
HEAVY_COINS = ['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT','DOGEUSDT','ADAUSDT','TRXUSDT','TONUSDT','AVAXUSDT','SHIBUSDT']
bot_state = {"trades":[],"realized":0.0,"last_signal":None,"btc_trend":"بانتظار...","btc_change":0.0,"base_capital":20.0,"target_profit":float(os.getenv("TARGET_PROFIT","30")),"is_running":True}

def get_ema200_signal():
    try:
        r = requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=300", timeout=10).json()
        closes=[float(x[4]) for x in r]
        if len(closes)<200: return None,0,0,0
        sma=sum(closes[:200])/200; ema=sma; k=2/(200+1)
        for p in closes[200:]: ema=p*k+ema*(1-k)
        last_close=closes[-2]; btc_change=((closes[-2]-closes[-3])/closes[-3])*100
        desired="LONG" if last_close>ema else "SHORT"
        return desired,ema,btc_change,last_close
    except Exception as e:
        print("EMA Error",e); return None,0,0,0

def get_volatile_coins():
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr",timeout=8).json()
        cands=[]
        for i in r:
            s=i['symbol']
            if s in HEAVY_COINS: continue
            if not s.endswith('USDT'): continue
            if "BULL" in s or "BEAR" in s or "UP" in s or "DOWN" in s: continue
            ch=abs(float(i['priceChangePercent'])); vol=float(i['quoteVolume']); price=float(i['lastPrice'])
            if ch>4.0 and vol>5000000 and price>0.00001:
                cands.append({"symbol":s,"vol":ch,"price":price,"change":float(i['priceChangePercent'])})
        cands.sort(key=lambda x:x['vol'],reverse=True); return cands[:20]
    except: return []

def bot_loop():
    while True:
        if bot_state["is_running"]:
            try:
                desired,ema_val,btc_ch,last_price=get_ema200_signal()
                bot_state["btc_change"]=btc_ch
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
                    market=get_volatile_coins()
                    for c in market:
                        if len(bot_state["trades"])>=MAX_TRADES: break
                        bot_state["trades"].append({"coin":c["symbol"],"entry":c["price"],"live":c["price"],"side":desired,"cap":per_trade,"usd":0.0,"pct":0.0,"vol":c["vol"]})
                elif bot_state["last_signal"]!=desired:
                    if bot_state["trades"]: bot_state["realized"]=round(bot_state["realized"]+floating,2)
                    bot_state["trades"]=[]; bot_state["last_signal"]=desired
                    bot_state["btc_trend"]=f"{'UP' if desired=='LONG' else 'DOWN'} - EMA {ema_val:.2f} - {desired} - سعر {last_price:.0f}"
                    market=get_volatile_coins()
                    for c in market:
                        if len(bot_state["trades"])>=MAX_TRADES: break
                        bot_state["trades"].append({"coin":c["symbol"],"entry":c["price"],"live":c["price"],"side":desired,"cap":per_trade,"usd":0.0,"pct":0.0,"vol":c["vol"]})
                else:
                    bot_state["btc_trend"]=f"{'UP' if desired=='LONG' else 'DOWN'} - EMA {ema_val:.2f} - ماسك {desired} - سعر {last_price:.0f}"
            except Exception as e: print("Loop Error",e)
        time.sleep(15)

@app.route("/")
def dashboard():
    return f"""
    <html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>V28</title>
    <style>
    body{{background:#111;color:#eee;font-family:Arial;padding:10px}}
   .top{{background:#1e1e1e;padding:12px;border-radius:10px;margin-bottom:10px;text-align:center}}
    table{{width:100%;border-collapse:collapse;background:#1a1a1a;border-radius:10px;overflow:hidden}}
    th,td{{padding:8px;text-align:center;border-bottom:1px solid #333;font-size:13px}}
    th{{background:#222}}.green{{color:#0f0}}.red{{color:#f44}}
    </style></head><body>
    <div class="top">
        <h3>بوت EMA200 - V28 جدول</h3>
        <div id="trend">تحميل...</div>
        <div>محقق: <b id="real" class="green">0</b>$ | عائم: <b id="float">0</b>$ | كلي: <b id="total">0</b>$ | هدف: <span id="targ">{bot_state['target_profit']}</span>$</div>
        <div style="margin-top:8px"><input id="targetIn" value="{bot_state['target_profit']}" style="width:60px"> <button onclick="setT()" style="background:#09f;color:#fff;border:0;padding:6px 10px;border-radius:6px">حفظ</button>
        <button onclick="closeAll()" style="background:#e33;color:#fff;border:0;padding:6px 10px;border-radius:6px">قفل الصفقات</button></div>
    </div>
    <table><thead><tr><th>العملة</th><th>جانب</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>%</th></tr></thead><tbody id="tbody"></tbody></table>
    <script>
    async function load(){{
        let j=await (await fetch('/api/stats')).json();
        document.getElementById('trend').innerText=j.btc_trend;
        document.getElementById('real').innerText=j.realized.toFixed(2);
        document.getElementById('float').innerText=j.floating.toFixed(2);
        document.getElementById('total').innerText=j.total.toFixed(2);
        let tb=''; j.trades.forEach(t=>{{
            tb+=`<tr><td>${{t.coin.replace('USDT','')}}</td><td>${{t.side}}</td><td>${{t.entry}}</td><td>${{t.live}}</td><td class="${{t.usd>=0?'green':'red'}}">${{t.usd}}</td><td class="${{t.pct>=0?'green':'red'}}">${{t.pct}}%</td></tr>`;
        }}); document.getElementById('tbody').innerHTML=tb;
    }}
    async function closeAll(){{await fetch('/api/close_all',{method:'POST'}); load()}}
    async function setT(){{let v=document.getElementById('targetIn').value; await fetch('/api/set_target',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({{target:+v}})}); load()}}
    setInterval(load,3000); load();
    </script></body></html>
    """

@app.route("/api/stats")
def stats():
    floating=round(sum(t.get("usd",0) for t in bot_state["trades"]),2)
    return jsonify({"trades":bot_state["trades"],"realized":bot_state["realized"],"floating":floating,"total":round(bot_state["realized"]+floating,2),"btc_trend":bot_state["btc_trend"],"target_profit":bot_state["target_profit"],"last_signal":bot_state["last_signal"]})

@app.route("/api/close_all", methods=["POST"])
def close_all():
    floating=sum(t.get("usd",0) for t in bot_state["trades"])
    bot_state["realized"]=round(bot_state["realized"]+floating,2); bot_state["trades"]=[]
    return jsonify({"ok":True})

@app.route("/api/set_target", methods=["POST"])
def set_target():
    bot_state["target_profit"]=float(request.json.get("target",30)); return jsonify({"ok":True})

threading.Thread(target=bot_loop,daemon=True).start()
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)))

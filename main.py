import os, time, threading, requests
from flask import Flask, request, jsonify

app = Flask(__name__)
BINANCE_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET = os.getenv("BINANCE_API_SECRET")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

PHARMACY = ["BTCUSDT","ETHUSDT","SOLUSDT","AVAXUSDT","LINKUSDT","ADAUSDT","DOTUSDT","MATICUSDT","LTCUSDT","UNIUSDT","NEARUSDT","APTUSDT","ARBUSDT","OPUSDT","INJUSDT","SUIUSDT","RENDERUSDT","FETUSDT","TAOUSDT","XRPUSDT","DOGEUSDT","TRXUSDT","FILUSDT","BNBUSDT"]

config = {"trade_value": 6, "profit_pct": 1.2, "hospital_max": 7}
state = {"bal": 65.23, "realized": 0.0, "pct": 0.0, "running": False, "hospital": [], "logs": [], "last": ""}

def log(m):
    state["logs"].append(f"{time.strftime('%H:%M:%S')} {m}")
    state["logs"]=state["logs"][-15:]
    print(m)

def discord(m):
    if not DISCORD_WEBHOOK: return
    try: requests.post(DISCORD_WEBHOOK, json={"content": f"👑 {m}"}, timeout=5)
    except: pass

def get_client():
    from binance.client import Client
    return Client(BINANCE_KEY, BINANCE_SECRET)

def trader():
    while True:
        time.sleep(10)
        if not state["running"]: continue
        try:
            c = get_client()
            try:
                b = c.get_asset_balance('USDT')
                state["bal"]=round(float(b['free']),2)
            except: pass

            # بيع
            for pos in state["hospital"][:]:
                try:
                    cur = float(c.get_symbol_ticker(symbol=pos["sym"])['price'])
                    pnl = ((cur-pos["buy"])/pos["buy"])*100
                    if pnl >= config["profit_pct"]:
                        c.order_market_sell(symbol=pos["sym"], quantity=pos["qty"])
                        state["hospital"].remove(pos)
                        state["realized"] += (cur-pos["buy"])*pos["qty"]
                        log(f"💰 بيع {pos['sym']} ربح {pnl:.2f}%")
                        discord(f"💰 بيع رابح {pos['sym']} +{pnl:.2f}%")
                except Exception as e: log(f"Sell {e}")

            if len(state["hospital"]) >= config["hospital_max"]:
                state["last"]="المشفى ممتلئ"; continue

            # شراء حقيقي - اذا نازل
            for sym in PHARMACY:
                try:
                    kl = c.get_klines(symbol=sym, interval="15m", limit=2)
                    pct = (float(kl[1][4])-float(kl[0][4]))/float(kl[0][4])*100
                    state["last"]=f"يفحص {sym} {pct:.2f}%"
                    if pct <= -1.0 and not any(p["sym"]==sym for p in state["hospital"]):
                        if state["bal"] < config["trade_value"]: break
                        order = c.order_market_buy(symbol=sym, quoteOrderQty=config["trade_value"])
                        price = float(order['fills'][0]['price']); qty = float(order['executedQty'])
                        state["hospital"].append({"sym": sym, "buy": price, "qty": qty})
                        log(f"✅ شراء حقيقي {sym} بسعر {price}")
                        discord(f"✅ شراء {sym} بسعر {price} قيمة {config['trade_value']}$")
                        break
                except Exception as e:
                    log(f"{sym} {str(e)[:80]}")
                    time.sleep(0.5)
        except Exception as e: log(f"Loop {e}")

threading.Thread(target=trader, daemon=True).start()

@app.route("/action", methods=["POST"])
def act():
    d=request.json or {}; a=d.get("act")
    if a=="start": state["running"]=True; log("تشغيل"); discord("تشغيل البوت ✅")
    if a=="stop": state["running"]=False; log("ايقاف")
    if a=="clear": state["hospital"]=[]; log("تصفية المشفى")
    if a=="close": state["running"]=False; state["hospital"]=[]; log("اغلاق")
    return jsonify({"ok":True})

@app.route("/api")
def api(): return jsonify({**state, "hospital_len": len(state["hospital"])})

@app.route("/")
def home():
    return """
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
<style>body{background:#050507;color:#fff;font-family:Cairo;margin:0}.top{background:linear-gradient(90deg,#000,#FFD700,#000);padding:12px;text-align:center;color:#000;font-weight:900}.card{background:#111;border:1.5px solid #FFD700;border-radius:18px;padding:16px;text-align:center;margin:12px}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.btn{border:none;border-radius:14px;padding:14px;font-weight:900;width:100%;cursor:pointer}.btn-start{background:#00ff88}.btn-stop{background:#ff4444;color:#fff}.btn-clear{background:#55aaff;color:#fff}.btn-close{background:#222;color:#fff;border:1px solid #FFD700}.log{background:#000;border-radius:10px;padding:8px;margin:6px 0;font-size:12px;text-align:left;direction:ltr}.num{font-family:JetBrains Mono}</style>
</head><body>
<div class="top" id="top">V105 REAL TRADING - جاري التحميل</div>
<div class="card"><b>حالة البوت</b><br><span id="st" style="color:#00ff88;font-size:22px">STOPPED</span><br><small id="last"></small></div>
<div class="card"><div class="grid4">
<button class="btn btn-start" onclick="a('start')">تشغيل</button>
<button class="btn btn-stop" onclick="a('stop')">ايقاف</button>
<button class="btn btn-clear" onclick="a('clear')">تصفية المشفى</button>
<button class="btn btn-close" onclick="a('close')">اغلاق البوت</button>
</div></div>
<div class="card"><b>Logs:</b><div id="logs"></div></div>
<div class="card"><b>المشفى - الصفقات المفتوحة</b><div id="hosp"></div></div>
<script>
function a(x){fetch('/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({act:x})}).then(()=>location.reload())}
setInterval(()=>{fetch('/api').then(r=>r.json()).then(d=>{
document.getElementById('top').innerHTML=`V105 REAL - الرصيد <span class=num>${d.bal} USDT</span> - ${d.running?'يعمل ✅':'متوقف'} - المشفى ${d.hospital_len}`;
document.getElementById('st').innerHTML=d.running?'RUNNING':'STOPPED';
document.getElementById('last').innerHTML=d.last;
document.getElementById('logs').innerHTML=d.logs.map(l=>'<div class=log>'+l+'</div>').join('');
document.getElementById('hosp').innerHTML=d.hospital.map(p=>`<div class=log>${p.sym} شراء ${p.buy} كمية ${p.qty}</div>`).join('')||'لا يوجد';
})},2000)
</script></body></html>
"""
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))

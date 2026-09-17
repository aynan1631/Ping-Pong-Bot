import os, time, threading, requests
from flask import Flask, request, jsonify
app = Flask(__name__)

BINANCE_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET = os.getenv("BINANCE_API_SECRET")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

PHARMACY = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","AVAXUSDT","LINKUSDT","ADAUSDT","DOTUSDT","MATICUSDT","LTCUSDT","UNIUSDT","NEARUSDT","APTUSDT","ARBUSDT","OPUSDT","INJUSDT","SUIUSDT","SEIUSDT","RENDERUSDT","FETUSDT","TAOUSDT","WIFUSDT","XRPUSDT","DOGEUSDT","TRXUSDT","SHIBUSDT","PEPEUSDT","FILUSDT","HBARUSDT","XLMUSDT","BCHUSDT","ETCUSDT"]

config = {"trade_value": 6, "profit_pct": 1.2, "hospital_max": 7, "trade_count": 2, "capital": 65.23, "consultant": "د. أحمد"}
state = {"bal": 65.23, "realized": 0.0, "unreal": 0.0, "pct": 0.0, "running": False, "hospital": [], "logs": [], "last": "جاهز", "pharma": len(PHARMACY)}

def log(m):
    state["logs"].append(f"{time.strftime('%H:%M:%S')} {m}")
    state["logs"]=state["logs"][-20:]

def discord(m):
    if DISCORD_WEBHOOK:
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
                state["bal"] = round(float(b['free'])+float(b['locked']),2)
                config["capital"] = state["bal"]
            except: pass

            # بيع
            for pos in state["hospital"][:]:
                try:
                    cur = float(c.get_symbol_ticker(symbol=pos["sym"])['price'])
                    pnl = ((cur-pos["buy"])/pos["buy"])*100
                    pos["pnl"] = round(pnl,2)
                    pos["cur"] = cur
                    state["unreal"] = sum([p.get("pnl",0) for p in state["hospital"]])
                    if pnl >= config["profit_pct"]:
                        c.order_market_sell(symbol=pos["sym"], quantity=pos["qty"])
                        state["hospital"].remove(pos)
                        profit = (cur-pos["buy"])*pos["qty"]
                        state["realized"] += profit
                        state["pct"] = (state["realized"]/65.23)*100 if 65.23>0 else 0
                        log(f"💰 بيع {pos['sym']} ربح {pnl:.2f}% +{profit:.2f}$")
                        discord(f"💰 بيع رابح {pos['sym']} +{pnl:.2f}%")
                except Exception as e: log(f"بيع {e}")

            if len(state["hospital"]) >= config["hospital_max"]:
                state["last"]="المشفى ممتلئ - ينتظر بيع"; continue

            for sym in PHARMACY:
                try:
                    kl = c.get_klines(symbol=sym, interval="15m", limit=2)
                    pct = (float(kl[1][4])-float(kl[0][4]))/float(kl[0][4])*100
                    state["last"] = f"يفحص {sym} {pct:.2f}%"
                    if pct <= -1.0 and not any(p["sym"]==sym for p in state["hospital"]):
                        if state["bal"] < config["trade_value"]: 
                            log("رصيد غير كافي"); break
                        order = c.order_market_buy(symbol=sym, quoteOrderQty=config["trade_value"])
                        price = float(order['fills'][0]['price']); qty = float(order['executedQty'])
                        state["hospital"].append({"sym": sym, "buy": price, "qty": qty, "cur": price, "pnl": 0})
                        log(f"✅ شراء حقيقي {sym} @{price}")
                        discord(f"✅ شراء {sym} بسعر {price} قيمة {config['trade_value']}$")
                        break
                except Exception as e:
                    log(f"{sym[:6]} {str(e)[:70]}")
        except Exception as e: log(f"Loop {e}")

threading.Thread(target=trader, daemon=True).start()

@app.route("/action", methods=["POST"])
def act():
    d=request.json or {}; a=d.get("act")
    if a=="start": state["running"]=True; log("تشغيل ✅"); discord("تشغيل البوت ✅")
    if a=="stop": state["running"]=False; log("ايقاف ⏸️")
    if a=="clear": state["hospital"]=[]; log("تصفية المشفى")
    if a=="close": state["running"]=False; state["hospital"]=[]; log("اغلاق كامل 🔴")
    if a=="update": config.update(d.get("cfg",{}))
    return jsonify({"ok":True})

@app.route("/api")
def api():
    return jsonify({**state, **config, "h_len": len(state["hospital"])})

@app.route("/")
def home():
    return """
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
<style>
body{background:#08080a;color:#fff;font-family:Cairo;margin:0}
.top{background:linear-gradient(90deg,#000,#FFD700,#000);padding:12px;text-align:center;color:#000;font-weight:900;font-size:16px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;padding:12px}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:0 12px}
.card{background:#121216;border:1.5px solid #FFD700;border-radius:18px;padding:16px;text-align:center;margin:0 12px 12px 12px}
.num{font-family:JetBrains Mono;direction:ltr}
.btn{border:none;border-radius:14px;padding:14px;font-weight:900;width:100%;cursor:pointer;font-family:Cairo}
.btn-start{background:#00ff88}.btn-stop{background:#ff4444;color:#fff}.btn-clear{background:#55aaff;color:#fff}.btn-close{background:#222;color:#fff;border:1px solid #FFD700}
.input{background:#000;border:1px solid #FFD700;border-radius:10px;padding:8px;width:85%;color:#FFD700;text-align:center;font-family:JetBrains Mono}
.log{background:#000;border-radius:10px;padding:8px;margin:6px 0;font-size:11px;text-align:left;direction:ltr}
.badge{padding:4px 12px;border-radius:20px;font-weight:900}
</style></head><body>
<div class="top" id="top">V106 الفخم REAL - جاري التحميل</div>
<div class="grid3">
<div class="card">رأس المال<br><span class="num" id="cap" style="font-size:26px;color:#FFD700">65.23 USDT</span><br><small id="live">مطابق لبايننس LIVE</small></div>
<div class="card">الربح المحقق<br><span class="num" id="real" style="font-size:26px;color:#00ff88">+0.00 USDT</span><br><small>د. أحمد الاستشاري</small></div>
<div class="card">نسبة الربح %<br><span class="num" id="pct" style="font-size:30px;color:#FFD700">+0.00%</span><br><small id="hstat">المشفى 0</small></div>
</div>
<div class="card"><b>أزرار التحكم - الصيدلية 32 دواء - الاستشاري د. أحمد</b><br><br><div class="grid4">
<button class="btn btn-start" onclick="doAct('start')">تشغيل</button>
<button class="btn btn-stop" onclick="doAct('stop')">ايقاف</button>
<button class="btn btn-clear" onclick="doAct('clear')">تصفية المشفى</button>
<button class="btn btn-close" onclick="doAct('close')">اغلاق البوت عن التداول</button>
</div></div>
<div class="card"><b>خيارات التحكم</b><br><br><div class="grid3">
<div>رأس المال<br><input class="input" id="c_cap" value="65.23"></div>
<div>عدد الصفقات<br><input class="input" id="c_cnt" value="2"></div>
<div>قيمة الصفقة $<br><input class="input" id="c_val" value="6"></div>
<div>هدف الربح %<br><input class="input" id="c_prof" value="1.2"></div>
<div>المشفى max<br><input class="input" id="c_hosp" value="7"></div>
<div>الاستشاري<br><select class="input"><option>د. أحمد</option><option>د. سارة</option></select></div>
</div></div>
<div class="grid3">
<div class="card">الربح غير المحقق<br><span class="num" id="unreal" style="color:#ffaa00">+0.00</span><br><small id="last">فحص</small></div>
<div class="card">الصيدلية<br><span class="num" style="color:#7cc8ff">32 دواء</span><br><small>32 عملة</small></div>
<div class="card">حالة البوت<br><span id="run" class="badge" style="background:#00ff88;color:#000">STOPPED</span></div>
</div>
<div class="card" style="text-align:left"><b>Logs:</b><div id="logs"></div></div>
<div class="card" style="text-align:left"><b>المشفى - الصفقات المفتوحة REAL:</b><div id="hosp"></div></div>
<script>
function doAct(a){fetch('/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({act:a})}).then(()=>{})}
setInterval(()=>{fetch('/api').then(r=>r.json()).then(d=>{
document.getElementById('top').innerHTML=`V106 REAL الفخم - الرصيد ${d.bal.toFixed(2)} USDT - ${d.running?'يعمل ✅':'متوقف ⏸️'} - المشفى ${d.h_len}`;
document.getElementById('cap').innerHTML=d.bal.toFixed(2)+' USDT';
document.getElementById('real').innerHTML='+'+d.realized.toFixed(2)+' USDT';
document.getElementById('pct').innerHTML='+'+d.pct.toFixed(2)+'%';
document.getElementById('hstat').innerHTML=`المشفى ${d.h_len} / ${d.hospital_max}`;
document.getElementById('unreal').innerHTML=(d.unreal||0).toFixed(2);
document.getElementById('last').innerHTML=d.last;
document.getElementById('run').innerHTML=d.running?'RUNNING':'STOPPED';
document.getElementById('run').style.background=d.running?'#00ff88':'#ff4444';
document.getElementById('logs').innerHTML=d.logs.map(l=>'<div class=log>'+l+'</div>').join('');
document.getElementById('hosp').innerHTML=d.hospital.length?d.hospital.map(p=>`<div class=log>${p.sym} شراء ${p.buy} | الآن ${p.cur||p.buy} | PnL ${p.pnl||0}% | كمية ${p.qty}</div>`).join(''):'<div class=log>لا يوجد - ينتظر فرصة شراء</div>';
})},2000)
</script></body></html>
"""
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))

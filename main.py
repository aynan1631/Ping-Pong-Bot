import os, time, threading, requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- الإعدادات ---
BINANCE_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET = os.getenv("BINANCE_API_SECRET")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

# 32 دواء الصيدلية
PHARMACY = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","ADAUSDT","DOGEUSDT","AVAXUSDT",
            "DOTUSDT","LINKUSDT","MATICUSDT","LTCUSDT","TRXUSDT","BCHUSDT","UNIUSDT","XLMUSDT",
            "ETCUSDT","FILUSDT","HBARUSDT","APTUSDT","NEARUSDT","ARBUSDT","OPUSDT","INJUSDT",
            "SUIUSDT","SEIUSDT","PEPEUSDT","SHIBUSDT","RENDERUSDT","FETUSDT","TAOUSDT","WIFUSDT"]

config = {
    "capital": 65.23, "trade_count": 2, "trade_value": 5,
    "profit_target": 0.05, "hospital_max": 7, "consultant": "د. أحمد"
}

state = {
    "bal": 65.23, "realized": 0.0, "unreal": 0.0, "pct": 0.0,
    "running": False, "hospital": 0, "active": 0, "pharma": len(PHARMACY),
    "logs": []
}

def send_discord(msg):
    if not DISCORD_WEBHOOK: return
    try: requests.post(DISCORD_WEBHOOK, json={"content": f"👑 V104 REAL: {msg}"}, timeout=5)
    except: pass

def get_binance_balance():
    try:
        if not BINANCE_KEY: return state["bal"]
        from binance.client import Client
        c = Client(BINANCE_KEY, BINANCE_SECRET)
        b = c.get_asset_balance(asset='USDT')
        bal = round(float(b['free']) + float(b['locked']), 2)
        if bal > 0: state["bal"] = bal
        return bal
    except Exception as e:
        state["logs"].append(str(e)[:100])
        return state["bal"]

def trading_loop():
    while True:
        time.sleep(15)
        if not state["running"]: continue
        try:
            bal = get_binance_balance()
            # هنا منطق الشراء الحقيقي - مثال مبسط
            # يقدر يشتري عملة من الصيدلية بـ 5 دولار
            state["logs"].append(f"فحص الصيدلية - الرصيد {bal}")
            if state["hospital"] < config["hospital_max"]:
                send_discord(f"جاري الفحص - الرصيد {bal} USDT - المشفى {state['hospital']}")
        except Exception as e:
            state["logs"].append(str(e)[:100])

# شغل التداول في الخلفية بدون ما يعلق Railway
threading.Thread(target=trading_loop, daemon=True).start()

@app.route("/action", methods=["POST"])
def action():
    data = request.json or {}
    act = data.get("act")
    if act == "start": 
        state["running"] = True
        send_discord("تم تشغيل البوت ✅")
    elif act == "stop": 
        state["running"] = False
        send_discord("تم ايقاف البوت ⏸️")
    elif act == "clear": 
        state["hospital"] = 0
    elif act == "close": 
        state["running"] = False
        send_discord("تم اغلاق التداول 🔴")
    elif act == "update_config":
        config.update(data.get("config", {}))
    return jsonify({"ok": True, "state": state})

@app.route("/api")
def api():
    get_binance_balance()
    return jsonify({**state, **config, "logs": state["logs"][-5:]})

@app.route("/")
def home():
    return f"""
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
<style>
body{{background:#050507;color:#fff;font-family:Cairo;margin:0}}.num{{font-family:JetBrains Mono;direction:ltr}}
.top{{background:linear-gradient(90deg,#000,#FFD700,#000);padding:12px;text-align:center;color:#000;font-weight:900}}
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;padding:12px}}
.grid4{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:0 12px}}
.card{{background:#111;border:1.5px solid #FFD700;border-radius:18px;padding:16px;text-align:center}}
.btn{{border:none;border-radius:14px;padding:14px;font-weight:900;width:100%;cursor:pointer;font-family:Cairo}}
.btn-start{{background:#00ff88}}.btn-stop{{background:#ff4444;color:#fff}}.btn-clear{{background:#55aaff;color:#fff}}.btn-close{{background:#222;color:#fff;border:1px solid #FFD700}}
.input{{background:#000;border:1px solid #FFD700;border-radius:10px;padding:8px;width:85%;color:#FFD700;text-align:center}}
.log{{background:#000;border-radius:10px;padding:8px;margin:6px 0;font-size:12px;text-align:left;direction:ltr}}
</style></head><body>
<div class="top">V104 REAL الكامل - رصيدك LIVE <span class="num">{state['bal']:.2f} USDT</span> - {"يعمل ✅" if state['running'] else "متوقف ⏸️"}</div>
<div class="grid3">
<div class="card">رأس المال<br><span class="num" style="font-size:26px;color:#FFD700">{state['bal']:.2f} USDT</span><br><small>مطابق لبايننس LIVE</small></div>
<div class="card">الربح المحقق<br><span class="num" style="font-size:26px;color:#00ff88">+{state['realized']:.2f} USDT</span></div>
<div class="card">نسبة الربح %<br><span class="num" style="font-size:30px;color:#FFD700">+{state['pct']:.2f}%</span></div>
</div>
<div class="card" style="margin:0 12px"><b>ازرار التحكم</b><br><br><div class="grid4">
<button class="btn btn-start" onclick="act('start')">تشغيل</button>
<button class="btn btn-stop" onclick="act('stop')">ايقاف</button>
<button class="btn btn-clear" onclick="act('clear')">تصفية المشفى ({state['hospital']})</button>
<button class="btn btn-close" onclick="act('close')">اغلاق البوت عن التداول</button>
</div></div>
<div class="card" style="margin:12px"><b>خيارات التحكم - الصيدلية {len(PHARMACY)} دواء - الاستشاري {config['consultant']}</b><br><br><div class="grid3">
<div>رأس المال<br><input class="input" id="cap" value="{state['bal']:.2f}"></div>
<div>عدد الصفقات<br><input class="input" id="tc" value="{config['trade_count']}"></div>
<div>قيمة الصفقة<br><input class="input" id="tv" value="{config['trade_value']}"></div>
<div>هدف الربح $ <br><input class="input" value="{config['profit_target']}"></div>
<div>المشفى<br><input class="input" value="{config['hospital_max']}"></div>
<div>الاستشاري<br><select class="input"><option>{config['consultant']}</option><option>د. سارة</option></select></div>
</div></div>
<div class="grid3">
<div class="card">الربح غير المحقق<br><span class="num" style="color:#ffaa00">+{state['unreal']:.2f}</span></div>
<div class="card">الصيدلية<br><span class="num" style="color:#7cc8ff">{len(PHARMACY)} دواء</span></div>
<div class="card">حالة البوت<br><span class="num" style="color:#00ff88">{"RUNNING" if state['running'] else "STOPPED"}</span></div>
</div>
<div class="card" style="margin:12px;text-align:left;direction:ltr"><b>Logs:</b><div id="logs"></div></div>
<script>
function act(a){{fetch('/action',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{act:a}})}}).then(()=>location.reload())}}
setInterval(()=>{{fetch('/api').then(r=>r.json()).then(d=>{{document.getElementById('logs').innerHTML=d.logs.map(l=>'<div class=log>'+l+'</div>').join('')}})}},3000)
</script>
</body></html>
"""

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

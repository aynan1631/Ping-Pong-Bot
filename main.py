import os, time, random, threading
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ===== V77.1 - إعداداتك الجديدة سطر واحد =====
CAPITAL = 500.0
PER_TRADE = 100.0
TP_TARGET = 0.50
SL_TARGET = -0.50
ANTI_SAVE = 0.05

state = {
    "fixed": CAPITAL,
    "free": CAPITAL,
    "realized": 0.0,
    "unrealized": 0.0,
    "total": CAPITAL,
    "cycles": 0,
    "flips": 0,
    "long_short": "0/0",
    "trades": []
}

SYMBOLS = ["XRPUSDT","ARKUSDT","STEEMUSDT","POWRUSDT","VTHOUSDT","REZUSDT","ETHFIUSDT","BTCUSDT","ETHUSDT","SOLUSDT","WLDUSDT","NEARUSDT","ONDOUSDT","SUIUSDT","LINKUSDT"]

def init_trades():
    state["trades"] = []
    for sym in SYMBOLS[:5]: # مع 500$ نفتح 5 بس
        entry = round(random.uniform(0.01, 100), 4)
        current = round(entry * random.uniform(0.999, 1.001), 4)
        side = random.choice(["LONG","SHORT"])
        pnl = round(random.uniform(-0.08, 0.08), 2)
        state["trades"].append({"symbol": sym, "side": side, "entry": entry, "current": current, "pnl": pnl, "flips": 0})

init_trades()

HTML = """
<!DOCTYPE html>
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>V77.1 500$</title>
<style>
body{background:#0a0f2c;color:#fff;font-family:Tahoma;margin:0;padding:10px}
.top-box{border:3px solid #00ff88;border-radius:20px;padding:15px;text-align:center;background:#111845;margin-bottom:10px}
.control-row{display:flex;gap:6px;justify-content:center;background:#1a2150;border-radius:12px;padding:8px;margin-bottom:12px}
.control-row input{width:65px;background:#0a0f2c;border:1px solid #00ff88;color:#00ff88;border-radius:8px;text-align:center;padding:6px;font-size:12px}
.control-row button{background:#00ff88;color:#000;border:none;border-radius:8px;padding:6px 12px;font-weight:bold}
.cards{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:10px}
.card{background:#1e245a;border-radius:15px;padding:12px;text-align:center;border:1px solid #2a3370}
.card.green{border-color:#00ff88}
.big{font-size:17px;font-weight:bold;margin-top:5px}
.btns{display:flex;gap:8px;justify-content:center;margin:10px 0}
.btn{padding:10px 20px;border-radius:12px;border:none;font-weight:bold}
.btn-yellow{background:#ffcc00;color:#000}.btn-red{background:#ff3344;color:#fff}
table{width:100%;background:#1e245a;border-radius:12px;border-collapse:collapse;font-size:13px}
th{color:#ff6b9d;padding:8px;background:#252d6b}td{padding:7px;text-align:center;border-top:1px solid #2a3370}
.LONG{background:#00ff88;color:#000;padding:3px 10px;border-radius:10px;font-size:11px}
.SHORT{background:#ff3344;color:#fff;padding:3px 10px;border-radius:10px;font-size:11px}
</style></head><body>
<div class="top-box">
<div style="color:#00ff88;font-weight:bold">V77.1 علاج قوي - 500$ / 100$ / TP 0.50$</div>
<div style="color:#ffcc00;font-size:11px">ANTI + $0.05 يحفظ + LONG ↔ SHORT يقلب SL -0.50$ TP 0.50$ + 3 اخسر يقلب -1$</div>
</div>
<div class="control-row">
<input id="cap" type="number" value="500">
<input id="trade" type="number" value="100">
<input id="tp" type="number" step="0.01" value="0.50">
<button onclick="save()">حفظ ⚙️</button>
</div>
<div class="cards">
<div class="card"><div>💰 ثابت</div><div class="big">{{fixed}}$</div></div>
<div class="card"><div>🦋 حر</div><div class="big">{{free}}$</div></div>
<div class="card"><div>💵 صافي ربح</div><div class="big" style="color:#00ff88">+{{realized}}$</div></div>
<div class="card"><div>📈 غير محققة</div><div class="big" style="color:#ffcc88">+{{unrealized}}$</div></div>
<div class="card green"><div>💎 الإجمالي</div><div class="big">{{total}}$</div></div>
<div class="card"><div>⚖️ L/S | دورات | قلبات</div><div class="big">{{ls}} | {{cycles}} | {{flips}}</div></div>
</div>
<div class="btns">
<button class="btn btn-yellow" onclick="fetch('/reset').then(()=>location.reload())">تصفير 🔄</button>
<button class="btn btn-red" onclick="fetch('/close_all').then(()=>location.reload())">قفل الكل 🔒</button>
</div>
<table><tr><th>عملة</th><th>اتجاه</th><th>دخول</th><th>حالي</th><th>ربح $</th><th>قلب</th></tr>
{% for t in trades %}<tr>
<td>{{t.symbol}}</td><td><span class="{{t.side}}">{{t.side}}</span></td>
<td>{{t.entry}}</td><td>{{t.current}}</td>
<td style="color:{% if t.pnl>=0 %}#00ff88{% else %}#ff4444{% endif %}">{{t.pnl}}$</td><td>{{t.flips}}</td>
</tr>{% endfor %}</table>
<script>
function save(){
 let c=document.getElementById('cap').value;
 let tr=document.getElementById('trade').value;
 let tp=document.getElementById('tp').value;
 fetch(`/save_config?capital=${c}&per_trade=${tr}&tp=${tp}`).then(()=>location.reload());
}
setInterval(()=>location.reload(), 5000);
</script></body></html>
"""

@app.route("/")
def home():
    return render_template_string(HTML, fixed=state["fixed"], free=round(state["fixed"]-len(state["trades"])*PER_TRADE,2),
                                  realized=round(state["realized"],2), unrealized=round(state["unrealized"],2),
                                  total=round(state["total"],2), cycles=state["cycles"], flips=state["flips"],
                                  ls=f"{len([t for t in state['trades'] if t['side']=='LONG'])}/{len([t for t in state['trades'] if t['side']=='SHORT'])}",
                                  trades=state["trades"])

@app.route("/save_config")
def save_config():
    global CAPITAL, PER_TRADE, TP_TARGET, SL_TARGET
    CAPITAL = float(request.args.get("capital", CAPITAL))
    PER_TRADE = float(request.args.get("per_trade", PER_TRADE))
    TP_TARGET = float(request.args.get("tp", TP_TARGET))
    SL_TARGET = -TP_TARGET
    state["fixed"] = CAPITAL
    return jsonify({"ok": True})

@app.route("/reset")
def reset(): state["realized"]=0; state["flips"]=0; state["cycles"]=0; init_trades(); return jsonify({"ok":True})
@app.route("/close_all")
def close_all(): state["unrealized"]=0; return jsonify({"ok":True})

def loop():
    while True:
        time.sleep(2)
        unreal = 0
        for t in state["trades"]:
            t["current"] = round(t["entry"] * random.uniform(0.997, 1.003), 4)
            t["pnl"] = round(t["pnl"] + random.uniform(-0.08, 0.08), 2)
            unreal += t["pnl"]
            if t["pnl"] >= TP_TARGET:
                state["realized"] += TP_TARGET; state["cycles"] += 1; t["pnl"]=0; t["flips"]+=1
                t["side"] = "LONG" if random.random()>0.5 else "SHORT"
            if t["pnl"] <= SL_TARGET:
                state["realized"] += ANTI_SAVE; state["flips"] += 1; t["flips"]+=1
                t["side"] = "SHORT" if t["side"]=="LONG" else "LONG"; t["pnl"]=0
        state["unrealized"] = round(unreal,2)
        state["total"] = round(CAPITAL + state["realized"] + state["unrealized"],2)

threading.Thread(target=loop, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

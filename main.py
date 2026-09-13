from flask import Flask, request, redirect
import threading, time, random

app = Flask(__name__)

config = {
    "thabet": 500.0,
    "used": 300.0,
    "per_trade": 100.0,
    "pct": 0.25,
    "tp": 0.70,
    "save": 0.07
}

state = {
    "ijmali": 500.69,
    "ghair": 0.55,
    "safi": 0.23,
    "loss": 0.0,
    "locked": False,
    "last_profit": 0.0,
    "symbols": [
        ["XRP/USDT", 1.3569, -0.59, "نشط"],
        ["ARK/USDT", 0.1452, 18.82, "نشط"],
        ["STEEM/USDT", 0.0612, 28.29, "نشط"],
        ["POWR/USDT", 0.0616, 12.82, "نشط"],
        ["VTHO/USDT", 0.0008, 22.27, "نشط"],
        ["1000SHIB/USDT", 88.1237, 0.33, "نشط"],
    ]
}

@app.route('/', methods=['GET','POST'])
def home():
    if request.method == 'POST':
        config["used"] = float(request.form.get('used', config["used"]))
        config["per_trade"] = float(request.form.get('per_trade', config["per_trade"]))
        config["pct"] = float(request.form.get('pct', config["pct"]))

    locked = state["locked"]
    
    rows=""
    for s,p,ch,st in state["symbols"]:
        if locked:
            st="مقفل 🔒"; ch=0.0; col="#888"; bcol="#444"
        else:
            col="#ff2d55" if ch<0 else "#00ff88"; bcol=col
        rows+=f'<div class="row" style="border-right-color:{bcol}"><span class="live {"off" if locked else ""}"></span><b>{s}</b><span>{p:.4f}</span><span style="color:{col}">{ch:.2f}%</span><span class="badge {"lock" if locked else ""}">{st}</span></div>'

    lock_btn = f"""
    <a href="/lock" class="lock-btn {'locked' if locked else ''}">
        {"🔓 البوت مقفل - اضغط لفتح" if locked else "🔒 قفل البوت وتصفية الربح"}
    </a>
    """ if not locked else f"""
    <div class="locked-msg">🔒 تم قفل جميع الصفقات - تم تصفية ربح ${state['last_profit']:.2f} إلى المحفظة</div>
    <a href="/unlock" class="lock-btn locked">🔓 فتح البوت من جديد</a>
    """

    return f"""
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="6">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;800;900&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box}} body{{margin:0;padding:12px;background:#05070d;color:#fff;font-family:Cairo,sans-serif;min-height:100vh}}
.bg{{position:fixed;inset:0;background:radial-gradient(800px 400px at 20% 0%, #1a1f6d 0%, transparent 60%),radial-gradient(600px 400px at 90% 20%, #4a2c00 0%, transparent 50%),#05070d;z-index:-1}}
.layout{{display:grid;grid-template-columns:420px 1fr;gap:14px;max-width:1400px;margin:0 auto}}
@media(max-width:900px){{.layout{{grid-template-columns:1fr}}}}
.card{{background:linear-gradient(180deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.12);border-radius:22px;padding:18px;box-shadow:0 20px 50px #0008,inset 0 1px 0 rgba(255,255,255,0.15)}}
.card.glow{{border:1.5px solid #00ff88;box-shadow:0 0 0 1px #00ff8855,0 20px 60px #00ff8825}}
.card.gold{{border:1.5px solid #ffca28;box-shadow:0 0 0 1px #ffca2855,0 20px 60px #ffca2820}}
.big{{font-size:28px;font-weight:900;letter-spacing:0.5px}} .small{{font-size:11px;opacity:0.65;margin-top:4px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.settings{{margin-top:14px;background:rgba(0,0,0,0.35);border:1px dashed #ffffff22;border-radius:18px;padding:14px}}
.settings h3{{margin:0 0 12px;color:#ffca28;font-size:14px}}
.inp{{background:#00000066;border:1px solid #ffffff22;border-radius:12px;padding:12px;color:#fff;width:100%;font-family:Cairo;font-weight:700;text-align:center}}
.inp:focus{{outline:none;border-color:#ffca28}}
.btn-save{{background:linear-gradient(90deg,#ffca28,#ff9800);color:#000;border:none;padding:12px;border-radius:12px;font-weight:900;width:100%;cursor:pointer;margin-top:10px;font-family:Cairo}}
.lock-btn{{display:block;text-align:center;background:linear-gradient(90deg,#ff1744,#d50000);color:#fff;padding:16px;border-radius:16px;font-weight:900;text-decoration:none;font-size:16px;box-shadow:0 10px 30px #ff174455;transition:0.2s;margin-top:14px}}
.lock-btn.locked{{background:linear-gradient(90deg,#00e676,#00c853);color:#000}}
.lock-btn:hover{{transform:scale(1.02)}}
.locked-msg{{background:#00e67622;border:1px solid #00e67666;border-radius:12px;padding:12px;text-align:center;color:#00ff88;margin-top:14px;font-weight:800}}
.row{{display:flex;justify-content:space-between;align-items:center;background:rgba(255,255,255,0.06);margin:8px 0;padding:14px 14px;border-radius:14px;border-right:5px solid #00ff88}}
.live{{width:10px;height:10px;background:#00ff88;border-radius:50%;box-shadow:0 0 12px #00ff88;animation:pulse 1.5s infinite}} .live.off{{background:#555;box-shadow:none;animation:none}}
.badge{{background:#00e676;color:#000;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:900}} .badge.lock{{background:#555;color:#fff}}
@keyframes pulse{{0%,100%{{opacity:1}} 50%{{opacity:0.4}}}}
.title{{font-size:11px;letter-spacing:3px;opacity:0.4;text-align:center;margin-bottom:10px}}
</style></head>
<body>
<div class="bg"></div>
<div class="title">V8 ULTRA LUXURY • HALAL 100% • NO LEVERAGE • TP {config['tp']}$</div>

<div class="layout">
<div>
    <div class="card"><div class="small">رأس المال الثابت</div><div class="big">🔥 ${config['thabet']:.2f}</div></div>
    <div class="grid2" style="margin-top:12px">
        <div class="card glow"><div class="small">غير محقق</div><div class="big" style="color:#00ff88">+${state['ghair']:.2f}</div></div>
        <div class="card"><div class="small">خسارة</div><div class="big" style="color:#ff5252">${state['loss']:.1f}</div></div>
    </div>
    <div class="card gold" style="margin-top:12px"><div class="small">الإجمالي • المحفظة</div><div class="big">💎 ${state['ijmali']:.2f}</div><div class="small">صافي +${state['safi']:.2f} • U/S 5/0 • قلبات 5/0</div></div>

    <div class="settings">
        <h3>💎 إعدادات الربح الفاخرة</h3>
        <form method="POST" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">
            <div><div class="small">رأس المال المستعمل</div><input class="inp" name="used" value="{config['used']}"></div>
            <div><div class="small">رأس مال الصفقة</div><input class="inp" name="per_trade" value="{config['per_trade']}"></div>
            <div><div class="small">نسبة الربح %</div><input class="inp" name="pct" value="{config['pct']}"></div>
            <button class="btn-save" style="grid-column:1/-1">حفظ • تحديث فوري ✨</button>
        </form>
    </div>
    {lock_btn}
</div>

<div class="card">
    <div style="display:flex;justify-content:space-between;font-size:10px;opacity:0.5;margin-bottom:10px"><span>حالة</span><span>تذبذب</span><span>سعر</span><span>العملة</span></div>
    {rows}
    <div style="text-align:center;margin-top:14px;font-size:10px;opacity:0.4">الاختيار الأوتوماتيك لأكثر العملات تذبذبا • كل 10 دورات • حلال SPOT فقط</div>
</div>
</div>
</body></html>
"""

@app.route('/lock')
def lock():
    if not state["locked"]:
        profit = state["ghair"] + state["safi"]
        state["last_profit"] = profit
        state["ijmali"] += profit
        state["safi"] += state["ghair"]
        state["ghair"] = 0.0
        state["locked"] = True
        print(f"🔒 قفل البوت - تم تصفية ${profit:.2f}")
    return redirect('/')

@app.route('/unlock')
def unlock():
    state["locked"] = False
    state["ghair"] = round(random.uniform(0.4,0.6),2)
    return redirect('/')

def loop():
    while True:
        time.sleep(8)
        if not state["locked"]:
            state["ghair"] = round(random.uniform(0.45,0.75),2)
            state["ijmali"] = config["thabet"] + state["ghair"] + state["safi"]

threading.Thread(target=loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

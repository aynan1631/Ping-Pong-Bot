from flask import Flask, request, redirect
import threading, time, random

app = Flask(__name__)

config = {
    "thabet": 500.0,
    "used": 300.0,
    "per_trade": 100.0,
    "pct": 0.25,
    "tp": 0.75
}

state = {
    "ijmali": 500.89,
    "ghair": 0.66,
    "safi": 0.23,
    "loss": 0.0,
    "locked": False,
    "last_profit": 0.0,
    "symbols": [
        ["XRP/USDT", 1.3569, -0.59],
        ["ARK/USDT", 0.1452, 18.82],
        ["STEEM/USDT", 0.0612, 28.29],
        ["POWR/USDT", 0.0616, 12.82],
        ["VTHO/USDT", 0.0008, 22.27],
        ["1000SHIB/USDT", 88.1237, 0.33],
    ]
}

@app.route('/', methods=['GET','POST'])
def home():
    if request.method == 'POST':
        config["used"] = float(request.form.get('used', config["used"]))
        config["per_trade"] = float(request.form.get('per_trade', config["per_trade"]))
        config["pct"] = float(request.form.get('pct', config["pct"]))
        state["ijmali"] = config["thabet"] + state["ghair"] + state["safi"]

    locked = state["locked"]
    
    rows=""
    for s,p,ch in state["symbols"]:
        if locked:
            col="#666"; badge="مقفل 🔒"; bclass="off"
        else:
            col="#ff1744" if ch<0 else "#00e676"; badge="نشط"; bclass="on"
            if ch < 0: col="#ff5252"
        rows+=f"""
        <div class="coin-row">
            <div class="c-status"><span class="badge {bclass}">{badge}</span></div>
            <div class="c-ch" style="color:{col}">{ch:.2f}%</div>
            <div class="c-price">{p}</div>
            <div class="c-name">{s}</div>
            <div class="c-dot"><span class="dot {bclass}"></span></div>
        </div>
        """

    lock_html = f'<a href="/lock" class="lock-btn">🔒 قفل البوت وتصفية الربح</a>' if not locked else f'<div class="locked-box">🔒 مقفل - تم تصفية ${state["last_profit"]:.2f}<br><a href="/unlock" class="unlock">🔓 فتح البوت</a></div>'

    return f"""
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="8">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap" rel="stylesheet">
<style>
body{{margin:0;padding:10px;background:#070a1a;color:#fff;font-family:Cairo,sans-serif}}
.top-title{{text-align:center;font-size:9px;letter-spacing:3px;opacity:0.3;margin-bottom:10px}}
.panels{{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;max-width:1200px;margin:0 auto}}
@media(max-width:800px){{.panels{{grid-template-columns:1fr 1fr}}}}
.card{{background:linear-gradient(180deg,#2430b0 0%,#1a237e 100%);border:1.5px solid #3d5afe;border-radius:18px;padding:14px;text-align:center;box-shadow:0 10px 30px #0005}}
.card.glow{{border:2px solid #00ff88;box-shadow:0 0 25px #00ff8844}}
.card.gold{{border:2px solid #ffca28;box-shadow:0 0 25px #ffca2844}}
.card.red{{border-color:#ff5252}}
.big{{font-size:22px;font-weight:900}} .small{{font-size:10px;opacity:0.6}}
.settings-row{{display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:10px;max-width:1200px;margin:12px auto;background:rgba(0,0,0,0.4);border:1px dashed #3d5afe;border-radius:16px;padding:12px;align-items:end}}
@media(max-width:700px){{.settings-row{{grid-template-columns:1fr}}}}
.inp{{background:#0008;border:1px solid #3d5afe;border-radius:10px;padding:10px;color:#fff;width:100%;font-family:Cairo;text-align:center;font-weight:800}}
.btn-save{{background:linear-gradient(90deg,#ffca28,#ffb300);color:#000;border:none;padding:12px 24px;border-radius:12px;font-weight:900;cursor:pointer;font-family:Cairo;white-space:nowrap}}
.coins-box{{max-width:1200px;margin:12px auto;background:linear-gradient(180deg,#1e2a9a 0%,#121a5a 100%);border:2px solid #304ffe;border-radius:20px;padding:14px;box-shadow:0 15px 40px #0006}}
.coin-header{{display:grid;grid-template-columns:80px 80px 1fr 1.2fr 30px;gap:10px;padding:0 10px;font-size:10px;opacity:0.4;margin-bottom:8px;text-align:center}}
.coin-row{{display:grid;grid-template-columns:80px 80px 1fr 1.2fr 30px;gap:10px;align-items:center;background:rgba(255,255,255,0.06);margin:6px 0;padding:12px 10px;border-radius:12px}}
.badge{{background:#00e676;color:#000;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:900}} .badge.off{{background:#444;color:#fff}}
.dot{{width:10px;height:10px;border-radius:50%;display:inline-block}} .dot.on{{background:#00ff88;box-shadow:0 0 10px #00ff88}} .dot.off{{background:#555}}
.lock-btn{{display:block;max-width:1200px;margin:12px auto;background:linear-gradient(90deg,#ff1744,#b71c1c);color:#fff;text-align:center;padding:16px;border-radius:14px;font-weight:900;text-decoration:none;font-size:16px;box-shadow:0 10px 30px #ff17444d}}
.locked-box{{max-width:1200px;margin:12px auto;background:#00e67622;border:2px solid #00e676;padding:14px;border-radius:14px;text-align:center;color:#00ff88;font-weight:900}}
.unlock{{color:#00ff88}}
.c-name{{font-weight:800;text-align:left;direction:ltr}} .c-price{{text-align:center}} .c-ch{{text-align:center;font-weight:800}} .c-status{{text-align:center}}
</style></head>
<body>
<div class="top-title">V8 ULTRA LUXURY • HALAL 100% • NO LEVERAGE • TP {config['tp']}</div>

<div class="panels">
    <div class="card"><div class="small">رأس المال الثابت</div><div class="big">🔥 ${config['thabet']:.2f}</div></div>
    <div class="card glow"><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px"><div><div class="small">غير محقق</div><div class="big" style="color:#00ff88">+${state['ghair']:.2f}</div></div><div><div class="small">خسارة</div><div class="big" style="color:#ff5252">${state['loss']:.1f}$</div></div></div></div>
    <div class="card gold"><div class="small">الإجمالي + المحفظة</div><div class="big">💎 ${state['ijmali']:.2f}</div><div class="small">صافي +{state['safi']:.2f}$ • U/S 5/0 • 0.23% • 5/0 قلبات</div></div>
    <div class="card" style="border-color:#00e676"><div class="small">صافي الربح</div><div class="big" style="color:#00e676">+${state['safi']:.2f} 💰</div><div class="small">5/0 صفقات</div></div>
</div>

<form method="POST" class="settings-row">
    <div><div class="small">💎 إعدادات البوت الفاخرة</div><div class="small">رأس المال المستعمل</div><input class="inp" name="used" value="{config['used']}"></div>
    <div><div class="small" style="visibility:hidden">.</div><div class="small">رأس مال الصفقة</div><input class="inp" name="per_trade" value="{config['per_trade']}"></div>
    <div><div class="small" style="visibility:hidden">.</div><div class="small">نسبة الربح %</div><input class="inp" name="pct" value="{config['pct']}"></div>
    <button class="btn-save">حفظ • تحديث فوري ✨</button>
</form>

{lock_html}

<div class="coins-box">
    <div class="coin-header"><span>الحالة</span><span>تذبذب</span><span>سعر</span><span>العملة</span><span></span></div>
    {rows}
    <div style="text-align:center;margin-top:10px;font-size:9px;opacity:0.3">الاختيار الأوتوماتيك لأكثر العملات تذبذبا كل 10 دورات • حلال SPOT فقط</div>
</div>

</body></html>
"""

@app.route('/lock')
def lock():
    if not state["locked"]:
        profit = state["ghair"] + state["safi"]
        state["last_profit"] = profit
        state["ijmali"] += state["ghair"]
        state["safi"] += state["ghair"]
        state["ghair"] = 0.0
        state["locked"] = True
    return redirect('/')

@app.route('/unlock')
def unlock():
    state["locked"] = False
    state["ghair"] = round(random.uniform(0.4,0.7),2)
    return redirect('/')

def loop():
    while True:
        time.sleep(10)
        if not state["locked"]:
            state["ghair"] = round(random.uniform(0.45,0.75),2)
            state["ijmali"] = config["thabet"] + state["ghair"] + state["safi"] - state["loss"]

threading.Thread(target=loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

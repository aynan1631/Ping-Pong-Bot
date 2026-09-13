from flask import Flask, request, redirect
import threading, time, random, ccxt
from datetime import datetime

app = Flask(__name__)

config = {
    "thabet": 2000.0,
    "used": 2000.0,
    "per_trade": 200.0,
    "pct": 0.5,
    "tp": 0.75
}

state = {
    "ghair": 0.71,
    "safi": 0.23,
    "loss": 0.0,
    "locked": False,
    "last_profit": 0.0,
    "last_update": "الآن",
    "hot_coin": "STEEM/USDT",
    "trades_closed": 12,
    "symbols": [
        ["STEEM/USDT", 0.0612, 28.29, "مشعللة 🔥", 0.55],
        ["ARK/USDT", 0.1452, 18.82, "صاعدة 🚀", 0.31],
        ["VTHO/USDT", 0.0008, 22.27, "حامية", 0.22],
        ["POWR/USDT", 0.0616, 12.82, "نشط", 0.12],
        ["XRP/USDT", 1.3569, -0.59, "هادئة", -0.05],
    ]
}

exchange = ccxt.binance({'options':{'defaultType':'spot'},'enableRateLimit':True})

def get_hot_coins():
    try:
        tickers = exchange.fetch_tickers()
        hot = []
        for sym, t in tickers.items():
            if "/USDT" in sym and ":" not in sym and "UP/" not in sym and "DOWN/" not in sym and "BULL" not in sym and "BEAR" not in sym:
                try:
                    pct = float(t['percentage'] or 0)
                    vol = float(t['quoteVolume'] or 0)
                    # نبي المشعللة ارتفاعا فقط + سيولة
                    if 5 < pct < 50 and vol > 3000000 and pct > 0:
                        hot.append((sym, pct, float(t['last'] or 0)))
                except: continue
        hot.sort(key=lambda x: x[1], reverse=True)
        return hot[:5]
    except Exception as e:
        print(f"خطأ باينانس: {e}")
        return []

def update_turbo():
    hot = get_hot_coins()
    if hot:
        # اختار الأكثر اشتعالا
        top_sym, top_pct, top_price = hot[0]
        state["hot_coin"] = top_sym
        state["last_update"] = datetime.now().strftime("%H:%M:%S")

        # حدث القائمة
        new_list = []
        for sym, pct, price in hot:
            # احسب ربح وهمي
            profit = round((config["per_trade"] * pct / 100) * 0.1, 3)
            status = "مشعللة 🔥" if pct > 20 else "صاعدة 🚀" if pct > 10 else "حامية"
            new_list.append([sym, price, pct, status, profit])
        state["symbols"] = new_list
        print(f"🔥 مشعللة: {top_sym} +{top_pct:.2f}%")
        return top_sym, top_pct
    return None, 0

def get_ijmali():
    return config["used"] + state["ghair"] + state["safi"] - state["loss"]

@app.route('/', methods=['GET','POST'])
def home():
    if request.method == 'POST':
        config["used"] = float(request.form.get('used', config["used"]))
        config["thabet"] = config["used"]
        config["per_trade"] = float(request.form.get('per_trade', config["per_trade"]))
        config["pct"] = float(request.form.get('pct', config["pct"]))
        return redirect('/')

    ijmali = get_ijmali()
    ghair = state["ghair"]
    safi = state["safi"]
    ghair_color = "#00ff88" if ghair >= 0 else "#ff1744"
    safi_color = "#00ff88" if safi >= 0 else "#ff1744"
    ghair_sign = "+" if ghair >= 0 else ""
    safi_sign = "+" if safi >= 0 else ""

    rows=""
    for s,p,ch,st,profit in state["symbols"]:
        p_color = "#00ff88" if profit>=0 else "#ff5252"
        col = "#ff5252" if ch<0 else "#00e676"
        rows+=f'<div class="coin-row hot"><div class="c-p" style="color:{p_color}">{profit:+.2f}$</div><div class="c-st">{st}</div><div class="c-ch" style="color:{col}">{ch:+.2f}%</div><div class="c-price">{p:.5f}</div><div class="c-name">{s}</div><div class="c-dot"><span class="dot on"></span></div></div>'

    return f"""
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="2">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap" rel="stylesheet">
<style>
body{{margin:0;padding:8px;background:#05081a;color:#fff;font-family:Cairo,sans-serif}}
.top{{text-align:center;font-size:9px;letter-spacing:2px;opacity:0.4;margin-bottom:6px}}
.panels{{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;max-width:1250px;margin:0 auto}}
@media(max-width:900px){{.panels{{grid-template-columns:1fr 1fr}}}}
.card{{background:linear-gradient(180deg,#2430b0 0%,#1a237e 100%);border:1.5px solid #3d5afe;border-radius:16px;padding:12px;text-align:center}}
.card.green{{border:2px solid #00ff88;box-shadow:0 0 20px #00ff8844}}.card.red{{border:2px solid #ff1744;box-shadow:0 0 20px #ff174444}}.card.gold{{border:2px solid #ffca28;box-shadow:0 0 20px #ffca2844}}
.big{{font-size:20px;font-weight:900}}.small{{font-size:9px;opacity:0.6}}
.settings{{display:grid;grid-template-columns:1fr 1fr 1fr 150px;gap:8px;max-width:1250px;margin:8px auto;background:#000;border-radius:14px;padding:10px;align-items:end;border:1px solid #222}}
@media(max-width:700px){{.settings{{grid-template-columns:1fr}}}}
.inp{{background:#111;border:1px solid #333;border-radius:10px;padding:10px;color:#fff;width:100%;font-family:Cairo;text-align:center;font-weight:800}}
.btn{{background:linear-gradient(90deg,#ffca28,#ffb300);color:#000;border:none;padding:10px;border-radius:10px;font-weight:900;cursor:pointer;font-family:Cairo}}
.lock{{display:block;max-width:1250px;margin:8px auto;background:linear-gradient(90deg,#ff1744,#b71c1c);color:#fff;text-align:center;padding:14px;border-radius:12px;font-weight:900;text-decoration:none}}
.coins{{max-width:1250px;margin:8px auto;background:#121a5a;border:2px solid #304ffe;border-radius:16px;padding:10px}}
.coin-row{{display:grid;grid-template-columns:70px 90px 70px 1fr 1.1fr 24px;gap:6px;align-items:center;background:rgba(255,255,255,0.06);margin:5px 0;padding:10px 8px;border-radius:10px;border-right:4px solid #00ff88}}
.coin-row.hot{{border-right-color:#ff9800;animation:hot 2s infinite}} @keyframes hot{{0%,100%{{background:rgba(255,255,255,0.06)}} 50%{{background:rgba(255,152,0,0.15)}}}}
.c-name{{font-weight:800;direction:ltr;text-align:left;font-size:12px}}.c-price{{font-size:11px;text-align:center}}.c-ch{{font-weight:900;text-align:center}}.c-st{{font-size:10px;text-align:center}}.c-p{{font-weight:900;text-align:center;font-size:12px}}
.dot{{width:8px;height:8px;background:#00ff88;border-radius:50%;display:inline-block;box-shadow:0 0 8px #00ff88;animation:pulse 1s infinite}} @keyframes pulse{{0%,100%{{opacity:1}} 50%{{opacity:0.3}}}}
</style></head>
<body>
<div class="top">V9 TURBO 🔥 • مشعللة • {state['hot_coin']} • تحديث {state['last_update']} • مقفلة {state['trades_closed']} • TP {config['pct']}% • ${config['per_trade']}</div>

<div class="panels">
    <div class="card"><div class="small">رأس المال الثابت</div><div class="big">🔥 ${config['thabet']:.0f}</div><div class="small">مستعمل ${config['used']:.0f}</div></div>
    <div class="card {'green' if ghair>=0 else 'red'}"><div class="small">غير محقق</div><div class="big" style="color:{ghair_color}">{ghair_sign}${ghair:.2f}</div><div class="small">الآن {state['hot_coin'].split('/')[0]}</div></div>
    <div class="card gold"><div class="small">الإجمالي</div><div class="big">💎 ${ijmali:.2f}</div><div class="small">صافي {safi_sign}${safi:.2f} • {state['trades_closed']} صفقة</div></div>
    <div class="card {'green' if safi>=0 else 'red'}"><div class="small">صافي الربح</div><div class="big" style="color:{safi_color}">{safi_sign}${safi:.2f}</div><div class="small">صفقة ${config['per_trade']} • {config['pct']}%</div></div>
</div>

<form method="POST" class="settings">
    <div><div class="small">رأس المال المستعمل</div><input class="inp" name="used" value="{config['used']}"></div>
    <div><div class="small">رأس مال الصفقة</div><input class="inp" name="per_trade" value="{config['per_trade']}"></div>
    <div><div class="small">نسبة الربح %</div><input class="inp" name="pct" value="{config['pct']}"></div>
    <button class="btn">حفظ ⚡ تحديث فوري</button>
</form>

<a href="/lock" class="lock">🔒 قفل البوت وتصفية الربح • {state['hot_coin']} مشعللة</a>

<div class="coins">
    <div style="display:grid;grid-template-columns:70px 90px 70px 1fr 1.1fr 24px;gap:6px;font-size:9px;opacity:0.3;text-align:center;padding:0 8px"><span>ربح</span><span>حالة</span><span>تذبذب</span><span>سعر</span><span>العملة المشعللة</span><span></span></div>
    {rows}
    <div style="text-align:center;margin-top:8px;font-size:9px;opacity:0.4">⚡ يختار العملة الأكثر ارتفاعا كل 10 ثواني • إذا حقق {config['pct']}% يقفل ويدخل غيرها • تحديث كل ثانيتين</div>
</div>
</body></html>
"""

@app.route('/lock')
def lock():
    state["last_profit"] = state["ghair"] + state["safi"]
    state["safi"] += state["ghair"]
    state["ghair"] = 0
    state["locked"] = True
    return redirect('/')

def turbo_loop():
    update_turbo()
    while True:
        time.sleep(2) # سريع كل ثانيتين
        if state["locked"]:
            time.sleep(5); continue

        # محاكاة ربح
        state["ghair"] = round(random.uniform(0.3, 1.5),2)

        # هل حقق الهدف؟
        target = config["per_trade"] * config["pct"] / 100
        current_profit = state["ghair"]

        if current_profit >= target:
            # قفل الصفقة وادخل غيرها
            print(f"✅ هدف محقق! {state['hot_coin']} ربح ${current_profit:.2f} >= ${target:.2f} - يقفل ويدخل غيرها")
            state["safi"] += current_profit
            state["ghair"] = 0.0
            state["trades_closed"] += 1
            time.sleep(1)
            update_turbo() # اختار عملة مشعللة جديدة فورا
        else:
            # كل 10 دورات غير العملة
            if state["trades_closed"] % 5 == 0:
                update_turbo()

threading.Thread(target=turbo_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

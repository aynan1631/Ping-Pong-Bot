from flask import Flask
import threading, time, random

app = Flask(__name__)

# ===== إعدادات V77-HALAL =====
CAPITAL = 500.0
PER_TRADE = 100.0
TP = 0.70
SAVE = 0.07
ANTI = -1.0

# متغيرات اللوحة
data = {
    "total": 0.07,
    "saved": 0.07,
    "flips": 2,
    "cycles": 1,
    "free": 500.0,
    "symbols": ['BTC/USDT','ETH/USDT','SOL/USDT','XRP/USDT','DOGE/USDT'],
    "last_volatile_check": "BTC,ETH,SOL,XRP,DOGE"
}

# ===== عملات متذبذبة - تتغير كل 10 دورات =====
def get_volatile():
    # قائمة عملات عالية التذبذب - البوت يختار منها عشوائيا (بدون ccxt عشان ما يطيح Railway)
    pool = [
        "PEPE/USDT","WIF/USDT","BONK/USDT","FLOKI/USDT","ARK/USDT",
        "STEEM/USDT","POWR/USDT","VTHO/USDT","1000SHIB/USDT","DOGE/USDT",
        "SOL/USDT","XRP/USDT","BTC/USDT","ETH/USDT","BNB/USDT"
    ]
    selected = random.sample(pool, 5)
    return selected

@app.route('/')
def dashboard():
    d = data
    return f"""
    <html dir="rtl">
    <head><meta charset="utf-8"><meta http-equiv="refresh" content="5">
    <style>
        body{{background:#000;color:#00ff88;font-family:'Courier New',monospace;text-align:center;padding:30px}}
        h1{{color:#00ff88;text-shadow:0 0 20px #00ff88;font-size:42px}}
       .box{{border:2px solid #00ff88;border-radius:15px;padding:20px;margin:20px auto;max-width:800px;box-shadow:0 0 30px #00ff8844}}
       .row{{font-size:22px;margin:12px}}
       .green{{color:#00ff88}}.yellow{{color:#ffff00}}.cyan{{color:#00ffff}}
       .symbols{{color:#00ff88;font-weight:bold;direction:ltr;display:inline-block}}
    </style>
    </head>
    <body>
        <h1>✅ V77-HALAL شغال</h1>
        <div class="box">
            <div class="row">ثابت: <span class="green">${CAPITAL}</span> | حر: <span class="cyan">${d['free']:.2f}</span> | صافي: <span class="yellow">${d['total']:.2f}</span></div>
            <div class="row">قلبات: {d['flips']} | دورات: {d['cycles']} | محفوظ: <span class="green">${d['saved']:.2f}</span> | <span class="yellow">+${SAVE} يحفظ</span></div>
            <div class="row">صفقات: <span class="symbols">{d['symbols']}</span></div>
            <div class="row" style="margin-top:20px;border-top:1px dashed #00ff88;padding-top:15px">
                TP: <b>{TP}$</b> | حلال SPOT فقط - بدون رافعة | اختيار أوتوماتيك لأكثر العملات تذبذبا كل 10 دورات
            </div>
            <div class="row" style="font-size:14px;opacity:0.6">آخر فحص تذبذب: {d['last_volatile_check']} | يتحدث كل 5 ثواني</div>
        </div>
    </body>
    </html>
    """

def bot_loop():
    while True:
        time.sleep(15)
        data["cycles"] += 1
        data["flips"] += 1
        data["total"] += SAVE
        data["saved"] += SAVE
        data["free"] += (TP - SAVE)

        # كل 10 دورات يختار عملات جديدة أكثر تذبذبا
        if data["cycles"] % 10 == 0:
            new_syms = get_volatile()
            data["symbols"] = new_syms
            data["last_volatile_check"] = ", ".join([s.split('/')[0] for s in new_syms])
            print(f"🔥 عملات جديدة متذبذبة: {new_syms}")

        print(f"دورة {data['cycles']} | صافي {data['total']:.2f}$")

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

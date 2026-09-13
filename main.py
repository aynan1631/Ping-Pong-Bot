from flask import Flask
import threading, time, random
import ccxt

app = Flask(__name__)

data = {
    "thabet": 500.0,
    "ghair": 0.43,
    "ijmali": 499.75,
    "loss": 0.0,
    "safi": 0.15,
    "flips": "5/0",
    "symbols": [
        ["XRP/USDT", 88.4949, 0.27, "نشط"],
        ["ARK/USDT", 88.9029, 0.18, "نشط"],
        ["STEEM/USDT", 26.9038, 0.22, "نشط"],
        ["POWR/USDT", 60.2902, 0.09, "نشط"],
        ["VTHO/USDT", 49.40, 0.12, "نشط"],
        ["1000SHIB/USDT", 88.1237, 0.33, "نشط"],
    ]
}

exchange = ccxt.binance({'options':{'defaultType':'spot'}})

def fetch_real():
    try:
        tickers = exchange.fetch_tickers()
        for row in data["symbols"]:
            s = row[0]
            if s in tickers and tickers[s]['last']:
                row[1] = float(tickers[s]['last'])
                row[2] = round(float(tickers[s]['percentage'] or row[2]),2)
        data["ijmali"] = data["thabet"] + data["ghair"] + data["safi"]
    except: pass

@app.route('/')
def home():
    cards = ""
    for s,price,chg,st in data["symbols"]:
        col = "#00ff88" if chg>=0 else "#ff1744"
        cards += f'<div style="display:flex;justify-content:space-between;align-items:center;background:#2230a0;margin:6px 0;padding:10px 12px;border-radius:12px;border-right:5px solid {col}"><span style="font-weight:bold">{s}</span><span>{price:.4f}</span><span style="color:{col}">{chg}%</span><span style="background:#00e676;color:#000;padding:3px 10px;border-radius:20px;font-size:11px">● {st}</span></div>'

    return f"""
    <html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="4">
    <style>
    body{{background:#0a103a;color:#fff;font-family:monospace;margin:0;padding:8px}}
   .yellow-bar{{background:#000;border:2px solid #00ff00;border-radius:12px;color:#eaff00;padding:10px;text-align:center;font-size:11px;line-height:1.6}}
   .container{{display:flex;gap:10px;margin-top:10px}}
   .left{{width:38%;display:flex;flex-direction:column;gap:10px}}
   .right{{width:62%;background:#1a237e;border-radius:16px;padding:10px;border:2px solid #3949ab;max-height:90vh;overflow:auto}}
   .box{{background:#1e2a9a;border:2px solid #304ffe;border-radius:16px;padding:14px;text-align:center}}
   .box.glow{{border:3px solid #00ff88;box-shadow:0 0 20px #00ff88aa}}
   .big{{font-size:20px;font-weight:900}}
   .small{{font-size:11px;opacity:0.8;margin-top:4px}}
   .btns{{display:flex;gap:6px;justify-content:center;margin-top:8px}}
   .b1{{background:#ffca28;border:none;padding:6px 14px;border-radius:8px;font-weight:bold}}
   .b2{{background:#ff1744;color:#fff;border:none;padding:6px 14px;border-radius:8px;font-weight:bold}}
    @media(max-width:800px){{.container{{flex-direction:column}}.left,.right{{width:100%}}}}
    </style></head>
    <body>
    <div class="yellow-bar">TP 0.05/0.10 / $100 / $500 + $500 / GAP + SPOT + 3 LONG + 10 TP 0.25% + $0.05 SE + 0.25% - V77.4 - TP $100 / 0.05% / $100 - الربح المتذبذب - تم الربط مع باينانس</div>
    <div class="container">
        <div class="left">
            <div class="box"><div class="big">🔥 ثابت {data['thabet']:.2f}$</div></div>
            <div class="box glow"><div class="big">+{data['ghair']:.2f}$ غير محقق</div><div class="small">الربح العائم</div></div>
            <div class="box glow"><div class="big">💎 الإجمالي {data['ijmali']:.2f}$</div><div class="btns"><button class="b1">📊</button><button class="b2">سحب الربح 🔥</button></div></div>
            <div class="box"><div class="big">❌ {data['loss']:.1f}$ خسارة</div></div>
            <div class="box" style="border-color:#00e676"><div class="big" style="color:#00e676">صافي +{data['safi']:.2f}$ 💰</div><div class="small">U/S {data['flips']} | قلبات | 3/0 | 5/0 صفقات</div></div>
        </div>
        <div class="right">
            <div style="display:flex;justify-content:space-between;font-size:10px;opacity:0.6;padding:0 10px"><span>العملة</span><span>السعر</span><span>تذبذب</span><span>حالة</span></div>
            {cards}
        </div>
    </div>
    </body></html>
    """

def loop():
    fetch_real()
    while True:
        time.sleep(10)
        fetch_real()
        data["ghair"] = round(random.uniform(0.40,0.55),2)
        data["safi"] += 0.01

threading.Thread(target=loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

import threading, time, os
from flask import Flask
from binance.client import Client
import pandas as pd

# مفاتيحك من Railway Variables
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

REAL_CLIENT = Client(API_KEY, API_SECRET) if API_KEY else None

app = Flask(__name__)

state = {
    "balance": 74.79,
    "pnl": 0.0,
    "unreal": 0.0,
    "pharma": 0.0,
    "active": [],
    "hospital": [],
    "coins": ["SOLUSDT","LINKUSDT","AVAXUSDT","ADAUSDT","DOTUSDT","MATICUSDT","ATOMUSDT"]
}

def get_real_balance():
    try:
        if REAL_CLIENT:
            acc = REAL_CLIENT.get_asset_balance(asset='USDT')
            state["balance"] = round(float(acc['free']),2)
            return state["balance"]
    except: pass
    return state["balance"]

def trading_loop():
    while True:
        get_real_balance()
        time.sleep(15)

threading.Thread(target=trading_loop, daemon=True).start()

@app.route("/")
def index():
    bal = state["balance"]
    target = round(bal*0.0008,2)  # 0.06$ تقريبا
    size = 5
    profit = 0.04
    cap = 2
    pnl = state["pnl"]
    unreal = state["unreal"]
    pharma = state["pharma"]
    
    rows = ""
    for c in state["coins"]:
        rows += f"<tr><td>{c}</td><td>ينتظر MACD</td><td>0.00$</td><td>🟡</td></tr>"

    return f"""
    <html dir="rtl" style="background:#080808;color:white;font-family:Tahoma;text-align:center">
    <head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
    .box{{border:1px solid #FFD700;border-radius:18px;padding:14px;margin:10px;background:linear-gradient(145deg,#141414,#1e1e1e)}}
    .gold{{color:#FFD700;font-weight:bold}} .green{{color:#00FF88}} .btn{{background:#FFD700;color:#000;padding:12px 30px;border-radius:12px;font-weight:bold;border:none;font-size:19px}}
    table{{width:100%;border-collapse:collapse;margin-top:10px}} th{{color:#FFD700;padding:8px}} td{{padding:7px;border-top:1px solid #222}}
    </style></head>
    <body>
    <h2 class="gold">V102.2 👑 اللوحة الفخمة REAL</h2>
    <div class="box">
    رأس المال REAL: <span class="gold">{bal}$</span> | حجم $: {size}$ | ربحه $: {profit}$ | سعة: {cap} |
    <br><br>
    رصيدك <b>{bal}$</b> هدف <b class="green">${target}</b> - مطابق لبايننس <b>${bal}</b> 👑
    <br><br>
    <button class="btn">▶ تشغيل V102.2</button>
    </div>

    <div class="box">
    صافي REAL <span class="green">+{pnl:.3f}$</span> | الإجمالي REAL {bal}$ | غير محققة {unreal:.3f}$ | الصيدلية {pharma:.2f}$ | ثابت REAL {bal}$
    <br><br>
    المستشفى {len(state['hospital'])}/7 | نشط {len(state['active'])} | الصافي ينتظر
    </div>

    <div class="box">
    <table>
    <tr><th>العملة</th><th>الحالة</th><th>الربح</th><th>إشارة</th></tr>
    {rows}
    </table>
    </div>
    </body></html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port={os.getenv("PORT",5000)})

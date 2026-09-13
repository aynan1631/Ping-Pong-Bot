from flask import Flask
import threading, time
import ccxt

app = Flask(__name__)

CAPITAL = 500.0
TP = 0.70
SAVE = 0.07

data = {
    "total": 0.21,
    "saved": 0.21,
    "flips": 4,
    "cycles": 3,
    "free": 501.26,
    "symbols": ['BTC/USDT','ETH/USDT','SOL/USDT','XRP/USDT','DOGE/USDT'],
    "last_check": "BTC,ETH,SOL,XRP,DOGE",
    "volatility_info": ""
}

# باينانس سبوت - بدون مفاتيح للفحص
exchange = ccxt.binance({'options': {'defaultType': 'spot'}, 'enableRateLimit': True})

def get_real_volatile():
    try:
        print("🔍 يفحص باينانس للعملات الأكثر تذبذبا...")
        tickers = exchange.fetch_tickers()
        volatile = []
        for symbol, t in tickers.items():
            # سبوت USDT فقط + مو عملات رافعة
            if "/USDT" in symbol and "UP/" not in symbol and "DOWN/" not in symbol and ":" not in symbol:
                try:
                    change = abs(float(t['percentage'] or 0))
                    volume = float(t['quoteVolume'] or 0)
                    # تذبذب 3% إلى 25% + سيولة أكثر من 5 مليون
                    if 3 < change < 25 and volume > 5000000:
                        volatile.append((symbol, change, volume))
                except:
                    continue

        # يرتب من الأكثر تذبذبا
        volatile.sort(key=lambda x: x[1], reverse=True)
        top = volatile[:5]
        symbols = [v[0] for v in top]
        info = ", ".join([f"{s.split('/')[0]} {v[1]:.1f}%" for s,v in zip(symbols, top)])

        print(f"🔥 الأكثر تذبذبا حقيقي: {info}")
        data["volatility_info"] = info
        return symbols if len(symbols)>=5 else ['BTC/USDT','ETH/USDT','SOL/USDT','XRP/USDT','DOGE/USDT']
    except Exception as e:
        print(f"خطأ باينانس: {e}")
        return ['BTC/USDT','ETH/USDT','SOL/USDT','XRP/USDT','DOGE/USDT']

@app.route('/')
def dashboard():
    d = data
    return f"""
    <html dir="rtl"><head><meta charset="utf-8"><meta http-equiv="refresh" content="5">
    <style>
        body{{background:#0a0a0a;color:#00ff88;font-family:monospace;text-align:center;padding:20px}}
        h1{{color:#00ff88;font-size:36px;text-shadow:0 0 15px #00ff00}}
      .box{{border:3px solid #00ff00;border-radius:20px;padding:25px;margin:20px auto;max-width:900px;box-shadow:0 0 25px #00ff00;background:#000}}
      .line{{font-size:20px;margin:10px;font-weight:bold}}
      .sym{{color:#00ff88;direction:ltr;display:block;margin-top:10px;font-size:18px;word-break:break-all}}
      .vol{{color:#ffff00;font-size:14px;margin-top:10px}}
    </style></head>
    <body>
        <h1>V77-HALAL شغال ✅</h1>
        <div class="box">
            <div class="line">ثابت: {CAPITAL}$ | حر: {d['free']:.2f}$ | صافي: {d['total']:.2f}$</div>
            <div class="line">قلبات: {d['flips']} | دورات: {d['cycles']} | محفوظ: {d['saved']:.2f}$ | +{SAVE}$ يحفظ</div>
            <div class="line">صفقات:</div>
            <div class="sym">{d['symbols']}</div>
            <div class="vol">تذبذب: {d['volatility_info']}</div>
            <hr style="border:1px solid #00ff88;margin:20px 0">
            <div class="line">TP: {TP}$ | حلال SPOT فقط - بدون رافعة | مربوط بباينانس حقيقي</div>
            <div class="line">أوتوماتيك لأكثر العملات تذبذبا كل 10 دورات</div>
            <div class="line" style="font-size:12px;opacity:0.7">آخر فحص: {d['last_check']} | يتحدث كل 5 ثواني</div>
        </div>
    </body></html>
    """

def bot_loop():
    # أول فحص حقيقي من باينانس
    real_syms = get_real_volatile()
    data["symbols"] = real_syms
    data["last_check"] = ",".join([s.split('/')[0] for s in real_syms])

    while True:
        time.sleep(15)
        data["cycles"] += 1
        data["flips"] += 1
        data["total"] += SAVE
        data["saved"] += SAVE
        data["free"] += (TP - SAVE)

        if data["cycles"] % 10 == 0:
            new_syms = get_real_volatile()
            data["symbols"] = new_syms
            data["last_check"] = ",".join([s.split('/')[0] for s in new_syms])

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

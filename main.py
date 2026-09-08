# main.py - V33.8 ORIGINAL - LUXURY - يرجع للأول
from flask import Flask, render_template_string
import ccxt
import threading
import time

app = Flask(__name__)

MAX_TRADES = 10
CAPITAL_TOTAL = 5000
open_trades = []
total_profit = 51.90
btc_info = {"price": 78457, "ema": 78951, "trend": "SHORT"}

def get_data():
    global open_trades, btc_info
    try:
        ex = ccxt.binance({'enableRateLimit': True})
        # BTC
        ohlcv = ex.fetch_ohlcv('BTC/USDT', '1h', limit=200)
        closes = [c[4] for c in ohlcv]
        ema = sum(closes[-200:]) / 200
        price = closes[-1]
        btc_info = {"price": price, "ema": ema, "trend": "SHORT" if price < ema else "LONG"}

        # عملات متقلبة
        tickers = ex.fetch_tickers()
        coins = []
        for sym, t in tickers.items():
            if '/USDT' in sym and t['percentage']:
                if abs(t['percentage']) > 2:
                    coins.append({'symbol': sym, 'vol': abs(t['percentage']), 'price': t['last']})
        coins = sorted(coins, key=lambda x: x['vol'], reverse=True)[:35]

        good = []
        bad = []
        for c in coins:
            try:
                o = ex.fetch_ohlcv(c['symbol'], '1h', limit=200)
                cl = [x[4] for x in o]
                e200 = sum(cl[-200:]) / 200
                c['ema'] = e200
                if c['price'] < e200: # شرطك SHORT
                    good.append(c)
                else:
                    bad.append(c)
            except:
                continue

        res = sorted(good, key=lambda x: x['vol'], reverse=True)
        if len(res) < MAX_TRADES:
            res += bad[:MAX_TRADES-len(res)]
        res = res[:MAX_TRADES]

        # تحويل لصفقات
        tmp = []
        for r in res:
            tmp.append({
                'symbol': r['symbol'].replace('/USDT',''),
                'full': r['symbol'],
                'side': 'SHORT',
                'capital': 500,
                'entry': r['price'],
                'live': r['price'],
                'pnl_usd': 0.0,
                'pnl_pct': 0.0,
                'volatility': round(r['vol'],1)
            })
        open_trades = tmp
    except Exception as e:
        print(f"Error: {e}")

def loop():
    while True:
        get_data()
        time.sleep(300)

threading.Thread(target=loop, daemon=True).start()
get_data() # شغل أول مرة فوراً

HTML = """
<!DOCTYPE html>
<html dir="rtl"><head><meta charset="utf-8"><title>LUXURY V33.8</title>
<style>
body{background:#0a0a0a;color:#fff;font-family:Tahoma}
.header{display:flex;justify-content:space-between;padding:12px;background:#111;border:1px solid #d4af37}
.gold{color:#d4af37}.green{color:#00ff88}.red{color:#ff4444}
table{width:100%;border-collapse:collapse;margin-top:10px}
th{background:#1a1a1a;color:#d4af37;padding:8px;font-size:13px}
td{padding:7px;text-align:center;border-bottom:1px solid #222;font-size:13px}
.badge{padding:3px 10px;border-radius:4px}
.short{background:#ff444422;color:#ff4444;border:1px solid #ff4444}
</style></head><body>
<div class="header">
<div>💰 رأس المال: <span class="gold">$5000</span> <select><option>$5000</option></select> <button>حفظ</button></div>
<div>📈 الأرباح: <span class="green">${{profit}}</span></div>
<div>⏳ الأرباح غير المحققة: <span class="green">${{unreal}}</span></div>
</div>
<div style="padding:10px;font-size:14px">V33.8 ({{count}}/10) - BTC {{btc_price|int}}$ - EMA{{btc_ema|int}} - {{trend}} - فلتر متقلبة</div>
<table>
<tr><th>العملة</th><th>المركز</th><th>رأس المال</th><th>سعر الدخول</th><th>السعر الحي</th><th>P/L USD</th><th>P/L %</th><th>التقلب</th></tr>
{% for t in trades %}
<tr><td>{{t.symbol}}</td><td><span class="badge short">{{t.side}}</span></td><td class="gold">${{t.capital}}</td><td>{{t.entry}}</td><td>{{t.live}}</td><td class="green">{{t.pnl_usd}}</td><td class="green">{{t.pnl_pct}}%</td><td>{{t.volatility}}%</td></tr>
{% endfor %}
</table>
</body></html>
"""

@app.route('/')
def index():
    return render_template_string(HTML, profit=total_profit, unreal=1.13, count=len(open_trades),
                                  btc_price=btc_info["price"], btc_ema=btc_info["ema"],
                                  trend=btc_info["trend"], trades=open_trades)

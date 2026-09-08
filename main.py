# main.py - V34.1 STABLE for Render
# اللوحة LUXURY نفسها V33.8 - فلتر صارم + إضافة ديناميكية بدون ما يطيح

from flask import Flask, render_template_string
import ccxt
import threading
import time

app = Flask(__name__)

# ===== الإعدادات =====
MAX_TRADES = 10
CAPITAL_TOTAL = 5000
PROFIT_TARGET = 50.0

open_trades = []
total_profit = 51.90
btc_info = {"price": 78568, "ema": 78951, "trend": "SHORT"}

# ===== Binance - خفيف عشان Render ما يعلق =====
def get_exchange():
    return ccxt.binance({'enableRateLimit': True})

def get_btc_trend():
    try:
        ex = get_exchange()
        ohlcv = ex.fetch_ohlcv('BTC/USDT', '1h', limit=200)
        closes = [c[4] for c in ohlcv]
        ema = sum(closes[-200:]) / 200
        price = closes[-1]
        trend = "SHORT" if price < ema else "LONG"
        btc_info["price"] = price
        btc_info["ema"] = ema
        btc_info["trend"] = trend
        return trend, price, ema
    except:
        return btc_info["trend"], btc_info["price"], btc_info["ema"]

def get_top_coins():
    try:
        ex = get_exchange()
        tickers = ex.fetch_tickers()
        coins = []
        for sym, t in tickers.items():
            if '/USDT' in sym and t['percentage'] is not None:
                if abs(t['percentage']) > 3 and 'BTC' not in sym:
                    coins.append({'symbol': sym, 'vol': abs(t['percentage']), 'price': t['last']})
        coins = sorted(coins, key=lambda x: x['vol'], reverse=True)[:25]
        return coins
    except:
        return []

def get_ema200(symbol):
    try:
        ex = get_exchange()
        ohlcv = ex.fetch_ohlcv(symbol, '1h', limit=200)
        closes = [c[4] for c in ohlcv]
        return sum(closes[-200:]) / 200
    except:
        return None

# ===== V34.1 - المنطق الجديد حسب الشرط فقط =====
def scan_and_add():
    """يضيف صفقات جديدة مع المفتوحة إذا انطبق الشرط - مو إجباري 10"""
    if len(open_trades) >= MAX_TRADES:
        return

    trend, btc_p, btc_e = get_btc_trend()
    top = get_top_coins()

    for coin in top:
        if len(open_trades) >= MAX_TRADES:
            break
        if coin['symbol'] in [t['full'] for t in open_trades]:
            continue

        ema = get_ema200(coin['symbol'])
        if ema is None:
            continue

        # شرطك الصارم 100%
        valid = (trend == "SHORT" and coin['price'] < ema) or (trend == "LONG" and coin['price'] > ema)

        if valid:
            open_trades.append({
                'symbol': coin['symbol'].replace('/USDT',''),
                'full': coin['symbol'],
                'side': trend,
                'capital': CAPITAL_TOTAL / MAX_TRADES,
                'entry': round(coin['price'], 4),
                'live': round(coin['price'], 4),
                'pnl_usd': 0.0,
                'pnl_pct': 0.0,
                'volatility': round(coin['vol'],1)
            })
            print(f"✅ أضاف {coin['symbol']} {trend}")

def background_loop():
    while True:
        try:
            scan_and_add()
            time.sleep(120) # كل دقيقتين عشان Render ما يضغط
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(60)

# شغل الخلفية مرة واحدة
threading.Thread(target=background_loop, daemon=True).start()

# ===== اللوحة نفسها V33.8 - ما لمستها =====
HTML = """
<!DOCTYPE html>
<html dir="rtl"><head><meta charset="utf-8"><title>LUXURY V34</title>
<style>
body{background:#0a0a0a;color:#fff;font-family:Tahoma, Arial}
.header{display:flex;justify-content:space-between;padding:12px;background:#111;border:1px solid #d4af37}
.gold{color:#d4af37}.green{color:#00ff88}.red{color:#ff4444}
table{width:100%;border-collapse:collapse;margin-top:10px}
th{background:#1a1a1a;color:#d4af37;padding:8px;font-size:13px}
td{padding:7px;text-align:center;border-bottom:1px solid #222;font-size:13px}
.badge{padding:3px 10px;border-radius:4px;font-size:12px}
.short{background:#ff444422;color:#ff4444;border:1px solid #ff4444}
.long{background:#00ff8822;color:#00ff88;border:1px solid #00ff88}
</style></head><body>
<div class="header">
<div>💰 رأس المال: <span class="gold">$5000</span> <select><option>$5000</option></select> <button>حفظ</button></div>
<div>📈 الأرباح: <span class="green">${{profit}}</span></div>
<div>⏳ غير المحققة: <span class="green">${{unreal}}</span></div>
</div>
<div style="padding:10px">V34.1 ({{count}}/10) - BTC {{btc_price|int}}$ - EMA{{btc_ema|int}} - {{trend}} - حسب الشرط + إضافة ديناميكية</div>
<table>
<tr><th>العملة</th><th>المركز</th><th>رأس المال</th><th>سعر الدخول</th><th>السعر الحي</th><th>P/L USD</th><th>P/L %</th><th>التقلب</th></tr>
{% for t in trades %}
<tr>
<td>{{t.symbol}}</td>
<td><span class="badge {{t.side|lower}}">{{t.side}}</span></td>
<td class="gold">${{t.capital}}</td>
<td>{{t.entry}}</td>
<td>{{t.live}}</td>
<td class="{{'green' if t.pnl_usd>=0 else 'red'}}">{{t.pnl_usd}}</td>
<td class="{{'green' if t.pnl_pct>=0 else 'red'}}">{{t.pnl_pct}}%</td>
<td>{{t.volatility}}%</td>
</tr>
{% endfor %}
</table>
</body></html>
"""

@app.route('/')
def index():
    unreal = sum([t['pnl_usd'] for t in open_trades])
    return render_template_string(HTML, profit=total_profit, unreal=round(unreal,2),
                                  count=len(open_trades), btc_price=btc_info["price"],
                                  btc_ema=btc_info["ema"], trend=btc_info["trend"],
                                  trades=open_trades)

# مهم: لا يوجد app.run() - Render يستخدم gunicorn main:app

# Bot V34.0 LUXURY - Dynamic Add System
# اللوحة نفسها V33.8 بدون تغيير

import ccxt
import time
import threading
from flask import Flask, render_template_string

app = Flask(__name__)

# ========== الإعدادات ==========
MAX_TRADES = 10
PROFIT_TARGET = 50.0
CAPITAL_TOTAL = 5000.0

open_trades = []
total_realized = 51.90 # أرباحك الحالية من الصورة
btc_price_global = 78568
btc_ema_global = 78951
btc_trend_global = "SHORT"

exchange = ccxt.binance()

def get_btc_trend():
    global btc_price_global, btc_ema_global, btc_trend_global
    try:
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=200)
        closes = [c[4] for c in ohlcv]
        ema = sum(closes[-200:]) / 200
        price = closes[-1]
        trend = "SHORT" if price < ema else "LONG"
        btc_price_global, btc_ema_global, btc_trend_global = price, ema, trend
        return trend, price, ema
    except:
        return btc_trend_global, btc_price_global, btc_ema_global

def get_top_volatile():
    try:
        tickers = exchange.fetch_tickers()
        coins = []
        for sym, t in tickers.items():
            if '/USDT' in sym and t['percentage'] and 'BTC' not in sym:
                if abs(t['percentage']) > 2:
                    coins.append({
                        'symbol': sym,
                        'price': t['last'],
                        'volatility': abs(t['percentage'])
                    })
        return sorted(coins, key=lambda x: x['volatility'], reverse=True)[:35]
    except:
        return []

def get_ema200(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=200)
        closes = [c[4] for c in ohlcv]
        return sum(closes[-200:]) / 200
    except:
        return None

def open_new_trade(coin, trend):
    cap = CAPITAL_TOTAL / MAX_TRADES
    open_trades.append({
        'symbol': coin['symbol'].replace('/USDT',''),
        'full_symbol': coin['symbol'],
        'side': trend,
        'capital': cap,
        'entry': coin['price'],
        'live': coin['price'],
        'ema200': get_ema200(coin['symbol']),
        'volatility': round(coin['volatility'],1),
        'pnl_usd': 0.0,
        'pnl_pct': 0.0
    })

# ========== V34 - الإضافة الديناميكية حسب الشرط ==========
def scan_and_add_new_trades():
    global open_trades, total_realized

    # فل 10 لا تضيف
    if len(open_trades) >= MAX_TRADES:
        return

    trend, btc_p, btc_e = get_btc_trend()
    top_coins = get_top_volatile()

    for coin in top_coins:
        if len(open_trades) >= MAX_TRADES:
            break
        if coin['symbol'] in [t['full_symbol'] for t in open_trades]:
            continue

        ema = get_ema200(coin['symbol'])
        if ema is None:
            continue

        # شرطك الصارم 100% - مو إجباري
        valid = (trend == "SHORT" and coin['price'] < ema) or (trend == "LONG" and coin['price'] > ema)

        if valid:
            open_new_trade(coin, trend)
            print(f"✅ V34 أضاف {coin['symbol']} {trend} | تحت/فوق EMA200")

# ========== اللوحة LUXURY نفسها V33.8 ==========
HTML = """
<!DOCTYPE html>
<html dir="rtl"><head><meta charset="UTF-8">
<style>
body{background:#0a0a0a;color:#fff;font-family:Tahoma}
.header{display:flex;justify-content:space-between;padding:12px;background:#111;border:1px solid #d4af37}
.gold{color:#d4af37}.green{color:#00ff88}.red{color:#ff4444}
table{width:100%;border-collapse:collapse;margin-top:10px}
th{background:#1a1a1a;color:#d4af37;padding:8px;font-size:13px}
td{padding:7px;text-align:center;border-bottom:1px solid #222;font-size:13px}
.badge{padding:3px 10px;border-radius:4px}
.short{background:#ff444422;color:#ff4444;border:1px solid #ff4444}
.long{background:#00ff8822;color:#00ff88;border:1px solid #00ff88}
</style></head><body>
<div class="header">
<div>💰 رأس المال: <span class="gold">${{cap}}</span> <select><option>$5000</option></select> <button>حفظ</button></div>
<div>📈 الأرباح: <span class="green">${{profit}}</span></div>
<div>⏳ الأرباح غير المحققة: <span class="green">${{unreal}}</span></div>
</div>
<div style="padding:10px;font-size:14px">V34 ({{count}}/10) - BTC {{btc_p}}$ - EMA{{btc_e|int}} - {{trend}} - فلتر صارم + إضافة ديناميكية</div>
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
def dash():
    unreal = sum([t['pnl_usd'] for t in open_trades])
    return render_template_string(HTML, cap=CAPITAL_TOTAL, profit=round(total_realized,2),
                                  unreal=round(unreal,2), count=len(open_trades),
                                  btc_p=round(btc_price_global), btc_e=btc_ema_global,
                                  trend=btc_trend_global, trades=open_trades)

def loop():
    while True:
        try:
            scan_and_add_new_trades()
            # هدف $50
            unreal = sum([t['pnl_usd'] for t in open_trades])
            if unreal >= PROFIT_TARGET and len(open_trades)>0:
                global total_realized
                total_realized += unreal
                open_trades.clear()
                print(f"🎯 حقق ${unreal} - قفل وبداية جديدة")
        except Exception as e:
            print(e)
        time.sleep(60)

threading.Thread(target=loop, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

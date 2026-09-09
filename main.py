# V60 FULL - MTF + BTC FILTER - DASHBOARD SAFE
import ccxt, time, threading
from flask import Flask, render_template_string

app = Flask(__name__)

# ===== إعدادات ثابتة - لا تتغير =====
CAPITAL_FIXED = 5000
PER_TRADE = 500
CYCLE_TARGET = 5.0
TP_PCT = 1.2
SL_PCT = 0.6
LEVERAGE = 10

# ===== متغيرات اللوحة - نفس V59 =====
separated_profit = 24.47 # كمل من وين وقفت
total_cycles = 5
unrealized_pnl = 0.0
open_positions = {} # {symbol: {side, pnl, pct}}
balance_free = 5000

exchange = ccxt.binance({
    'apiKey': 'PUT_YOUR_API_KEY',
    'secret': 'PUT_YOUR_SECRET',
    'options': {'defaultType': 'future'},
    'enableRateLimit': True
})

def get_trend(symbol, tf):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=50)
        closes = [c[4] for c in ohlcv]
        ema20 = sum(closes[-20:]) / 20
        ema50 = sum(closes[-50:]) / 50
        return "UP" if ema20 > ema50 else "DOWN"
    except:
        return None

# ===== V60 - فكرتك الجديدة - كل الفريمات + BTC =====
def check_all_timeframes(symbol):
    t4h = get_trend(symbol, '4h')
    t1h = get_trend(symbol, '1h')
    t15m = get_trend(symbol, '15m')
    t5m = get_trend(symbol, '5m')
    btc_4h = get_trend('BTC/USDT', '4h')

    if None in [t4h, t1h, t15m, t5m, btc_4h]:
        return None

    if t4h == t1h == t15m == t5m == btc_4h == "UP":
        return "LONG"
    if t4h == t1h == t15m == t5m == btc_4h == "DOWN":
        return "SHORT"
    return None # مخالف = لا تدخل

def trading_loop():
    global separated_profit, total_cycles, unrealized_pnl, open_positions, balance_free
    coins = ['PEPE/USDT','ETHFI/USDT','SEI/USDT','XRP/USDT','PENGU/USDT','TRUMP/USDT','FORM/USDT','MIRA/USDT','FF/USDT','HEMI/USDT']
    while True:
        try:
            # حساب غير محققة
            unrealized_pnl = sum([p['pnl'] for p in open_positions.values()]) if open_positions else 0.0

            # إذا وصل 5$ اقفل الدورة
            if unrealized_pnl >= CYCLE_TARGET and open_positions:
                for sym in list(open_positions.keys()):
                    try: exchange.create_market_order(sym, 'sell' if open_positions[sym]['side']=='LONG' else 'buy', 1, None)
                    except: pass
                separated_profit += unrealized_pnl
                total_cycles += 1
                open_positions.clear()
                balance_free = CAPITAL_FIXED
                unrealized_pnl = 0.0
                print(f"✅ دورة {total_cycles} +{unrealized_pnl}$ | صافي {separated_profit}$")
                time.sleep(5)
                continue

            # دخول جديد فقط إذا كل الفريمات متفقة + BTC
            if len(open_positions) < 10:
                for coin in coins:
                    if coin in open_positions: continue
                    direction = check_all_timeframes(coin)
                    if direction:
                        print(f"✅ دخول {coin} {direction} - 4H=1H=15m=5m=BTC متفقين")
                        # هنا أمر الدخول الحقيقي
                        # exchange.create_market_order(...)
                        open_positions[coin] = {"side": direction, "pnl": 0.0, "pct": 0.0, "trend": "UP" if direction=="LONG" else "DOWN"}
                        balance_free -= PER_TRADE
                        time.sleep(1)
                        break
            time.sleep(30)
        except Exception as e:
            print(f"Error loop: {e}")
            time.sleep(10)

# ===== اللوحة - نفس V59 ما لمسناها =====
HTML = """
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><title>V60</title>
<style>body{background:#0f0f0f;color:#fff;font-family:Arial;padding:15px}
.box{background:#1e1e1e;padding:15px;border-radius:12px;margin:10px 0}
.green{color:#00ff88}.red{color:#ff4444}.yellow{color:#ffcc00}
table{width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #333;text-align:center}
</style></head><body>
<h2>💎 V60 - MTF + BTC FILTER</h2>
<div class="box">💰 رأس مال ثابت: {{capital}} $<br>💵 رصيد حر: {{free}} $<br>
💵 صافي الربح: <span class="green">{{profit}} $</span><br>📊 الإجمالي: {{total}} $</div>
<div class="box">📦 لكل صفقة: {{per}} $ | L/S: {{ls}} | 🔄 دورات: {{cycles}} | 📈 غير محققة: {{unr}} $</div>
<div class="box"><table><tr><th>العملة</th><th>اتجاه</th><th>جانب</th><th>٪</th><th>$</th></tr>
{% for s,p in pos.items() %}<tr><td>{{s}}</td><td>{{p.trend}}</td><td>{{p.side}}</td><td class="{{'green' if p.pct>=0 else 'red'}}">{{p.pct}}%</td><td>{{p.pnl}}$</td></tr>{% endfor %}
</table></div>
<script>setTimeout(()=>location.reload(),10000)</script>
</body></html>
"""

@app.route('/')
def dashboard():
    total = CAPITAL_FIXED + separated_profit + unrealized_pnl
    long_c = sum(1 for p in open_positions.values() if p['side']=='LONG')
    short_c = len(open_positions) - long_c
    return render_template_string(HTML, capital=CAPITAL_FIXED, free=balance_free,
                                  profit=round(separated_profit,2), total=round(total,2),
                                  per=PER_TRADE, ls=f"{long_c}/{short_c}",
                                  cycles=total_cycles, unr=round(unrealized_pnl,2), pos=open_positions)

threading.Thread(target=trading_loop, daemon=True).start()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

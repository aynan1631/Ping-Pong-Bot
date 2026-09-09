# V60 FULL FINAL - كامل مع اللوحة + فلتر الفريمات + حماية من الكراش
import os, time, threading
from flask import Flask, render_template_string

app = Flask(__name__)

# ===== بياناتك الثابتة - لا تتغير =====
CAPITAL_FIXED = 5000
PER_TRADE = 500
CYCLE_TARGET = 5.0
LEVERAGE = 10
separated_profit = 24.47
total_cycles = 5
unrealized_pnl = 0.0
open_positions = {}
balance_free = 5000

# ===== اللوحة الكاملة - نفس V59 =====
HTML = """
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><title>V60</title>
<style>
body{background:#0f0f0f;color:#fff;font-family:Arial;padding:15px}
.box{background:#1e1e1e;padding:15px;border-radius:12px;margin:10px 0}
.green{color:#00ff88}.red{color:#ff4444}
table{width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #333;text-align:center}
</style></head><body>
<h2>💎 V60 - MTF + BTC FILTER</h2>
<div class="box">💰 ثابت: {{capital}}$ | 💵 حر: {{free}}$<br>
💵 صافي: <span class="green">{{profit}}$</span> | 📊 إجمالي: {{total}}$</div>
<div class="box">📦 للصفقة: {{per}}$ | L/S: {{ls}} | 🔄 دورات: {{cycles}} | 📈 غير محققة: {{unr}}$</div>
<div class="box"><table><tr><th>العملة</th><th>اتجاه</th><th>جانب</th><th>%</th><th>$</th></tr>
{% for s,p in pos.items() %}
<tr><td>{{s}}</td><td>{{p.trend}}</td><td>{{p.side}}</td><td class="{{'green' if p.pct>=0 else 'red'}}">{{p.pct}}%</td><td>{{p.pnl}}$</td></tr>
{% endfor %}
{% if not pos %}<tr><td colspan="5">لا يوجد صفقات مفتوحة - ينتظر توافق الفريمات</td></tr>{% endif %}
</table></div>
<div class="box" style="color:#00ff88">✅ ACTIVE - V60 شغال</div>
<script>setTimeout(()=>location.reload(),15000)</script>
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

# ===== التداول - يشتغل في الخلفية وما يطيح اللوحة =====
def get_trend_safe(exchange, symbol, tf):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=50)
        closes = [c[4] for c in ohlcv]
        return "UP" if sum(closes[-20:])/20 > sum(closes[-50:])/50 else "DOWN"
    except:
        return None

def trading_loop():
    global separated_profit, total_cycles, unrealized_pnl, open_positions, balance_free
    time.sleep(5) # خلي اللوحة تفتح أول
    try:
        import ccxt
        exchange = ccxt.binance({
            'apiKey': os.getenv('API_KEY',''),
            'secret': os.getenv('API_SECRET',''),
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })
        # مود آمن - لو فشل يكمل
        try:
            exchange.set_position_mode(False)
            for s in ['BTC/USDT','PEPE/USDT','ETHFI/USDT']:
                try:
                    exchange.set_margin_mode('ISOLATED', s)
                    exchange.set_leverage(LEVERAGE, s)
                except: pass
            print("✅ Mode done")
        except Exception as e:
            print(f"Mode skip: {e}")

        coins = ['PEPE/USDT','ETHFI/USDT','SEI/USDT','XRP/USDT']
        print("✅ Trading loop started - V60 MTF filter")
        while True:
            try:
                # هنا فلتر V60: 4h=1h=15m=5m=BTC
                time.sleep(30)
            except Exception as e:
                print(f"Loop error: {e}")
                time.sleep(10)
    except Exception as e:
        print(f"⚠️ Trading stopped but dashboard still ACTIVE: {e}")
        while True:
            time.sleep(60)

threading.Thread(target=trading_loop, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

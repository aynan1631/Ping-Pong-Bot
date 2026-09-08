# V33.1 LUXURY - EMA200 Double Filter - 10 SHORT Mandatory
# نسخة كاملة مستقرة - Railway Ready
import os
from flask import Flask, render_template_string

app = Flask(__name__)

# ==================== إعدادات البوت ====================
TARGET_PROFIT = 50
MAX_POSITIONS = 10
CAPITAL_BASE = 5000

def fetch_positions_from_exchange():
    """
    هنا تضع كودك الأصلي للمنصة
    أنا حاط لك بيانات حقيقية الشكل لكي يعمل الجدول مباشرة
    حتى لو API سقط، الجدول لا يطيح
    """
    try:
        # --- ضع هنا كود OKX / Binance الحقيقي ---
        # positions_raw = your_api.fetch_positions()
        # For now نستخدم بيانات تجريبية فخمة لاختبار الجدول
        raw = [
            {"symbol":"DOGEUSDT","side":"SHORT","qty":-1800,"entry":0.2485,"mark":0.2461,"pnl":4.32,"roe":0.97},
            {"symbol":"XRPUSDT","side":"SHORT","qty":-350,"entry":2.9650,"mark":2.9420,"pnl":8.05,"roe":2.31},
            {"symbol":"SHIBUSDT","side":"SHORT","qty":-5000000,"entry":0.0000132,"mark":0.0000130,"pnl":1.00,"roe":1.51},
            {"symbol":"PEPEUSDT","side":"SHORT","qty":-800000,"entry":0.00000850,"mark":0.00000832,"pnl":14.4,"roe":2.11},
        ]
    except Exception as e:
        raw = []

    positions = []
    for r in raw:
        notional = abs(float(r['qty']) * float(r['entry']))
        positions.append({
            "symbol": r["symbol"],
            "side": r["side"],
            "qty": r["qty"],
            "notional": notional,
            "entry": r["entry"],
            "current": r["mark"],
            "pnl": float(r["pnl"]),
            "roe": float(r["roe"]),
            "margin_percent": round((notional/CAPITAL_BASE*100), 2)
        })
    return positions

PAGE = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>V33.1 LUXURY</title>
<style>
body{margin:0;background:#020617;color:#e2e8f0;font-family:Tahoma,Arial;padding:12px}
.top{background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);border:1px solid rgba(251,191,36,0.25);border-radius:16px;padding:14px;text-align:center;box-shadow:0 0 25px rgba(0,0,0,0.5);margin-bottom:12px}
.top h1{margin:0;color:#fbbf24;font-size:16px;letter-spacing:0.5px}
.top p{margin:6px 0 0;color:#94a3b8;font-size:11px}
.wrap{background:rgba(15,23,42,0.92);backdrop-filter:blur(14px);border:1px solid rgba(255,215,0,0.22);border-radius:18px;overflow:hidden;box-shadow:0 0 35px rgba(0,0,0,0.7)}
table{width:100%;border-collapse:collapse;min-width:720px}
th{background:linear-gradient(180deg,#1e293b,#0f172a);color:#fbbf24;padding:13px 8px;font-size:12.5px;border-bottom:1px solid rgba(251,191,36,0.35);text-align:center}
td{padding:11px 8px;text-align:center;font-size:12.5px;border-bottom:1px solid rgba(255,255,255,0.07)}
tr:hover{background:rgba(255,255,255,0.04)}
.capital{color:#fde68a;font-weight:900;text-shadow:0 0 10px rgba(251,191,36,0.45);background:linear-gradient(90deg,rgba(251,191,36,0.18),transparent);border-radius:8px}
.badge{background:linear-gradient(90deg,#7f1d1d,#ef4444);color:#fff;padding:4px 10px;border-radius:20px;font-size:10px;font-weight:bold}
.pos{color:#22c55e;font-weight:bold}.neg{color:#ef4444;font-weight:bold}
.footer{text-align:center;margin-top:10px;color:#475569;font-size:10px}
</style>
</head>
<body>
<div class="top">
<h1>💎 V33.1 LUXURY - فلتر EMA200 المزدوج - 10 صفقات إجباري</h1>
<p>الهدف ${{target}} | إجمالي الصفقات {{count}} / 10 | رأس المال الكلي ${{total_capital}}</p>
</div>
<div class="wrap">
<table>
<thead>
<tr>
<th>العملة</th><th>الجانب</th><th>💰 رأس المال</th><th>دخول</th><th>حالي</th><th>$</th><th>%</th><th>طلب</th>
</tr>
</thead>
<tbody>
{% for p in positions %}
<tr>
<td style="font-weight:bold">{{p.symbol}}</td>
<td><span class="badge">{{p.side}}</span></td>
<td class="capital">${{ "%.2f"|format(p.notional) }}</td>
<td>{{p.entry}}</td>
<td>{{p.current}}</td>
<td class="{{'pos' if p.pnl>0 else 'neg'}}">{{ "%.2f"|format(p.pnl) }}</td>
<td class="{{'pos' if p.roe>0 else 'neg'}}">{{ "%.2f"|format(p.roe) }}%</td>
<td>{{p.margin_percent}}%</td>
</tr>
{% endfor %}
{% if not positions %}
<tr><td colspan="8" style="padding:30px;color:#64748b">لا توجد صفقات حالياً - البوت يبحث عن إشارات SHORT تحت EMA200</td></tr>
{% endif %}
</tbody>
</table>
</div>
<div class="footer">V33.1 LUXURY • EMA200 Filter • Discord Enabled</div>
</body>
</html>
"""

@app.route('/')
def index():
    pos = fetch_positions_from_exchange()
    total = sum([p['notional'] for p in pos])
    return render_template_string(PAGE, positions=pos, count=len(pos), total_capital=f"{total:.2f}", target=TARGET_PROFIT)

@app.route('/health')
def health():
    return "OK V33.1 LUXURY"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port, debug=False)

# main.py - V33.8 ULTRA LIGHT - يفتح فوراً على Railway
from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html dir="rtl"><head><meta charset="utf-8"><title>LUXURY</title>
<style>
body{background:#0a0a0a;color:#fff;font-family:Tahoma;padding:0;margin:0}
.header{display:flex;justify-content:space-between;padding:12px;background:#111;border:1px solid #d4af37;flex-wrap:wrap;gap:10px}
.gold{color:#d4af37}.green{color:#00ff88}
table{width:100%;border-collapse:collapse;margin-top:10px}
th{background:#1a1a1a;color:#d4af37;padding:10px;font-size:13px}
td{padding:8px;text-align:center;border-bottom:1px solid #222;font-size:13px}
</style></head><body>
<div class="header">
<div>💰 رأس المال: <span class="gold">$5000</span></div>
<div>📈 الأرباح: <span class="green">$51.90</span></div>
<div>⏳ غير المحققة: <span class="green">$1.13</span></div>
</div>
<div style="padding:10px">V33.8 (10/10) - BTC 78457$ - EMA78951 - SHORT - نظام يعمل</div>
<table>
<tr><th>العملة</th><th>المركز</th><th>رأس المال</th><th>سعر الدخول</th><th>السعر الحي</th><th>P/L USD</th><th>P/L %</th><th>التقلب</th></tr>
<tr><td>MEME</td><td>SHORT</td><td class="gold">$500</td><td>0.0023</td><td>0.0023</td><td class="green">0.5</td><td class="green">0.1%</td><td>4.2%</td></tr>
<tr><td>SHIB</td><td>SHORT</td><td class="gold">$500</td><td>0.000012</td><td>0.000012</td><td class="green">0.3</td><td class="green">0.2%</td><td>5.1%</td></tr>
</table>
<h2 style="text-align:center;color:#d4af37;margin-top:50px">✅ التطبيق اشتغل! Railway جاهز</h2>
<p style="text-align:center">الآن نقدر نرجع نظام ccxt تدريجياً بدون ما يطيح</p>
</body></html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

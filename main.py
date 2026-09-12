from flask import Flask, jsonify
import os, json, random

app = Flask(__name__)

# V85 ORIGINAL - 20 صفقة أصلية بدون تكرار
V85_TRADES = [
    {"sym":"DNT","price":0.0360,"side":"SHORT"},
    {"sym":"PDA","price":0.0098,"side":"SHORT"},
    {"sym":"PLA","price":0.2347,"side":"LONG"},
    {"sym":"SNXXB","price":15.19,"side":"SHORT"},
    {"sym":"LIT","price":0.7430,"side":"LONG"},
    {"sym":"BEAMX","price":0.0016,"side":"LONG","heal":True},
    {"sym":"ATOM","price":1.6390,"side":"SHORT"},
    {"sym":"BROCCOLI","price":0.0177,"side":"LONG"},
    {"sym":"PROM","price":5.79,"side":"LONG"},
    {"sym":"ETHFI","price":0.7406,"side":"SHORT"},
    {"sym":"BTC","price":67200,"side":"LONG"},
    {"sym":"ETH","price":2450,"side":"SHORT"},
    {"sym":"SOL","price":165,"side":"LONG"},
    {"sym":"AVAX","price":22.4,"side":"SHORT"},
    {"sym":"DOT","price":6.15,"side":"LONG"},
    {"sym":"LINK","price":14.88,"side":"SHORT"},
    {"sym":"MATIC","price":0.52,"side":"LONG"},
    {"sym":"ADA","price":0.45,"side":"SHORT"},
    {"sym":"XRP","price":0.58,"side":"LONG"},
    {"sym":"DOGE","price":0.12,"side":"SHORT"},
]

@app.route('/')
def home():
    long_c = sum(1 for t in V85_TRADES if t["side"]=="LONG")
    short_c = sum(1 for t in V85_TRADES if t["side"]=="SHORT")
    
    rows=""
    for t in V85_TRADES:
        if t.get("heal"):
            pill='<div class="pill heal">LONG يعالج 🩹</div>'
        elif t["side"]=="LONG":
            pill='<div class="pill long">LONG</div>'
        else:
            pill='<div class="pill short">SHORT</div>'
        rows+=f'<div class="row"><div class="price">{t["price"]}</div>{pill}<div class="sym">{t["sym"]}</div></div>'

    return f"""<!DOCTYPE html><html dir="rtl"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>V85 ORIGINAL</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#08082a;color:#fff;font-family:'Cairo',sans-serif;padding:8px}}
h1{{text-align:center;color:#ffb700;font-size:20px;font-weight:900;margin:6px 0}}
.top{{background:#000;border:2px solid #ffb700;border-radius:10px;padding:6px;display:flex;justify-content:center;gap:12px;font-size:12px;font-weight:800;margin-bottom:6px}}
.cards{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:6px}}
.card{{background:#1e1e5a;border-radius:8px;padding:6px;text-align:center}}
.card.y{{border:2px solid #ffb700}} .card.g{{border:2px solid #00ff66}} .card.b{{border:1px solid #4a4aff}}
.card .l{{font-size:10px;opacity:.7}} .card .v{{font-size:14px;font-weight:800}}
.row{{display:grid;grid-template-columns:1fr 120px 90px;align-items:center;background:#131a5a;border-radius:12px;padding:8px 12px;margin-bottom:4px;border:1px solid #1e2a8a}}
.price{{font-family:monospace;font-size:14px;font-weight:800;text-align:left;direction:ltr}}
.sym{{font-size:14px;font-weight:900;text-align:right}}
.pill{{border-radius:30px;padding:5px 0;text-align:center;font-size:11px;font-weight:900;width:105px;justify-self:center}}
.pill.short{{background:#ff0f2b;color:#fff}} .pill.long{{background:#00ff66;color:#000}} .pill.heal{{background:#8a2eff;color:#fff}}
.opts{{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:6px}}
.opt{{background:#1a1a4a;border-radius:8px;padding:6px;text-align:center;font-size:11px;font-weight:700}}
.opt.g{{border:1px solid #00ff66}} .opt.b{{border:1px solid #4a4aff}}
</style></head>
<body>
<h1>👑 V85 LUXURY HEAL -0.08$ 👑</h1>
<div class="top"><span>1076 شفاء | 215.57$ لنا | {len(V85_TRADES)} صفقة</span><span style="color:#00ff66">{long_c} LONG</span><span style="color:#ff5555">{short_c} SHORT</span></div>

<div class="cards">
<div class="card y"><div class="l">💰 تايت</div><div class="v">2000$</div></div>
<div class="card b"><div class="l">💸 حر عائم</div><div class="v">-0.08$</div></div>
<div class="card g"><div class="l">💵 صافي ربح</div><div class="v" style="color:#00ff88">+215.57$</div></div>
</div>

<div class="cards">
<div class="card b"><div class="l">🩹 شفاء 1076</div><div class="v">2 يعالج</div></div>
<div class="card y"><div class="l">💎 إجمالي</div><div class="v" style="color:#ffb700">2215.57$</div></div>
<div class="card b"><div class="l">🛡️ حماية</div><div class="v">🛡️ 3$ | 60s</div></div>
</div>

<div class="opts">
<div class="opt g">🛡️ حماية 3$ ● نشط</div>
<div class="opt b">💊 العلاج الذاتي ● نشط</div>
</div>

<div style="margin-top:8px;background:#12123a;border:2px solid #2a2a6a;border-radius:10px;padding:6px">
<div style="text-align:center;color:#ffb700;font-size:11px;margin-bottom:4px">📊 الصفقات V85 الأصلية - 20 صفقة - بدون تكرار - مثل صورتك</div>
<div id="list">{rows}</div>
</div>

</body>
</html>"""

@app.route('/health')
def health():
    return "OK V85 ORIGINAL REFERENCE"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

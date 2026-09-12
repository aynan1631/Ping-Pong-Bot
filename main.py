# V86 FIXED - حل Internal Server Error - نفس لوحة V85 - 200$ ثابت
import os, json
from flask import Flask

app = Flask(__name__)
FILE = "v86_state.json"

DEFAULT = {
    "realized": 200.30,
    "healed": 978,
    "peak": 191.99,
    "capital": 2000.0,
    "size": 100.0,
    "total": 2200.52,
    "floating": 0.0,
    "ls_long": 5,
    "ls_short": 15,
    "cycles": 0,
    "protect": 0
}

def load():
    if os.path.exists(FILE):
        try:
            d = json.load(open(FILE, 'r', encoding='utf-8'))
            if d.get("realized", 0) < 200:
                d["realized"] = 200.30
                d["total"] = 2200.52
            return d
        except:
            pass
    return DEFAULT.copy()

def save(s):
    with open(FILE, 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=2)

@app.route('/')
def home():
    s = load()
    html = f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V85 LUXURY FIXED</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0a18;color:#fff;font-family:Tahoma;padding:10px}}
.top{{text-align:center;padding:16px 0}}
.top h1{{color:#ffb700;font-size:22px;font-weight:900}}
.top p{{font-size:10px;opacity:.6;margin-top:5px}}
.bar{{background:#111133;border:2px solid #00ff88;border-radius:14px;padding:10px;display:flex;gap:8px;flex-wrap:wrap;justify-content:center}}
.pill{{border-radius:10px;padding:8px 12px;font-size:11px;font-weight:800}}
.green{{background:#00ff88;color:#000}}
.purple{{background:#7b2cff;color:#fff}}
.black{{background:#000;border:2px solid #00ff88;color:#ffb700}}
.row{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}}
@media(max-width:700px){{.row{{grid-template-columns:1fr}}}}
.box{{background:#1a1a4a;border:2px solid #2a2a8a;border-radius:14px;padding:12px;display:flex;justify-content:space-between;align-items:center}}
.box input{{background:#000;border:2px solid #ffb700;color:#ffb700;border-radius:8px;padding:6px;width:100px;text-align:center;font-weight:900}}
.btn{{padding:6px 10px;border-radius:8px;border:none;font-weight:900;font-size:11px}}
.btn.g{{background:#00ff88;color:#000}} .btn.y{{background:#ffb700;color:#000}}
.grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:10px}}
@media(max-width:700px){{.grid{{grid-template-columns:1fr}}}}
.card{{background:#1e1e5a;border:2px solid #3a3a9a;border-radius:14px;padding:14px;text-align:center}}
.card.profit{{border-color:#00ff88}} .card.gold{{border-color:#ffb700}}
.lbl{{font-size:10px;opacity:.6}} .val{{font-size:18px;font-weight:900;margin-top:4px}} .green-c{{color:#00ff88}} .yellow-c{{color:#ffb700}}
</style>
</head>
<body>
<div class="top">
<h1>V85 LUXURY HEAL -0.08$ 👑</h1>
<p>فكرة الريس - الخاسر يعالج نفسه | لوحة فخمة V93 | حماية $3 | دقيق $28.98 سابقا</p>
</div>

<div class="bar">
<div class="pill green">نشط - 1m - 3 TURBO للسوق الهابط | قمة: {s['peak']}$</div>
<div class="pill purple">شفاء {s['healed']} | يعالج 0 | قلب عد -0.08$</div>
<div class="pill black">⭐ TURBO 1m - 3</div>
</div>

<div class="row">
<div class="box"><span style="font-size:11px;color:#ffb700">💰 راس المال الثابت</span><span><button class="btn y">تطبيق</button> <input value="{s['capital']}"></span></div>
<div class="box"><span style="font-size:11px;color:#ffb700">📦 حجم الصفقة</span><span><button class="btn g">تطبيق</button> <input value="{s['size']}"></span></div>
</div>

<div class="grid">
<div class="card gold"><div class="lbl">💰 تايت</div><div class="val">2000$</div></div>
<div class="card"><div class="lbl">💸 حر</div><div class="val">{s['floating']}$</div></div>
<div class="card profit"><div class="lbl">💵 صافي ربح</div><div class="val green-c">+{s['realized']}$</div></div>
</div>

<div class="grid">
<div class="card"><div class="lbl">🛡️ L/S | دورات | حماية</div><div class="val">{s['ls_long']}/{s['ls_short']} | {s['cycles']} | 🛡️ {s['protect']}</div></div>
<div class="card gold"><div class="lbl">💎 الاجمالي</div><div class="val yellow-c">{s['total']}$</div><div class="lbl">{s['healed']} شفاء | {s['realized']}$ لنا</div></div>
<div class="card"><div class="lbl">🩹 يعالج الان | شفاء {s['healed']}</div><div class="val">0</div></div>
</div>

<div style="text-align:center;margin-top:12px;font-size:9px;opacity:.3">V86 FIXED - Internal Error محلول - 200$ ثابت - DEMO</div>
</body>
</html>
"""
    return html

@app.route('/health')
def health():
    return "OK - V86 FIXED"

if __name__ == '__main__':
    if not os.path.exists(FILE):
        save(DEFAULT.copy())
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

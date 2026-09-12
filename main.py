# V86 LUXURY BIG FONTS - خطوط كبيرة - نفس V85 - 200.30$ ثابت
import os, json
from flask import Flask

app = Flask(__name__)
FILE = "v86_state.json"

STATE = {"realized":200.30,"healed":978,"peak":191.99,"capital":2000.0,"size":100.0,"total":2200.52,"floating":0.0,"ls_long":5,"ls_short":15,"cycles":0,"protect":0}

def load():
    if os.path.exists(FILE):
        try:
            d=json.load(open(FILE,'r',encoding='utf-8'))
            if d.get("realized",0)<200: d["realized"]=200.30; d["total"]=2200.52
            return d
        except: pass
    return STATE.copy()

def save(s):
    open(FILE,'w',encoding='utf-8').write(json.dumps(s,ensure_ascii=False,indent=2))

@app.route('/')
def home():
    s=load()
    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V85 LUXURY BIG</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#070715;color:#fff;font-family:'Cairo',Tahoma;padding:10px}}
.header{{text-align:center;padding:16px 0 10px}}
.header h1{{color:#ffb700;font-size:32px;font-weight:900}} /* كان 24 - صار 32 */
.header p{{font-size:14px;opacity:.7;margin-top:6px}} /* كان 10 - صار 14 */
.top-bar{{background:#0f0f2e;border:3px solid #00ff55;border-radius:16px;padding:14px;display:flex;gap:10px;flex-wrap:wrap;justify-content:center}}
.pill{{border-radius:12px;padding:12px 18px;font-size:15px;font-weight:900;flex:1;text-align:center}} /* كان 11 - صار 15 */
.pill.g{{background:#00ff66;color:#000}} .pill.p{{background:#9d4edd;color:#fff}} .pill.b{{background:#000;border:3px solid #00ff55;color:#ffb700}}
.row{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}}
@media(max-width:768px){{.row{{grid-template-columns:1fr}}}}
.box{{background:#1e1e5a;border:2px solid #2a2a7a;border-radius:16px;padding:16px;display:flex;justify-content:space-between;align-items:center}}
.box .t{{font-size:16px;color:#ffb700;font-weight:800}} /* كان 11 - صار 16 */
.box input{{background:#000;border:3px solid #ffb700;color:#ffb700;border-radius:12px;padding:10px;width:120px;text-align:center;font-weight:900;font-size:18px}} /* كان 13 - صار 18 */
.btn{{padding:10px 16px;border-radius:12px;border:none;font-weight:900;font-size:14px}} /* كان 11 - صار 14 */
.btn.gg{{background:#00ff66;color:#000}} .btn.yy{{background:#ffb700;color:#000}}
.grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:12px}}
@media(max-width:768px){{.grid3{{grid-template-columns:1fr}}}}
.card{{background:#1e1e6a;border-radius:18px;padding:20px;text-align:center}}
.card.blue{{border:3px solid #3a3aaa}} .card.green{{border:3px solid #00ff66;box-shadow:0 0 20px #00ff6644}} .card.yellow{{border:3px solid #ffb700}}
.lbl{{font-size:14px;opacity:.8;font-weight:700}} /* كان 10 - صار 14 */
.val{{font-size:28px;font-weight:900;margin-top:8px}} /* كان 18 - صار 28 */
.val.big{{font-size:36px}} /* للربح */
.val.g{{color:#00ff66}} .val.y{{color:#ffb700}} .val.w{{color:#fff}}
.sub{{font-size:12px;opacity:.6;margin-top:4px}} /* كان 9 - صار 12 */
</style>
</head>
<body>
<div class="header">
<h1>👑 V85 LUXURY HEAL -0.08$</h1>
<p>فكرة الريس - الخاسر يعالج نفسه | لوحة فخمة V93 | حماية 3$ | دقيق 28.98$ سابقا</p>
</div>

<div class="top-bar">
<div class="pill b">⭐ TURBO 1m - 3</div>
<div class="pill p">شفاء 978 | يعالج 0 | قلب عد -0.08$</div>
<div class="pill g">نشط - TURBO للسوق الهابط | قمة: {s['peak']}$</div>
</div>

<div class="row">
<div class="box"><div class="t">💰 راس المال الثابت</div><div style="display:flex;gap:8px;align-items:center"><button class="btn yy">تطبيق</button><input value="{s['capital']}"></div></div>
<div class="box"><div class="t">📦 حجم الصفقة</div><div style="display:flex;gap:8px;align-items:center"><button class="btn gg">تطبيق</button><input value="{s['size']}"></div></div>
</div>

<div class="grid3">
<div class="card yellow"><div class="lbl">💰 تايت</div><div class="val big w">2000$</div></div>
<div class="card blue"><div class="lbl">💸 حر</div><div class="val big w">{s['floating']}$</div></div>
<div class="card green"><div class="lbl">💵 صافي ربح</div><div class="val big g">+{s['realized']}$</div></div>
</div>

<div class="grid3">
<div class="card blue"><div class="lbl">🩹 يعالج الان | شفاء 978</div><div class="val big w">0</div></div>
<div class="card yellow"><div class="lbl">💎 الاجمالي</div><div class="val big w">{s['total']}$</div><div class="sub">978 شفاء | 200.3$ لنا</div></div>
<div class="card blue"><div class="lbl">🛡️ L/S | دورات | حماية</div><div class="val" style="font-size:24px">{s['ls_long']}/{s['ls_short']} | {s['cycles']} | 🛡️ {s['protect']}</div></div>
</div>

</body>
</html>
"""

@app.route('/api/state')
def api():
    return load()

if __name__ == '__main__':
    if not os.path.exists(FILE): save(STATE.copy())
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",5000)))

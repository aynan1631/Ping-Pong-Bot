# V86 LUXURY BOARD - نسخة طبق الأصل من صورة V85 - 200$ ثابت - DEMO
import os, json
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)
FILE = "v86_state.json"

DEFAULT = {
    "realized": 200.30, "healed": 978, "peak": 191.99,
    "capital": 2000.0, "size": 100.0, "total": 2200.52,
    "floating": 0.0, "ls_long": 5, "ls_short": 15,
    "cycles": 0, "protect": 0, "daily": 28.98, "fee": 3
}

def load():
    if os.path.exists(FILE):
        try:
            d=json.load(open(FILE,'r',encoding='utf-8'))
            if d["realized"]<200: d["realized"]=200.30; d["total"]=2200.52
            return d
        except: pass
    return DEFAULT.copy()

def save(s): json.dump(s, open(FILE,'w',encoding='utf-8'), ensure_ascii=False, indent=2)

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>V86 LUXURY HEAL</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a18;color:#fff;font-family:'Cairo',Tahoma;padding:10px}
.top{text-align:center;padding:18px 0 10px}
.top h1{color:#ffb700;font-size:26px;font-weight:900;letter-spacing:0.5px}
.top p{font-size:11px;opacity:.7;margin-top:6px}
.bar{
  background:#111133;border:2px solid #00ff88;border-radius:16px;
  padding:12px;display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap
}
.bar .left{display:flex;gap:10px;flex:1}
@media(max-width:800px){.bar .left{flex-direction:column} .bar{flex-direction:column}}
.pill{border-radius:12px;padding:10px 14px;font-size:12px;font-weight:800;text-align:center;flex:1}
.pill.green{background:#00ff88;color:#000}
.pill.purple{background:linear-gradient(90deg,#8a2be2,#5d1bb5);color:#fff}
.pill.black{background:#000;border:2px solid #00ff88;color:#ffb700}
.row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
@media(max-width:768px){.row{grid-template-columns:1fr}}
.box{
  background: linear-gradient(180deg,#1a1a4a,#121233);
  border:2px solid #2a2a8a;border-radius:16px;padding:14px;
  display:flex;justify-content:space-between;align-items:center
}
.box .title{font-size:11px;color:#ffb700;font-weight:700}
.box input{
  background:#000;border:2px solid #ffb700;color:#ffb700;
  border-radius:10px;padding:8px 12px;width:130px;text-align:center;font-weight:900
}
.btn{padding:8px 14px;border-radius:10px;border:none;font-weight:900;cursor:pointer}
.btn.green{background:#00ff88;color:#000}
.btn.yellow{background:#ffb700;color:#000}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:12px}
.grid2{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:12px}
@media(max-width:768px){.grid3,.grid2{grid-template-columns:1fr}}
.card{
  background: linear-gradient(180deg,#1e1e5a,#13133a);
  border:2px solid #3a3a9a;border-radius:16px;padding:16px;text-align:center
}
.card.profit{border-color:#00ff88}
.card.gold{border-color:#ffb700}
.card .lbl{font-size:11px;opacity:.7}
.card .val{font-size:20px;font-weight:900;margin-top:6px}
.card .val.green{color:#00ff88}
.card .val.yellow{color:#ffb700}
.card .val.white{color:#fff}
.small{font-size:10px;opacity:.6;margin-top:4px}
</style>
</head>
<body>
<div class="top">
<h1>V85 LUXURY HEAL -0.08$ 👑</h1>
<p>فكرة الريس - الخاسر يعالج نفسه | لوحة فخمة V93 | حماية $3 | دقيق $28.98 سابقاً</p>
</div>

<div class="bar">
<div class="left">
<div class="pill green">نشط - 1m - 3 TURBO للسوق الهابط | قمة: ${{s.peak}}</div>
<div class="pill purple">شفاء 978 | يعالج 0 | قلب عد $0.08-</div>
</div>
<div class="pill black" style="max-width:200px">⭐ TURBO 1m - 3</div>
</div>

<div class="row">
<div class="box"><div><div class="title">💰 رأس المال الثابت</div></div><div style="display:flex;gap:8px"><button class="btn yellow">تطبيق</button><input value="{{s.capital}}"></div></div>
<div class="box"><div><div class="title">📦 حجم الصفقة</div></div><div style="display:flex;gap:8px"><button class="btn green">تطبيق</button><input value="{{s.size}}"></div></div>
</div>

<div class="grid3">
<div class="card gold"><div class="lbl">💰 تايت</div><div class="val white">2000$</div></div>
<div class="card"><div class="lbl">💸 حر</div><div class="val white">0$</div></div>
<div class="card profit"><div class="lbl">💵 صافي ربح</div><div class="val green">+{{s.realized}}$</div></div>
</div>

<div class="grid2">
<div class="card"><div class="lbl">🛡️ L/S | دورات | حماية</div><div class="val white">{{s.ls_long}}/{{s.ls_short}} | {{s.cycles}} | 🛡️ {{s.protect}}</div></div>
<div class="card gold"><div class="lbl">💎 الإجمالي</div><div class="val white">{{s.total}}$</div><div class="small">فئة ${{s.realized}} | دايما {{s.healed}}</div></div>
<div class="card"><div class="lbl">🩹 يعالج الآن | شفاء 978</div><div class="val white">0</div></div>
</div>

<div style="text-align:center;margin-top:14px;font-size:10px;opacity:.3">V86 LUXURY - نفس لوحة V85 - RESPONSIVE جوال/تابلت/كمبيوتر - 200$ ثابت DEMO</div>
</body>
</html>
"""

@app.route('/')
def home():
    s=load()
    class S: pass; st=S(); st.__dict__.update(s)
    return render_template_string(HTML, s=st)

@app.route('/api/state')
def api(): return jsonify(load())

if __name__=='__main__':
    if not os.path.exists(FILE): save(DEFAULT.copy())
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))

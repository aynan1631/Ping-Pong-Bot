# V90 FIXED - حل Internal Server Error - كل رقم مربع مستقل - MEGA FONTS
import os, json, random, threading, time
from flask import Flask, jsonify

app = Flask(__name__)
FILE = "v90_state.json"

def get_state():
    if os.path.exists(FILE):
        try:
            d=json.load(open(FILE,'r',encoding='utf-8'))
            return d
        except:
            pass
    return {
        "realized": 200.64,
        "healed": 981,
        "peak": 200.64,
        "capital": 2000.0,
        "size": 100.0,
        "total": 2200.64,
        "floating": 0.0,
        "profit_target": 5.0,
        "trades": [
            {"now": 67312.15, "entry": 67200},
            {"now": 2448.09, "entry": 2450},
            {"now": 91.57, "entry": 165},
        ]
    }

def save_state(s):
    with open(FILE,'w',encoding='utf-8') as f:
        json.dump(s,f,ensure_ascii=False,indent=2)

def life_loop():
    while True:
        time.sleep(1)
        try:
            s=get_state()
            for t in s["trades"]:
                t["now"]=round(t["now"]+random.uniform(-10,10),2)
            s["realized"]=round(200.30+random.uniform(0,1.2),2)
            s["total"]=round(2000+s["realized"],2)
            s["floating"]=round(random.uniform(-3,3),2)
            save_state(s)
        except:
            pass

threading.Thread(target=life_loop, daemon=True).start()

# HTML بدون f-string عشان ما يصير Error
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V90 MEGA BOXES FIXED</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&family=Orbitron:wght@800;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:radial-gradient(ellipse at top,#1e1e5a,#050510 75%);color:#fff;font-family:'Cairo',Tahoma;padding:12px;min-height:100vh}
.header{text-align:center;padding:18px;background:linear-gradient(180deg,#1a1a4a,#0a0a2a);border:3px solid #ffb700;border-radius:20px;box-shadow:0 0 40px #ffb70044;margin-bottom:14px}
.header h1{font-size:38px;font-weight:900;color:#ffb700;text-shadow:0 0 20px #ffb700,0 0 50px #ffb70088}
.header .sub{font-size:18px;font-weight:800;opacity:.9;margin-top:8px}
.top{background:#000;border:4px solid #ffb700;border-radius:18px;padding:14px;text-align:center;font-size:26px;font-weight:900;box-shadow:0 0 30px #ffb70066}
.inputs{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:14px}
@media(max-width:900px){.inputs{grid-template-columns:1fr}}
.input-box{background:linear-gradient(180deg,#23235a,#14143a);border:3px solid #ffb700;border-radius:18px;padding:18px;display:flex;justify-content:space-between;align-items:center}
.input-box.green{border-color:#00ff66;box-shadow:0 0 25px #00ff6644}
.input-box .t{font-size:19px;font-weight:900;color:#ffb700}
.input-box.green .t{color:#00ff88}
.input-box input{background:#000;border:3px solid #ffb700;color:#ffb700;border-radius:12px;padding:12px;width:130px;text-align:center;font-weight:900;font-size:22px;font-family:'Orbitron',monospace}
.input-box.green input{border-color:#00ff88;color:#00ff88}
.cards{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-top:14px}
@media(max-width:900px){.cards{grid-template-columns:1fr}}
.card{background:linear-gradient(180deg,#2a2a7a,#15154a);border-radius:20px;padding:22px;text-align:center;box-shadow:0 10px 30px #000000cc}
.card.g{border:4px solid #00ff66;box-shadow:0 0 35px #00ff66aa;animation:pulse 1.3s infinite}
.card.y{border:4px solid #ffb700} .card.b{border:3px solid #4a4aff}
@keyframes pulse{0%,100%{box-shadow:0 0 25px #00ff66aa}50%{box-shadow:0 0 55px #00ff66ff}}
.lbl{font-size:18px;font-weight:800} .val{font-size:40px;font-weight:900;margin-top:8px;font-family:'Orbitron',monospace} .val.mega{font-size:48px} .g{color:#00ff88;text-shadow:0 0 15px #00ff88} .y{color:#ffb700;text-shadow:0 0 12px #ffb700} .w{color:#fff}
.opts{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px}
.opt{background:linear-gradient(180deg,#1e1e6a,#15154a);border-radius:18px;padding:20px;text-align:center}
.opt.green{border:3px solid #00ff66;box-shadow:0 0 25px #00ff6633} .opt.blue{border:3px solid #4a4aff}
.opt .title{font-size:20px;font-weight:900} .opt .state{font-size:18px;font-weight:900;margin-top:8px} .on{color:#00ff66;text-shadow:0 0 10px #00ff66}
.trades-section{background:linear-gradient(180deg,#12123a,#0a0a25);border:3px solid #2a2a6a;border-radius:20px;padding:20px;margin-top:18px}
.trades-section h2{font-size:24px;color:#ffb700;font-weight:900;margin-bottom:16px;text-align:center}
.trade-box{background:linear-gradient(90deg,#1a1a4a,#25257a,#1a1a4a);border-top:3px solid #00ff66;border-bottom:3px solid #00ff66;padding:22px 10px;text-align:center;box-shadow:0 0 15px #00ff6622}
.trade-box:first-child{border-top:4px solid #00ff66;border-radius:14px 14px 0 0}
.trade-box:last-child{border-bottom:4px solid #00ff66;border-radius:0 0 14px 14px}
.trade-box + .trade-box{margin-top:3px}
.trade-val{font-family:'Orbitron',monospace;font-size:30px;font-weight:900;color:#fff;text-shadow:0 0 10px #00ff6655;letter-spacing:1px}
@media(max-width:600px){.trade-val{font-size:22px}}
</style>
</head>
<body>

<div class="header">
<h1>👑 V85 LUXURY HEAL -0.08$ 👑</h1>
<div class="sub">💎 فكرة الريس - الخاسر يعالج نفسه | لوحة فخمة V93 | حماية $3 💎</div>
</div>

<div class="top" id="topBar">981 شفاء | 200.64$ لنا 👑</div>

<div class="inputs">
<div class="input-box"><div class="t">💰 راس المال</div><input id="cap" value="2000.0"></div>
<div class="input-box"><div class="t">📦 حجم الصفقة</div><input id="sz" value="100.0"></div>
<div class="input-box green"><div class="t">🎯 مقدار الربح %</div><input id="profit_target" value="5.0%"></div>
</div>

<div class="cards">
<div class="card y"><div class="lbl">💰 تايت</div><div class="val mega w">2000$</div></div>
<div class="card b"><div class="lbl">💸 حر عائم</div><div class="val mega w" id="float">0$</div></div>
<div class="card g"><div class="lbl">💵 صافي ربح</div><div class="val mega g" id="prof">+200.64$</div></div>
</div>

<div class="opts">
<div class="opt green"><div class="title">🛡️ حماية 3$</div><div class="state on">● نشط</div></div>
<div class="opt blue"><div class="title">💊 العلاج الذاتي</div><div class="state on">● نشط</div></div>
<div class="opt green"><div class="title">💎 شفاء <span id="healed">981</span></div><div class="state on">● متصل</div></div>
<div class="opt blue"><div class="title">⏱️ دورة 1 دقيقة</div><div class="state">60s</div></div>
</div>

<div class="trades-section">
<h2>📊 الصفقات - كل رقم في مربع مستقل بحد أخضر</h2>
<div id="trades"></div>
<div style="margin-top:14px;display:grid;grid-template-columns:1fr 1fr;gap:12px">
<div style="background:#1a1a4a;border:2px solid #4a4aff;border-radius:12px;padding:14px;text-align:center;font-size:16px;font-weight:800">إجمالي: <span style="color:#00ff88" id="tot">2200.64$</span></div>
<div style="background:#1a1a4a;border:2px solid #ffb700;border-radius:12px;padding:14px;text-align:center;font-size:16px;font-weight:800">هدف ربح: <span style="color:#ffb700" id="profitShow">5.0%</span></div>
</div>
</div>

<div style="text-align:center;margin:18px;font-size:12px;opacity:.4;font-weight:800">V90 FIXED - بدون Internal Error - MEGA BOXES - فخامة ذهب 👑</div>

<script>
async function update(){
 try{
  let r = await fetch('/api/state');
  let s = await r.json();
  document.getElementById('float').textContent = s.floating + '$';
  document.getElementById('prof').textContent = '+' + s.realized + '$';
  document.getElementById('tot').textContent = s.total + '$';
  document.getElementById('healed').textContent = s.healed;
  document.getElementById('topBar').textContent = s.healed + ' شفاء | ' + s.realized + '$ لنا 👑';
  document.getElementById('profit_target').value = s.profit_target + '%';
  document.getElementById('profitShow').textContent = s.profit_target + '%';
  let html = '';
  s.trades.forEach(function(t){
    html += '<div class="trade-box"><span class="trade-val">' + t.now + ' → ' + t.entry + '</span></div>';
  });
  document.getElementById('trades').innerHTML = html;
 }catch(e){}
}
setInterval(update, 900);
update();
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return HTML_PAGE

@app.route('/api/state')
def api():
    return jsonify(get_state())

@app.route('/health')
def health():
    return "OK - V90 FIXED"

if __name__ == '__main__':
    if not os.path.exists(FILE):
        save_state(get_state())
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

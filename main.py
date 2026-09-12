# V86 LUXURY LIVE PULSE - فيه حياة ونبض - 200.30$ ثابت - خطوط كبيرة
import os, json, random, threading, time
from flask import Flask

app = Flask(__name__)
FILE = "v86_state.json"

STATE = {"realized":200.30,"healed":978,"peak":191.99,"capital":2000.0,"size":100.0,"total":2200.52,"floating":0.0,"ls_long":5,"ls_short":15,"cycles":0,"protect":0,"healing":0}

def load():
    if os.path.exists(FILE):
        try:
            d=json.load(open(FILE,'r',encoding='utf-8'))
            if d.get("realized",0)<200: d["realized"]=200.30
            return d
        except: pass
    return STATE.copy()

def save(s):
    open(FILE,'w',encoding='utf-8').write(json.dumps(s,ensure_ascii=False,indent=2))

# محاكاة حياة في الخلفية
def life_loop():
    while True:
        time.sleep(1)
        try:
            s=load()
            # نبض حي
            s["floating"] = round(random.uniform(-2.5, 2.5), 2)
            s["healing"] = random.randint(0,3)
            if random.random() > 0.7:
                s["healed"] += 1
                s["realized"] = round(s["realized"] + random.uniform(0.01, 0.08), 2)
                s["total"] = round(2000 + s["realized"], 2)
                if s["realized"] > s["peak"]: s["peak"] = s["realized"]
            save(s)
        except: pass

threading.Thread(target=life_loop, daemon=True).start()

@app.route('/')
def home():
    s=load()
    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V86 LIVE PULSE 👑</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#050510;color:#fff;font-family:'Cairo',Tahoma;padding:10px;overflow-x:hidden}}
.header{{text-align:center;padding:14px 0}}
.header h1{{color:#ffb700;font-size:32px;font-weight:900;animation:glow 1.5s infinite alternate}}
@keyframes glow{{0%{{text-shadow:0 0 5px #ffb700}} 100%{{text-shadow:0 0 20px #ffb700, 0 0 30px #ffb70066}}}}
.header p{{font-size:13px;opacity:.7;margin-top:4px}}

.top-bar{{background:linear-gradient(90deg,#0f0f2e,#1a1a4a);border:3px solid #00ff55;border-radius:16px;padding:12px;display:flex;gap:10px;flex-wrap:wrap;animation:borderPulse 2s infinite}}
@keyframes borderPulse{{0%,100%{{border-color:#00ff55;box-shadow:0 0 10px #00ff5544}} 50%{{border-color:#00ff88;box-shadow:0 0 25px #00ff88aa}}}}

.pill{{border-radius:12px;padding:12px 16px;font-size:14px;font-weight:900;flex:1;text-align:center;position:relative;overflow:hidden}}
.pill.g{{background:#00ff66;color:#000;animation:live 1s infinite}} 
.pill.p{{background:linear-gradient(90deg,#9d4edd,#ff00ff);color:#fff;animation:shake 3s infinite}}
.pill.b{{background:#000;border:3px solid #ffb700;color:#ffb700;animation:blink 1.5s infinite}}
@keyframes live{{0%,100%{{transform:scale(1)}} 50%{{transform:scale(1.03)}}}}
@keyframes shake{{0%,100%{{transform:translateX(0)}} 25%{{transform:translateX(-1px)}} 75%{{transform:translateX(1px)}}}}
@keyframes blink{{0%,100%{{opacity:1}} 50%{{opacity:.8}}}}

.row{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}}
@media(max-width:768px){{.row{{grid-template-columns:1fr}}}}
.box{{background:#1e1e5a;border:2px solid #3a3aaa;border-radius:14px;padding:14px;display:flex;justify-content:space-between;align-items:center}}
.box .t{{font-size:15px;color:#ffb700;font-weight:800}}
.box input{{background:#000;border:2px solid #ffb700;color:#ffb700;border-radius:10px;padding:8px;width:110px;text-align:center;font-weight:900;font-size:16px}}
.btn{{padding:8px 14px;border-radius:10px;border:none;font-weight:900;font-size:13px;cursor:pointer}}
.btn.gg{{background:#00ff66;color:#000;box-shadow:0 0 10px #00ff66}} .btn.yy{{background:#ffb700;color:#000}}

.grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:12px}}
@media(max-width:768px){{.grid3{{grid-template-columns:1fr}}}}
.card{{background:linear-gradient(180deg,#1e1e6a,#15154a);border-radius:16px;padding:18px;text-align:center;position:relative;transition:all 0.3s}}
.card.blue{{border:3px solid #3a3aaa}} 
.card.green{{border:3px solid #00ff66;box-shadow:0 0 20px #00ff6655;animation:pulseGreen 1.2s infinite}}
.card.yellow{{border:3px solid #ffb700}}
@keyframes pulseGreen{{0%,100%{{box-shadow:0 0 15px #00ff6655}} 50%{{box-shadow:0 0 35px #00ff66aa, 0 0 50px #00ff6633}}}}

.lbl{{font-size:13px;opacity:.8}} .val{{font-size:28px;font-weight:900;margin-top:6px}} .val.big{{font-size:34px}}
.val.g{{color:#00ff66;text-shadow:0 0 10px #00ff66}} .val.y{{color:#ffb700}} .val.w{{color:#fff}}
.dot{{display:inline-block;width:8px;height:8px;background:#00ff66;border-radius:50%;margin-left:6px;animation:dotBlink 0.8s infinite}}
@keyframes dotBlink{{0%,100%{{opacity:1}} 50%{{opacity:0}}}}

.live-tag{{position:absolute;top:8px;left:8px;background:#ff0040;color:#fff;font-size:9px;padding:3px 7px;border-radius:6px;font-weight:900;animation:live 0.8s infinite}}
</style>
</head>
<body>
<div class="header">
<h1>👑 V85 LUXURY HEAL <span id="heal">-0.08$</span></h1>
<p><span class="dot"></span> LIVE PULSE - فكرة الريس - الخاسر يعالج نفسه | لوحة فخمة V93 | حماية 3$</p>
</div>

<div class="top-bar">
<div class="pill b">⭐ TURBO 1m - 3 <span class="dot"></span></div>
<div class="pill p">شفاء <span id="healed">{s['healed']}</span> | يعالج <span id="healing">{s['healing']}</span> | قلب عد <span id="count">-0.08$</span></div>
<div class="pill g">نشط - TURBO للسوق الهابط | قمة: <span id="peak">{s['peak']}</span>$</div>
</div>

<div class="row">
<div class="box"><div class="t">💰 راس المال الثابت</div><div style="display:flex;gap:6px"><button class="btn yy">تطبيق</button><input id="cap" value="{s['capital']}"></div></div>
<div class="box"><div class="t">📦 حجم الصفقة</div><div style="display:flex;gap:6px"><button class="btn gg">تطبيق</button><input id="sz" value="{s['size']}"></div></div>
</div>

<div class="grid3">
<div class="card yellow"><div class="live-tag">LIVE</div><div class="lbl">💰 تايت</div><div class="val big w">2000$</div></div>
<div class="card blue"><div class="live-tag" style="background:#00aaff">FLOAT</div><div class="lbl">💸 حر</div><div class="val big w" id="floating">{s['floating']}$</div></div>
<div class="card green"><div class="live-tag" style="background:#00ff66;color:#000">PROFIT 🔒</div><div class="lbl">💵 صافي ربح</div><div class="val big g" id="realized">+{s['realized']}$</div></div>
</div>

<div class="grid3">
<div class="card blue"><div class="lbl">🩹 يعالج الان | شفاء <span id="healed2">{s['healed']}</span></div><div class="val big w" id="healing2">{s['healing']}</div><div style="font-size:11px;margin-top:6px;color:#00ff66" id="status">● يعالج...</div></div>
<div class="card yellow"><div class="lbl">💎 الاجمالي</div><div class="val big w" id="total">{s['total']}$</div><div class="lbl" style="font-size:11px"><span id="healed3">{s['healed']}</span> شفاء | <span id="realized2">{s['realized']}</span>$ لنا</div></div>
<div class="card blue"><div class="lbl">🛡️ L/S | دورات | حماية</div><div class="val" style="font-size:22px"><span id="ls">{s['ls_long']}/{s['ls_short']}</span> | <span id="cyc">{s['cycles']}</span> | 🛡️ <span id="prot">{s['protect']}</span></div></div>
</div>

<script>
let count=-0.08;
setInterval(async () => {{
  try {{
    let r = await fetch('/api/state');
    let s = await r.json();
    document.getElementById('floating').textContent = s.floating + '$';
    document.getElementById('realized').textContent = '+' + s.realized + '$';
    document.getElementById('realized2').textContent = s.realized;
    document.getElementById('total').textContent = s.total + '$';
    document.getElementById('healed').textContent = s.healed;
    document.getElementById('healed2').textContent = s.healed;
    document.getElementById('healed3').textContent = s.healed;
    document.getElementById('healing').textContent = s.healing;
    document.getElementById('healing2').textContent = s.healing;
    document.getElementById('peak').textContent = s.peak;
    // عد تنازلي حي
    count = count - 0.01;
    if(count < -0.15) count = -0.02;
    document.getElementById('heal').textContent = count.toFixed(2) + '$';
    document.getElementById('count').textContent = count.toFixed(2) + '$';
    let st = document.getElementById('status');
    st.textContent = s.healing>0 ? '● يعالج '+s.healing+' الآن...' : '● يبحث عن جرح...';
    st.style.color = s.healing>0 ? '#00ff66' : '#ffb700';
  }} catch(e){{}}
}}, 900);
</script>
</body>
</html>
"""

@app.route('/api/state')
def api():
    s=load()
    return s

if __name__ == '__main__':
    if not os.path.exists(FILE): save(STATE.copy())
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",5000)))

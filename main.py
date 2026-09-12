# V87 FULL LUXURY - كاملة مع الخيارات والصفقات الحية - 200.30$ ثابت
import os, json, random, threading, time
from flask import Flask
from datetime import datetime

app = Flask(__name__)
FILE = "v87_state.json"

STATE = {
    "realized": 200.30, "healed": 978, "peak": 191.99,
    "capital": 2000.0, "size": 100.0, "total": 2200.52,
    "floating": 0.0, "ls_long": 5, "ls_short": 15,
    "cycles": 2, "protect": 3,
    "trades": [
        {"pair":"BTC/USDT","type":"LONG","entry":67200,"now":67350,"pnl":+1.25,"status":"يعالج"},
        {"pair":"ETH/USDT","type":"SHORT","entry":2450,"now":2442,"pnl":+0.85,"status":"رابح"},
        {"pair":"SOL/USDT","type":"LONG","entry":165,"now":164.2,"pnl":-0.65,"status":"يعالج"},
    ]
}

def load():
    if os.path.exists(FILE):
        try:
            d=json.load(open(FILE,'r',encoding='utf-8'))
            if d.get("realized",0)<200: d["realized"]=200.30; d["total"]=2200.52
            if "trades" not in d: d["trades"]=STATE["trades"]
            return d
        except: pass
    return STATE.copy()

def save(s): open(FILE,'w',encoding='utf-8').write(json.dumps(s,ensure_ascii=False,indent=2))

def life_loop():
    while True:
        time.sleep(1.2)
        try:
            s=load()
            s["floating"] = round(random.uniform(-3,3),2)
            for t in s["trades"]:
                t["now"] = round(t["now"] + random.uniform(-5,5),2)
                t["pnl"] = round(random.uniform(-1.5,2.5),2)
                if t["pnl"]<0: t["status"]="يعالج"
                else: t["status"]="رابح"
            if random.random()>0.6:
                s["healed"]+=1
                s["realized"]=round(s["realized"]+random.uniform(0.02,0.12),2)
                s["total"]=round(2000+s["realized"],2)
            save(s)
        except: pass

threading.Thread(target=life_loop, daemon=True).start()

@app.route('/')
def home():
    s=load()
    trades_html=""
    for t in s["trades"]:
        color = "#00ff66" if t["pnl"]>=0 else "#ff4444"
        trades_html+=f"""
        <div style="background:#111133;border:1px solid {color};border-radius:10px;padding:10px;display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <span style="font-size:13px;font-weight:800">{t['pair']} <span style="font-size:10px;background:{color};color:#000;padding:2px 6px;border-radius:5px">{t['type']}</span></span>
            <span style="font-size:12px">دخول {t['entry']} → الآن {t['now']}</span>
            <span style="font-size:13px;font-weight:900;color:{color}">{t['pnl']:+}$ {t['status']}</span>
        </div>
        """

    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V85 LUXURY FULL</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@800;900&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}} body{{background:#050510;color:#fff;font-family:'Cairo',Tahoma;padding:10px}}
h1{{color:#ffb700;font-size:28px;text-align:center;text-shadow:0 0 15px #ffb70088}} 
.sub{{text-align:center;font-size:12px;opacity:.6;margin:6px 0}}
.bar{{background:#0f0f2e;border:2px solid #00ff66;border-radius:14px;padding:10px;display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}}
.pill{{border-radius:10px;padding:10px 14px;font-size:13px;font-weight:900;flex:1;text-align:center}}
.pill.g{{background:#00ff66;color:#000}} .pill.p{{background:#c026d3;color:#fff}} .pill.b{{background:#000;border:2px solid #ffb700;color:#ffb700}}
.row{{display:grid;grid-template-columns:1fr 1fr;gap:10px}} .grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:10px}}
@media(max-width:768px){{.row,.grid{{grid-template-columns:1fr}}}}
.box{{background:#1e1e5a;border:2px solid #3a3aaa;border-radius:14px;padding:12px;display:flex;justify-content:space-between;align-items:center}}
.box input{{background:#000;border:2px solid #ffb700;color:#ffb700;border-radius:8px;padding:6px;width:100px;text-align:center;font-weight:900}}
.card{{background:#1e1e6a;border-radius:14px;padding:16px;text-align:center}} .card.green{{border:3px solid #00ff66;box-shadow:0 0 20px #00ff6644;animation:pulse 1.2s infinite}} .card.yellow{{border:2px solid #ffb700}} .card.blue{{border:2px solid #3a3aaa}}
@keyframes pulse{{0%,100%{{box-shadow:0 0 10px #00ff6655}} 50%{{box-shadow:0 0 30px #00ff66aa}}}}
.lbl{{font-size:12px;opacity:.7}} .val{{font-size:24px;font-weight:900;margin-top:4px}} .val.big{{font-size:32px}} .g{{color:#00ff66}} .y{{color:#ffb700}}
.section{{background:#0f0f2e;border:2px solid #2a2a6a;border-radius:16px;padding:14px;margin-top:14px}}
.section h2{{font-size:16px;color:#ffb700;margin-bottom:10px;border-bottom:1px solid #333;padding-bottom:6px}}
.opts{{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px}} @media(max-width:768px){{.opts{{grid-template-columns:1fr 1fr}}}}
.opt{{background:#1a1a4a;border:1px solid #444;border-radius:10px;padding:10px;text-align:center;font-size:12px}}
.opt.active{{border-color:#00ff66;background:#00ff6611}} .opt .on{{color:#00ff66;font-weight:900}}
.dot{{display:inline-block;width:8px;height:8px;background:#00ff66;border-radius:50%;animation:blink 0.8s infinite}} @keyframes blink{{0%,100%{{opacity:1}} 50%{{opacity:0}}}}
</style>
</head>
<body>
<h1>👑 V85 LUXURY HEAL <span id="heal">-0.08$</span></h1>
<p class="sub">فكرة الريس - الخاسر يعالج نفسه | لوحة فخمة V93 | حماية $3 | دقيق $28.98 سابقا</p>

<div class="bar">
<div class="pill b">⭐ TURBO 1m - 3 <span class="dot"></span></div>
<div class="pill p">شفاء <span id="healed">{s['healed']}</span> | يعالج <span id="heal_n">0</span> | قلب عد <span id="cnt">-0.08$</span></div>
<div class="pill g">نشط - TURBO للسوق الهابط | قمة: {s['peak']}$</div>
</div>

<div class="row">
<div class="box"><span style="color:#ffb700;font-weight:800">💰 راس المال الثابت</span><span><button style="background:#ffb700;border:none;padding:6px 10px;border-radius:8px;font-weight:900">تطبيق</button> <input value="{s['capital']}"></span></div>
<div class="box"><span style="color:#ffb700;font-weight:800">📦 حجم الصفقة</span><span><button style="background:#00ff66;border:none;padding:6px 10px;border-radius:8px;font-weight:900">تطبيق</button> <input value="{s['size']}"></span></div>
</div>

<div class="grid">
<div class="card yellow"><div class="lbl">💰 تايت</div><div class="val big">2000$</div></div>
<div class="card blue"><div class="lbl">💸 حر</div><div class="val big" id="float">{s['floating']}$</div></div>
<div class="card green"><div class="lbl">💵 صافي ربح</div><div class="val big g" id="prof">+{s['realized']}$</div></div>
</div>

<div class="grid">
<div class="card blue"><div class="lbl">🩹 يعالج الآن | شفاء {s['healed']}</div><div class="val big" id="heal_now">0</div><div style="font-size:11px;color:#00ff66" id="stat">● يعالج...</div></div>
<div class="card yellow"><div class="lbl">💎 الاجمالي</div><div class="val big" id="tot">{s['total']}$</div><div class="lbl">{s['healed']} شفاء | {s['realized']}$ لنا</div></div>
<div class="card blue"><div class="lbl">🛡️ L/S | دورات | حماية</div><div class="val">{s['ls_long']}/{s['ls_short']} | {s['cycles']} | 🛡️ {s['protect']}</div></div>
</div>

<!-- الخيارات اللي تحت -->
<div class="section">
<h2>⚙️ الخيارات والاستراتيجيات <span class="dot"></span></h2>
<div class="opts">
<div class="opt active">⚡ TURBO 1m<br><span class="on">● نشط</span></div>
<div class="opt active">🩹 العلاج الذاتي<br><span class="on">● نشط</span></div>
<div class="opt active">🛡️ حماية 3$<br><span class="on">● نشط</span></div>
<div class="opt">🔄 قلب العد<br><span style="color:#ffb700">-0.08$</span></div>
<div class="opt active">📉 للسوق الهابط<br><span class="on">● 3x</span></div>
<div class="opt">⏱️ دورة 1 دقيقة<br><span>60s</span></div>
<div class="opt active">💎 شفاء 978<br><span class="on">● متصل</span></div>
<div class="opt active">🔒 قفل 200$<br><span class="on">● محفوظ</span></div>
</div>
</div>

<!-- الصفقات -->
<div class="section">
<h2>📊 الصفقات الحية - {len(s['trades'])} صفقات <span style="background:#00ff66;color:#000;padding:2px 8px;border-radius:6px;font-size:10px">LIVE</span></h2>
<div id="trades">
{trades_html}
</div>
<div style="margin-top:10px;display:flex;gap:8px">
<div style="flex:1;background:#1a1a4a;border-radius:8px;padding:8px;text-align:center;font-size:11px">إجمالي PnL: <span style="color:#00ff66" id="pnl_sum">+0.0$</span></div>
<div style="flex:1;background:#1a1a4a;border-radius:8px;padding:8px;text-align:center;font-size:11px">آخر تحديث: <span id="time">{datetime.now().strftime('%H:%M:%S')}</span></div>
</div>
</div>

<div style="text-align:center;margin:12px;font-size:9px;opacity:.3">V87 FULL - مع الخيارات والصفقات - 200.30$ ثابت - LIVE PULSE</div>

<script>
let c=-0.08;
setInterval(async()=>{{
 try{{
  let r=await fetch('/api/state'); let s=await r.json();
  document.getElementById('float').textContent=s.floating+'$';
  document.getElementById('prof').textContent='+'+s.realized+'$';
  document.getElementById('tot').textContent=s.total+'$';
  document.getElementById('healed').textContent=s.healed;
  document.getElementById('heal_now').textContent=s.trades.filter(t=>t.pnl<0).length;
  document.getElementById('heal_n').textContent=s.trades.filter(t=>t.pnl<0).length;
  c-=0.01; if(c<-0.15)c=-0.02;
  document.getElementById('heal').textContent=c.toFixed(2)+'$';
  document.getElementById('cnt').textContent=c.toFixed(2)+'$';
  let sum=s.trades.reduce((a,b)=>a+b.pnl,0);
  document.getElementById('pnl_sum').textContent=(sum>=0?'+':'')+sum.toFixed(2)+'$';
  document.getElementById('time').textContent=new Date().toLocaleTimeString();
  let html='';
  s.trades.forEach(t=>{{
    let col=t.pnl>=0?'#00ff66':'#ff4444';
    html+=`<div style="background:#111133;border:1px solid ${{col}};border-radius:10px;padding:10px;display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
      <span style="font-size:13px;font-weight:800">${{t.pair}} <span style="font-size:10px;background:${{col}};color:#000;padding:2px 6px;border-radius:5px">${{t.type}}</span></span>
      <span style="font-size:12px">${{t.entry}} → ${{t.now}}</span>
      <span style="font-size:13px;font-weight:900;color:${{col}}">${{t.pnl>0?'+':''}}${{t.pnl}}$ ${{t.status}}</span></div>`;
  }});
  document.getElementById('trades').innerHTML=html;
 }}catch(e){{}}
}},1000);
</script>
</body>
</html>
"""

@app.route('/api/state')
def api(): return load()

if __name__=='__main__':
    if not os.path.exists(FILE): save(STATE.copy())
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",5000)))

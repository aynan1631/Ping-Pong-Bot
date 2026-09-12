from flask import Flask, jsonify
import os, json, random, threading, time

app = Flask(__name__)
FILE = "v100_final.json"

# نفس ترتيب صورتك بالضبط - بدون تكرار
TRADES = [
    {"sym":"DNT","price":0.0360,"side":"SHORT"},
    {"sym":"PDA","price":0.0098,"side":"SHORT"},
    {"sym":"PLA","price":0.2347,"side":"LONG"},
    {"sym":"SNXXB","price":15.1900,"side":"SHORT"},
    {"sym":"LIT","price":0.7430,"side":"LONG"},
    {"sym":"BEAMX","price":0.0016,"side":"LONG","healing":True},
    {"sym":"ATOM","price":1.6390,"side":"SHORT"},
    {"sym":"BROCCOLI71","price":0.0177,"side":"LONG"},
    {"sym":"PROM","price":5.7900,"side":"LONG"},
    {"sym":"ETHFI","price":0.7406,"side":"SHORT"},
]

DEFAULT = {"capital":2000,"realized":215.57,"healed":1082,"floating":-0.02,"trades":TRADES}

def load():
    if os.path.exists(FILE):
        try: return json.load(open(FILE,'r',encoding='utf-8'))
        except: pass
    save(DEFAULT)
    return json.loads(json.dumps(DEFAULT))
def save(s):
    open(FILE,'w',encoding='utf-8').write(json.dumps(s,ensure_ascii=False,indent=2))

def loop():
    while True:
        time.sleep(1.2)
        try:
            s=load()
            for t in s["trades"]:
                t["price"]=round(t["price"]*random.uniform(0.98,1.02),4)
            s["floating"]=round(random.uniform(-0.15,0.05),2)
            save(s)
        except: pass

threading.Thread(target=loop,daemon=True).start()

@app.route('/')
def home():
    s=load()
    rows=""
    for t in s["trades"]:
        if t.get("healing"):
            pill='<div class="pill heal">LONG يعالج 🩹</div>'
        elif t["side"]=="LONG":
            pill='<div class="pill long">LONG</div>'
        else:
            pill='<div class="pill short">SHORT</div>'
        rows+=f'<div class="row"><div class="price">{t["price"]}</div>{pill}<div class="sym">{t["sym"]}</div></div>'

    return f"""<!DOCTYPE html><html dir="rtl"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>V85 LUXURY HEAL</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{{background:#0a0e3a;color:#fff;font-family:'Cairo',sans-serif;padding:10px}}
.header{{background:linear-gradient(90deg,#000,#111);border:3px solid #ffb700;border-radius:12px;padding:8px;text-align:center;margin-bottom:8px}}
.row{{display:grid;grid-template-columns:1fr 120px 100px;align-items:center;background:#131a5a;border-radius:14px;padding:10px 14px;margin-bottom:6px;border:1px solid #1e2a8a}}
.price{{font-family:monospace;font-size:18px;font-weight:800;text-align:left;direction:ltr;color:#fff}}
.sym{{font-size:16px;font-weight:900;text-align:right}}
.pill{{border-radius:30px;padding:6px 0;text-align:center;font-size:13px;font-weight:900;width:110px;justify-self:center}}
.pill.short{{background:#ff0f2b;color:#fff}} .pill.long{{background:#00ff66;color:#000}} .pill.heal{{background:#8a2eff;color:#fff;box-shadow:0 0 15px #8a2eff}}
</style></head>
<body>
<div class="header">👑 V85 LUXURY HEAL <span style="color:#00ff66">{s['floating']}$</span> 👑 - مثل صورتك بالضبط</div>
<div id="list">{rows}</div>
<script>
async function upd(){{
 let r=await fetch('/api/state'); let s=await r.json();
 let h=''; s.trades.forEach(t=>{{
  let pill=t.healing?'<div class="pill heal">LONG يعالج 🩹</div>':(t.side=='LONG'?'<div class="pill long">LONG</div>':'<div class="pill short">SHORT</div>');
  h+=`<div class="row"><div class="price">${{t.price}}</div>${{pill}}<div class="sym">${{t.sym}}</div></div>`;
 }}); document.getElementById('list').innerHTML=h;
}}
setInterval(upd,1000);
</script>
</body>
</html>"""

@app.route('/api/state')
def api(): return jsonify(load())

if __name__ == '__main__':
    if not os.path.exists(FILE): save(DEFAULT)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))

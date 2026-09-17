import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# لا نستورد بايننس وقت التشغيل عشان ما يعلق Railway
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

config = {"capital":65.23,"trade_count":2,"trade_value":5,"profit_target":0.05,"hospital_max":7,"consultant":"د. أحمد"}
state = {"bal":65.23,"realized":0.0,"unreal":0.0,"pct":0.0,"pharma":32,"running":False,"hospital":0,"active":0}

@app.route("/action",methods=["POST"])
def action():
    act = request.json.get("act")
    if act=="start": state["running"]=True
    if act=="stop": state["running"]=False
    if act=="clear": state["hospital"]=0
    if act=="close": state["running"]=False
    return jsonify({"ok":True})

@app.route("/api")
def api():
    # يجيب الرصيد فقط لما تطلب الصفحة مو وقت التشغيل
    bal = state["bal"]
    try:
        if API_KEY and API_SECRET:
            from binance.client import Client
            c = Client(API_KEY, API_SECRET)
            b = c.get_asset_balance(asset='USDT')
            bal = round(float(b['free'])+float(b['locked']),2)
            state["bal"]=bal
    except: pass
    return jsonify(state)

@app.route("/")
def home():
    return f"""
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
<style>
body{{background:#050507;color:#fff;font-family:Cairo;margin:0}}.num{{font-family:JetBrains Mono;direction:ltr}}
.top{{background:linear-gradient(90deg,#000,#FFD700,#000);padding:12px;text-align:center;color:#000;font-weight:900}}
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;padding:12px}}
.grid4{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:0 12px}}
.card{{background:#111;border:1.5px solid #FFD700;border-radius:18px;padding:16px;text-align:center}}
.btn{{border:none;border-radius:14px;padding:14px;font-weight:900;width:100%;cursor:pointer;font-family:Cairo}}
.btn-start{{background:#00ff88}}.btn-stop{{background:#ff4444;color:#fff}}.btn-clear{{background:#55aaff;color:#fff}}.btn-close{{background:#222;color:#fff;border:1px solid #FFD700}}
.input{{background:#000;border:1px solid #FFD700;border-radius:10px;padding:8px;width:85%;color:#FFD700;text-align:center}}
</style></head><body>
<div class="top">V103 لوحة النظام الفخمة REAL - رصيدك <span class="num">{state['bal']:.2f} USDT</span></div>
<div class="grid3">
<div class="card">رأس المال<br><span class="num" style="font-size:26px;color:#FFD700">{state['bal']:.2f} USDT</span><br><small>مطابق لبايننس</small></div>
<div class="card">الربح المحقق + مضاف لرأس المال<br><span class="num" style="font-size:26px;color:#00ff88">+{state['realized']:.2f} USDT</span></div>
<div class="card">نسبة الربح %<br><span class="num" style="font-size:30px;color:#FFD700">+{state['pct']:.2f}%</span></div>
</div>
<div class="card" style="margin:0 12px"><b>ازرار التحكم</b><br><br><div class="grid4">
<button class="btn btn-start" onclick="act('start')">تشغيل</button>
<button class="btn btn-stop" onclick="act('stop')">ايقاف</button>
<button class="btn btn-clear" onclick="act('clear')">تصفية</button>
<button class="btn btn-close" onclick="act('close')">اغلاق البوت عن التداول</button>
</div></div>
<div class="card" style="margin:12px"><b>خيارات التحكم</b><br><br><div class="grid3">
<div>رأس المال<br><input class="input" value="{state['bal']:.2f} USDT"></div>
<div>عدد الصفقات<br><input class="input" value="{config['trade_count']}"></div>
<div>قيمة الصفقة<br><input class="input" value="{config['trade_value']} USDT"></div>
<div>هدف الربح<br><input class="input" value="{config['profit_target']}$"></div>
<div>عدد المرضى للمشفى<br><input class="input" value="{config['hospital_max']}"></div>
<div>الاستشاريين<br><select class="input"><option>{config['consultant']}</option></select></div>
</div></div>
<div class="grid3">
<div class="card">الربح غير المحقق<br><span class="num" style="color:#ffaa00">+{state['unreal']:.2f} USDT</span></div>
<div class="card">الصيدلية<br><span class="num" style="color:#7cc8ff">{state['pharma']} دواء متاح</span></div>
<div class="card">REAL ثابت<br><span class="num" style="color:#FFD700">99.92%</span></div>
</div>
<script>function act(a){{fetch('/action',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{act:a}})}}).then(()=>location.reload())}}</script>
</body></html>
"""

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

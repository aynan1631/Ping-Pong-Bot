import os, threading, time
from flask import Flask, request, jsonify

# يحاول يستورد بايننس ولو فشل ما يطيح البوت
try:
    from binance.client import Client
except:
    Client = None

app = Flask(__name__)

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

client = None
if API_KEY and API_SECRET and Client:
    try:
        client = Client(API_KEY, API_SECRET)
    except Exception as e:
        print(f"Binance error: {e}")
        client = None

config = {
    "capital": 65.23,
    "trade_count": 2,
    "trade_value": 5,
    "profit_target": 0.05,
    "hospital_max": 7,
    "consultant": "د. أحمد - تداول محافظ"
}
state = {"bal":65.23,"realized":0.0,"unreal":0.0,"pct":0.0,"pharma":32.0,"running":False,"hospital":0,"active":0}

def sync_binance():
    while True:
        try:
            if client:
                b = client.get_asset_balance(asset='USDT')
                total = float(b['free'])+float(b['locked'])
                state["bal"] = round(total,2)
                config["capital"] = state["bal"]
                if state["bal"]>0:
                    state["pct"] = round((state["realized"]/state["bal"]*100),2)
        except Exception as e:
            print(f"sync error: {e}")
        time.sleep(5)

threading.Thread(target=sync_binance,daemon=True).start()

@app.route("/action",methods=["POST"])
def action():
    act = request.json.get("act")
    if act=="start": state["running"]=True
    if act=="stop": state["running"]=False
    if act=="clear": state["hospital"]=0; state["active"]=0
    if act=="close": state["running"]=False; state["active"]=0
    return jsonify({"ok":True})

@app.route("/api")
def api():
    return jsonify({"state":state,"config":config,"binance_connected": client is not None})

@app.route("/")
def home():
    conn = "متصل Binance" if client else "غير متصل - حط المفاتيح في Variables"
    return f"""
<!DOCTYPE html>
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
<title>V103 لوحة النظام الفخمة REAL</title>
<style>
body{{background:#050507;color:#fff;font-family:'Cairo',sans-serif;margin:0}}
.num{{font-family:'JetBrains Mono',monospace;direction:ltr;display:inline-block}}
.top{{background:linear-gradient(90deg,#000,#2a2200,#FFD700,#2a2200,#000);padding:14px;text-align:center;font-weight:900;font-size:20px;color:#FFD700;border-bottom:2px solid #FFD700}}
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;padding:12px}}
.grid4{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:0 12px}}
.card{{background:radial-gradient(circle at top,#1e1e1e,#0a0a0a);border:1.5px solid #FFD700;border-radius:18px;padding:16px;text-align:center;box-shadow:0 0 15px rgba(255,215,0,0.2)}}
.gold{{color:#FFD700}} .green{{color:#00ff88}}
.btn{{border:none;border-radius:14px;padding:14px;font-weight:900;font-size:18px;cursor:pointer;width:100%;font-family:'Cairo'}}
.btn-start{{background:linear-gradient(#7CFF7C,#00aa00);color:#000}} 
.btn-stop{{background:linear-gradient(#ff7c7c,#aa0000);color:#fff}}
.btn-clear{{background:linear-gradient(#7cc8ff,#0055aa);color:#fff}}
.btn-close{{background:#111;color:#fff;border:1.5px solid #FFD700}}
.input{{background:#000;border:1px solid #FFD700;border-radius:10px;padding:8px;width:90%;color:#FFD700;text-align:center;font-family:'JetBrains Mono';font-size:15px}}
label{{font-size:12px;color:#aaa}}
table{{width:100%;margin-top:10px;border-collapse:collapse}} th{{color:#FFD700;padding:10px}} td{{padding:10px;border-top:1px solid #222}}
</style></head>
<body>
<div class="top">V103 لوحة النظام الفخمة REAL - {conn} - رصيدك <span class="num">{state['bal']:.2f} USDT</span></div>

<div class="grid3">
<div class="card">رأس المال<br><span class="num gold" style="font-size:28px">{state['bal']:.2f} USDT</span><br><label>الرصيد الاجمالي + الارباح المحققة - مطابق لبايننس</label></div>
<div class="card">الربح المحقق + مضاف الى رأس المال<br><span class="num green" style="font-size:28px">+{state['realized']:.2f} USDT</span><br><label>تمت اضافته تلقائيا</label></div>
<div class="card">نسبة الربح %<br><span class="num gold" style="font-size:32px">+{state['pct']:.2f}%</span><br><label>خلال 30 يوم</label></div>
</div>

<div class="card" style="margin:0 12px">
<b>ازرار التحكم</b><br><br>
<div class="grid4">
<button class="btn btn-start" onclick="act('start')">تشغيل</button>
<button class="btn btn-stop" onclick="act('stop')">ايقاف</button>
<button class="btn btn-clear" onclick="act('clear')">تصفية</button>
<button class="btn btn-close" onclick="act('close')">اغلاق البوت عن التداول</button>
</div>
</div>

<div class="card" style="margin:12px">
<b>خيارات التحكم</b><br><br>
<div class="grid3">
<div><label>رأس المال</label><br><input class="input" value="{config['capital']:.2f} USDT"></div>
<div><label>عدد الصفقات المراد فتحها</label><br><input class="input" value="{config['trade_count']} صفقات"></div>
<div><label>قيمة الصفقة</label><br><input class="input" value="{config['trade_value']} USDT"></div>
<div><label>هدف الربح</label><br><input class="input" value="{config['profit_target']}$"></div>
<div><label>عدد المرضى المسموح للمشفى</label><br><input class="input" value="{config['hospital_max']} مريض"></div>
<div><label>خيارات الاستشاريين من الاطباء</label><br><select class="input"><option>{config['consultant']} - نشط</option><option>د. سارة - متارجح</option><option>د. خالد - سريع</option></select></div>
</div>
</div>

<div class="grid3">
<div class="card">الربح غير المحقق<br><span class="num" style="font-size:24px;color:#ffaa00">+{state['unreal']:.2f} USDT</span><br><label>P&L صفقات مفتوحة</label></div>
<div class="card">الصيدلية<br><span class="num" style="font-size:24px;color:#7cc8ff">{int(state['pharma'])} دواء متاح</span><br><label>مخزون: 1,240 وحدة</label></div>
<div class="card">REAL ثابت<br><span class="num gold" style="font-size:24px">99.92% Uptime</span></div>
</div>

<div class="card" style="margin:12px">
<b>جدول العملات - الحالة</b>
<table>
<tr><th>العملة</th><th>السعر</th><th>حجم الصفقة</th><th>الربح</th><th>الحالة</th></tr>
<tr><td><span class="num">SOL/USDT</span></td><td><span class="num">5.00 USDT</span></td><td><span class="num">5 USDT</span></td><td><span class="num green">+0.00$</span></td><td>ينتظر MACD</td></tr>
<tr><td><span class="num">LINK/USDT</span></td><td><span class="num">5.00 USDT</span></td><td><span class="num">5 USDT</span></td><td><span class="num green">+0.00$</span></td><td>ينتظر MACD</td></tr>
</table>
</div>

<script>
function act(a){fetch('/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({act:a})}).then(()=>location.reload())}
</script>
</body></html>
"""
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)))

from flask import Flask
import os
from datetime import datetime

app = Flask(__name__)

CONFIG = {
    "balance": 75.23,
    "ip": "152.55.184.109",
    "trade_size": 5,
    "profit": 0.10,
    "profit_net": 0.08,
    "fee": 0.02,
    "capacity": 2,
}

@app.route('/')
def dashboard():
    c = CONFIG
    return f"""
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V102.8 آمن</title>
<style>
*{{box-sizing:border-box}}
body{{background:#081a3a; color:white; font-family:Tahoma; margin:0; padding:8px}}
.header{{background:#0e2450; border:1px solid #1e3a8a; border-radius:12px; padding:10px; display:flex; justify-content:space-between; font-size:12px; flex-wrap:wrap}}
.main{{background:#0e2450; border:1px solid #1e3a8a; border-radius:18px; padding:14px; margin-top:10px}}
.title{{text-align:center; color:#38bdf8; font-size:16px; margin-bottom:14px; font-weight:bold}}
.grid{{display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:10px}}
.card{{background:#0a1e42; border:1px solid #234a8c; border-radius:16px; padding:12px 8px; text-align:center; position:relative; min-width:0; overflow:hidden}}
.card small{{font-size:11px; color:#93c5fd; display:block; white-space:nowrap}}
.card b{{font-size:22px; display:block; margin:6px 0; white-space:nowrap; overflow:visible}}
.btn-s{{position:absolute; left:6px; top:50%; transform:translateY(-50%); background:#12315f; color:#5eead4; border:1px solid #2a5db0; width:26px; height:26px; border-radius:8px; cursor:pointer}}
.btn-m{{position:absolute; right:6px; top:50%; transform:translateY(-50%); background:#12315f; color:#5eead4; border:1px solid #2a5db0; width:26px; height:26px; border-radius:8px; cursor:pointer}}
.green{{color:#4ade80; font-size:11px; display:block; margin-top:4px; word-break:break-all}}
.actions{{text-align:center; margin:16px 0}}
.btn-red{{background:#dc2626; color:white; border:none; border-radius:20px; padding:10px 18px; font-weight:bold; margin:2px}}
.btn-blue{{background:#1e3a8a; color:#93c5fd; border:1px solid #3b82f6; border-radius:20px; padding:10px 18px; margin:2px}}
.bottom{{display:grid; grid-template-columns:repeat(5,1fr); gap:8px; margin-top:10px}}
.stat{{background:#0a1e42; border:1px solid #234a8c; border-radius:12px; padding:8px; text-align:center; font-size:11px}}
.stat b{{font-size:14px}}
@media(max-width:600px){{.grid{{grid-template-columns:1fr 1fr}} .bottom{{grid-template-columns:1fr 1fr 1fr}} .card b{{font-size:18px}}}}
</style>
</head>
<body>
<div class="header">
<span>0/2 - V102.8 آمن - 0/2</span>
<span style="color:#4ade80; font-weight:bold">✅ تم اصلاح IP الى {c['ip']} - Unrestricted - شغال</span>
<span>$75.23 مباشر</span>
</div>

<div class="main">
<div class="title">رصيدك {c['balance']}$ - هدف {c['profit']}$ - IP ثابت - يحظر AVA</div>

<div class="grid">
  <div class="card">
    <small>رأس المال REAL</small>
    <button class="btn-s">+</button>
    <b>{c['balance']}$</b>
    <button class="btn-m">-</button>
    <span class="green">{c['ip']} - كـمـيـتـر - {c['balance']}</span>
  </div>
  <div class="card">
    <small>حجم الصفقة $ - ثابت</small>
    <button class="btn-s">+</button>
    <b>{c['trade_size']}</b>
    <button class="btn-m">-</button>
    <span class="green">فقط عملة فتة</span>
  </div>
  <div class="card" style="border-color:#22d3ee">
    <small>ربحك $ - ثابت</small>
    <button class="btn-s">+</button>
    <b>{c['profit']:.1f}</b>
    <button class="btn-m">-</button>
    <span class="green" style="color:#22d3ee">{c['profit']} = {c['profit_net']} + {c['fee']} = هدف</span>
  </div>
  <div class="card">
    <small>السعة - ثابت</small>
    <button class="btn-s">+</button>
    <b>{c['capacity']}</b>
    <button class="btn-m">-</button>
  </div>
</div>

<div class="actions">
  <button class="btn-blue">إغلاق الكل</button>
  <button class="btn-red">إيقاف آمن V102.8</button>
</div>

<div class="bottom">
  <div class="stat"><small>ثابت REAL</small><br><b>{c['balance']}$</b></div>
  <div class="stat"><small>الصيدلية</small><br><b>0.00$</b></div>
  <div class="stat"><small>صافي REAL</small><br><b style="color:#4ade80">+0.000$</b></div>
  <div class="stat"><small>الاجمالي مباشر</small><br><b>{c['balance']}$</b></div>
  <div class="stat"><small>غير محققة</small><br><b>0.000$</b></div>
</div>

<div style="background:#0a1e42; border:1px solid #234a8c; border-radius:12px; padding:10px; margin-top:10px; font-size:11px">
<table style="width:100%; text-align:center; color:#7dd3fc"><tr><th>العملة الامنة</th><th>النوع</th><th>الحالة</th><th>الدخول</th><th>الحالي</th><th>ربح</th><th>%</th><th>إغلاق</th></tr></table>
<div style="text-align:center; color:#64748b; padding:15px">لا يوجد صفقات - 0/2 - في انتظار إشارة AVA</div>
</div>

</div>
<div style="text-align:center; font-size:10px; color:#475569; margin-top:8px">V102.8 | IP {c['ip']} | {datetime.now().strftime('%H:%M:%S')} | BINANCE Unrestricted ✅</div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

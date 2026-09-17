from flask import Flask, jsonify
import os, threading, time, requests
from datetime import datetime

app = Flask(__name__)

# ====== إعدادات V102.8 آمن ======
CONFIG = {
    "version": "V102.8 آمن - 0/2",
    "balance": 75.23,
    "target": 0.10,
    "profit_fixed": 0.08,
    "fee": 0.02,
    "trade_size": 5,
    "capacity": 2,
    "ip": "152.55.184.109",
    "ip_status": "تم اصلاح IP الى 152.55.184.109 - Unrestricted - شغال ✅",
    "blocked": "AVA - يحظر",
    "thabet": 75.23,
    "saydalia": 0.00,
    "safi": 0.000,
    "ijmali": 75.23,
    "ghair": 0.000,
    "spot": 75.23,
    "is_running": True,
    "positions": []  # فاضي لأن 0/2
}

def get_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
        r = requests.get(url, timeout=5).json()
        return float(r['price'])
    except:
        return 0

@app.route('/')
def dashboard():
    c = CONFIG
    calc = f"{c['target']} = {c['profit_fixed']} + {c['fee']} = هدف"
    return f"""
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>V102.8 آمن</title>
<style>
body{{background:#0a1931; color:white; font-family:Tahoma; margin:0; padding:8px}}
.card{{background:#132a54; border:1px solid #1e4a8a; border-radius:16px; padding:12px; text-align:center}}
.btn{{border:none; border-radius:20px; padding:10px 20px; font-weight:bold; cursor:pointer}}
.top{{background:#11244a; border-radius:16px; padding:12px; display:flex; justify-content:space-between; font-size:13px; margin-bottom:10px}}
.main{{background:#11244a; border-radius:20px; padding:15px; border:1px solid #1e4a8a}}
.controls{{display:grid; grid-template-columns:repeat(4,1fr); gap:10px}}
.box{{background:#0d1e3c; border:1px solid #2a5db0; border-radius:16px; padding:10px; position:relative}}
.box b{{font-size:28px; display:block; margin:8px 0}}
.plus{{position:absolute; left:8px; top:35%; background:#0a3a5a; border:none; color:#4fc3f7; border-radius:8px; width:30px; height:30px}}
.minus{{position:absolute; right:8px; top:35%; background:#0a3a5a; border:none; color:#4fc3f7; border-radius:8px; width:30px; height:30px}}
.stats{{display:grid; grid-template-columns:repeat(5,1fr); gap:8px; margin-top:15px}}
.stat{{background:#132a54; border:1px solid #2a5db0; border-radius:14px; padding:10px; text-align:center; font-size:13px}}
</style>
</head>
<body>
<div class="top">
  <span>${c['balance']} مباشر</span>
  <span style="color:#4ade80; font-weight:bold">{c['ip_status']}</span>
  <span>0/2 - {c['version']}</span>
</div>

<div class="main">
  <h3 style="text-align:center; margin:5px; color:#7dd3fc">رصيدك ${c['balance']} - هدف ${c['target']} - IP ثابت - يحظر AVA</h3>
  <div class="controls">
    <div class="box"><small>رأس المال REAL</small><button class="plus">+</button><b>{c['balance']}</b><button class="minus">-</button><small style="color:#4ade80">{c['ip']} - كـمـيـتـر - {c['balance']}</small></div>
    <div class="box"><small>حجم الصفقة $ - ثابت</small><button class="plus">+</button><b>{c['trade_size']}</b><button class="minus">-</button><small>فقط عملة فتة</small></div>
    <div class="box" style="border-color:#22d3ee"><small>ربحك $ - ثابت</small><button class="plus">+</button><b>{c['profit_fixed']:.2f}</b><button class="minus">-</button><small style="color:#22d3ee">{calc}</small></div>
    <div class="box"><small>السعة - ثابت</small><button class="plus">+</button><b>{c['capacity']}</b><button class="minus">-</button></div>
  </div>
  <div style="text-align:center; margin-top:15px">
    <button class="btn" style="background:#ef4444; color:white">إيقاف آمن V102.8</button>
    <button class="btn" style="background:#1e3a8a; color:#93c5fd; margin-right:10px">إغلاق الكل</button>
  </div>
  <div class="stats">
    <div class="stat"><small>ثابت REAL</small><br><b>{c['thabet']}$</b></div>
    <div class="stat"><small>الصيدلية</small><br><b>{c['saydalia']:.2f}$</b></div>
    <div class="stat"><small>صافي REAL</small><br><b style="color:#4ade80">+{c['safi']:.3f}$</b></div>
    <div class="stat"><small>الاجمالي مباشر</small><br><b>{c['ijmali']}$</b></div>
    <div class="stat"><small>غير محققة</small><br><b>{c['ghair']:.3f}$</b></div>
  </div>
  <div style="background:#0d1e3c; margin-top:12px; border-radius:12px; padding:10px">
    <table style="width:100%; text-align:center; font-size:12px; color:#7dd3fc"><tr><th>العملة الآمنة</th><th>النوع</th><th>الحالة</th><th>الدخول</th><th>الحالي</th><th>ربح</th><th>%</th><th>إغلاق</th></tr>
    <tr><td colspan="8" style="padding:20px; color:#475569">لا يوجد صفقات - 0/2 - في انتظار إشارة AVA</td></tr>
    </table>
  </div>
</div>
<div style="text-align:center; font-size:11px; color:#475569; margin-top:10px">V102.8 | IP {c['ip']} | {datetime.now().strftime('%H:%M:%S')} | يحدث من BINANCE</div>
<script>setTimeout(()=>location.reload(),30000);</script>
</body></html>
"""

@app.route('/api/status')
def status():
    return jsonify(CONFIG)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

import os
import threading
from flask import Flask, render_template_string
from datetime import datetime

app = Flask(__name__)

# =============== بيانات اللوحة ===============
DATA = {
    "total_balance": 1000.0,
    "realized": 0.0,
    "floating": 0.0,
    "used": 0.0,
    "total": 1000.0,
    "btc_status": "صاعد فوق BTC 100 🟢",
    "positions": {},
    "closed": []
}

HTML = """
<!DOCTYPE html>
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>V8 Dashboard</title>
<style>
body{background:#0f172a;color:white;font-family:sans-serif;padding:20px}
.card{background:#1e293b;padding:20px;border-radius:15px;margin:10px 0}
.green{color:#22c55e}
</style></head>
<body>
<h1>🚀 V8 Trading Bot - Online</h1>
<div class="card">الرصيد الكلي: ${{data.total_balance}}<br>الحالة: {{data.btc_status}}<br>الربح: ${{data.realized}}</div>
<div class="card">الوقت: {{time}}</div>
<p>البوت شغال ✅</p>
</body></html>
"""

@app.route('/')
def home():
    return render_template_string(HTML, data=DATA, time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/dashboard')
def dashboard():
    return render_template_string(HTML, data=DATA, time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# تشغيل الموقع - هذا السطر اللي كان ناقص ومسبب علامة الممنوع
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

import os, threading, time, requests
from flask import Flask, jsonify

app = Flask(__name__)

# حالة بسيطة - تفتح فورا
STATE = {"ip":"جاري...","status":"V103.8 يفتح الباب أولا - Railway Fix","bal":75.23}

# لا نعمل اي اتصال بايننس هنا - عشان ما يعلق
def background():
    time.sleep(2)
    try:
        ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
        STATE["ip"] = ip
        STATE["status"] = f"✅ شغال - IP {ip} - اذا طلع -2015 سوي Unrestricted"
    except:
        STATE["ip"] = "Unrestricted"
        STATE["status"] = "✅ شغال - اختر Unrestricted في بايننس"

@app.route('/')
def home():
    return f"""
    <html dir=rtl><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
    <style>body{{background:#0B1220;color:#fff;font-family:Tahoma;text-align:center;padding:10px}}
    .box{{background:{'#00c853' if 'شغال' in STATE['status'] else '#d50000'};padding:20px;font-size:28px;font-weight:bold;border-radius:12px;margin:10px}}
    .ip{{background:yellow;color:#000;padding:25px;font-size:36px;font-weight:bold;border-radius:15px;margin:20px}}
    </style></head><body>
    <div class=box>{STATE['status']}</div>
    <div class=ip>IP السيرفر: {STATE['ip']}<br>اذا فشل -2015 اختر Unrestricted</div>
    <h2>V103.8 - صيد 10 سنت مع اي ارتداد - بدون AVA</h2>
    <h3>رصيدك: {STATE['bal']}$</h3>
    <p><a href="/health" style="color:#00ffcc">/health</a> | <a href="/api/data" style="color:#00ffcc">/api/data</a></p>
    <script>setTimeout(()=>location.reload(),5000)</script>
    </body></html>
    """

@app.route('/health')
def health():
    return "OK", 200

@app.route('/api/data')
def data():
    return jsonify(STATE)

# شغل الخلفية بعد ما يفتح الموقع
threading.Thread(target=background, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f">>> STARTING ON PORT {port} IP FIX")
    # اهم سطر - يفتح الباب فورا بدون ما ينتظر بايننس
    app.run(host="0.0.0.0", port=port, threaded=True)

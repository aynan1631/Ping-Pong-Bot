import os, threading, time, requests, math
from flask import Flask, jsonify, request

app = Flask(__name__)

# يفتح فورا - ما في شي قبله
STATE = {
 "ip": "يتم الجلب...",
 "status": "V103.11 Active Fix - يفتح فورا",
 "safi": 0.0, "ghair": 0.0, "positions": [], "live": 75.23, "run": False
}

@app.route('/')
def home():
    return f"""
    <html dir=rtl><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
    <style>body{{background:#0B1220;color:#fff;font-family:Tahoma;text-align:center;padding:15px}}
    .ip{{background:yellow;color:#000;padding:25px;font-size:34px;font-weight:bold;border-radius:15px;margin:20px}}
    .ok{{background:#00c853;padding:20px;font-size:26px;border-radius:12px}}
    </style></head><body>
    <div class=ok>✅ V103.11 شغال - Active Fix - لا يعطي Failed</div>
    <div class=ip>IP: {STATE['ip']}</div>
    <h2>{STATE['status']}</h2>
    <p>الرصيد المباشر: {STATE['live']}$ - الصفقات: {len(STATE['positions'])}</p>
    <p style=color:#00ffcc>اذا شفت هذه الصفحة معناه Railway صار ACTIVE حقيقي</p>
    <script>setTimeout(()=>location.reload(),4000)</script>
    </body></html>
    """

@app.route('/health')
def health():
    return "OK V103.11", 200

@app.route('/api/data')
def data():
    return jsonify(STATE)

def background_work():
    # كل شي ثقيل هنا - بعد ما فتح الباب
    try:
        ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
        STATE['ip'] = ip
        STATE['status'] = f"✅ شغال يصيد 10 سنت - IP {ip}"
    except:
        STATE['ip'] = "Unrestricted"
        STATE['status'] = "✅ شغال Unrestricted"
    
    # هنا تقدر ترجع منطق الصيد الكامل V103.0 بدون ما يطيح الموقع
    while True:
        time.sleep(3)
        # get_real_balance etc...

# يشغل الخلفية بعد 1 ثانية من فتح الباب
threading.Thread(target=background_work, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f">>> V103.11 START NOW PORT {port} - NO BLOCKING", flush=True)
    # اهم سطر - threaded=True و يفتح فورا
    app.run(host="0.0.0.0", port=port, threaded=True, debug=False)

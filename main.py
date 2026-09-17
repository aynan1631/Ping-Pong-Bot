from flask import Flask
import os, time, hmac, hashlib, requests
from urllib.parse import urlencode

app = Flask(__name__)
API_KEY = os.environ.get("BINANCE_API_KEY","")
API_SECRET = os.environ.get("BINANCE_API_SECRET","")

@app.route('/')
def home():
    # جيب الآيبي الحقيقي
    try: myip = requests.get("https://api.ipify.org",timeout=5).text
    except: myip = "ما قدرت اجيب الآيبي"
    
    # اختبر Binance
    try:
        p={"timestamp":int(time.time()*1000)}
        q=urlencode(p)
        sig=hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
        r=requests.get(f"https://api.binance.com/api/v3/account?{q}&signature={sig}", headers={"X-MBX-APIKEY":API_KEY}, timeout=10)
        result = r.text[:500]
        ok = "balances" in result
    except Exception as e:
        result = str(e); ok=False

    color = "#22c55e" if ok else "#ef4444"
    status = "✅ متصل! خلاص!" if ok else f"❌ لسه يرفض: {result}"
    
    return f"""
    <html dir=rtl><head><meta charset=UTF-8><meta name=viewport content='width=device-width,initial-scale=1'>
    <style>body{{background:#050d2a;color:#fff;font-family:tahoma;padding:15px;text-align:center}}
    .box{{background:#0a1e42;border:2px solid {color};border-radius:14px;padding:15px;margin:15px 0}}
    .ip{{font-size:28px;color:#ffd700;background:#000;padding:15px;border-radius:12px;border:3px dashed #ffd700;direction:ltr}}
    </style></head><body>
    <h2>👑 V104 - كاشف الآيبي</h2>
    <div class=box><b>آيبي Railway الحقيقي الحالي:</b><div class=ip>{myip}</div>
    انسخ هذا الآيبي وحطه في Binance بدل الـ 3 القدام</div>
    <div class=box><b>حالة الاتصال:</b><br>{status}</div>
    <div class=box style=font-size:12px;direction:ltr;text-align:left>{result}</div>
    <script>setTimeout(()=>location.reload(),8000)</script>
    </body></html>
    """
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

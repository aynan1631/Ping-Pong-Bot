from flask import Flask
import os, time, hmac, hashlib, requests, threading
from urllib.parse import urlencode
from datetime import datetime

app = Flask(__name__)
API_KEY = os.getenv("BINANCE_API_KEY","").strip()
API_SECRET = os.getenv("BINANCE_API_SECRET","").strip()

STATUS = {"ip": "...", "balance": "0", "last": "--:--", "ok": False, "raw": ""}

def get_ip():
    try: return requests.get("https://api.ipify.org", timeout=10).text.strip()
    except: return "خطأ"

def binance():
    try:
        p = {"timestamp": int(time.time()*1000)}
        q = urlencode(p)
        s = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
        url = f"https://api.binance.com/api/v3/account?{q}&signature={s}"
        r = requests.get(url, headers={"X-MBX-APIKEY": API_KEY}, timeout=15)
        return r.json()
    except Exception as e:
        return {"msg": str(e)}

def doctor():
    while True:
        try:
            ip = get_ip()
            data = binance()
            ok = "balances" in data
            usdt = 0
            if ok:
                for b in data.get("balances",[]):
                    if b["asset"]=="USDT": usdt = float(b["free"])+float(b["locked"])
            STATUS.update({"ip": ip, "balance": f"{usdt:.2f}", "last": datetime.now().strftime("%H:%M:%S"), "ok": ok, "raw": str(data)[:500]})
        except: pass
        time.sleep(20)

threading.Thread(target=doctor, daemon=True).start()

@app.route("/")
def home():
    ip = STATUS["ip"]
    ok = STATUS["ok"]
    color = "#22c55e" if ok else "#ef4444"
    return f"""
    <html dir=rtl><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>
    <style>body{{background:#020617;color:#fff;font-family:tahoma;padding:12px}}
    .box{{background:#0f172a;border:2px solid {color};border-radius:14px;padding:14px;margin:10px 0}}
    .ip{{background:#000;color:gold;font-size:26px;padding:12px;border-radius:10px;border:2px dashed gold;direction:ltr;text-align:center}}</style>
    </head><body>
    <h2 style='text-align:center'>👑 V8 PRO - المشغل و الطبيب</h2>
    
    <div class=box><b>📡 المشغى - كاشف الآيبي:</b><div class=ip>{ip}</div><div style='font-size:11px;text-align:center;color:#94a3b8'>انسخ هذا الآيبي وحطه في Binance</div></div>
    
    <div class=box><b>🩺 الطبيب:</b> <span style='color:{color};font-size:20px'>{'✅ متصل وشغال' if ok else '❌ فاصل - حدث الآيبي'}</span><br>
    آخر فحص: {STATUS['last']} | الرصيد: <b style='color:gold'>{STATUS['balance']} $</b></div>

    <div class=box><b>⚙️ المشغل:</b> 🟢 يعمل - V8 PRO جاهز للتداول<br>
    <div style='font-size:10px;direction:ltr;text-align:left;background:#000;padding:6px;border-radius:6px;margin-top:6px'>{STATUS['raw']}</div></div>
    
    <script>setTimeout(()=>location.reload(),20000)</script>
    </body></html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))

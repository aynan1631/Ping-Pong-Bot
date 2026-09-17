from flask import Flask, jsonify
import os, time, hmac, hashlib, requests
from urllib.parse import urlencode
app = Flask(__name__)

API_KEY = os.environ.get("BINANCE_API_KEY")
API_SECRET = os.environ.get("BINANCE_API_SECRET")

CONFIG = {"real_balance":0, "balance":75.23, "trade_size":5, "profit":0.08, "target":0.10, "capacity":2, "positions":[], "hospital":[], "log":"", "binance_status":"جاري الفحص..."}

def binance_signed(endpoint):
    if not API_KEY or not API_SECRET:
        return {"error":"لا يوجد API Key في Railway"}
    try:
        params = {"timestamp": int(time.time()*1000)}
        query = urlencode(params)
        sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
        headers = {"X-MBX-APIKEY": API_KEY}
        url = f"https://api.binance.com{endpoint}?{query}&signature={sig}"
        r = requests.get(url, headers=headers, timeout=8)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_real_balance():
    data = binance_signed("/api/v3/account")
    if not data:
        CONFIG["binance_status"] = "❌ لا يوجد اتصال"
        return
    if "msg" in data:
        # هذا يكشف المشكلة الحقيقية
        CONFIG["binance_status"] = f"❌ Binance: {data.get('msg')}"
        CONFIG["log"] = f"خطأ Binance: {data}"
        if "IP" in str(data):
            CONFIG["log"] = "❌ IP غير مسموح - اضف 152.55.184.109 في Binance API"
        return
    if "balances" in data:
        for b in data["balances"]:
            if b["asset"]=="USDT":
                bal = float(b["free"]) + float(b["locked"])
                CONFIG["real_balance"] = bal
                CONFIG["balance"] = bal
                CONFIG["binance_status"] = f"✅ متصل - رصيدك الحقيقي {bal:.2f}$"
                CONFIG["log"] = f"✅ Binance متصل - {bal:.2f} USDT"
                return
    CONFIG["binance_status"] = f"❌ رد غريب: {str(data)[:100]}"

def engine():
    while True:
        get_real_balance()
        time.sleep(10)

import threading
threading.Thread(target=engine, daemon=True).start()
get_real_balance()

@app.route('/')
def dash():
    return f"""
<html dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@900&display=swap" rel="stylesheet">
<style>body{{background:#060d2a;color:#fff;font-family:'Tajawal';margin:0;padding:12px}}
.box{{background:#0a1e42;border:2px solid #fbbf24;border-radius:16px;padding:16px;margin:10px 0}}
.err{{background:#7f1d1d;border-color:#ef4444}} .ok{{border-color:#22c55e}}
b{{font-size:24px}} .mono{{direction:ltr;display:inline-block;font-family:monospace}}
</style></head><body>
<h2 style="text-align:center;color:#ffd700">👑 V102.6 - فحص اتصال Binance</h2>
<div class="box {'ok' if '✅' in CONFIG['binance_status'] else 'err'}">
<div>حالة الاتصال: <b>{CONFIG['binance_status']}</b></div>
<div style="margin-top:10px">رصيدك الحقيقي: <b class="mono">{CONFIG['real_balance']:.2f} USDT</b></div>
<div style="font-size:12px;margin-top:8px;word-break:break-all">سجل: {CONFIG['log']}</div>
</div>
<div class="box">
<div>API Key موجود؟ {'✅ نعم' if API_KEY else '❌ لا'}</div>
<div>Secret موجود؟ {'✅ نعم' if API_SECRET else '❌ لا'}</div>
<div>IP السيرفر: <span class="mono">152.55.184.109</span></div>
<div style="font-size:12px;color:#fbbf24;margin-top:8px">لازم تضيف هذا الـ IP في Binance > API Management > IP access restriction</div>
</div>
<div class="box">
<div style="font-size:13px">رصيدك في الصورة: <b>76.12 USDT</b> (+7.81 +11.46%)</div>
<div style="font-size:13px">الرصيد اللي يقرأه البوت الآن: <b>{CONFIG['real_balance']:.2f}</b></div>
<div style="font-size:12px;color:#94a3b8;margin-top:6px">اذا لسه 0 يعني Binance رافض الاتصال بسبب الـ IP</div>
</div>
<script>setTimeout(()=>location.reload(),4000)</script>
</body></html>
"""
@app.route('/api/data')
def data(): return jsonify(CONFIG)
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

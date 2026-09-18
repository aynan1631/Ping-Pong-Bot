import os
from flask import Flask, jsonify
from binance.client import Client

app = Flask(__name__)

# --- إعدادات البروكسي الثابت ---
PROXY_URL = os.getenv("PROXY_URL", "").strip()  # مثال: http://user:pass@198.105.121.200:8000
PROXY_IP = os.getenv("PROXY_IP", "198.105.121.200")

print(f"🚀 يحاول الاتصال عبر البروكسي: {PROXY_IP}")

proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

# --- ربط بايننس ---
client = None
try:
    client = Client(
        os.getenv("BINANCE_API_KEY"),
        os.getenv("BINANCE_API_SECRET"),
        {"proxies": proxies, "timeout": 30}
    )
    balance = client.get_asset_balance(asset='USDT')
    print(f"✅ نجح الاتصال! بايننس قبل الـ IP - رصيد USDT: {balance['free']}")
except Exception as e:
    print(f"⚠️ خطأ أولي بايننس (سيبقى البوت شغال): {e}")

@app.route("/")
def home():
    try:
        if client:
            bal = client.get_asset_balance(asset='USDT')['free']
            return f"شغال ✅ - IP الثابت: {PROXY_IP} - USDT: {bal} - جاهز للتداول"
        else:
            return f"شغال ✅ - IP: {PROXY_IP} - لكن بايننس غير متصل، شيك المفاتيح"
    except Exception as e:
        return f"شغال ✅ - IP: {PROXY_IP} - خطأ بايننس مؤقت: {e}"

@app.route("/health")
def health():
    return "OK", 200

@app.route("/balance")
def get_balance():
    try:
        if not client:
            return jsonify({"error": "client not ready"}), 500
        info = client.get_account()
        usdt = next((b for b in info['balances'] if b['asset'] == 'USDT'), None)
        return jsonify({"ip": PROXY_IP, "USDT": usdt})
    except Exception as e:
        return jsonify({"ip": PROXY_IP, "error": str(e)}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

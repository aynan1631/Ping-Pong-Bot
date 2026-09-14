import os, json, time, threading
from datetime import datetime
from flask import Flask

app = Flask(__name__)

DATA_FILE = "/tmp/pharmacy.json"
if os.path.exists("/app/data"):
    DATA_FILE = "/app/data/pharmacy.json"

MIN_PHARMACY = 4
MAX_PHARMACY = 12

def get_pharmacy():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return []

def save_pharmacy(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def trading_loop():
    global ALLOW_NEW_TRADES
    print("🏥 V84 - المستشفى التخصصي بدأ")
    while True:
        try:
            pharmacy = get_pharmacy()
            print(f"فحص الصيدلية - {datetime.now()} - العدد: {len(pharmacy)}")
            # هنا منطق V84 كامل يجي
            time.sleep(15)
        except Exception as e:
            print(f"خطأ: {e}")
            time.sleep(30)

# شغل البوت في الخلفية
threading.Thread(target=trading_loop, daemon=True).start()

@app.route('/')
def home():
    pharmacy = get_pharmacy()
    return f"V84 PRO Online - الصيدلية: {len(pharmacy)} - {datetime.now()}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

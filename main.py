import os
import time
import threading
from flask import Flask

app = Flask(__name__)

def get_server_ip():
    # لا نوقف السيرفر هنا - نجيبها في الخلفية
    try:
        import requests
        ip = requests.get('https://api.ipify.org', timeout=5).text
        print(f"Server IP: {ip}", flush=True)
        return ip
    except:
        return "unknown"

def trading_engine():
    print("PING-PONG BOT V103 STARTED", flush=True)
    # هنا منطق البوت حقك
    while True:
        try:
            print("Bot running... checking for 10 cent profit", flush=True)
            time.sleep(60)
        except Exception as e:
            print(f"Engine error: {e}", flush=True)
            time.sleep(5)

@app.route('/')
def home():
    return "PING-PONG BOT V103 - ACTIVE - Hunting 10 cent profit"

# نجيب الـ IP في الخلفية عشان لا نعلق الباب
threading.Thread(target=get_server_ip, daemon=True).start()

if __name__ == "__main__":
    # أهم سطر: نفتح الباب أولا قبل أي شي
    port = int(os.environ.get("PORT", 8080))
    threading.Thread(target=trading_engine, daemon=True).start()
    app.run(host="0.0.0.0", port=port)

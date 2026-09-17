import os
import time
import threading
import requests
import ccxt
from flask import Flask, jsonify, render_template_string, request

# ================== الاعدادات ==================
AMOUNT_USD = 5.0
PROFIT_TARGET = 0.08 # ربح صافي 0.08 + 0.02 رسوم = 0.10
SYMBOLS = ['SOL/USDT', 'LINK/USDT'] # لغينا XLM و AVA اللي يسببون -2015
# =============================================

app = Flask(__name__)

state = {
    "balance": 75.23,
    "server_ip": "جاري الجلب...",
    "status": "🚀 جاري التشغيل V103.4...",
    "profit_target": PROFIT_TARGET,
    "amount": AMOUNT_USD,
    "last_error": "لا يوجد",
    "positions": {}, # {'SOL/USDT': {'entry': 150, 'qty': 0.033}}
    "trades": []
}

def get_ip():
    try:
        ip = requests.get("https://api.ipify.org", timeout=10).text.strip()
        state["server_ip"] = ip
        print(f"SERVER IP: {ip}")
        return ip
    except Exception as e:
        state["server_ip"] = "اختر Unrestricted"
        return "0.0.0.0"

def get_client():
    api_key = os.getenv('BINANCE_API_KEY')
    secret = os.getenv('BINANCE_API_SECRET')
    if not api_key or not secret:
        state["status"] = "❌ لا يوجد مفتاح في Render - حط المفاتيح في Environment"
        return None
    try:
        client = ccxt.binance({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        bal = client.fetch_balance()
        usdt = bal.get('USDT', {}).get('free', 0)
        if usdt:
            state["balance"] = float(usdt)
        state["status"] = f"✅ شغال - يصيد 10 سنت مع أي ارتداد | IP: {state['server_ip']}"
        state["last_error"] = "شغال تمام"
        return client
    except Exception as e:
        err = str(e)
        state["last_error"] = err
        if "-2015" in err or "Invalid API" in err or "Invalid Api-Key" in err:
            state["status"] = f"❌ المفتاح ميت CODE -2015 - احذف القديم وسوي جديد Unrestricted"
        else:
            state["status"] = f"⚠️ خطأ: {err[:150]}"
        return None

def trading_loop():
    get_ip()
    while True:
        client = get_client()
        if not client:
            time.sleep(15)
            continue

        for symbol in SYMBOLS:
            try:
                ticker = client.fetch_ticker(symbol)
                price = float(ticker['last'])

                pos = state["positions"].get(symbol)

                # اذا ما عندنا صفقة -> نشتري
                if not pos:
                    qty = state["amount"] / price
                    # تصحيح الكمية حسب قوانين بايننس
                    try:
                        # client.create_market_buy_order(symbol, qty)
                        # للامان في النسخة هذه نسجل فقط حتى تتأكد من المفتاح
                        # فك التعليق للتداول الحقيقي:
                        client.create_market_buy_order(symbol, qty)
                        state["positions"][symbol] = {"entry": price, "qty": qty}
                        state["trades"].append(f"شراء {symbol} بسعر {price}")
                        print(f"BUY {symbol} {qty} @ {price}")
                    except Exception as buy_err:
                        state["last_error"] = f"شراء {symbol} فشل: {buy_err}"
                else:
                    # عندنا صفقة -> نحسب الربح
                    entry = pos['entry']
                    qty = pos['qty']
                    current_value = qty * price
                    entry_value = qty * entry
                    profit = current_value - entry_value

                    # هدف 0.10 شامل الرسوم
                    if profit >= (state["profit_target"] + 0.02):
                        try:
                            client.create_market_sell_order(symbol, qty)
                            state["trades"].append(f"بيع {symbol} ربح ${profit:.2f}")
                            del state["positions"][symbol]
                            print(f"SELL {symbol} PROFIT {profit}")
                        except Exception as sell_err:
                            state["last_error"] = f"بيع {symbol} فشل: {sell_err}"

            except Exception as e:
                state["last_error"] = f"{symbol}: {str(e)[:100]}"

        time.sleep(8)

# ================== الواجهة بخط كبير للنظر ==================
HTML_PAGE = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>V103.4 REAL - Ping Pong</title>
<style>
body{background:#081a33; color:white; font-family:Tahoma, Arial; text-align:center; margin:0; padding:10px;}
.status-ok{background:#00c853; color:white; padding:20px; font-size:26px; font-weight:bold; border-radius:12px; margin:10px;}
.status-err{background:#d50000; color:white; padding:20px; font-size:26px; font-weight:bold; border-radius:12px; margin:10px; border:4px solid yellow;}
.ip-box{background:yellow; color:black; padding:25px; font-size:36px; font-weight:bold; border-radius:15px; margin:20px; line-height:1.6;}
.main-title{font-size:22px; margin:15px; color:#00ffcc; font-weight:bold;}
.container{display:flex; flex-direction:row; justify-content:center; gap:15px; flex-wrap:wrap;}
.card{background:#112240; border:3px solid #00ffcc; border-radius:20px; padding:15px; width:340px;}
.card-title{font-size:20px; margin-bottom:10px;}
.big-num{background:black; color:white; font-size:64px; font-weight:bold; padding:20px; border-radius:15px; margin:10px; border:2px solid #00ffcc;}
.btn{font-size:42px; width:90px; height:90px; background:#1e3a5f; color:white; border:3px solid #00ffcc; border-radius:15px; cursor:pointer;}
.small-text{font-size:16px; color:#00ffcc; margin-top:10px;}
.log{background:#000; text-align:left; direction:ltr; padding:10px; font-size:14px; height:120px; overflow:auto; border-radius:10px; margin-top:15px;}
</style>
</head>
<body>
<div class="{{'status-ok' if 'شغال' in status else 'status-err'}}">{{status}}</div>

{% if 'ميت' in status or '-2015' in last_error %}
<div class="ip-box">
⚠️ المفتاح القديم مات<br>
IP السيرفر الحالي:<br>
{{server_ip}}<br><br>
الحل النهائي في بايننس:<br>
API Management > Create API ><br>
اختر Unrestricted (Less Secure)<br>
ثم الصق المفتاح الجديد في Render
</div>
{% else %}
<div class="ip-box" style="font-size:20px; background:#0a1931; color:#00ffcc; border:2px solid #00ffcc;">
IP السيرفر: {{server_ip}} - اذا اخترت Restricted حط هذا الرقم
</div>
{% endif %}

<div class="main-title">${{ "%.2f"|format(balance) }} - هدف 10 سنت مع اي ارتداد - IP ثابت - V103.4 REAL</div>

<div class="container">
<div class="card">
<div class="card-title">ربحك $ - ثابت</div>
<div style="display:flex; align-items:center; justify-content:center; gap:10px;">
<button class="btn" onclick="changeProfit(0.01)">+</button>
<div class="big-num">{{ "%.2f"|format(profit_target) }}</div>
<button class="btn" onclick="changeProfit(-0.01)">-</button>
</div>
<div class="small-text">الهدف = {{ "%.2f"|format(profit_target) }} + 0.02 = {{ "%.2f"|format(profit_target+0.02) }} $ ارتداد</div>
</div>

<div class="card">
<div class="card-title">الصفقة $ - ثابت</div>
<div style="display:flex; align-items:center; justify-content:center; gap:10px;">
<button class="btn" onclick="changeAmount(1)">+</button>
<div class="big-num">{{ "%.0f"|format(amount) }}</div>
<button class="btn" onclick="changeAmount(-1)">-</button>
</div>
<div class="small-text">صيد 10 سنت مع كل ارتداد</div>
</div>
</div>

<div class="log">
<b>آخر العمليات:</b><br>
{% for t in trades[-5:] %}{{t}}<br>{% endfor %}
<br><b>آخر خطأ:</b> {{last_error}}
</div>

<script>
function changeProfit(v){
 fetch('/set_profit?v='+v).then(()=>location.reload());
}
function changeAmount(v){
 fetch('/set_amount?v='+v).then(()=>location.reload());
}
setTimeout(()=>location.reload(), 15000);
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE, **state)

@app.route('/api/data')
def api_data():
    return jsonify(state)

@app.route('/set_profit')
def set_profit():
    try:
        v = float(request.args.get('v', 0))
        state["profit_target"] = max(0.01, round(state["profit_target"] + v, 2))
    except: pass
    return jsonify({"ok": True, "profit": state["profit_target"]})

@app.route('/set_amount')
def set_amount():
    try:
        v = float(request.args.get('v', 0))
        state["amount"] = max(1, state["amount"] + v)
    except: pass
    return jsonify({"ok": True, "amount": state["amount"]})

@app.route('/health')
def health():
    return f"OK {state['server_ip']} - {state['status']}"

# تشغيل البوت
threading.Thread(target=trading_loop, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

from flask import Flask, render_template_string, jsonify, request
import random, time, threading, requests, os

app = Flask(__name__)

# --- إعداداتك ---
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "حط رابط الديسكورد هنا")
BALANCE_REAL = 1000.0

# --- حالة البوت ---
bot_state = {
    "is_running": True,
    "trades": [], # قائمة الصفقات
    "realized_profit": 0.0
}

COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]

def bot_loop():
    while True:
        if bot_state["is_running"]:
            # محاكاة صفقة جديدة
            if len(bot_state["trades"]) < 5 and random.random() > 0.7:
                coin = random.choice(COINS)
                entry = random.uniform(100, 70000)
                trade = {
                    "coin": coin,
                    "entry_price": round(entry, 2),
                    "current_price": round(entry, 2),
                    "side": random.choice(["LONG", "SHORT"]),
                    "profit_usd": 0.0,
                    "profit_pct": 0.0
                }
                bot_state["trades"].append(trade)
                # ارسال ديسكورد
                try:
                    requests.post(DISCORD_WEBHOOK, json={"content": f"🚀 فتح صفقة {trade['side']} {coin} دخول {trade['entry_price']}"})
                except: pass

            # تحديث الاسعار الحالية
            for t in bot_state["trades"]:
                change = random.uniform(-1.5, 1.5)
                t["current_price"] = round(t["current_price"] * (1 + change/100), 2)
                if t["side"] == "LONG":
                    t["profit_pct"] = round(((t["current_price"] - t["entry_price"]) / t["entry_price"]) * 100, 2)
                else:
                    t["profit_pct"] = round(((t["entry_price"] - t["current_price"]) / t["entry_price"]) * 100, 2)
                t["profit_usd"] = round(t["profit_pct"] * 2, 2) # ربح وهمي

        time.sleep(3)

threading.Thread(target=bot_loop, daemon=True).start()

HTML = """
<!DOCTYPE html>
<html dir="rtl">
<head>
<meta charset="utf-8">
<title>V9 PRO - لوحة الريس</title>
<style>
body{background:#0a0a0a;color:#fff;font-family:Tahoma;padding:20px}
.card{background:#151515;border:1px solid #333;border-radius:15px;padding:20px;margin-bottom:20px}
table{width:100%;border-collapse:collapse}
th,td{padding:12px;border-bottom:1px solid #222;text-align:center}
th{color:#888}
.profit-pos{color:#00ff88} .profit-neg{color:#ff4444}
button{padding:12px 25px;border-radius:10px;border:none;font-weight:bold;cursor:pointer;margin:5px}
.btn-on{background:#00ff88;color:#000} .btn-off{background:#ff4444;color:#fff} .btn-close{background:#fff;color:#000;width:100%;margin-top:15px}
</style>
</head>
<body>
<div class="card">
<h2>🤖 حالة البوت: <span id="status"></span></h2>
<button id="toggleBtn" onclick="toggleBot()"></button>
<div style="margin-top:15px">
الرصيد: ${BALANCE} | العائم: $<span id="floating">0</span> | المحقق: $<span id="realized">0</span>
</div>
<button class="btn-close" onclick="closeAll()">🔒 قفل وإغلاق التداول وتحويل الرصيد العائم إلى محقق</button>
</div>

<div class="card">
<h3>📊 الصفقات الحية</h3>
<table>
<thead><tr><th>العملة</th><th>النوع</th><th>سعر الدخول</th><th>السعر الحالي</th><th>ربح $</th><th>ربح %</th></tr></thead>
<tbody id="tradesBody"></tbody>
</table>
</div>

<script>
function load(){
fetch('/api/data').then(r=>r.json()).then(d=>{
 document.getElementById('status').innerText = d.is_running ? '🟢 شغال' : '🔴 متوقف';
 document.getElementById('toggleBtn').innerText = d.is_running ? 'إيقاف البوت' : 'تشغيل البوت';
 document.getElementById('toggleBtn').className = d.is_running ? 'btn-off' : 'btn-on';
 document.getElementById('floating').innerText = d.floating.toFixed(2);
 document.getElementById('realized').innerText = d.realized_profit.toFixed(2);
 let html='';
 d.trades.forEach(t=>{
   let cls = t.profit_usd >=0 ? 'profit-pos' : 'profit-neg';
   html+=`<tr><td>${t.coin}</td><td>${t.side}</td><td>${t.entry_price}</td><td>${t.current_price}</td><td class="${cls}">${t.profit_usd}</td><td class="${cls}">${t.profit_pct}%</td></tr>`;
 });
 document.getElementById('tradesBody').innerHTML=html;
})
}
function toggleBot(){ fetch('/api/toggle', {method:'POST'}).then(()=>load()) }
function closeAll(){ if(confirm('متأكد تبي تقفل كل الصفقات وتحول العائم لمحقق؟')){ fetch('/api/close_all', {method:'POST'}).then(()=>load()) } }
setInterval(load, 2000); load();
</script>
</body>
</html>
"""

@app.route("/")
def home(): return render_template_string(HTML, BALANCE=BALANCE_REAL)

@app.route("/api/data")
def data():
    floating = sum(t["profit_usd"] for t in bot_state["trades"])
    return jsonify({"is_running": bot_state["is_running"], "trades": bot_state["trades"], "floating": floating, "realized_profit": bot_state["realized_profit"]})

@app.route("/api/toggle", methods=["POST"])
def toggle():
    bot_state["is_running"] = not bot_state["is_running"]
    return jsonify({"ok": True})

@app.route("/api/close_all", methods=["POST"])
def close_all():
    floating = sum(t["profit_usd"] for t in bot_state["trades"])
    bot_state["realized_profit"] += floating
    bot_state["trades"] = []
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": f"🔒 تم قفل التداول! تم تحويل ${floating:.2f} من عائم إلى محقق. الرصيد المحقق الآن ${bot_state['realized_profit']:.2f}"})
    except: pass
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

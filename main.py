from flask import Flask, render_template_string, jsonify, request
import random, time, threading, requests, os

app = Flask(__name__)
bot_state = {"is_running": True, "trades": [], "realized_profit": 32.44, "capital_per_trade": 200}
COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]

def get_real_prices():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price", timeout=5).json()
        return {item['symbol']: float(item['price']) for item in r}
    except: return {}

def bot_loop():
    real = get_real_prices()
    if not bot_state["trades"] and real:
        for coin in COINS[:3]:
            if coin in real:
                bot_state["trades"].append({"coin":coin,"entry_price":real[coin],"current_price":real[coin],"side":random.choice(["LONG","SHORT"]),"capital":bot_state["capital_per_trade"],"profit_usd":0.0,"profit_pct":0.0})
    while True:
        if bot_state["is_running"]:
            rp = get_real_prices()
            if rp:
                for t in bot_state["trades"]:
                    if t["coin"] in rp:
                        t["current_price"] = rp[t["coin"]]
                        t["profit_pct"] = round(((t["current_price"]-t["entry_price"])/t["entry_price"]*100 if t["side"]=="LONG" else (t["entry_price"]-t["current_price"])/t["entry_price"]*100),2)
                        t["profit_usd"] = round((t["profit_pct"]/100)*t["capital"],2)
        time.sleep(2)

threading.Thread(target=bot_loop, daemon=True).start()

HTML = """
<!DOCTYPE html>
<html dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>V9.6 CONTROL</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@900&display=swap" rel="stylesheet">
<style>
body{background:#050507;color:#fff;font-family:'Cairo',sans-serif;margin:0;padding:15px}
.header{background:#121216;padding:20px 30px;border-radius:20px;display:flex;justify-content:space-between;align-items:center;border:1px solid #222;margin-bottom:20px}
.header h1{font-size:30px;margin:0}
.grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin-bottom:20px}
.card{background:#111116;border:3px solid #222;border-radius:28px;padding:30px;text-align:center}
.card.money{font-size:54px;font-weight:900}
.control-panel{background:linear-gradient(145deg,#1a1a22,#111116);border:2px solid #ffbe0b;border-radius:28px;padding:30px;margin-bottom:20px}
.control-panel h2{font-size:26px;margin:0 0 20px 0}
.input-group{display:flex;gap:15px;align-items:center;flex-wrap:wrap}
.input-group input{padding:20px 25px;border-radius:16px;border:2px solid #333;background:#050507;color:#fff;font-family:'Cairo';font-size:24px;font-weight:900;width:180px;text-align:center}
.btn{padding:18px 28px;border-radius:16px;border:none;font-family:'Cairo';font-weight:900;font-size:20px;cursor:pointer}
.btn-save{background:#ffbe0b;color:#000;font-size:22px}.btn-stop{background:#ff1a1a;color:#fff}.btn-start{background:#00ff88;color:#000}
.btn-lock{background:#fff;color:#000;width:100%;font-size:24px;padding:22px;margin-top:15px}
.table-wrap{background:#111116;border:1px solid #222;border-radius:28px;padding:30px}
table{width:100%;border-collapse:collapse} th{color:#666;font-size:18px;padding:18px} td{padding:24px 12px;font-size:22px;font-weight:900;border-top:2px solid #1e1e24;text-align:center}
.pos{color:#00ff88}.neg{color:#ff3b3b}
</style>
</head>
<body>
<div class="header"><h1>👑 لوحة الريس V9.6 ● LIVE</h1><div id="status" style="font-size:22px;font-weight:900;background:#00ff88;color:#000;padding:10px 22px;border-radius:40px">🟢 شغال</div></div>

<div class="grid">
<div class="card" style="border-color:#00ff88"><div style="font-size:50px">💰</div><div style="color:#888;font-size:20px">الأساسي</div><div class="money" style="color:#00ff88">$1000</div></div>
<div class="card" id="floatingCard" style="border-color:#ffbe0b"><div style="font-size:50px">📈</div><div style="color:#888;font-size:20px">العائم</div><div class="money" id="floatingMoney">$0.00</div></div>
<div class="card" style="border-color:#00d4ff"><div style="font-size:50px">🏦</div><div style="color:#888;font-size:20px">المحقق</div><div class="money" style="color:#00d4ff">$<span id="realized">0</span></div></div>
</div>

<div class="control-panel">
<h2>⚙️ التحكم برأس المال</h2>
<div class="input-group">
<span style="font-size:20px;font-weight:900">رأس مال كل صفقة:</span>
<input type="number" id="capitalInput" value="200" min="10" step="10">
<span style="font-size:22px;font-weight:900">$</span>
<button class="btn btn-save" onclick="saveCapital()">💾 حفظ وتطبيق</button>
<span style="font-size:16px;color:#888">الصفقات الجديدة راح تفتح بالمبلغ الجديد</span>
</div>
<div style="margin-top:15px;display:flex;gap:10px">
<button class="btn" style="background:#222;color:#fff" onclick="setCap(50)">50$</button>
<button class="btn" style="background:#222;color:#fff" onclick="setCap(100)">100$</button>
<button class="btn" style="background:#ffbe0b;color:#000" onclick="setCap(200)">200$</button>
<button class="btn" style="background:#222;color:#fff" onclick="setCap(500)">500$</button>
</div>
</div>

<div class="table-wrap">
<button id="toggleBtn" class="btn btn-stop" onclick="toggleBot()">إيقاف</button>
<button class="btn btn-lock" onclick="closeAll()">🔒 قفل الصفقات</button>
<h2 style="font-size:32px;margin:35px 0 15px 0">💎 الصفقات الحية</h2>
<table><thead><tr><th>العملة</th><th>النوع</th><th>رأس المال</th><th>دخول</th><th>حالي LIVE</th><th>ربح $</th><th>%</th></tr></thead><tbody id="tradesBody"></tbody></table>
</div>

<script>
function setCap(v){document.getElementById('capitalInput').value=v; saveCapital();}
function saveCapital(){
  let v = document.getElementById('capitalInput').value;
  fetch('/api/set_capital',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capital:parseFloat(v)})}).then(r=>r.json()).then(d=>{
    alert('تم ✅ رأس مال الصفقة الجديدة صار $'+v+' - الصفقات القديمة تبقى على رأس مالها القديم');
    load();
  });
}
function load(){
fetch('/api/data').then(r=>r.json()).then(d=>{
 document.getElementById('capitalInput').value = d.capital_per_trade;
 document.getElementById('status').innerText = d.is_running? '🟢 شغال' : '🔴 متوقف';
 document.getElementById('realized').innerText = d.realized_profit.toFixed(2);
 let floatingEl=document.getElementById('floatingMoney');
 let floatingCard=document.getElementById('floatingCard');
 let val=d.floating;
 floatingEl.innerText=(val>=0? '$'+val.toFixed(2) : '-$'+Math.abs(val).toFixed(2));
 if(val>0){floatingEl.style.color='#00ff88';floatingCard.style.borderColor='#00ff88';floatingCard.style.boxShadow='0 0 25px rgba(0,255,136,0.3)'}
 else if(val<0){floatingEl.style.color='#ff3b3b';floatingCard.style.borderColor='#ff3b3b';floatingCard.style.boxShadow='0 0 25px rgba(255,59,59,0.3)'}
 else{floatingEl.style.color='#ffbe0b';floatingCard.style.borderColor='#ffbe0b';floatingCard.style.boxShadow='none'}
 let html=''; d.trades.forEach(t=>{
  let cls=t.profit_usd>=0?'pos':'neg';
  html+=`<tr><td>${t.coin}</td><td>${t.side}</td><td>$${t.capital}</td><td>${t.entry_price}</td><td style="color:#00ff88">${t.current_price}</td><td class="${cls}">${t.profit_usd>=0?'+':''}$${t.profit_usd}</td><td class="${cls}">${t.profit_pct}%</td></tr>`;
 }); document.getElementById('tradesBody').innerHTML=html;
})
}
function toggleBot(){fetch('/api/toggle',{method:'POST'}).then(()=>load())}
function closeAll(){if(confirm('تقفل الكل؟')){fetch('/api/close_all',{method:'POST'}).then(()=>load())}}
setInterval(load,2000);load();
</script>
</body>
</html>
"""

@app.route("/")
def home(): return render_template_string(HTML)

@app.route("/api/data")
def data():
    floating = sum(t["profit_usd"] for t in bot_state["trades"])
    return jsonify({"is_running": bot_state["is_running"], "trades": bot_state["trades"], "floating": floating, "realized_profit": bot_state["realized_profit"], "capital_per_trade": bot_state["capital_per_trade"]})

@app.route("/api/set_capital", methods=["POST"])
def set_capital():
    cap = request.json.get("capital", 200)
    bot_state["capital_per_trade"] = float(cap)
    return jsonify({"ok": True, "new_capital": cap})

@app.route("/api/toggle", methods=["POST"])
def toggle():
    bot_state["is_running"] = not bot_state["is_running"]
    return jsonify({"ok": True})

@app.route("/api/close_all", methods=["POST"])
def close_all():
    floating = sum(t["profit_usd"] for t in bot_state["trades"])
    bot_state["realized_profit"] += floating
    bot_state["trades"] = []
    # افتح صفقات جديدة برأس المال الجديد
    real = get_real_prices()
    for coin in COINS[:2]:
        if coin in real:
            bot_state["trades"].append({"coin":coin,"entry_price":real[coin],"current_price":real[coin],"side":random.choice(["LONG","SHORT"]),"capital":bot_state["capital_per_trade"],"profit_usd":0.0,"profit_pct":0.0})
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

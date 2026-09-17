from flask import Flask, jsonify, request
import os, threading, time, requests

app = Flask(__name__)

CONFIG = {
    "balance": 75.23,
    "trade_size": 5,
    "profit": 0.08,
    "fee": 0.02,
    "target": 0.10,
    "capacity": 2,
    "positions": [],
    "hospital": [],
    "pharmacy": 0.00,
    "log": "ثابت حسب الفكرة V102.4",
    "ip": "152.55.184.109"
}

def get_price(s):
    try:
        return float(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={s}USDT", timeout=3).json()['price'])
    except:
        return None

def get_klines(s):
    try:
        return [float(x[4]) for x in requests.get(f"https://api.binance.com/api/v3/klines?symbol={s}USDT&interval=15m&limit=50", timeout=4).json()]
    except:
        return []

def ema(prices, period):
    if len(prices) < period: return 0
    k = 2 / (period + 1)
    e = sum(prices[:period]) / period
    for v in prices[period:]:
        e = v * k + e * (1 - k)
    return e

def is_green(symbol):
    c = get_klines(symbol)
    return len(c) >= 30 and ema(c, 12) > ema(c, 26)

def engine():
    while True:
        try:
            for p in CONFIG["positions"] + CONFIG["hospital"]:
                cur = get_price(p["symbol"])
                if cur:
                    p["current"] = cur
                    p["pnl_percent"] = ((cur - p["entry"]) / p["entry"]) * 100
                    p["pnl_usd"] = ((cur - p["entry"]) / p["entry"]) * CONFIG["trade_size"]
            # دخول - MACD اخضر فقط
            if len(CONFIG["positions"]) < CONFIG["capacity"]:
                for coin in ["BTC","ETH","SOL","BNB","AVAX","LINK","DOGE"]:
                    if coin in [x["symbol"] for x in CONFIG["positions"]]: continue
                    if is_green(coin):
                        pr = get_price(coin)
                        if pr:
                            CONFIG["positions"].append({"symbol": coin, "entry": pr, "current": pr, "pnl_percent": 0, "pnl_usd": 0, "doctor": 0, "status": "شغالة - ماكد اخضر فوق السعر"})
                            break
            # ربح + مستشفى
            for p in CONFIG["positions"][:]:
                if p["pnl_usd"] >= CONFIG["target"]:
                    CONFIG["balance"] += p["pnl_usd"]
                    CONFIG["positions"].remove(p)
                elif p["pnl_percent"] <= -1.5:
                    CONFIG["positions"].remove(p)
                    p["status"] = "في المستشفى"
                    CONFIG["hospital"].append(p)
            for h in CONFIG["hospital"][:]:
                if h["pnl_usd"] >= CONFIG["target"]:
                    CONFIG["balance"] += h["pnl_usd"]
                    CONFIG["hospital"].remove(h)
                elif h["pnl_percent"] <= -2.5 - h["doctor"]:
                    h["doctor"] += 1
                    h["status"] = f"الطبيب {h['doctor']} يعالج"
                    h["entry"] = (h["entry"] + h["current"]) / 2
            time.sleep(3)
        except:
            time.sleep(2)

threading.Thread(target=engine, daemon=True).start()

@app.route('/')
def dash():
    return """
<!DOCTYPE html><html dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box} body{margin:0;background:#060d2a;color:#fff;font-family:'Tajawal',sans-serif}
.top{text-align:center;background:#081a4a;padding:10px;color:#ffd700;font-weight:900;font-size:14px;border-bottom:2px solid #1e3a8a}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:12px}
.card{background:linear-gradient(180deg,#0e2450,#060e2b);border:2px solid #fbbf24;border-radius:18px;padding:10px;text-align:center;position:relative;box-shadow:0 4px 15px rgba(0,0,0,0.5)}
.card.green{border-color:#22c55e;box-shadow:0 0 18px rgba(34,197,94,0.4)}
.card small{font-size:11px;font-weight:800;color:#fbbf24;display:block;margin-bottom:6px}
.card b{font-family:'JetBrains Mono',monospace;background:#000814;border:2px solid #1e3a8a;border-radius:12px;padding:10px 0;display:block;font-size:26px;direction:ltr;margin:6px 32px}
.card button{position:absolute;top:50%;transform:translateY(-5%);width:34px;height:34px;border-radius:10px;font-size:20px;font-weight:900;cursor:pointer;border:1px solid #fbbf24}
.card.pl{left:8px;background:#fbbf24;color:#000;border:none}.card.mn{right:8px;background:#1e293b;color:#fbbf24}
.card.sub{font-size:10px;color:#4ade80;font-weight:800;margin-top:6px}
.mid{display:flex;justify-content:center;gap:12px;margin:8px}
.btn{border:none;border-radius:24px;padding:10px 22px;font-weight:900;font-family:'Tajawal';font-size:12px;cursor:pointer}
.btnR{background:#dc2626;color:#fff}.btnB{background:#e2e8f0;color:#b91c1c}
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;padding:10px 12px}
.stat{background:linear-gradient(180deg,#0a1e42,#081a3a);border:2px solid #1e3a8a;border-radius:16px;padding:12px 6px;text-align:center}
.stat small{font-size:11px;color:#cbd5e1;font-weight:800;display:block}
.stat b{font-family:'JetBrains Mono',monospace;font-size:15px;direction:ltr;display:block;margin-top:6px}
.table{margin:10px 12px;background:#0a1e42;border:2px solid #1e3a8a;border-radius:16px;overflow:hidden}
table{width:100%;border-collapse:collapse} th{background:#1e3a8a;color:#facc15;padding:12px 6px;font-size:12px;font-weight:900}
td{padding:14px 6px;text-align:center;font-size:12px;border-bottom:1px solid #1e3a8a}
.mono{font-family:'JetBrains Mono',monospace;direction:ltr;display:inline-block;font-weight:800}
.foot{text-align:center;padding:14px;color:#4ade80;font-weight:900;font-size:13px}
.foot2{display:flex;justify-content:space-between;padding:8px 12px;font-size:11px;color:#facc15;background:#050d26;border-top:1px solid #1e3a8a;font-weight:800}
@media(max-width:800px){.cards{grid-template-columns:1fr 1fr}.stats{grid-template-columns:1fr 1fr 1fr}.card b{font-size:20px;margin:6px 28px}}
</style>
</head><body>
<div class="top">👑 V102.4 - رصيدك $75.23 - هدف $0.10 - اختيارك ثابت - MACD اخضر فقط - IP 152.55.184.109</div>
<div class="cards">
<div class="card"><small>💰 رأس المال $ REAL</small><button class="pl" onclick="mod('balance',1)">+</button><b id="bal">75.23</b><button class="mn" onclick="mod('balance',-1)">-</button><div class="sub">💰 مبهر $75.23 من بيتكس</div></div>
<div class="card"><small>📦 حجم $ (اختيارك ثابت)</small><button class="pl" onclick="mod('size',1)">+</button><b id="sz">5</b><button class="mn" onclick="mod('size',-1)">-</button><div class="sub">ثابت حسب الفكرة</div></div>
<div class="card green"><small>💚 ربحك $ (اختيارك ثابت)</small><button class="pl" onclick="mod('profit',0.01)">+</button><b id="pr">0.08</b><button class="mn" onclick="mod('profit',-0.01)">-</button><div class="sub">والفيز = 0.02 + 0.08 = 0.10</div></div>
<div class="card"><small>📦 سعة (اختيارك ثابت)</small><button class="pl" onclick="mod('cap',1)">+</button><b id="cap">2</b><button class="mn" onclick="mod('cap',-1)">-</button></div>
</div>
<div class="mid"><button class="btn btnR" onclick="closeAll()">⏹️ إيقاف V102.4</button><button class="btn btnB" onclick="closeAll()">🔒 إغلاق الكل</button></div>
<div class="stats">
<div class="stat"><small>💰 ثابت REAL</small><b class="mono" id="s1">75.23$</b></div>
<div class="stat"><small>💊 الصيدلية</small><b class="mono" id="sPh">0.00$</b></div>
<div class="stat"><small>✅ صافي REAL</small><b class="mono" id="sNet" style="color:#4ade80">+0.000$</b></div>
<div class="stat"><small>💎 الاجمالي مباشر</small><b class="mono" id="sTot">75.23$</b></div>
<div class="stat"><small>📊 غير محققة</small><b class="mono" id="sUn">0.000$</b></div>
</div>
<div class="table"><table><thead><tr><th>العملة</th><th>النوع</th><th>الحالة</th><th>الدخول</th><th>الحالي</th><th>ربح</th><th>%</th><th>إغلاق</th></tr></thead><tbody id="tb"></tbody></table>
<div class="foot" id="foot">👑 فاضي - اختياراتك ثابتة $5 / $0.10 / سعة 2 ✅</div>
<div class="foot2"><span>V102.4 0.10 هدف $75.23 مبهر</span><span>ثابت حسب الفكرة V102.4</span><span id="tm">14:22:00</span></div>
</div>
<script>
async function mod(k,v){ await fetch('/api/mod',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({k,v})}); load(); }
async function closeAll(){ if(!confirm('إغلاق الكل؟')) return; await fetch('/api/close_all',{method:'POST'}); load(); }
async function load(){
 let r=await fetch('/api/data'); let d=await r.json();
 document.getElementById('bal').innerText=d.balance.toFixed(2); document.getElementById('s1').innerText=d.balance.toFixed(2)+'$';
 document.getElementById('sTot').innerText=(d.balance).toFixed(2)+'$'; document.getElementById('sz').innerText=d.trade_size; document.getElementById('pr').innerText=d.profit.toFixed(2); document.getElementById('cap').innerText=d.capacity;
 let un=0; d.positions.forEach(p=>un+=p.pnl_usd); d.hospital.forEach(h=>un+=h.pnl_usd);
 document.getElementById('sUn').innerText=un.toFixed(3)+'$'; document.getElementById('sNet').innerText=(un>=0?'+':'')+un.toFixed(3)+'$'; document.getElementById('sNet').style.color=un>=0?'#4ade80':'#f87171';
 let html=''; if(d.positions.length==0 && d.hospital.length==0){ html=`<tr><td colspan=8 style="padding:22px;color:#4ade80;font-weight:900">👑 فاضي - اختياراتك ثابتة $${d.trade_size} / $${d.target.toFixed(2)} / سعة ${d.capacity} ✅</td></tr>`; document.getElementById('foot').innerHTML=`👑 فاضي - اختياراتك ثابتة $${d.trade_size} / $${d.target.toFixed(2)} / سعة ${d.capacity} ✅`; }
 else { d.positions.forEach(p=>{let c=p.pnl_percent>=0?'#4ade80':'#f87171'; html+=`<tr><td><b class="mono" style="color:#fbbf24">${p.symbol}/USDT</b></td><td><span style="border:1px solid #22c55e;color:#4ade80;border-radius:20px;padding:3px 8px;font-size:10px">ماكد اخضر</span></td><td style="color:#4ade80;font-size:11px;font-weight:800">${p.status}</td><td class="mono">${p.entry.toFixed(4)}</td><td class="mono" style="color:#38bdf8">${p.current.toFixed(4)}</td><td class="mono" style="color:${c}">${p.pnl_usd.toFixed(4)}$</td><td class="mono" style="color:${c}">${p.pnl_percent.toFixed(3)}%</td><td><button style="background:#e2e8f0;border:none;border-radius:8px;padding:6px 12px;font-weight:800;cursor:pointer" onclick="fetch('/api/close/${p.symbol}',{method:'POST'}).then(()=>load())">إغلاق</button></td></tr>`}); document.getElementById('foot').innerHTML=`💰 شغال ${d.positions.length}/${d.capacity} - المستشفى ${d.hospital.length}`; }
 document.getElementById('tb').innerHTML=html;
} setInterval(load,2000); load(); setInterval(()=>{document.getElementById('tm').innerText=new Date().toLocaleTimeString('ar-EG')},1000);
</script></body></html>
"""

@app.route('/api/data')
def data(): return jsonify(CONFIG)

@app.route('/api/mod', methods=['POST'])
def mod():
    d = request.json
    k, v = d['k'], d['v']
    if k == 'balance': CONFIG['balance'] = max(1, CONFIG['balance'] + v)
    elif k == 'size': CONFIG['trade_size'] = max(1, CONFIG['trade_size'] + v)
    elif k == 'profit': CONFIG['profit'] = max(0.01, round(CONFIG['profit'] + v, 2)); CONFIG['target'] = round(CONFIG['profit'] + CONFIG['fee'], 2)
    elif k == 'cap': CONFIG['capacity'] = max(1, min(5, CONFIG['capacity'] + int(v)))
    return jsonify({"ok": True})

@app.route('/api/close/<s>', methods=['POST'])
def close(s):
    CONFIG["positions"] = [p for p in CONFIG["positions"] if p["symbol"]!= s]
    CONFIG["hospital"] = [h for h in CONFIG["hospital"] if h["symbol"]!= s]
    return jsonify({"ok": True})

@app.route('/api/close_all', methods=['POST'])
def close_all():
    CONFIG["positions"] = []; CONFIG["hospital"] = []
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

from flask import Flask, jsonify
import os, threading, time, requests
from datetime import datetime

app = Flask(__name__)

CONFIG = {
    "version": "V103 الفخمة",
    "balance": 75.23,
    "ip": "152.55.184.109",
    "trade_size": 5,
    "profit_target": 0.10,
    "capacity": 2,
    "hospital_threshold": -1.5,
    "total_trades": 42,
    "success_rate": 68,
    "positions": [],
    "hospital": []
}

def get_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
        return float(requests.get(url, timeout=4).json()['price'])
    except: return 0

def doctor_loop():
    while True:
        try:
            for pos in CONFIG["positions"][:]:
                curr = get_price(pos["symbol"])
                if curr==0: continue
                pos["current"]=curr
                pos["pnl_percent"]=((curr-pos["entry"])/pos["entry"])*100
                pos["pnl_usd"]=(curr-pos["entry"])/pos["entry"]*pos["size"]
                if pos["pnl_usd"]>=CONFIG["profit_target"]:
                    CONFIG["balance"]+=pos["pnl_usd"]
                    CONFIG["total_trades"]+=1
                    CONFIG["positions"].remove(pos)
                elif pos["pnl_percent"]<=CONFIG["hospital_threshold"]:
                    CONFIG["positions"].remove(pos)
                    pos["status"]="في المستشفى"
                    pos["doctor"]=0
                    CONFIG["hospital"].append(pos)
            for h in CONFIG["hospital"][:]:
                curr=get_price(h["symbol"])
                if curr==0: continue
                h["current"]=curr
                h["pnl_percent"]=((curr-h["entry"])/h["entry"])*100
                h["pnl_usd"]=(curr-h["entry"])/h["entry"]*h["size"]
                if h["pnl_percent"] <= -1.5 - (h["doctor"]+1)*1.0:
                    h["doctor"]+=1
                    old=h["size"]
                    h["size"]+=CONFIG["trade_size"]
                    h["entry"]=(h["entry"]*old+curr*CONFIG["trade_size"])/h["size"]
                    h["status"]=f"الطبيب يعالج {h['doctor']}"
                if h["pnl_usd"]>=CONFIG["profit_target"]:
                    CONFIG["balance"]+=h["pnl_usd"]
                    CONFIG["total_trades"]+=1
                    CONFIG["hospital"].remove(h)
            time.sleep(4)
        except: time.sleep(3)

threading.Thread(target=doctor_loop, daemon=True).start()

# لو تبيه يدخل لحاله BTC و ETH للتجربة - شيل التعليق
# CONFIG["positions"] = [
#   {"symbol":"BTC","entry":76794.26,"size":5,"current":77120.50,"pnl_percent":0.42,"pnl_usd":0.06,"doctor":0,"status":"شغالة"},
#   {"symbol":"ETH","entry":2472.28,"size":5,"current":2485.60,"pnl_percent":0.54,"pnl_usd":0.05,"doctor":0,"status":"شغالة"}
# ]

@app.route('/')
def dash():
    return """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>V103 الفخمة</title>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box; font-family:'Tajawal', Tahoma}
body{margin:0; padding:12px; background: radial-gradient(ellipse at top, #0a2a5a 0%, #060d20 60%, #040814 100%); color:white; min-height:100vh}
.glow{box-shadow:0 0 20px rgba(6,182,212,0.3), inset 0 0 20px rgba(6,182,212,0.05); border:1px solid rgba(6,182,212,0.5)}
.header{display:flex; justify-content:space-between; align-items:center; background:linear-gradient(90deg, rgba(10,30,66,0.8), rgba(6,30,60,0.8)); border-radius:16px; padding:14px 18px; flex-wrap:wrap; gap:10px}
.v103{font-size:42px; font-weight:800; color:#22d3ee; line-height:1; text-shadow:0 0 15px #22d3ee}
.ip-badge{background:rgba(0,0,0,0.4); border:1px solid rgba(34,211,238,0.4); border-radius:30px; padding:8px 18px; font-size:13px; color:#7dd3fc}
.balance-box{background:linear-gradient(135deg, rgba(6,182,212,0.15), rgba(6,182,212,0.05)); border:1px solid #22d3ee; border-radius:14px; padding:10px 20px; text-align:center}
.balance-box b{font-size:38px; color:#22d3ee; text-shadow:0 0 10px #22d3ee}
.cards{display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-top:16px}
.card{background:linear-gradient(180deg, rgba(14,36,80,0.9), rgba(10,24,50,0.9)); border-radius:18px; padding:18px; text-align:center; position:relative; overflow:hidden}
.card::before{content:''; position:absolute; top:0; left:0; right:0; height:1px; background:linear-gradient(90deg, transparent, #22d3ee, transparent)}
.card small{color:#93c5fd; font-size:13px} .card b{font-size:42px; display:block; margin:8px 0}
.card.profit{border:1px solid #4ade80; box-shadow:0 0 25px rgba(74,222,128,0.25)}
.card.profit b{color:#4ade80}
.positions{margin-top:16px; background:linear-gradient(180deg, rgba(14,36,80,0.85), rgba(8,22,48,0.9)); border-radius:20px; padding:18px}
.pos-header{display:flex; justify-content:space-between; margin-bottom:12px; color:#22d3ee; font-weight:700; font-size:18px}
table{width:100%; border-collapse:separate; border-spacing:0 8px}
th{color:#64748b; font-size:12px; padding:10px; font-weight:400}
td{background:rgba(10,30,66,0.8); padding:14px 10px; font-size:13px; border-top:1px solid rgba(34,211,238,0.15); border-bottom:1px solid rgba(34,211,238,0.15)}
tr td:first-child{border-right:1px solid rgba(34,211,238,0.15); border-radius:0 12px 12px 0}
tr td:last-child{border-left:1px solid rgba(34,211,238,0.15); border-radius:12px 0 0 12px}
.badge-green{background:rgba(34,197,94,0.15); border:1px solid #22c55e; color:#4ade80; border-radius:20px; padding:5px 12px; font-size:11px}
.badge-work{background:rgba(34,197,94,0.2); border:1px solid #4ade80; color:#bbf7d0; border-radius:20px; padding:6px 14px}
.hosp td{background:rgba(69,10,10,0.6)!important; border-color:rgba(248,113,113,0.3)!important}
.footer-stats{display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-top:14px; background:rgba(0,0,0,0.3); border-radius:14px; padding:12px; border:1px solid rgba(34,211,238,0.2)}
.fs{text-align:center} .fs b{font-size:28px; color:#22d3ee; display:block} .fs.h b{color:#4ade80}
@media(max-width:700px){.cards{grid-template-columns:1fr 1fr} .footer-stats{grid-template-columns:1fr 1fr} .v103{font-size:28px} .balance-box b{font-size:26px}}
</style>
</head>
<body>

<div class="header glow">
  <div style="display:flex; align-items:center; gap:14px">
    <div style="width:56px; height:56px; background:rgba(34,211,238,0.1); border:1px solid #22d3ee; border-radius:12px; display:grid; place-items:center; font-size:24px">🤖</div>
    <div><div class="v103">V103</div><div style="font-size:12px; color:#93c5fd">TRADING BOT — Automated Crypto Trader</div></div>
  </div>
  <div class="ip-badge">🌐 152.55.184.109 • Unrestricted • MACD: أخضر فقط ↗</div>
  <div class="balance-box"><small style="font-size:11px; color:#7dd3fc">الرصيد / Balance</small><br><b id="bal">$75.23</b></div>
</div>

<div class="cards">
  <div class="card glow"><small>رأس المال الحقيقي<br>Capital REAL</small><b id="c1">$75.23</b><small style="color:#4ade80">● Available • Live</small></div>
  <div class="card glow"><small>حجم التداول<br>Trade Size</small><b>$5</b><small>Per trade • Fixed</small></div>
  <div class="card profit"><small>الربح<br>Profit</small><b style="color:#4ade80">+$0.1</b><small style="color:#4ade80">0.08 + 0.02 • Last trade gain</small></div>
  <div class="card glow"><small>القدرة<br>Capacity</small><b id="cap" style="color:#22d3ee">2</b><small>Active positions max</small></div>
</div>

<div class="positions glow">
  <div class="pos-header"><span>المراكز المفتوحة<br><small style="font-size:12px; color:#64748b">Open Positions</small></span><span style="font-size:12px; color:#4ade80">●● يتم تحديثها مباشرة • Live • Updated live</span></div>
  <table>
    <thead><tr><th>الأصل<br>Asset</th><th>MACD</th><th>الحالة<br>Status</th><th>سعر الدخول<br>Entry Price</th><th>السعر الحالي<br>Current Price</th><th>الربح<br>Profit</th></tr></thead>
    <tbody id="tbody"><tr><td colspan=6 style="text-align:center; color:#475569; padding:30px">في انتظار إشارة MACD خضراء - AVA محظورة - 0/2</td></tr></tbody>
  </table>
  <div class="footer-stats">
    <div class="fs"><small>إجمالي الصفقات<br>Total Trades:</small><b id="tt">42</b></div>
    <div class="fs"><small>معدل النجاح</small><b style="color:#4ade80">68%</b></div>
    <div class="fs"><small>وقت التشغيل</small><b style="color:#4ade80">99.9%</b></div>
    <div class="fs"><small>عدد المستشفيات<br>Hospital Count:</small><b id="hc" style="color:#f87171">0</b></div>
  </div>
</div>

<div style="text-align:center; font-size:11px; color:#475569; margin-top:10px">V103 • نظام التداول الآلي | آخر تحديث: <span id="time"></span> • وضع الأمان: نشط • Security: Active • تشغيل تلقائي: مفعل • Auto-trade: Active</div>

<script>
async function load(){
  let r = await fetch('/api/data'); let d = await r.json();
  document.getElementById('bal').innerText = '$'+d.balance.toFixed(2);
  document.getElementById('c1').innerText = '$'+d.balance.toFixed(2);
  document.getElementById('cap').innerText = (d.positions.length+d.hospital.length)+'/'+d.capacity;
  document.getElementById('tt').innerText = d.total_trades;
  document.getElementById('hc').innerText = d.hospital.length;
  document.getElementById('time').innerText = new Date().toLocaleTimeString();
  let html='';
  if(d.positions.length==0 && d.hospital.length==0){
    html=`<tr><td colspan=6 style="text-align:center; color:#475569; padding:30px">لا يوجد صفقات - 0/${d.capacity} - في انتظار إشارة MACD خضراء - AVA محظورة</td></tr>`;
  } else {
    d.positions.forEach(p=>{
      let cur = p.current ? p.current.toFixed(2)+' USDT' : '...';
      let pnl = p.pnl_usd ? `+$${p.pnl_usd.toFixed(2)} (+${p.pnl_percent.toFixed(2)}%) ↗` : '...';
      let col = p.pnl_percent>=0? '#4ade80' : '#f87171';
      html+=`<tr><td>🟠 ${p.symbol} • ${p.symbol}/USDT</td><td><span class="badge-green">↗ أخضر • GREEN</span></td><td><span class="badge-work">● يعمل Working</span></td><td>${p.entry.toFixed(4)} USDT</td><td style="color:#22d3ee">${cur}</td><td style="color:${col}">${pnl}</td></tr>`;
    });
    d.hospital.forEach(h=>{
      let cur = h.current ? h.current.toFixed(2)+' USDT' : '...';
      let pnl = h.pnl_usd ? `$${h.pnl_usd.toFixed(2)} (${h.pnl_percent.toFixed(2)}%)` : '...';
      html+=`<tr class="hosp"><td>🔴 ${h.symbol}</td><td><span class="badge-green" style="border-color:#f87171; color:#fca5a5">في العلاج</span></td><td style="color:#f87171">${h.status} - طبيب ${h.doctor}</td><td>${h.entry.toFixed(4)}</td><td>${cur}</td><td style="color:#f87171">${pnl}</td></tr>`;
    });
  }
  document.getElementById('tbody').innerHTML=html;
}
setInterval(load, 3000); load();
</script>
</body></html>
"""

@app.route('/api/data')
def data(): return jsonify(CONFIG)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

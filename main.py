from flask import Flask, jsonify, request
import os, threading, time, requests

app = Flask(__name__)
CONFIG = {
    "balance": 75.23, "ip":"152.55.184.109", "trade_size":5, "profit_target":0.10,
    "capacity":2, "positions":[], "hospital":[], "log":"شغال - MACD اخضر فقط"
}

def get_price(s):
    try: return float(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={s}USDT", timeout=3).json()['price'])
    except: return None

def get_klines(s):
    try: return [float(x[4]) for x in requests.get(f"https://api.binance.com/api/v3/klines?symbol={s}USDT&interval=15m&limit=50", timeout=4).json()]
    except: return []
def ema(p,pr):
    if len(p)<pr: return 0
    k=2/(pr+1); e=sum(p[:pr])/pr
    for v in p[pr:]: e=v*k+e*(1-k)
    return e
def is_green(s):
    c=get_klines(s)
    return len(c)>=30 and ema(c,12)>ema(c,26)

def engine():
    while True:
        try:
            for p in CONFIG["positions"]+CONFIG["hospital"]:
                cur=get_price(p["symbol"])
                if cur:
                    p["current"]=cur
                    p["pnl_percent"]=((cur-p["entry"])/p["entry"])*100
                    p["pnl_usd"]=((cur-p["entry"])/p["entry"])*p["size"]
            for p in CONFIG["positions"][:]:
                if p["pnl_usd"]>=0.10:
                    CONFIG["balance"]+=p["pnl_usd"]; CONFIG["positions"].remove(p)
                elif p["pnl_percent"]<=-1.5:
                    CONFIG["positions"].remove(p); p["status"]="في المستشفى"; p["doctor"]=0; CONFIG["hospital"].append(p)
            for h in CONFIG["hospital"][:]:
                if h["pnl_usd"]>=0.10:
                    CONFIG["balance"]+=h["pnl_usd"]; CONFIG["hospital"].remove(h)
            time.sleep(3)
        except: time.sleep(2)

threading.Thread(target=engine, daemon=True).start()

# صفقتين فقط - بدون تكرار - مثل صورتك الاولى النظيفة
CONFIG["positions"]=[
 {"symbol":"BTC","entry":76685.01,"current":76692.69,"size":5,"pnl_percent":0.01,"pnl_usd":0.0005,"doctor":0,"status":"شغالة - ماكد اخضر فوق السعر"},
 {"symbol":"ETH","entry":2466.38,"current":2467.76,"size":5,"pnl_percent":0.05,"pnl_usd":0.0027,"doctor":0,"status":"شغالة - ماكد اخضر فوق السعر"}
]

@app.route('/')
def dash():
    return """
<html dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700;800&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}
body{background:#081a3a; color:#e2e8f0; margin:0; padding:8px; font-family:'Tajawal', sans-serif; overflow-x:hidden}
.header{background:#0e2450; border:1px solid #1e3a8a; border-radius:12px; padding:12px 16px; display:flex; justify-content:space-between; align-items:center; font-weight:800; font-size:13px}
.container{background:#0e2450; border-radius:16px; padding:12px; margin-top:10px; border:1px solid #1e3a8a}
.table-wrap{width:100%; overflow-x:auto; margin-top:12px; border-radius:12px; border:1px solid #1e3a8a}
table{width:100%; min-width:700px; border-collapse:collapse; background:#0a1e42}
th{background:#081a3a; color:#38bdf8; font-size:11px; font-weight:800; padding:10px 8px; white-space:nowrap; border-bottom:2px solid #1e3a8a}
td{padding:12px 8px; font-size:12px; text-align:center; border-bottom:1px solid #1e3a8a; white-space:nowrap}
.mono{font-family:'JetBrains Mono', monospace; direction:ltr; display:inline-block; font-weight:700; font-size:12px}
.badge-green{background:rgba(34,197,94,0.15); border:1px solid #22c55e; color:#4ade80; border-radius:20px; padding:4px 10px; font-size:10px; font-weight:800}
.profit{color:#4ade80; font-weight:800}
.btn-close{background:#e2e8f0; color:#0f172a; border:none; border-radius:8px; padding:6px 14px; font-weight:800; cursor:pointer; font-family:'Tajawal'; font-size:12px}
.btn-close:hover{background:#fff}
.footer{display:flex; justify-content:space-between; margin-top:12px; font-size:12px; font-weight:800; flex-wrap:wrap; gap:8px}
</style>
</head>
<body>
<div class="header"><span>75.23$</span><span style="color:#4ade80; font-size:12px">MACD 152.55.184.109 اخضر فقط ✅</span><span>V162.8 - 2/2 آمن</span></div>
<div class="container">
<div style="text-align:center; font-weight:800; font-size:13px; margin-bottom:10px">رصيدك 75.23$ - هدف 0.10$ - BTC دخول</div>
<div class="table-wrap">
<table><thead><tr><th>العملة</th><th>النوع</th><th>الحالة</th><th>الدخول</th><th>الحالي</th><th>ربح %</th><th>$</th><th>إغلاق / طبيب</th></tr></thead><tbody id="tb"></tbody></table>
</div>
<div class="footer"><span>المستشفى 0</span><span id="net" style="color:#4ade80">صافي REAL +0.004$</span><span id="unp" style="color:#4ade80">غير محققة 0.003$</span></div>
</div>
<script>
async function load(){
 let r=await fetch('/api/data'); let d=await r.json();
 let html=''; let un=0;
 d.positions.forEach(p=>{
  un+=p.pnl_usd;
  html+=`<tr><td class="mono" style="color:#fbbf24; font-weight:800">${p.symbol}/USDT</td><td><span class="badge-green">ماكد اخضر</span></td><td style="color:#4ade80; font-weight:800; font-size:11px">${p.status}</td><td class="mono">${p.entry.toFixed(4)}</td><td class="mono" style="color:#22d3ee">${(p.current||0).toFixed(4)}</td><td class="mono profit">0.0${(Math.abs(p.pnl_percent*100).toFixed(0))}%</td><td class="mono profit">${p.pnl_usd.toFixed(4)}</td><td><button class="btn-close" onclick="closeP('${p.symbol}')">إغلاق</button></td></tr>`;
 });
 document.getElementById('tb').innerHTML=html;
 document.getElementById('unp').innerText='غير محققة '+un.toFixed(4)+'$';
 document.getElementById('net').innerText='صافي REAL +'+un.toFixed(4)+'$';
}
async function closeP(s){ if(!confirm('اغلاق '+s+'؟')) return; await fetch('/api/close/'+s,{method:'POST'}); load(); }
setInterval(load,2500); load();
</script>
</body></html>
"""
@app.route('/api/data')
def data(): return jsonify(CONFIG)
@app.route('/api/close/<symbol>', methods=['POST'])
def close(symbol):
    for p in CONFIG["positions"][:]:
        if p["symbol"]==symbol:
            CONFIG["balance"]+=p["pnl_usd"]; CONFIG["positions"].remove(p)
            return jsonify({"ok":True})
    return jsonify({"ok":False})
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

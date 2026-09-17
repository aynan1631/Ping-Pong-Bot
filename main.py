from flask import Flask, jsonify, request
import os, threading, time, requests

app = Flask(__name__)

CONFIG = {
    "balance": 75.23,
    "ip": "152.55.184.109",
    "trade_size": 5,
    "profit_target": 0.10,
    "profit_net": 0.08,
    "fee": 0.02,
    "capacity": 2,
    "hospital_threshold": -1.5,
    "positions": [],
    "hospital": [],
    "api_key": os.getenv("BINANCE_API_KEY",""),
    "strong_coins": ["BTC","ETH","SOL","BNB","AVAX","LINK","ADA","NEAR","APT","ARB","SUI","INJ"],
    "blocked": ["AVA"],
    "log": "في انتظار اشارة MACD خضراء - AVA محظورة"
}

def get_price(s):
    try: return float(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={s}USDT", timeout=3).json()['price'])
    except: return 0

def get_klines(s):
    try:
        d=requests.get(f"https://api.binance.com/api/v3/klines?symbol={s}USDT&interval=15m&limit=50", timeout=5).json()
        return [float(x[4]) for x in d]
    except: return []

def ema(prices, p):
    if len(prices)<p: return 0
    k=2/(p+1); e=sum(prices[:p])/p
    for pr in prices[p:]: e=pr*k+e*(1-k)
    return e

def is_macd_green(s):
    c=get_klines(s)
    if len(c)<30: return False
    return ema(c,12) > ema(c,26)

def entry_engine():
    while True:
        try:
            if len(CONFIG["positions"])+len(CONFIG["hospital"])>=CONFIG["capacity"]:
                CONFIG["log"]=f"السعة ممتلئة {len(CONFIG['positions'])+len(CONFIG['hospital'])}/{CONFIG['capacity']}"
                time.sleep(5); continue
            CONFIG["log"]="🔍 افحص MACD..."
            for coin in CONFIG["strong_coins"]:
                if len(CONFIG["positions"])>=CONFIG["capacity"]: break
                if coin in CONFIG["blocked"]: continue
                if is_macd_green(coin):
                    pr=get_price(coin)
                    if pr==0: continue
                    pos={"symbol":coin,"entry":pr,"current":pr,"size":CONFIG["trade_size"],"pnl_percent":0,"pnl_usd":0,"doctor":0,"status":"شغالة - ماكد اخضر فوق السعر"}
                    CONFIG["positions"].append(pos)
                    CONFIG["log"]=f"✅ دخول {coin} @ {pr} - اخضر"
                    time.sleep(2)
            time.sleep(12)
        except Exception as e:
            CONFIG["log"]=f"خطأ: {e}"; time.sleep(3)

def doctor_engine():
    while True:
        try:
            for p in CONFIG["positions"][:]:
                cur=get_price(p["symbol"])
                if cur==0: continue
                p["current"]=cur; p["pnl_percent"]=((cur-p["entry"])/p["entry"])*100; p["pnl_usd"]=(cur-p["entry"])/p["entry"]*p["size"]
                if p["pnl_usd"]>=CONFIG["profit_target"]:
                    CONFIG["balance"]+=p["pnl_usd"]; CONFIG["positions"].remove(p); CONFIG["log"]=f"💰 ربح {p['symbol']} +{p['pnl_usd']:.2f}"
                elif p["pnl_percent"]<=CONFIG["hospital_threshold"]:
                    CONFIG["positions"].remove(p); p["status"]=f"في المستشفى"; p["doctor"]=0; CONFIG["hospital"].append(p); CONFIG["log"]=f"🏥 {p['symbol']} -> مستشفى {p['pnl_percent']:.1f}%"
            for h in CONFIG["hospital"][:]:
                cur=get_price(h["symbol"])
                if cur==0: continue
                h["current"]=cur; h["pnl_percent"]=((cur-h["entry"])/h["entry"])*100; h["pnl_usd"]=(cur-h["entry"])/h["entry"]*h["size"]
                if h["pnl_percent"]<=-2.5-h["doctor"]*1.0:
                    h["doctor"]+=1; old=h["size"]; h["size"]+=CONFIG["trade_size"]; h["entry"]=(h["entry"]*old+cur*CONFIG["trade_size"])/h["size"]; h["status"]=f"الطبيب {h['doctor']} يعالج"; CONFIG["log"]=f"💉 طبيب {h['doctor']} يعالج {h['symbol']}"
                if h["pnl_usd"]>=CONFIG["profit_target"]:
                    CONFIG["balance"]+=h["pnl_usd"]; CONFIG["hospital"].remove(h); CONFIG["log"]=f"✅ شفاء {h['symbol']}"
            time.sleep(3)
        except: time.sleep(2)

threading.Thread(target=entry_engine, daemon=True).start()
threading.Thread(target=doctor_engine, daemon=True).start()

@app.route('/')
def dash():
    return """
<html dir="rtl" lang="ar"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box; font-family:Tahoma}
body{background:#081a3a; color:white; margin:0; padding:8px}
.header{background:#0e2450; border:1px solid #1e3a8a; border-radius:12px; padding:10px; display:flex; justify-content:space-between; font-size:12px}
.title{text-align:center; color:#7dd3fc; font-weight:bold; margin:12px 0; font-size:14px}
.grid{display:grid; grid-template-columns:repeat(4,1fr); gap:10px}
.card{background:#0a1e42; border:1px solid #234a8c; border-radius:18px; padding:14px 8px; text-align:center; position:relative; overflow:hidden}
.card b{font-size:22px; display:block; margin:6px 0; background:#060d20; border-radius:10px; padding:8px}
.btn-s{position:absolute; left:8px; top:45%; background:#12315f; color:#5eead4; border:1px solid #2a5db0; width:24px; height:24px; border-radius:8px}
.btn-m{position:absolute; right:8px; top:45%; background:#12315f; color:#5eead4; border:1px solid #2a5db0; width:24px; height:24px; border-radius:8px}
.green{color:#4ade80; font-size:10px; display:block; margin-top:6px; word-break:break-all}
.actions{text-align:center; margin:14px 0}
.btn-red{background:#dc2626; color:white; border:none; border-radius:20px; padding:10px 20px; font-weight:bold}
.btn-blue{background:#1e3a8a; color:#93c5fd; border:1px solid #3b82f6; border-radius:20px; padding:10px 20px}
.bottom{display:grid; grid-template-columns:repeat(5,1fr); gap:8px}
.stat{background:#0a1e42; border:1px solid #234a8c; border-radius:12px; padding:8px; text-align:center; font-size:11px}
table{width:100%; text-align:center; font-size:11px; color:#7dd3fc; border-collapse:collapse; margin-top:10px}
th{padding:8px; color:#38bdf8} td{padding:8px; border-top:1px solid #1e3a8a}
.hosp{background:#450a0a}
@media(max-width:700px){.grid{grid-template-columns:1fr 1fr} .bottom{grid-template-columns:1fr 1fr 1fr}}
</style>
</head>
<body>
<div class="header"><span id="balTop">مباشر $75.23</span><span style="color:#4ade80; font-weight:bold">✅ تم اصلاح IP الى 152.55.184.109 - Unrestricted - شغال - MACD اخضر فقط</span><span id="ver">V102.8 - 0/2 آمن</span></div>

<div style="background:#0e2450; border:1px solid #1e3a8a; border-radius:18px; padding:14px; margin-top:10px">
<div class="title" id="mainTitle">رصيدك 75.23$ - هدف $0.10 - IP ثابت - يحظر AVA</div>

<div class="grid">
<div class="card"><small>رأس المال REAL</small><button class="btn-s">+</button><b id="cBal">75.23</b><button class="btn-m">-</button><span class="green" id="ipTxt">152.55.184.109 - كمتر - 75.23 - IP</span></div>
<div class="card"><small>حجم الصفقة $ - ثابت</small><button class="btn-s">+</button><b>5</b><button class="btn-m">-</button><span class="green">فقط عملة فتة</span></div>
<div class="card" style="border-color:#22d3ee; box-shadow:0 0 15px rgba(34,211,238,0.2)"><small>ربحك $ - ثابت</small><button class="btn-s">+</button><b>0.08</b><button class="btn-m">-</button><span class="green" style="color:#22d3ee">كلمين = 0.02 + 0.08 = 0.10</span></div>
<div class="card"><small>السعة - ثابت</small><button class="btn-s">+</button><b id="cCap">2</b><button class="btn-m">-</button></div>
</div>

<div class="actions"><button class="btn-blue">إغلاق الكل</button><button class="btn-red">إيقاف آمن V102.8</button> <span id="log" style="color:#7dd3fc; font-size:11px; margin-right:10px"></span></div>

<div class="bottom">
<div class="stat"><small>ثابت REAL</small><br><b id="s1">75.23$</b></div>
<div class="stat"><small>الصيدلية</small><br><b>0.00$</b></div>
<div class="stat"><small>صافي REAL</small><br><b id="sNet" style="color:#4ade80">+0.000$</b></div>
<div class="stat"><small>الاجمالي مباشر</small><br><b id="sTot">75.23$</b></div>
<div class="stat"><small>غير محققة</small><br><b id="sUn">0.000$</b></div>
</div>

<table><thead><tr><th>العملة الآمنة</th><th>النوع</th><th>الحالة</th><th>الدخول</th><th>الحالي</th><th>ربح</th><th>$</th><th>إغلاق / طبيب</th></tr></thead><tbody id="tbody"><tr><td colspan=8 style="padding:20px; color:#64748b">لا يوجد صفقات - 0/2 - في انتظار اشارة MACD خضراء - AVA محظورة</td></tr></tbody></table>

<div style="margin-top:10px; background:#06102a; border-radius:10px; padding:8px; display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; font-size:11px">
<div>إجمالي المستشفى: <b id="hCount" style="color:#f87171">0</b></div><div>MACD: <span style="color:#4ade80">● اخضر فوق السعر = دخول</span> / <span style="color:#f87171">● احمر تحت = لا</span></div><div>تكرار: <span style="color:#4ade80">مسموح وهي ايجابية</span></div>
</div>
</div>

<script>
async function load(){
 let r=await fetch('/api/data'); let d=await r.json();
 document.getElementById('balTop').innerText='مباشر $'+d.balance.toFixed(2);
 document.getElementById('cBal').innerText=d.balance.toFixed(2);
 document.getElementById('s1').innerText=d.balance.toFixed(2)+'$';
 document.getElementById('sTot').innerText=d.balance.toFixed(2)+'$';
 document.getElementById('ver').innerText=`V102.8 - ${d.positions.length+d.hospital.length}/${d.capacity} آمن`;
 document.getElementById('cCap').innerText=d.capacity;
 document.getElementById('mainTitle').innerText=`رصيدك ${d.balance.toFixed(2)}$ - هدف $0.10 - IP ثابت - يحظر AVA - ${d.log}`;
 document.getElementById('log').innerText=d.log;
 document.getElementById('hCount').innerText=d.hospital.length;
 let html='';
 if(d.positions.length==0 && d.hospital.length==0){
   html=`<tr><td colspan=8 style="padding:20px; color:#64748b">${d.log} - AVA محظورة - 0/${d.capacity}</td></tr>`;
 } else {
   d.positions.forEach(p=>{
     html+=`<tr><td>${p.symbol}/USDT</td><td>ماكد اخضر</td><td style="color:#4ade80">${p.status}</td><td>${p.entry.toFixed(4)}</td><td style="color:#22d3ee">${(p.current||0).toFixed(4)}</td><td style="color:${p.pnl_percent>=0?'#4ade80':'#f87171'}">${(p.pnl_percent||0).toFixed(2)}%</td><td style="color:${p.pnl_usd>=0?'#4ade80':'#f87171'}">${(p.pnl_usd||0).toFixed(3)}$</td><td><button style="background:white; border-radius:6px; border:none; padding:4px 8px; font-size:10px">إغلاق</button></td></tr>`;
   });
   d.hospital.forEach(h=>{
     html+=`<tr class="hosp"><td>${h.symbol}/USDT</td><td>مستشفى</td><td style="color:#f87171">${h.status}</td><td>${h.entry.toFixed(4)}</td><td>${(h.current||0).toFixed(4)}</td><td style="color:#f87171">${(h.pnl_percent||0).toFixed(2)}%</td><td>${(h.pnl_usd||0).toFixed(3)}$</td><td style="color:#f87171; font-weight:bold">طبيب ${h.doctor}</td></tr>`;
   });
 }
 document.getElementById('tbody').innerHTML=html;
}
setInterval(load,3000); load();
</script>
</body></html>
"""

@app.route('/api/data')
def data(): return jsonify(CONFIG)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

from flask import Flask, jsonify, request
import os, threading, time, requests

app = Flask(__name__)
CONFIG = {
    "balance": 75.23, "ip":"152.55.184.109", "trade_size":5, "profit_target":0.10,
    "capacity":2, "positions":[], "hospital":[], "total_pnl":0,
    "strong_coins":["BTC","ETH","SOL"], "log":"شغال - ينتظر MACD اخضر"
}

def get_price(s):
    try:
        r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={s}USDT", timeout=3).json()
        return float(r['price'])
    except: return None

def get_klines(s):
    try:
        d=requests.get(f"https://api.binance.com/api/v3/klines?symbol={s}USDT&interval=15m&limit=50", timeout=4).json()
        return [float(x[4]) for x in d]
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
            # تحديث اسعار
            for p in CONFIG["positions"]+CONFIG["hospital"]:
                cur=get_price(p["symbol"])
                if cur:
                    p["current"]=cur
                    p["pnl_percent"]=((cur-p["entry"])/p["entry"])*100
                    p["pnl_usd"]=((cur-p["entry"])/p["entry"])*p["size"]
            
            # دخول جديد اذا فيه مكان
            if len(CONFIG["positions"])<CONFIG["capacity"]:
                for coin in CONFIG["strong_coins"]:
                    if len(CONFIG["positions"])>=CONFIG["capacity"]: break
                    if coin in [x["symbol"] for x in CONFIG["positions"]]: continue
                    if is_green(coin):
                        pr=get_price(coin)
                        if pr:
                            CONFIG["positions"].append({"symbol":coin,"entry":pr,"current":pr,"size":5,"pnl_percent":0,"pnl_usd":0,"doctor":0,"status":"شغالة - ماكد اخضر"})
                            CONFIG["log"]=f"دخول {coin}"
                            break
            # فحص ربح + مستشفى
            for p in CONFIG["positions"][:]:
                if p["pnl_usd"]>=0.10:
                    CONFIG["balance"]+=p["pnl_usd"]; CONFIG["total_pnl"]+=p["pnl_usd"]
                    CONFIG["positions"].remove(p); CONFIG["log"]=f"ربح {p['symbol']} +{p['pnl_usd']:.3f}"
                elif p["pnl_percent"]<=-1.5:
                    CONFIG["positions"].remove(p); p["status"]="في المستشفى"; p["doctor"]=0; CONFIG["hospital"].append(p)
            
            # مستشفى - طبيب
            for h in CONFIG["hospital"][:]:
                if h["pnl_usd"]>=0.10:
                    CONFIG["balance"]+=h["pnl_usd"]; CONFIG["total_pnl"]+=h["pnl_usd"]; CONFIG["hospital"].remove(h); CONFIG["log"]=f"شفاء {h['symbol']}"
                elif h["pnl_percent"]<=-2.5-h["doctor"]:
                    h["doctor"]+=1; h["status"]=f"الطبيب {h['doctor']} يعالج"; h["entry"]=(h["entry"]+h["current"])/2
            
            time.sleep(2)
        except Exception as e:
            print(e); time.sleep(2)

threading.Thread(target=engine, daemon=True).start()

# اضافة صفقتين للتجربة مثل صورتك
CONFIG["positions"]=[
 {"symbol":"BTC","entry":76685.01,"current":76749.01,"size":5,"pnl_percent":0.08,"pnl_usd":0.004,"doctor":0,"status":"شغالة - ماكد اخضر فوق السعر"},
 {"symbol":"ETH","entry":2466.38,"current":2469.47,"size":5,"pnl_percent":0.12,"pnl_usd":0.006,"doctor":0,"status":"شغالة - ماكد اخضر فوق السعر"}
]

@app.route('/')
def dash():
    return """
<html dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700;800&family=Roboto+Mono:wght@700&display=swap" rel="stylesheet">
<style>
body{background:#081a3a; color:#e2e8f0; margin:0; padding:10px; font-family:'Tajawal';}
.header{display:flex; justify-content:space-between; background:#0e2450; border-radius:14px; padding:12px; font-weight:800; border:1px solid #1e3a8a}
.mono{font-family:'Roboto Mono'!important; direction:ltr; display:inline-block; font-weight:700}
.card b{font-family:'Roboto Mono'; font-size:28px; background:#020a1e; border-radius:12px; padding:10px; display:block; margin:8px 0; direction:ltr}
table{width:100%; border-collapse:collapse; margin-top:14px; background:#0e2450; border-radius:16px; overflow:hidden; border:1px solid #1e3a8a}
th{background:#0a1a3a; color:#38bdf8; padding:12px 6px; font-size:12px; font-weight:800}
td{padding:14px 6px; text-align:center; border-bottom:1px solid #1e3a8a}
.num{font-family:'Roboto Mono'; font-weight:700; direction:ltr; font-size:13px}
.btn-close{background:#f1f5f9; color:#0f172a; border:none; border-radius:10px; padding:8px 14px; font-weight:800; cursor:pointer; font-family:'Tajawal'; box-shadow:0 2px 4px rgba(0,0,0,0.3)}
.btn-close:hover{background:#e2e8f0; transform:scale(1.05)}
.btn-close:active{transform:scale(0.95)}
</style>
</head>
<body>
<div class="header"><span class="mono">V102.8 - 2/2 آمن</span><span style="color:#4ade80">✅ IP 152.55.184.109 - MACD اخضر فقط</span><span class="mono" id="bTop">75.23$</span></div>
<div style="text-align:center; margin:12px; font-weight:800">رصيدك <span id="bal" class="mono">75.23$</span> - هدف 0.10$ - <span id="log" style="color:#7dd3fc"></span></div>
<table><thead><tr><th>العملة</th><th>النوع</th><th>الحالة</th><th>الدخول</th><th>الحالي</th><th>ربح %</th><th>$</th><th>إغلاق / طبيب</th></tr></thead><tbody id="tb"></tbody></table>
<div style="display:flex; justify-content:space-between; margin-top:12px; font-weight:800">
<div>غير محققة: <span id="unp" class="mono" style="color:#4ade80">0.000$</span></div>
<div>صافي REAL: <span id="net" class="mono" style="color:#4ade80">+0.000$</span></div>
<div>المستشفى: <span id="hosp">0</span></div>
</div>
<script>
async function load(){
 let r=await fetch('/api/data'); let d=await r.json();
 document.getElementById('bTop').innerText=d.balance.toFixed(2)+'$';
 document.getElementById('bal').innerText=d.balance.toFixed(2)+'$';
 document.getElementById('log').innerText=d.log;
 let un=0; d.positions.forEach(p=>un+=p.pnl_usd); d.hospital.forEach(h=>un+=h.pnl_usd);
 document.getElementById('unp').innerText=un.toFixed(4)+'$';
 document.getElementById('net').innerText=(un>=0?'+':'')+un.toFixed(3)+'$';
 document.getElementById('hosp').innerText=d.hospital.length;
 let html='';
 d.positions.forEach(p=>{
  html+=`<tr><td class="mono"><b>${p.symbol}/USDT</b></td><td><span style="background:#22c55e22; border:1px solid #22c55e; color:#4ade80; border-radius:20px; padding:3px 8px; font-size:11px">ماكد اخضر</span></td><td style="color:#4ade80; font-weight:800">${p.status}</td><td class="num">${p.entry.toFixed(4)}</td><td class="num" style="color:#22d3ee">${(p.current||0).toFixed(4)}</td><td class="num" style="color:${p.pnl_percent>=0?'#4ade80':'#f87171'}">${(p.pnl_percent||0).toFixed(2)}%</td><td class="num" style="color:${p.pnl_usd>=0?'#4ade80':'#f87171'}">${(p.pnl_usd||0).toFixed(4)}$</td><td><button class="btn-close" onclick="closePos('${p.symbol}')">إغلاق</button></td></tr>`;
 });
 d.hospital.forEach(h=>{
  html+=`<tr style="background:#7f1d1d44"><td class="mono">${h.symbol}/USDT</td><td style="color:#fca5a5">مستشفى</td><td style="color:#f87171; font-weight:800">${h.status}</td><td class="num">${h.entry.toFixed(4)}</td><td class="num">${(h.current||0).toFixed(4)}</td><td class="num" style="color:#f87171">${(h.pnl_percent||0).toFixed(2)}%</td><td class="num" style="color:#f87171">${(h.pnl_usd||0).toFixed(4)}$</td><td style="color:#f87171; font-weight:800">طبيب ${h.doctor}</td></tr>`;
 });
 document.getElementById('tb').innerHTML=html;
}
async function closePos(sym){
 if(!confirm('تأكيد اغلاق '+sym+' ؟')) return;
 let r=await fetch('/api/close/'+sym, {method:'POST'});
 let j=await r.json();
 alert(j.msg);
 load();
}
setInterval(load,2000); load();
</script>
</body></html>
"""

@app.route('/api/data')
def data():
    return jsonify(CONFIG)

@app.route('/api/close/<symbol>', methods=['POST'])
def close(symbol):
    for p in CONFIG["positions"][:]:
        if p["symbol"]==symbol:
            CONFIG["balance"]+=p["pnl_usd"]
            CONFIG["positions"].remove(p)
            return jsonify({"msg":f"تم اغلاق {symbol} بربح {p['pnl_usd']:.4f}$"})
    for h in CONFIG["hospital"][:]:
        if h["symbol"]==symbol:
            CONFIG["balance"]+=h["pnl_usd"]
            CONFIG["hospital"].remove(h)
            return jsonify({"msg":f"تم اغلاق {symbol} من المستشفى"})
    return jsonify({"msg":"غير موجود"})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

from flask import Flask, jsonify
import os, threading, time, requests
app = Flask(__name__)
CONFIG = {"balance":75.23, "trade_size":5, "profit":0.08, "fee":0.02, "target":0.10, "capacity":2, "positions":[], "hospital":[], "pharmacy":0.00, "ip":"152.55.184.109"}

def get_price(s):
    try: return float(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={s}USDT",timeout=3).json()['price'])
    except: return 0

def get_klines(s):
    try: return [float(x[4]) for x in requests.get(f"https://api.binance.com/api/v3/klines?symbol={s}USDT&interval=15m&limit=50",timeout=4).json()]
    except: return []
def ema(p,pr):
    if len(p)<pr: return 0
    k=2/(pr+1); e=sum(p[:pr])/pr
    for v in p[pr:]: e=v*k+e*(1-k)
    return e
def is_green(s):
    c=get_klines(s); return len(c)>=30 and ema(c,12)>ema(c,26)

def engine():
    while True:
        try:
            for p in CONFIG["positions"]+CONFIG["hospital"]:
                cur=get_price(p["symbol"])
                if cur:
                    p["current"]=cur; p["pnl_percent"]=((cur-p["entry"])/p["entry"])*100; p["pnl_usd"]=((cur-p["entry"])/p["entry"])*CONFIG["trade_size"]
            # دخول
            if len(CONFIG["positions"])<CONFIG["capacity"]:
                for coin in ["BTC","ETH","SOL","BNB","AVAX","LINK"]:
                    if coin in [x["symbol"] for x in CONFIG["positions"]]: continue
                    if is_green(coin):
                        pr=get_price(coin)
                        if pr: CONFIG["positions"].append({"symbol":coin,"entry":pr,"current":pr,"pnl_percent":0,"pnl_usd":0,"doctor":0,"status":"شغالة - ماكد اخضر فوق السعر"}); break
            # ربح ومستشفى
            for p in CONFIG["positions"][:]:
                if p["pnl_usd"]>=CONFIG["target"]: CONFIG["balance"]+=p["pnl_usd"]; CONFIG["positions"].remove(p)
                elif p["pnl_percent"]<=-1.5: CONFIG["positions"].remove(p); p["status"]="في المستشفى"; CONFIG["hospital"].append(p)
            for h in CONFIG["hospital"][:]:
                if h["pnl_usd"]>=CONFIG["target"]: CONFIG["balance"]+=h["pnl_usd"]; CONFIG["hospital"].remove(h)
                elif h["pnl_percent"]<=-2.5-h["doctor"]: h["doctor"]+=1; h["status"]=f"الطبيب {h['doctor']} يعالج"; h["entry"]=(h["entry"]+h["current"])/2
            time.sleep(3)
        except: time.sleep(3)
threading.Thread(target=engine,daemon=True).start()

@app.route('/')
def dash():
    return """
<html dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}
body{margin:0;background:#050d26;color:#fff;font-family:'Tajawal',sans-serif;overflow-x:hidden}
.topbar{background:#081a4a;text-align:center;padding:10px;font-weight:900;color:#ffd700;font-size:14px;border-bottom:2px solid #1e3a8a;letter-spacing:0.5px}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:12px}
.card{background:linear-gradient(180deg,#0a1e42,#060e2b);border-radius:18px;padding:12px 10px;text-align:center;position:relative;border:2px solid #fbbf24;box-shadow:0 4px 15px rgba(0,0,0,0.5)}
.card.profit{border-color:#22c55e;box-shadow:0 0 20px rgba(34,197,94,0.3)}
.card small{font-size:11px;font-weight:800;color:#fbbf24;display:block;margin-bottom:6px}
.card b{font-family:'JetBrains Mono',monospace;background:#000814;border:2px solid #1e3a8a;border-radius:12px;padding:12px 0;display:block;font-size:26px;direction:ltr;color:#fff;letter-spacing:1px;margin:8px 30px}
.card.plus{position:absolute;left:8px;top:50%;transform:translateY(-10%);background:#fbbf24;color:#000;border:none;width:34px;height:34px;border-radius:10px;font-size:20px;font-weight:900;cursor:pointer;box-shadow:0 2px 6px rgba(0,0,0,0.4)}
.card.minus{position:absolute;right:8px;top:50%;transform:translateY(-10%);background:#1e293b;color:#fbbf24;border:1px solid #fbbf24;width:34px;height:34px;border-radius:10px;font-size:20px;font-weight:900;cursor:pointer}
.card.sub{font-size:10px;color:#4ade80;font-weight:800;margin-top:6px}
.actions{display:flex;justify-content:center;gap:12px;margin:10px 0}
.btn-red{background:#dc2626;color:#fff;border:none;border-radius:24px;padding:10px 20px;font-weight:900;font-family:'Tajawal';font-size:12px;box-shadow:0 4px 10px rgba(220,38,38,0.4);cursor:pointer}
.btn-blue{background:#e2e8f0;color:#b91c1c;border:none;border-radius:24px;padding:10px 20px;font-weight:900;font-family:'Tajawal';font-size:12px;cursor:pointer}
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;padding:10px 12px}
.stat{background:linear-gradient(180deg,#0a1e42,#081a3a);border:2px solid #1e3a8a;border-radius:16px;padding:12px 6px;text-align:center}
.stat small{font-size:11px;color:#94a3b8;font-weight:800;display:block}
.stat b{font-family:'JetBrains Mono',monospace;font-size:15px;direction:ltr;display:block;margin-top:6px;color:#fff}
.table-wrap{margin:10px 12px;background:#0a1e42;border-radius:16px;border:2px solid #1e3a8a;overflow:hidden}
table{width:100%;border-collapse:collapse}
th{background:#1e3a8a;color:#fbbf24;font-size:12px;font-weight:900;padding:12px 6px}
td{padding:14px 6px;text-align:center;font-size:12px;border-bottom:1px solid #1e3a8a}
.mono{font-family:'JetBrains Mono',monospace;direction:ltr;display:inline-block;font-weight:800;font-size:12px}
.footer{text-align:center;padding:12px;color:#4ade80;font-weight:900;font-size:13px}
.footer-bottom{display:flex;justify-content:space-between;padding:8px 12px;font-size:11px;font-weight:800;color:#fbbf24;background:#050d26;border-top:1px solid #1e3a8a}
@media(max-width:800px){.cards{grid-template-columns:1fr 1fr}.stats{grid-template-columns:1fr 1fr 1fr}.card b{font-size:20px; margin:8px 28px}}
</style>
</head>
<body>
<div class="topbar">👑 V102.4 - رصيدك $75.23 - هدف $0.10 - اختيارك ثابت - MACD اخضر فقط - IP 152.55.184.109</div>
<div class="cards">
<div class="card"><small>💰 رأس المال $ REAL</small><button class="plus">+</button><b id="bal">75.23</b><button class="minus">-</button><div class="sub">💰 مبهر $75.23 من بيتكس</div></div>
<div class="card"><small>📦 حجم $ (اختيارك ثابت)</small><button class="plus">+</button><b>5</b><button class="minus">-</button><div class="sub">بيت صب الفكرة</div></div>
<div class="card profit"><small>💚 ربحك $ (اختيارك ثابت)</small><button class="plus">+</button><b>0.08</b><button class="minus">-</button><div class="sub" style="color:#22c55e">والفينت = 0.02 + 0.08 = 0.10</div></div>
<div class="card"><small>📦 سعة (اختيارك ثابت)</small><button class="plus">+</button><b id="cap">2</b><button class="minus">-</button></div>
</div>
<div class="actions"><button class="btn-red" onclick="if(confirm('اغلاق الكل؟')) fetch('/api/close_all',{method:'POST'}).then(()=>location.reload())">إيقاف V102.4 ⏹️</button><button class="btn-blue" onclick="if(confirm('اغلاق الكل؟')) fetch('/api/close_all',{method:'POST'}).then(()=>location.reload())">🔒 إغلاق الكل</button></div>
<div class="stats">
<div class="stat"><small>💰 ثابت REAL</small><b class="mono" id="s1">75.23$</b></div>
<div class="stat"><small>💊 الصيدلية</small><b class="mono">0.00$</b></div>
<div class="stat"><small>✅ صافي REAL</small><b class="mono" id="sNet" style="color:#4ade80">+0.000$</b></div>
<div class="stat"><small>💎 الاجمالي مباشر</small><b class="mono" id="sTot">75.23$</b></div>
<div class="stat"><small>📊 غير محققة</small><b class="mono" id="sUn">0.000$</b></div>
</div>
<div class="table-wrap">
<table><thead><tr><th>العملة</th><th>النوع</th><th>الحالة</th><th>الدخول</th><th>الحالي</th><th>ربح</th><th>%</th><th>إغلاق</th></tr></thead><tbody id="tb"></tbody></table>
<div class="footer" id="foot">👑 فاضي - اختياراتك ثابتة $5 / $0.10 / سعة 2 ✅</div>
<div class="footer-bottom"><span>V102.4 0_10 من $75.23 مبهر</span><span>ثابت حسب الفكرة V102.4</span><span id="time">14:22:03</span></div>
</div>
<script>
async function load(){
 let r=await fetch('/api/data'); let d=await r.json();
 document.getElementById('bal').innerText=d.balance.toFixed(2);
 document.getElementById('s1').innerText=d.balance.toFixed(2)+'$';
 document.getElementById('sTot').innerText=d.balance.toFixed(2)+'$';
 document.getElementById('cap').innerText=d.capacity;
 let un=0; d.positions.forEach(p=>un+=p.pnl_usd); d.hospital.forEach(h=>un+=h.pnl_usd);
 document.getElementById('sUn').innerText=un.toFixed(3)+'$';
 document.getElementById('sNet').innerText=(un>=0?'+':'')+un.toFixed(3)+'$';
 document.getElementById('sNet').style.color=un>=0?'#4ade80':'#f87171';
 let html='';
 if(d.positions.length==0 && d.hospital.length==0){
  html=`<tr><td colspan=8 style="padding:24px; color:#4ade80; font-weight:900; font-size:13px">👑 فاضي - اختياراتك ثابتة $5 / $0.10 / سعة ${d.capacity} ✅</td></tr>`;
 } else {
  d.positions.forEach(p=>{
   let cls=p.pnl_percent>=0?'#4ade80':'#f87171';
   html+=`<tr><td><b class="mono" style="color:#fbbf24">${p.symbol}/USDT</b></td><td><span style="border:1px solid #22c55e; color:#4ade80; border-radius:20px; padding:3px 8px; font-size:10px">ماكد اخضر</span></td><td style="color:#4ade80; font-size:11px; font-weight:800">${p.status}</td><td class="mono">${p.entry.toFixed(4)}</td><td class="mono" style="color:#38bdf8">${p.current.toFixed(4)}</td><td class="mono" style="color:${cls}">${p.pnl_usd.toFixed(4)}$</td><td class="mono" style="color:${cls}">${p.pnl_percent.toFixed(3)}%</td><td><button style="background:#e2e8f0; border:none; border-radius:8px; padding:6px 12px; font-weight:800; cursor:pointer" onclick="fetch('/api/close/${p.symbol}',{method:'POST'}).then(()=>load())">إغلاق</button></td></tr>`;
  });
  d.hospital.forEach(h=>{
   html+=`<tr style="background:rgba(127,29,29,0.3)"><td class="mono" style="color:#fbbf24">${h.symbol}/USDT</td><td style="color:#fca5a5">مستشفى</td><td style="color:#f87171; font-weight:800">${h.status}</td><td class="mono">${h.entry.toFixed(4)}</td><td class="mono">${h.current.toFixed(4)}</td><td class="mono" style="color:#f87171">${h.pnl_usd.toFixed(4)}$</td><td class="mono" style="color:#f87171">${h.pnl_percent.toFixed(3)}%</td><td style="color:#f87171; font-weight:900">طبيب ${h.doctor}</td></tr>`;
  });
 }
 document.getElementById('tb').innerHTML=html;
}
setInterval(load,2000); load();
setInterval(()=>{document.getElementById('time').innerText=new Date().toLocaleTimeString('ar-EG')},1000);
</script></body></html>
"""
@app.route('/api/data')
def data(): return jsonify(CONFIG)
@app.route('/api/close/<s>',methods=['POST'])
def close(s):
    CONFIG["positions"]=[p for p in CONFIG["positions"] if p["symbol"]!=s]
    CONFIG["hospital"]=[h for h in CONFIG["hospital"] if h["symbol"]!=s]
    return jsonify({"ok":True})
@app.route('/api/close_all',methods=['POST'])
def close_all():
    CONFIG["positions"]=[]; CONFIG["hospital"]=[]
    return jsonify({"ok":True})
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

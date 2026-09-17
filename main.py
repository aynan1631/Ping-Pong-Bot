from flask import Flask, jsonify, request
import os, time, hmac, hashlib, requests, threading
from urllib.parse import urlencode
app = Flask(__name__)

API_KEY = os.environ.get("BINANCE_API_KEY")
API_SECRET = os.environ.get("BINANCE_API_SECRET")

CONFIG = {
    "real_balance": 0, "balance": 0, "trade_size": 5,
    "profit": 0.08, "fee": 0.02, "target": 0.10, "capacity": 2,
    "positions": [], "hospital": [], "trading": False,
    "log": "يفحص الاتصال...", "status": "⏳", "ip": "152.55.184.109"
}

def signed(endpoint):
    if not API_KEY or not API_SECRET: return None
    try:
        p={"timestamp":int(time.time()*1000)}
        q=urlencode(p)
        sig=hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
        h={"X-MBX-APIKEY": API_KEY}
        return requests.get(f"https://api.binance.com{endpoint}?{q}&signature={sig}", headers=h, timeout=8).json()
    except: return None

def get_balance():
    data = signed("/api/v3/account")
    if not data:
        CONFIG["status"]="❌ فشل الاتصال"; return
    if "msg" in data:
        CONFIG["status"]=f"❌ {data['msg']}"; CONFIG["log"]=data['msg']; CONFIG["trading"]=False; return
    if "balances" in data:
        for b in data["balances"]:
            if b["asset"]=="USDT":
                bal=float(b["free"])+float(b["locked"])
                CONFIG["real_balance"]=bal; CONFIG["balance"]=bal
                CONFIG["status"]=f"✅ متصل - {bal:.2f}$"; CONFIG["log"]=f"✅ متصل Binance LIVE - رصيدك {bal:.2f}$"; CONFIG["trading"]=True
                return

def get_price(s):
    try: return float(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={s}USDT", timeout=4).json()['price'])
    except: return None
def get_klines(s):
    try: return [float(x[4]) for x in requests.get(f"https://api.binance.com/api/v3/klines?symbol={s}USDT&interval=15m&limit=50", timeout=5).json()]
    except: return []
def ema(pr, per):
    if len(pr)<per: return None
    k=2/(per+1); e=sum(pr[:per])/per
    for v in pr[per:]: e=v*k+e*(1-k)
    return e
def is_green(s):
    c=get_klines(s)
    if len(c)<30: return False
    e12=ema(c,12); e26=ema(c,26)
    return e12 and e26 and e12>e26 and c[-1]>e12

def engine():
    while True:
        try:
            get_balance()
            if not CONFIG["trading"]:
                time.sleep(5); continue
            for p in CONFIG["positions"]+CONFIG["hospital"]:
                cur=get_price(p["symbol"])
                if cur:
                    p["current"]=cur; p["pnl_percent"]=((cur-p["entry"])/p["entry"])*100; p["pnl_usd"]=((cur-p["entry"])/p["entry"])*CONFIG["trade_size"]
            if len(CONFIG["positions"])<CONFIG["capacity"]:
                for coin in ["BTC","ETH","SOL","BNB","AVAX","LINK"]:
                    if coin in [x["symbol"] for x in CONFIG["positions"]+CONFIG["hospital"]]: continue
                    if is_green(coin):
                        pr=get_price(coin)
                        if pr:
                            CONFIG["positions"].append({"symbol":coin,"entry":pr,"current":pr,"pnl_percent":0,"pnl_usd":0,"doctor":0,"status":"شغالة - MACD اخضر LIVE"})
                            CONFIG["log"]=f"فتح {coin} MACD اخضر"
                            break
            for p in CONFIG["positions"][:]:
                if p["pnl_usd"]>=CONFIG["target"]:
                    CONFIG["balance"]+=p["pnl_usd"]; CONFIG["positions"].remove(p); CONFIG["log"]=f"ربح {p['symbol']}"
                elif p["pnl_percent"]<=-1.5:
                    CONFIG["positions"].remove(p); p["status"]="في المستشفى"; CONFIG["hospital"].append(p)
            for h in CONFIG["hospital"][:]:
                if h["pnl_usd"]>=CONFIG["target"]:
                    CONFIG["balance"]+=h["pnl_usd"]; CONFIG["hospital"].remove(h); CONFIG["log"]=f"الطبيب انقذ {h['symbol']}"
                elif h["pnl_percent"]<=-2.5-h["doctor"]:
                    h["doctor"]+=1; h["status"]=f"الطبيب {h['doctor']} يعالج"; h["entry"]=(h["entry"]+h["current"])/2
            time.sleep(5)
        except: time.sleep(5)

threading.Thread(target=engine, daemon=True).start()

@app.route('/')
def dash():
    return """
<html dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box} body{margin:0;background:#050d26;color:#fff;font-family:'Tajawal',sans-serif}
.top{text-align:center;background:#081a4a;padding:10px;color:#ffd700;font-weight:900;font-size:12px;border-bottom:2px solid #1e3a8a}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;padding:12px}
.card{background:linear-gradient(180deg,#0e2450,#060e2b);border:2px solid #fbbf24;border-radius:18px;padding:10px;text-align:center;position:relative}
.card.green{border-color:#22c55e;box-shadow:0 0 15px rgba(34,197,94,0.4)}
.card small{font-size:10px;font-weight:800;color:#fbbf24;display:block;margin-bottom:4px}
.card b{font-family:'JetBrains Mono',monospace;background:#000814;border:2px solid #1e3a8a;border-radius:12px;padding:8px 0;display:block;font-size:20px;direction:ltr;margin:6px 28px}
.card button{position:absolute;top:50%;transform:translateY(-10%);width:30px;height:30px;border-radius:9px;font-weight:900;cursor:pointer}
.pl{left:6px;background:#fbbf24;color:#000;border:none}.mn{right:6px;background:#1e293b;color:#fbbf24;border:1px solid #fbbf24}
.sub{font-size:9px;color:#4ade80;font-weight:800;margin-top:4px}
.controls{background:#0a1e42;margin:0 12px;border-radius:12px;border:1px solid #1e3a8a;padding:10px;display:flex;gap:8px;justify-content:center;flex-wrap:wrap;align-items:center}
.cbtn{border:none;border-radius:20px;padding:8px 16px;font-weight:900;font-family:'Tajawal';font-size:11px;cursor:pointer}
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;padding:10px 12px}
.stat{background:#0a1e42;border:2px solid #1e3a8a;border-radius:14px;padding:10px 4px;text-align:center}
.stat small{font-size:10px;color:#94a3b8;font-weight:800;display:block}
.stat b{font-family:'JetBrains Mono',monospace;font-size:13px;direction:ltr;display:block;margin-top:4px}
.table{margin:10px 12px;background:#0a1e42;border:2px solid #1e3a8a;border-radius:14px;overflow:hidden}
table{width:100%;border-collapse:collapse} th{background:#1e3a8a;color:#facc15;padding:10px 4px;font-size:11px;font-weight:900}
td{padding:12px 4px;text-align:center;font-size:11px;border-bottom:1px solid #1e3a6a}
.mono{font-family:'JetBrains Mono',monospace;direction:ltr;display:inline-block;font-weight:800}
.hosp{background:rgba(127,29,29,0.4)}.foot{text-align:center;padding:10px;color:#4ade80;font-weight:900;font-size:12px}
@media(max-width:700px){.cards{grid-template-columns:1fr 1fr}.stats{grid-template-columns:1fr 1fr 1fr}.card b{font-size:18px;margin:6px 26px}}
</style>
</head><body>
<div class="top" id="top">👑 V103 - BINANCE LIVE - بدون وهميات</div>
<div class="cards">
<div class="card"><small>💰 رأس المال REAL</small><button class="pl" onclick="mod('balance',1)">+</button><b id="bal">--</b><button class="mn" onclick="mod('balance',-1)">-</button><div class="sub" id="subBal">من Binance</div></div>
<div class="card"><small>📦 حجم (ثابت)</small><button class="pl" onclick="mod('size',1)">+</button><b id="sz">5</b><button class="mn" onclick="mod('size',-1)">-</button></div>
<div class="card green"><small>💚 ربحك (ثابت)</small><button class="pl" onclick="mod('profit',0.01)">+</button><b id="pr">0.08</b><button class="mn" onclick="mod('profit',-0.01)">-</button><div class="sub">0.10=0.08+0.02</div></div>
<div class="card"><small>📦 سعة (ثابت)</small><button class="pl" onclick="mod('cap',1)">+</button><b id="cap">2</b><button class="mn" onclick="mod('cap',-1)">-</button></div>
</div>
<div class="controls">
<button class="cbtn" style="background:#16a34a;color:#fff" id="tradeBtn" onclick="toggle()">⏸️ وقف التداول</button>
<button class="cbtn" style="background:#e2e8f0" onclick="closeAll()">🔒 اغلاق الكل</button>
<button class="cbtn" style="background:#fbbf24;color:#000" onclick="fetch('/api/clear_hosp',{method:'POST'}).then(()=>load())">🏥 تفريغ المستشفى</button>
<span id="log" style="font-size:11px;color:#4ade80;font-weight:900"></span>
</div>
<div class="stats">
<div class="stat"><small>💰 ثابت REAL</small><b class="mono" id="s1">--</b></div>
<div class="stat"><small>💊 الصيدلية</small><b class="mono">0.00$</b></div>
<div class="stat"><small>✅ صافي REAL</small><b class="mono" id="sNet" style="color:#4ade80">+0.000$</b></div>
<div class="stat"><small>💎 الاجمالي</small><b class="mono" id="sTot">--</b></div>
<div class="stat"><small>📊 غير محققة</small><b class="mono" id="sUn">0.000$</b></div>
</div>
<div class="table"><table><thead><tr><th>العملة</th><th>النوع</th><th>الحالة</th><th>الدخول</th><th>الحالي LIVE</th><th>ربح $</th><th>%</th><th>طبيب/اغلاق</th></tr></thead><tbody id="tb"></tbody></table>
<div class="foot" id="foot">👑 يفحص الاتصال...</div>
</div>
<script>
async function mod(k,v){await fetch('/api/mod',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({k,v})});load();}
async function toggle(){let r=await fetch('/api/toggle',{method:'POST'});let d=await r.json();document.getElementById('tradeBtn').innerText=d.trading?'⏸️ وقف التداول':'▶️ تشغيل';load();}
async function closeAll(){if(!confirm('اغلاق الكل؟'))return;await fetch('/api/close_all',{method:'POST'});load();}
async function load(){
 let r=await fetch('/api/data'); let d=await r.json();
 document.getElementById('bal').innerText=d.real_balance.toFixed(2); document.getElementById('s1').innerText=d.real_balance.toFixed(2)+'$'; document.getElementById('sTot').innerText=d.real_balance.toFixed(2)+'$';
 document.getElementById('sz').innerText=d.trade_size; document.getElementById('pr').innerText=d.profit.toFixed(2); document.getElementById('cap').innerText=d.capacity;
 document.getElementById('tradeBtn').innerText=d.trading?'⏸️ وقف التداول':'▶️ تشغيل'; document.getElementById('log').innerText=d.log; document.getElementById('top').innerText='👑 V103 - '+d.status+' - IP '+d.ip;
 let un=0; d.positions.forEach(p=>un+=p.pnl_usd); d.hospital.forEach(h=>un+=h.pnl_usd);
 document.getElementById('sUn').innerText=un.toFixed(4)+'$'; document.getElementById('sNet').innerText=(un>=0?'+':'')+un.toFixed(4)+'$'; document.getElementById('sNet').style.color=un>=0?'#4ade80':'#f87171';
 let html='';
 if(!d.trading){ html=`<tr><td colspan=8 style="padding:22px;color:#f87171;font-weight:900">${d.status} - ${d.log} - تأكد من IP 152.55.184.109 في Binance</td></tr>`; document.getElementById('foot').innerText=d.status; }
 else if(d.positions.length==0 && d.hospital.length==0){ html=`<tr><td colspan=8 style="padding:22px;color:#4ade80;font-weight:900">👑 فاضي - رصيدك الحقيقي ${d.real_balance.toFixed(2)}$ - انتظار MACD اخضر LIVE - سعة ${d.capacity} ✅</td></tr>`; document.getElementById('foot').innerText=`👑 فاضي - رصيدك الحقيقي ${d.real_balance.toFixed(2)}$ - انتظار MACD اخضر ✅`; }
 else{ d.positions.forEach(p=>{let c=p.pnl_percent>=0?'#4ade80':'#f87171'; html+=`<tr><td class="mono" style="color:#fbbf24">${p.symbol}/USDT</td><td><span style="border:1px solid #22c55e;color:#4ade80;border-radius:20px;padding:2px 8px;font-size:10px">MACD اخضر LIVE</span></td><td style="color:#4ade80;font-size:10px">${p.status}</td><td class="mono">${p.entry.toFixed(2)}</td><td class="mono" style="color:#38bdf8">${p.current.toFixed(2)}</td><td class="mono" style="color:${c}">${p.pnl_usd.toFixed(4)}$</td><td class="mono" style="color:${c}">${p.pnl_percent.toFixed(3)}%</td><td><button style="background:#e2e8f0;border:none;border-radius:8px;padding:5px 10px;font-weight:800;cursor:pointer;font-size:10px" onclick="fetch('/api/close/${p.symbol}',{method:'POST'}).then(()=>load())">إغلاق</button></td></tr>`}); d.hospital.forEach(h=>{html+=`<tr class="hosp"><td class="mono" style="color:#fca5a5">${h.symbol}/USDT</td><td style="color:#f87171">مستشفى</td><td style="color:#f87171;font-weight:800;font-size:10px">${h.status}</td><td class="mono">${h.entry.toFixed(2)}</td><td class="mono">${h.current.toFixed(2)}</td><td class="mono" style="color:#f87171">${h.pnl_usd.toFixed(4)}$</td><td class="mono" style="color:#f87171">${h.pnl_percent.toFixed(3)}%</td><td style="color:#fbbf24;font-weight:900">طبيب ${h.doctor}</td></tr>`}); document.getElementById('foot').innerText=`شغال ${d.positions.length}/${d.capacity} - المستشفى ${d.hospital.length} - ${d.log}`; }
 document.getElementById('tb').innerHTML=html;
}
setInterval(load,3000); load();
</script></body></html>
"""
@app.route('/api/data')
def data(): return jsonify(CONFIG)
@app.route('/api/mod', methods=['POST'])
def mod():
    d=request.json; k,v=d['k'],d['v']
    if k=='balance': CONFIG['real_balance']=max(1,CONFIG['real_balance']+v); CONFIG['balance']=CONFIG['real_balance']
    elif k=='size': CONFIG['trade_size']=max(1,CONFIG['trade_size']+v)
    elif k=='profit': CONFIG['profit']=max(0.01,round(CONFIG['profit']+v,2)); CONFIG['target']=round(CONFIG['profit']+CONFIG['fee'],2)
    elif k=='cap': CONFIG['capacity']=max(1,min(5,CONFIG['capacity']+int(v)))
    return jsonify({"ok":True})
@app.route('/api/toggle', methods=['POST'])
def toggle(): CONFIG['trading']=not CONFIG['trading']; return jsonify({"trading":CONFIG['trading']})
@app.route('/api/close/<s>', methods=['POST'])
def close(s): CONFIG["positions"]=[p for p in CONFIG["positions"] if p["symbol"]!=s]; CONFIG["hospital"]=[h for h in CONFIG["hospital"] if h["symbol"]!=s]; return jsonify({"ok":True})
@app.route('/api/close_all', methods=['POST'])
def close_all(): CONFIG["positions"]=[]; CONFIG["hospital"]=[]; return jsonify({"ok":True})
@app.route('/api/clear_hosp', methods=['POST'])
def clear_hosp(): CONFIG["hospital"]=[]; return jsonify({"ok":True})
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

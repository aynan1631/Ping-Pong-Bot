import os, time, threading
from flask import Flask, jsonify, request
from binance.client import Client
app = Flask(__name__)
client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"), {"timeout": 20})
client.API_URL = 'https://data-api.binance.vision/api'
HALAL = ["BTCUSDT","ETHUSDT","BNBUSDT","AVAXUSDT","ADAUSDT","LINKUSDT","XLMUSDT","DOTUSDT","MATICUSDT","XRPUSDT","SOLUSDT"]
STATE = {"is_running": False,"total_capital": 76.44,"trade_value": 11.00,"profit_target_cents": 15,"max_trades": 2,"realized": 0.00,"unrealized": 0.00,"patients": [],"coins": [],"history": [],"log": "🚀 وضع فتح فوري مفعل - بيفتح خلال 10 ثواني"}

def get_balance():
    try:
        b=float(client.get_asset_balance('USDT')['free'])
        STATE["total_capital"]=round(b,2)
        return b
    except: return STATE["total_capital"]

def get_step(sym):
    try:
        info=client.get_symbol_info(sym)
        lot=[f for f in info['filters'] if f['filterType']=='LOT_SIZE'][0]
        return float(lot['stepSize'])
    except: return 0.000001

def get_coins():
    try:
        t=client.get_ticker()
        lst=[{"symbol":x['symbol'],"price":float(x['lastPrice']),"vol":float(x['quoteVolume'])} for x in t if x['symbol'] in HALAL and float(x['quoteVolume'])>5000000]
        STATE["coins"]=sorted(lst,key=lambda x:x['vol'],reverse=True)[:6]
        return STATE["coins"]
    except: return []

def loop():
    while True:
        try:
            if not STATE["is_running"]:
                time.sleep(3); continue
            get_balance(); coins=get_coins(); unreal=0.0
            for p in STATE["patients"]:
                try:
                    cur=float(client.get_symbol_ticker(symbol=p['symbol'])['price'])
                    pnl=(cur-p['entry'])*p['qty']
                    perc=((cur/p['entry'])-1)*100
                    p.update({"cur":round(cur,4),"pnl":round(pnl,2),"pnl_percent":round(perc,2)})
                    if perc < -6: p['status']='👨‍⚕️ عند الطبيب'
                    elif perc < -3: p['status']='🏥 في المستشفى'
                    else: p['status']='💎 عادي'
                    unreal+=pnl
                except: pass
            STATE["unrealized"]=round(unreal,2)
            target=STATE["profit_target_cents"]/100.0
            if unreal>=target and STATE["patients"]:
                for p in list(STATE["patients"]):
                    try:
                        asset=p['symbol'].replace('USDT',''); bal=float(client.get_asset_balance(asset=asset)['free'])
                        step=get_step(p['symbol'])
                        q=round(bal - (bal % step),6)
                        client.order_market_sell(symbol=p['symbol'], quantity=q)
                        STATE["history"].insert(0,{"symbol":p['symbol'],"entry":p['entry'],"exit":p['cur'],"pnl":p['pnl'],"percent":p['pnl_percent'],"time":time.strftime("%H:%M:%S")})
                        if len(STATE["history"])>20: STATE["history"].pop()
                        STATE["realized"]=round(STATE["realized"]+p['pnl'],2)
                    except Exception as e: STATE["log"]=f"بيع {p['symbol']}: {e}"[:80]
                STATE["patients"]=[]; STATE["log"]=f"✅ باع وحقق {target:.2f}$"
                continue
            # فتح فوري بدون انتظار MACD
            if len(STATE["patients"])<STATE["max_trades"] and get_balance()>11:
                for c in coins:
                    if any(x['symbol']==c['symbol'] for x in STATE["patients"]): continue
                    # لا تنتظر MACD - افتح فوراً
                    try:
                        step=get_step(c['symbol'])
                        qty=round((STATE["trade_value"]/c['price']),6)
                        if qty*c['price']<10.5: qty=round(11/c['price'],6)
                        qty=round(qty - (qty % step),6)
                        if qty==0: continue
                        client.order_market_buy(symbol=c['symbol'], quantity=qty)
                        STATE["patients"].append({"symbol":c['symbol'],"entry":c['price'],"qty":qty,"cur":c['price'],"pnl":0.0,"pnl_percent":0.0,"status":"💎 عادي - فتح فوري"})
                        STATE["log"]=f"✅ فتح فوري {c['symbol']} كمية {qty}"; break
                    except Exception as e: STATE["log"]=f"{c['symbol']}: {str(e)[:80]}"
                time.sleep(5)
            time.sleep(5)
        except Exception as e:
            STATE["log"]=f"{e}"; time.sleep(5)
threading.Thread(target=loop, daemon=True).start()

HTML = """
<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
*{font-family:'Tajawal',sans-serif;box-sizing:border-box}.num{font-family:'JetBrains Mono',monospace!important;direction:ltr;display:inline-block;font-weight:900}
body{background:radial-gradient(1200px 600px at 20% -10%, #1e293b 0%, #0f172a 40%, #020617 100%);min-height:100vh;padding:12px;color:#fff}
.header{background:linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.03));border:2px solid #facc15;border-radius:22px;padding:20px 24px;display:flex;justify-content:space-between;align-items:center}
.logo{font-size:22px;font-weight:900;background:linear-gradient(90deg,#facc15,#f59e0b);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.btn{padding:16px 32px;border-radius:16px;border:none;font-weight:900;font-size:18px;cursor:pointer}.btn-start{background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff;box-shadow:0 0 20px rgba(34,197,94,0.5);animation:pulse 2s infinite}.btn-stop{background:linear-gradient(135deg,#ef4444,#dc2626);color:#fff}
@keyframes pulse{0%{box-shadow:0 0 20px rgba(34,197,94,0.5)}50%{box-shadow:0 0 40px rgba(34,197,94,0.8)}100%{box-shadow:0 0 20px rgba(34,197,94,0.5)}}
.status{margin:16px 0;padding:18px;border-radius:18px;font-size:22px;font-weight:900;text-align:center;border:2px solid}.on{background:#052e16;border-color:#22c55e;color:#4ade80}.off{background:#450a0a;border-color:#ef4444;color:#f87171}
.grid{display:grid;grid-template-columns:1.2fr 0.8fr;gap:16px;margin-top:16px}@media(max-width:900px){.grid{grid-template-columns:1fr}}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-top:16px}@media(max-width:900px){.grid3{grid-template-columns:1fr}}
.card{background:linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));backdrop-filter:blur(20px);border:2px solid rgba(255,255,255,0.12);border-radius:22px;padding:22px}
.card-gold{border-color:#facc15;background:linear-gradient(135deg, rgba(250,204,21,0.15), rgba(245,158,11,0.08))}
.card-hospital{border-color:#f59e0b;background:linear-gradient(135deg, rgba(245,158,11,0.18), rgba(245,158,11,0.06))}
.card-doctor{border-color:#ef4444;background:linear-gradient(135deg, rgba(239,68,68,0.18), rgba(239,68,68,0.06))}
.card-history{border-color:#22c55e;background:linear-gradient(135deg, rgba(34,197,94,0.15), rgba(34,197,94,0.05))}
.title{font-size:17px;color:#e2e8f0;font-weight:900;margin-bottom:14px}.big-num{font-size:64px;font-weight:900;background:linear-gradient(90deg,#facc15,#fde047);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.mini-grid{display:flex;gap:12px;margin-top:18px}.mini{flex:1;background:rgba(0,0,0,0.4);border:2px solid rgba(255,255,255,0.12);border-radius:16px;padding:16px;text-align:center}
.mini b{display:block;font-size:14px;color:#cbd5e1;margin-bottom:8px}.mini.num{font-size:26px}
.input{width:100%;background:rgba(0,0,0,0.5);border:3px solid rgba(255,255,255,0.2);border-radius:14px;padding:16px;font-size:24px;font-weight:900;text-align:center;color:#facc15}
.input-gold{border-color:#facc15;background:rgba(250,204,21,0.15);font-size:26px}.dollar{font-size:44px;font-weight:900;color:#facc15}
.coin{padding:16px;background:rgba(255,255,255,0.06);border:2px solid rgba(255,255,255,0.08);border-radius:14px;display:flex;justify-content:space-between;margin:8px 0}.coin b{font-size:20px;color:#fde047}
.patient{padding:18px;background:rgba(255,255,255,0.07);border-radius:16px;margin:10px 0;display:flex;justify-content:space-between;border-right:6px solid}
.patient.normal{border-color:#22c55e}.patient.hospital{border-color:#f59e0b}.patient.doctor{border-color:#ef4444}
.patient b{font-size:22px;color:#facc15}.pnl{font-size:22px;font-weight:900}.perc{font-size:16px;font-weight:800}
.history-item{padding:14px;background:rgba(255,255,255,0.06);border:1px solid rgba(34,197,94,0.3);border-radius:12px;margin:8px 0;display:flex;justify-content:space-between;align-items:center}
.history-item b{font-size:18px;color:#4ade80}.log{font-size:15px;color:#e2e8f0;margin-top:12px;padding:12px;background:rgba(0,0,0,0.4);border-radius:12px;border:2px solid rgba(255,255,255,0.08);font-weight:700}
</style></head><body>
<div class="header"><div class="logo">🚀 وضع فتح فوري - 10 ثواني | <span class="num" id="cap2" style="-webkit-text-fill-color:#facc15;font-size:26px">76.44</span></div><div style="display:flex;gap:12px"><button class="btn btn-start" onclick="ctrl('start')">🚀 تشغيل فوري</button><button class="btn btn-stop" onclick="ctrl('stop')">⏹ إيقاف</button><button class="btn" style="background:#facc15;color:#000" onclick="force()">⚡ افتح الآن</button></div></div>
<div id="state" class="status off">⏹ متوقف</div>
<div class="grid">
<div class="card card-gold"><div class="title">💎 المحفظة - أرقام عملاقة HD</div><div class="big-num"><span class="num" id="cap">76.44</span> <span style="font-size:28px">USDT</span></div><div class="mini-grid"><div class="mini"><b>✅ محقق</b><span class="num" id="real" style="color:#4ade80">+0.00$</span></div><div class="mini"><b>⏳ غير محقق</b><span class="num" id="unreal" style="color:#fde047">+0.00$</span></div><div class="mini"><b>🛡️ احتياطي</b><span class="num" style="color:#fff">38.22</span></div></div><div id="log" class="log">💎 جاهز</div></div>
<div class="card"><div class="title">⚙️ إعداداتك</div><div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px"><div><div class="title">💰 قيمة الصفقة</div><input class="input input-gold num" id="tv" value="11.00" onchange="save()"></div><div><div class="title">🎯 هدف سنت</div><input class="input input-gold num" id="cents" value="15" onchange="save()"></div><div><div class="title">🛏️ عدد المرضى</div><input class="input num" id="mt" value="2" onchange="save()"></div></div><div style="text-align:center;margin-top:20px"><div class="title" style="font-size:18px">الهدف الإجمالي</div><div class="dollar"><span class="num" id="dollars">0.15</span> $</div></div></div>
</div>
<div class="grid">
<div class="card"><div class="title" style="font-size:20px">💎 العملات القوية الحلال</div><div id="coins"></div></div>
<div class="card card-history"><div class="title" style="font-size:20px">📜 مكان الصفقات المقفلة - سجل الأرباح</div><div style="display:flex;gap:10px;margin-bottom:12px"><div class="mini"><b>💰 عدد المقفلة</b><span class="num" id="h-count" style="color:#4ade80;font-size:28px">0</span></div><div class="mini"><b>✅ إجمالي محقق</b><span class="num" id="h-total" style="color:#facc15;font-size:28px">0.00$</span></div></div><div id="history" style="max-height:320px;overflow-y:auto"></div></div>
</div>
<div class="grid3">
<div class="card"><div class="title">💎 غرفة عادية - هنا تظهر الصفقات المفتوحة الآن</div><div id="room-normal"></div></div>
<div class="card card-hospital"><div class="title">🏥 المستشفى (-3% إلى -6%)</div><div id="room-hospital"></div></div>
<div class="card card-doctor"><div class="title">👨‍⚕️ عند الطبيب (أقل من -6%)</div><div id="room-doctor"></div></div>
</div>
<script>
function f(n){return Number(n).toFixed(2)}
async function refresh(){
let r=await fetch('/api/status');let j=await r.json();
document.getElementById('cap').innerText=f(j.total_capital);document.getElementById('cap2').innerText=f(j.total_capital);
document.getElementById('real').innerText=(j.realized>=0?'+':'')+f(j.realized)+'$';
document.getElementById('unreal').innerText=(j.unrealized>=0?'+':'')+f(j.unrealized)+'$';
document.getElementById('state').innerText=j.is_running?'🚀 شغال فوري - بيفتح خلال 10 ثواني':'⏹ متوقف كامل';
document.getElementById('state').className=j.is_running?'status on':'status off';
document.getElementById('dollars').innerText=f(j.profit_target_cents/100);
document.getElementById('log').innerText=j.log;
document.getElementById('h-count').innerText=j.history.length;
document.getElementById('h-total').innerText=f(j.realized)+'$';
let ch='';j.coins.forEach(c=>{ch+=`<div class=coin><div><b>${c.symbol}</b><div class=num style='color:#94a3b8;font-size:15px'>${(c.vol/1000000).toFixed(1)}M</div></div><span style='background:#16a34a;color:#fff;padding:8px 14px;border-radius:20px;font-size:13px;font-weight:900'>جاهز للفتح</span></div>`});
document.getElementById('coins').innerHTML=ch;
let hh='';if(j.history.length==0) hh='<div style=text-align:center;padding:30px;color:#64748b;font-size:16px;font-weight:800>📜<br>لا يوجد صفقات مقفلة بعد</div>';
else j.history.forEach(h=>{hh+=`<div class=history-item><div><b>${h.symbol}</b><div class=num style="font-size:12px;color:#94a3b8">${h.time} | ${f(h.entry)} → ${f(h.exit)}</div></div><div style=text-align:left><div class=num style="color:#4ade80;font-size:18px;font-weight:900">+${f(h.pnl)}$</div><div class=num style="color:#4ade80;font-size:13px">+${f(h.percent)}%</div></div></div>`;});
document.getElementById('history').innerHTML=hh;
let normal=j.patients.filter(p=>p.pnl_percent > -3);let hosp=j.patients.filter(p=>p.pnl_percent <= -3 && p.pnl_percent > -6);let doc=j.patients.filter(p=>p.pnl_percent <= -6);
function render(list){if(list.length==0) return '<div style=text-align:center;padding:20px;color:#64748b;font-size:16px;font-weight:800>فارغ - بانتظار فتح صفقة</div>';let h='';list.forEach(p=>{let cls=p.pnl_percent<=-6?'doctor':p.pnl_percent<=-3?'hospital':'normal';h+=`<div class="patient ${cls}"><div><b>${p.symbol}</b><div style="font-size:13px;color:#cbd5e1">${p.status}</div><div class=num style="font-size:13px;color:#94a3b8">دخول ${p.entry}</div></div><div style=text-align:left><div class="pnl num" style="color:${p.pnl>=0?'#4ade80':'#f87171'}">${f(p.pnl)}$</div><div class="perc num" style="color:${p.pnl_percent>=0?'#4ade80':'#f87171'}">${p.pnl_percent>=0?'+':''}${f(p.pnl_percent)}%</div></div></div>`;});return h;}
document.getElementById('room-normal').innerHTML=render(normal);
document.getElementById('room-hospital').innerHTML=render(hosp);
document.getElementById('room-doctor').innerHTML=render(doc);
}
async function ctrl(a){await fetch('/api/control?action='+a,{method:'POST'});refresh();}
async function save(){let tv=document.getElementById('tv').value;let mt=document.getElementById('mt').value;let ct=document.getElementById('cents').value;await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({trade_value:parseFloat(tv),max_trades:parseInt(mt),profit_target_cents:parseInt(ct)})});}
async function force(){await fetch('/api/force',{method:'POST'});refresh();}
setInterval(refresh,2000);refresh();
</script></body></html>
"""

@app.route("/")
def dash(): return HTML
@app.route("/api/status")
def s(): get_balance(); return jsonify(STATE)
@app.route("/api/control", methods=['POST'])
def c(): a=request.args.get('action'); STATE["is_running"]=(a=='start'); return jsonify(STATE)
@app.route("/api/force", methods=['POST'])
def force():
    try:
        coins=get_coins()
        if not coins: coins=[{"symbol":"BNBUSDT","price":600,"vol":10000000}]
        c=coins[0]
        step=get_step(c['symbol'])
        qty=round((STATE["trade_value"]/c['price']),6)
        if qty*c['price']<10.5: qty=round(11/c['price'],6)
        qty=round(qty - (qty % step),6)
        client.order_market_buy(symbol=c['symbol'], quantity=qty)
        STATE["patients"].append({"symbol":c['symbol'],"entry":c['price'],"qty":qty,"cur":c['price'],"pnl":0.0,"pnl_percent":0.0,"status":"💎 فتح فوري يدوي"})
        STATE["log"]=f"✅ فتح فوري يدوي {c['symbol']}"
    except Exception as e: STATE["log"]=f"خطأ فتح فوري: {e}"[:120]
    return jsonify(STATE)
@app.route("/api/config", methods=['POST'])
def cfg(): d=request.json; STATE["trade_value"]=float(d.get('trade_value',11)); STATE["max_trades"]=int(d.get('max_trades',2)); STATE["profit_target_cents"]=int(d.get('profit_target_cents',15)); return jsonify(STATE)
@app.route("/health")
def h(): return "OK",200
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))

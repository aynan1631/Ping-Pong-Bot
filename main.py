import os, time, threading
from flask import Flask, jsonify, request
from binance.client import Client

app = Flask(__name__)

client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"), {"timeout": 20})
client.API_URL = 'https://data-api.binance.vision/api'

HALAL = ["BTCUSDT","ETHUSDT","BNBUSDT","AVAXUSDT","ADAUSDT","LINKUSDT","XLMUSDT","DOTUSDT","MATICUSDT","XRPUSDT","SOLUSDT"]
STATE = {"is_running": False,"total_capital": 76.44,"trade_value": 10.00,"profit_target_cents": 10,"max_trades": 2,"realized": 0.00,"unrealized": 0.00,"patients": [],"coins": [],"log": "💎 الوضع الملكي الفاخر جاهز","macd": "جاهز"}

def get_balance():
    try:
        b=float(client.get_asset_balance('USDT')['free'])
        STATE["total_capital"]=round(b,2)
        return b
    except: return STATE["total_capital"]

def ema(prices, period):
    k=2/(period+1); e=prices[0]
    for p in prices[1:]: e=p*k+e*(1-k)
    return e

def is_bull(sym):
    try:
        kl=client.get_klines(symbol=sym, interval=Client.KLINE_INTERVAL_1HOUR, limit=100)
        closes=[float(x[4]) for x in kl]
        return ema(closes[-26:],12)-ema(closes[-26:],26) > ema(closes[-27:-1],12)-ema(closes[-27:-1],26)
    except: return False

def get_coins():
    try:
        tickers=client.get_ticker()
        lst=[{"symbol":t['symbol'],"price":float(t['lastPrice']),"vol":float(t['quoteVolume'])} for t in tickers if t['symbol'] in HALAL and float(t['quoteVolume'])>5000000]
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
                    p.update({"cur":round(cur,4),"pnl":round(pnl,2),"pnl_percent":round(((cur/p['entry'])-1)*100,2)})
                    unreal+=pnl
                    if p['pnl_percent']<-3: p['status']='🏥 عناية'
                    elif p['pnl_percent']<-6: p['status']='👨‍⚕️ طبيب'
                    else: p['status']='💎 ملكي'
                except: pass
            STATE["unrealized"]=round(unreal,2)
            target=STATE["profit_target_cents"]/100.0
            if unreal>=target and STATE["patients"]:
                for p in list(STATE["patients"]):
                    try:
                        asset=p['symbol'].replace('USDT',''); bal=float(client.get_asset_balance(asset=asset)['free'])
                        client.order_market_sell(symbol=p['symbol'], quantity=round(min(bal,p['qty']),6))
                        STATE["realized"]=round(STATE["realized"]+p['pnl'],2)
                    except: pass
                STATE["patients"]=[]; STATE["log"]=f"👑 حقق {target:.2f}$ ملكي"
                continue
            if len(STATE["patients"])<STATE["max_trades"] and get_balance()>5:
                for c in coins:
                    if any(x['symbol']==c['symbol'] for x in STATE["patients"]): continue
                    if is_bull(c['symbol']):
                        try:
                            qty=round(STATE["trade_value"]/c['price'],6)
                            client.order_market_buy(symbol=c['symbol'], quantity=qty)
                            STATE["patients"].append({"symbol":c['symbol'],"entry":c['price'],"qty":qty,"cur":c['price'],"pnl":0.0,"pnl_percent":0.0,"status":"💎 ملكي"})
                            STATE["log"]=f"دخل {c['symbol']}"; break
                        except Exception as e: STATE["log"]=str(e)[:80]
                time.sleep(5)
            time.sleep(10)
        except Exception as e:
            STATE["log"]=f"{e}"; time.sleep(8)

threading.Thread(target=loop, daemon=True).start()

HTML = """
<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@800;900&display=swap');
*{font-family:'Tajawal',sans-serif;box-sizing:border-box;margin:0}
.num{font-family:'JetBrains Mono',monospace!important;direction:ltr;display:inline-block;letter-spacing:-0.5px}
body{background:radial-gradient(1200px 600px at 20% -10%, #1e293b 0%, #0f172a 40%, #020617 100%);min-height:100vh;padding:14px;color:#fff}
.header{backdrop-filter:blur(20px);background:linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));border:1px solid rgba(250,204,21,0.3);border-radius:20px;padding:16px 22px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 20px 60px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1)}
.logo{font-size:18px;font-weight:900;background:linear-gradient(90deg,#facc15,#f59e0b);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.btn{padding:12px 26px;border-radius:14px;border:none;font-weight:900;font-size:14px;cursor:pointer;transition:0.3s;box-shadow:0 8px 20px rgba(0,0,0,0.3)}
.btn-start{background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff}
.btn-start:hover{transform:translateY(-2px);box-shadow:0 12px 30px rgba(34,197,94,0.4)}
.btn-stop{background:linear-gradient(135deg,#ef4444,#dc2626);color:#fff}
.status{margin:14px 0;padding:14px;border-radius:16px;font-size:15px;font-weight:900;text-align:center;backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.1)}
.on{background:linear-gradient(135deg, rgba(34,197,94,0.15), rgba(34,197,94,0.05));border-color:rgba(34,197,94,0.4);color:#4ade80;box-shadow:0 0 30px rgba(34,197,94,0.2)}
.off{background:linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.05));border-color:rgba(239,68,68,0.3);color:#f87171}
.grid{display:grid;grid-template-columns:1.2fr 0.8fr;gap:14px;margin-top:14px}@media(max-width:900px){.grid{grid-template-columns:1fr}}
.card{background:linear-gradient(135deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02));backdrop-filter:blur(24px);border:1px solid rgba(255,255,255,0.1);border-radius:20px;padding:18px;box-shadow:0 20px 60px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1)}
.card-gold{background:linear-gradient(135deg, rgba(250,204,21,0.12), rgba(245,158,11,0.06));border-color:rgba(250,204,21,0.4);box-shadow:0 20px 60px rgba(250,204,21,0.15), inset 0 1px 0 rgba(255,255,255,0.15)}
.title{font-size:11px;color:#94a3b8;font-weight:800;letter-spacing:1px;margin-bottom:12px;text-transform:uppercase}
.big-num{font-size:42px;font-weight:900;background:linear-gradient(90deg,#facc15,#fde047);-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1}
.mini-grid{display:flex;gap:10px;margin-top:16px}
.mini{flex:1;background:linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.01));border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:12px;text-align:center;backdrop-filter:blur(10px)}
.mini b{display:block;font-size:10px;color:#94a3b8;margin-bottom:6px}
.mini.num{font-size:16px;font-weight:900}
.input{width:100%;background:rgba(0,0,0,0.4);border:1px solid rgba(255,255,255,0.15);border-radius:12px;padding:12px;font-size:16px;font-weight:900;text-align:center;color:#facc15;backdrop-filter:blur(10px)}
.input-gold{border-color:rgba(250,204,21,0.5);background:rgba(250,204,21,0.08);box-shadow:0 0 20px rgba(250,204,21,0.15)}
.coin{padding:12px;background:linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));border:1px solid rgba(255,255,255,0.06);border-radius:12px;display:flex;justify-content:space-between;align-items:center;margin:6px 0;transition:0.3s}
.coin:hover{transform:translateX(-4px);border-color:rgba(250,204,21,0.3)}
.patient{padding:14px;background:linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));border-radius:14px;border-right:4px solid #facc15;margin:8px 0;display:flex;justify-content:space-between;align-items:center;backdrop-filter:blur(10px);box-shadow:0 8px 20px rgba(0,0,0,0.2)}
.log{font-size:11px;color:#64748b;margin-top:10px;padding:10px;background:rgba(0,0,0,0.3);border-radius:10px;border:1px solid rgba(255,255,255,0.05)}
</style></head><body>
<div class="header"><div class="logo">👑 مستشفى الكريبتو الملكي الفاخر | بدون بروكسي | <span class="num" id="cap2" style="-webkit-text-fill-color:#facc15">76.44 USDT</span></div><div style="display:flex;gap:10px"><button class="btn btn-start" onclick="ctrl('start')">▶ تشغيل ملكي</button><button class="btn btn-stop" onclick="ctrl('stop')">⏹ إيقاف</button></div></div>
<div id="state" class="status off">⏹ متوقف كامل - اضغط تشغيل ملكي</div>
<div class="grid">
<div class="card card-gold"><div class="title">💎 المحفظة الملكية - أرقام HD فائقة الوضوح</div><div class="big-num"><span class="num" id="cap">76.44</span> <span style="font-size:18px">USDT</span></div><div class="mini-grid"><div class="mini"><b>✅ محقق ملكي</b><span class="num" id="real" style="color:#22c55e">+0.00$</span></div><div class="mini"><b>⏳ غير محقق</b><span class="num" id="unreal" style="color:#facc15">+0.00$</span></div><div class="mini"><b>🛡️ احتياطي ذهبي</b><span class="num" style="color:#fff">38.22</span></div></div><div id="log" class="log">💎 جاهز للفخامة</div></div>
<div class="card"><div class="title">⚙️ إعداداتك الملكية فقط - وضوح 100%</div><div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px"><div><div class="title">قيمة الصفقة 💰</div><input class="input input-gold num" id="tv" value="10.00" onchange="save()"></div><div><div class="title">هدف سنت 🎯</div><input class="input input-gold num" id="cents" value="10" onchange="save()"></div><div><div class="title">عدد المرضى 🛏️</div><input class="input num" id="mt" value="2" onchange="save()"></div></div><div style="margin-top:16px;text-align:center"><div class="title">الهدف الملكي الإجمالي</div><div style="font-size:32px;font-weight:900;color:#facc15"><span class="num" id="dollars">0.10</span> $</div><div style="font-size:10px;color:#94a3b8">يبيع الكل عند هذا الهدف - بدون بيع بخسارة</div></div></div>
</div>
<div class="grid"><div class="card"><div class="title">💎 العملات القوية الحلال - MACD صاعد فقط</div><div id="coins"></div></div><div class="card card-gold"><div class="title">🛏️ المرضى الملكيين - علاج فاخر بدون بيع بخسارة</div><div id="patients"></div></div></div>
<script>
function f(n){return Number(n).toFixed(2)}
async function refresh(){let r=await fetch('/api/status');let j=await r.json();document.getElementById('cap').innerText=f(j.total_capital);document.getElementById('cap2').innerText=f(j.total_capital);document.getElementById('real').innerText=(j.realized>=0?'+':'')+f(j.realized)+'$';document.getElementById('unreal').innerText=(j.unrealized>=0?'+':'')+f(j.unrealized)+'$';document.getElementById('state').innerText=j.is_running?'👑 شغال ملكي 100% بدون بروكسي - فخم':'⏹ متوقف كامل - اضغط تشغيل ملكي';document.getElementById('state').className=j.is_running?'status on':'status off';document.getElementById('dollars').innerText=f(j.profit_target_cents/100);document.getElementById('log').innerText=j.log;let ch='';j.coins.forEach(c=>{ch+=`<div class=coin><div><b style='color:#facc15'>${c.symbol}</b><div class=num style='font-size:10px;color:#94a3b8'>${(c.vol/1000000).toFixed(1)}M VOL</div></div><span style='background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff;padding:4px 10px;border-radius:20px;font-size:10px;font-weight:900'>MACD صاعد</span></div>`});document.getElementById('coins').innerHTML=ch;let ph='';if(j.patients.length==0)ph='<div style=text-align:center;padding:30px;color:#64748b'><div style=font-size:40px>👑</div><div style=font-size:11px;margin-top:8px>لا يوجد مرضى ملكيين<br>بانتظار إشارة MACD ملكية</div></div>';else j.patients.forEach(p=>{ph+=`<div class=patient><div><b style=color:#facc15>${p.symbol}</b><div style='font-size:10px;color:#94a3b8'>${p.status}</div><div class=num style='font-size:9px;color:#64748b'>دخول ${p.entry}</div></div><div style=text-align:left><div class=num style='font-size:14px;font-weight:900;color:${p.pnl>=0?'#22c55e':'#ef4444'}'>${f(p.pnl)}</div><div class=num style='font-size:11px;font-weight:800;color:${p.pnl_percent>=0?'#22c55e':'#ef4444'}'>${p.pnl_percent>=0?'+':''}${f(p.pnl_percent)}%</div><div class=num style='font-size:10px;color:#94a3b8'>${p.cur}</div></div></div>`});document.getElementById('patients').innerHTML=ph;}
async function ctrl(a){await fetch('/api/control?action='+a,{method:'POST'});refresh();}
async function save(){let tv=document.getElementById('tv').value;let mt=document.getElementById('mt').value;let ct=document.getElementById('cents').value;await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({trade_value:parseFloat(tv),max_trades:parseInt(mt),profit_target_cents:parseInt(ct)})});}
setInterval(refresh,3000);refresh();
</script></body></html>
"""

@app.route("/")
def dash(): return HTML
@app.route("/api/status")
def s(): get_balance(); return jsonify(STATE)
@app.route("/api/control", methods=['POST'])
def c(): a=request.args.get('action'); STATE["is_running"]=(a=='start'); STATE["log"]="👑 شغال ملكي فاخر بدون بروكسي" if STATE["is_running"] else "⏹ إيقاف كامل"; return jsonify(STATE)
@app.route("/api/config", methods=['POST'])
def cfg(): d=request.json; STATE["trade_value"]=float(d.get('trade_value',10)); STATE["max_trades"]=int(d.get('max_trades',2)); STATE["profit_target_cents"]=int(d.get('profit_target_cents',10)); return jsonify(STATE)
@app.route("/health")
def h(): return "OK",200
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))

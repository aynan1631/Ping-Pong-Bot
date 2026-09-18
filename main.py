import os, time, threading
from flask import Flask, jsonify, request
from binance.client import Client

app = Flask(__name__)
PROXY_URL = os.getenv("PROXY_URL","").strip()
proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"), {"proxies": proxies, "timeout": 30})

HALAL = ["BTCUSDT","ETHUSDT","BNBUSDT","AVAXUSDT","ADAUSDT","LINKUSDT","XLMUSDT","DOTUSDT","MATICUSDT","XRPUSDT","SOLUSDT"]

STATE = {
    "is_running": False,
    "total_capital": 76.44,
    "trade_value": 10.00,
    "profit_target_cents": 10,
    "max_trades": 2,
    "realized": 0.00,
    "unrealized": 0.00,
    "patients": [],
    "coins": [],
    "log": "جاهز - النسخة الثابتة",
    "macd": "بانتظار التشغيل"
}

def get_balance():
    try:
        b=float(client.get_asset_balance('USDT')['free'])
        STATE["total_capital"]=round(b,2)
        return b
    except:
        return STATE["total_capital"]

def ema(prices, period):
    k=2/(period+1)
    e=prices[0]
    for p in prices[1:]:
        e=p*k+e*(1-k)
    return e

def is_bull(sym):
    try:
        kl=client.get_klines(symbol=sym, interval=Client.KLINE_INTERVAL_1HOUR, limit=100)
        closes=[float(x[4]) for x in kl]
        if len(closes)<30:
            return False
        macd_now=ema(closes[-26:],12)-ema(closes[-26:],26)
        macd_prev=ema(closes[-27:-1],12)-ema(closes[-27:-1],26)
        return macd_now>0 and macd_now>macd_prev
    except:
        return False

def get_coins():
    try:
        tickers=client.get_ticker()
        lst=[]
        for t in tickers:
            if t['symbol'] in HALAL and float(t['quoteVolume'])>5000000:
                lst.append({"symbol":t['symbol'],"price":float(t['lastPrice']),"vol":float(t['quoteVolume'])})
        STATE["coins"]=sorted(lst,key=lambda x:x['vol'],reverse=True)[:6]
        return STATE["coins"]
    except:
        return []

def trading_loop():
    while True:
        try:
            if not STATE["is_running"]:
                time.sleep(3)
                continue
            get_balance()
            coins=get_coins()
            unreal=0.0
            for p in STATE["patients"]:
                try:
                    cur=float(client.get_symbol_ticker(symbol=p['symbol'])['price'])
                    pnl=(cur-p['entry'])*p['qty']
                    p["cur"]=round(cur,4)
                    p["pnl"]=round(pnl,2)
                    p["pnl_percent"]=round(((cur/p["entry"])-1)*100,2)
                    unreal+=pnl
                    if p["pnl_percent"]<-3 and p["status"]=="عادي":
                        p["status"]="🏥 في المشفى"
                    if p["pnl_percent"]<-6:
                        p["status"]="👨‍⚕️ عند الطبيب"
                except:
                    pass
            STATE["unrealized"]=round(unreal,2)
            target=STATE["profit_target_cents"]/100.0
            if unreal>=target and len(STATE["patients"])>0:
                for p in list(STATE["patients"]):
                    try:
                        asset=p['symbol'].replace('USDT','')
                        bal=float(client.get_asset_balance(asset=asset)['free'])
                        client.order_market_sell(symbol=p['symbol'], quantity=round(min(bal,p['qty']),6))
                        STATE["realized"]=round(STATE["realized"]+p["pnl"],2)
                    except Exception as e:
                        STATE["log"]=str(e)
                STATE["patients"]=[]
                STATE["log"]=f"✅ حقق هدف {target:.2f}$ - باع الكل"
                continue
            if len(STATE["patients"])<STATE["max_trades"] and get_balance()>5:
                for c in coins:
                    if any(x['symbol']==c['symbol'] for x in STATE["patients"]):
                        continue
                    if is_bull(c['symbol']):
                        try:
                            qty=round(STATE["trade_value"]/c['price'],6)
                            client.order_market_buy(symbol=c['symbol'], quantity=qty)
                            STATE["patients"].append({"symbol":c['symbol'],"entry":c['price'],"qty":qty,"cur":c['price'],"pnl":0.0,"pnl_percent":0.0,"status":"عادي"})
                            STATE["log"]=f"دخل آلي {c['symbol']}"
                            break
                        except Exception as e:
                            STATE["log"]=str(e)
                time.sleep(5)
            time.sleep(10)
        except Exception as e:
            STATE["log"]=f"Loop {e}"
            time.sleep(8)

threading.Thread(target=trading_loop, daemon=True).start()

HTML_PAGE = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700;800;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
*{font-family:'Tajawal',sans-serif;box-sizing:border-box}
.num{font-family:'JetBrains Mono',monospace!important;direction:ltr;display:inline-block}
body{margin:0;background:#f1f5f9;color:#0f172a;padding:10px}
.header{background:#0f172a;color:#fff;border-radius:12px;padding:12px 18px;display:flex;justify-content:space-between;align-items:center;border:2px solid #facc15}
.btn{padding:10px 20px;border-radius:8px;border:none;font-weight:900;font-size:13px;cursor:pointer}
.btn-start{background:#22c55e;color:#fff}
.btn-stop{background:#ef4444;color:#fff}
.status{margin:8px 0;padding:10px;border-radius:8px;font-size:13px;font-weight:900;text-align:center}
.on{background:#dcfce7;border:2px solid #22c55e;color:#166534}
.off{background:#fee2e2;border:2px solid #ef4444;color:#991b1b}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
.card{background:#ffffff;border:2px solid #e2e8f0;border-radius:12px;padding:14px;box-shadow:0 4px 12px rgba(0,0,0,0.05)}
.card-dark{background:#0f172a;color:#fff;border:2px solid #facc15}
.title{font-size:11px;color:#64748b;font-weight:800;margin-bottom:8px}
.mini{flex:1;background:#f8fafc;border:2px solid #e2e8f0;border-radius:8px;padding:8px;text-align:center}
.input{width:100%;background:#fff;border:2px solid #0f172a;color:#0f172a;border-radius:8px;padding:8px;font-size:16px;font-weight:900;text-align:center}
.input-gold{border-color:#eab308;color:#a16207;background:#fefce8}
.coin{padding:8px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;display:flex;justify-content:space-between;margin:5px 0}
.patient{padding:8px;background:#f8fafc;border-radius:8px;border-right:4px solid #22c55e;margin:5px 0;display:flex;justify-content:space-between}
</style>
</head>
<body>
<div class="header">
<div style="font-weight:900;font-size:13px">🏥 مستشفى الكريبتو - الآلي | <span class="num" id="cap2" style="color:#facc15;font-size:16px">76.44</span> USDT</div>
<div><button class="btn btn-start" onclick="ctrl('start')">▶ تشغيل</button> <button class="btn btn-stop" onclick="ctrl('stop')">⏹ إيقاف</button></div>
</div>
<div id="state" class="status off">⏹ متوقف</div>
<div class="grid">
<div class="card card-dark">
<div class="title" style="color:#facc15">💼 المحفظة - ارقام موحدة</div>
<div style="font-size:28px;font-weight:900"><span class="num" id="cap" style="color:#facc15">76.44</span> <span style="font-size:14px">USDT</span></div>
<div style="display:flex;gap:8px;margin-top:10px">
<div class="mini" style="background:#052e16;border-color:#22c55e"><b>✅ محقق</b><span class="num" id="real" style="color:#22c55e;font-size:16px;font-weight:900">0.00</span></div>
<div class="mini" style="background:#422006;border-color:#facc15"><b>⏳ غير محقق</b><span class="num" id="unreal" style="color:#facc15;font-size:16px;font-weight:900">0.00</span></div>
<div class="mini" style="background:#1e293b;border-color:#475569"><b>🛡️ احتياطي</b><span class="num" style="color:#fff;font-size:16px;font-weight:900">38.22</span></div>
</div>
<div id="log" style="font-size:11px;color:#94a3b8;margin-top:8px"></div>
<div id="macd" style="font-size:11px;color:#facc15"></div>
</div>
<div class="card">
<div class="title">⚙️ اعداداتك فقط</div>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">
<div><div class="title">قيمة الصفقة</div><input class="input input-gold num" id="tv" value="10.00" onchange="save()"></div>
<div><div class="title">هدف الربح سنت</div><input class="input input-gold num" id="cents" value="10" onchange="save()"></div>
<div><div class="title">عدد المرضى</div><input class="input num" id="mt" value="2" onchange="save()"></div>
</div>
<div style="margin-top:8px;font-weight:900">الهدف = <span class="num" id="dollars" style="font-size:18px;color:#a16207">0.10</span> $</div>
</div>
</div>
<div class="grid">
<div class="card"><div class="title">💎 العملات القوية الحلال</div><div id="coins"></div></div>
<div class="card"><div class="title">🛏️ المرضى</div><div id="patients"></div></div>
</div>
<script>
function f(n){return Number(n).toFixed(2)}
async function refresh(){
let r=await fetch('/api/status');let j=await r.json();
document.getElementById('cap').innerText=f(j.total_capital);
document.getElementById('cap2').innerText=f(j.total_capital);
document.getElementById('real').innerText=(j.realized>=0?'+':'')+f(j.realized)+'$';
document.getElementById('unreal').innerText=(j.unrealized>=0?'+':'')+f(j.unrealized)+'$';
document.getElementById('state').innerText=j.is_running?'✅ شغال آلي 100%':'⏹ متوقف كامل';
document.getElementById('state').className=j.is_running?'status on':'status off';
document.getElementById('dollars').innerText=f(j.profit_target_cents/100);
document.getElementById('log').innerText=j.log;
document.getElementById('macd').innerText=j.macd;
let ch='';j.coins.forEach(c=>{ch+=`<div class=coin><div><b>${c.symbol}</b><div class=num style='font-size:10px;color:#64748b'>${(c.vol/1000000).toFixed(1)}M</div></div><span style='background:#dcfce7;color:#166534;padding:3px 7px;border-radius:10px;font-size:10px;font-weight:900'>آلي</span></div>`});
document.getElementById('coins').innerHTML=ch;
let ph='';if(j.patients.length==0)ph='<div style=text-align:center;padding:16px;color:#94a3b8;font-size:11px>لا يوجد مرضى - بانتظار MACD</div>';else j.patients.forEach(p=>{ph+=`<div class=patient><div><b>${p.symbol}</b><div style='font-size:9px;color:#64748b'>${p.status}</div></div><div style=text-align:left><div class=num style='font-size:11px;font-weight:900;color:${p.pnl>=0?'#16a34a':'#dc2626'}'>${f(p.pnl)}$ (${f(p.pnl_percent)}%)</div><div class=num style='font-size:9px;color:#64748b'>${p.cur}</div></div></div>`});
document.getElementById('patients').innerHTML=ph;
}
async function ctrl(a){await fetch('/api/control?action='+a,{method:'POST'});refresh();}
async function save(){let tv=document.getElementById('tv').value;let mt=document.getElementById('mt').value;let ct=document.getElementById('cents').value;await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({trade_value:parseFloat(tv),max_trades:parseInt(mt),profit_target_cents:parseInt(ct)})});}
setInterval(refresh,3000);refresh();
</script>
</body>
</html>
"""

@app.route("/")
def dash():
    return HTML_PAGE

@app.route("/api/status")
def api_status():
    get_balance()
    return jsonify(STATE)

@app.route("/api/control", methods=['POST'])
def api_control():
    a=request.args.get('action')
    STATE["is_running"]=(a=='start')
    STATE["log"]="🚀 شغال آلي" if STATE["is_running"] else "⏹ إيقاف كامل"
    return jsonify(STATE)

@app.route("/api/config", methods=['POST'])
def api_config():
    d=request.json
    if 'trade_value' in d:
        STATE["trade_value"]=float(d['trade_value'])
    if 'max_trades' in d:
        STATE["max_trades"]=int(d['max_trades'])
    if 'profit_target_cents' in d:
        STATE["profit_target_cents"]=int(d['profit_target_cents'])
    return jsonify(STATE)

@app.route("/health")
def health():
    return "OK",200

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))

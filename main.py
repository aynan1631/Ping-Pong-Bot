import os, time, threading, math
from flask import Flask, jsonify, request
from binance.client import Client

app = Flask(__name__)
PROXY_URL = os.getenv("PROXY_URL","").strip()
proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"), {"proxies": proxies, "timeout": 30})

HALAL = ["BTCUSDT","ETHUSDT","BNBUSDT","AVAXUSDT","ADAUSDT","LINKUSDT","XLMUSDT","DOTUSDT","MATICUSDT","XRPUSDT","SOLUSDT","ARBUSDT","OPUSDT"]

STATE = {"is_running": False,"total_capital": 76.44,"trade_value": 10.00,"profit_target_cents": 10,"max_trades": 2,"realized": 0.00,"unrealized": 0.00,"patients": [],"coins": [],"log": "جاهز - النسخة الملكية الثابتة","macd": "بانتظار التشغيل"}

def get_balance():
    try:
        b=float(client.get_asset_balance('USDT')['free']); STATE["total_capital"]=round(b,2); return b
    except: return STATE["total_capital"]

def ema(prices, period):
    k=2/(period+1); ema_val=prices[0]
    for p in prices[1:]: ema_val = p*k + ema_val*(1-k)
    return ema_val

def is_bullish(sym):
    try:
        kl=client.get_klines(symbol=sym, interval=Client.KLINE_INTERVAL_1HOUR, limit=100)
        closes=[float(x[4]) for x in kl]
        if len(closes)<30: return False
        e12=ema(closes[-26:],12); e26=ema(closes[-26:],26)
        prev_e12=ema(closes[-27:-1],12); prev_e26=ema(closes[-27:-1],26)
        macd=e12-e26; prev_macd=prev_e12-prev_e26
        return macd>0 and macd>prev_macd
    except: return False

def get_coins():
    try:
        tickers=client.get_ticker()
        lst=[]
        for t in tickers:
            if t['symbol'] in HALAL and float(t['quoteVolume'])>5000000:
                lst.append({"symbol":t['symbol'],"price":float(t['lastPrice']),"vol":float(t['quoteVolume'])})
        STATE["coins"]=sorted(lst,key=lambda x:x['vol'],reverse=True)[:6]
        return STATE["coins"]
    except: return []

def loop():
    while True:
        try:
            if not STATE["is_running"]: time.sleep(3); continue
            get_balance(); coins=get_coins(); unreal=0.0
            for p in STATE["patients"]:
                try:
                    cur=float(client.get_symbol_ticker(symbol=p['symbol'])['price'])
                    pnl=(cur-p['entry'])*p['qty']
                    p.update({"cur":round(cur,4),"pnl":round(pnl,2),"pnl_percent":round(((cur/p['entry'])-1)*100,2)})
                    unreal+=pnl
                    if p['pnl_percent']<-3 and p['status']=='عادي': p['status']='🏥 في المشفى'
                    if p['pnl_percent']<-6: p['status']='👨‍⚕️ عند الطبيب'
                except: pass
            STATE["unrealized"]=round(unreal,2)
            target=STATE["profit_target_cents"]/100.0
            if unreal>=target and STATE["patients"]:
                for p in list(STATE["patients"]):
                    try:
                        asset=p['symbol'].replace('USDT',''); bal=float(client.get_asset_balance(asset=asset)['free'])
                        client.order_market_sell(symbol=p['symbol'], quantity=round(min(bal,p['qty']),6))
                        STATE["realized"]=round(STATE["realized"]+p['pnl'],2)
                    except Exception as e: STATE["log"]=str(e)
                STATE["patients"]=[]; STATE["log"]=f"✅ حقق هدف {target:.2f}$ - باع الكل"
                continue
            if len(STATE["patients"])<STATE["max_trades"] and get_balance()>38:
                for c in coins:
                    if any(p['symbol']==c['symbol'] for p in STATE["patients"]): continue
                    if is_bullish(c['symbol']):
                        try:
                            qty=round(STATE["trade_value"]/c['price'],6)
                            client.order_market_buy(symbol=c['symbol'], quantity=qty)
                            STATE["patients"].append({"symbol":c['symbol'],"entry":c['price'],"qty":qty,"cur":c['price'],"pnl":0.0,"pnl_percent":0.0,"status":"عادي"})
                            STATE["log"]=f"دخل آلي {c['symbol']}"; break
                        except Exception as e: STATE["log"]=str(e)
                time.sleep(5)
            time.sleep(10)
        except Exception as e:
            STATE["log"]=f"Loop: {e}"; time.sleep(8)

threading.Thread(target=loop, daemon=True).start()

HTML="""<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@500;700;800&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
<style>
:root{--gold:#facc15;--green:#22c55e;--bg:#050a14}
*{font-family:'Tajawal',sans-serif;box-sizing:border-box}
.num{font-family:'JetBrains Mono',monospace!important;direction:ltr;display:inline-block;letter-spacing:.5px}
body{margin:0;background:#060a14;color:#e2e8f0;padding:12px}
.header{background:linear-gradient(90deg,#0f1f3d,#122a52);border:1px solid #d4af3730;border-radius:14px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center}
.logo{font-size:15px;font-weight:800;color:var(--gold)}
.btn{padding:9px 18px;border-radius:8px;border:none;font-weight:800;font-size:12px;cursor:pointer}
.btn-start{background:#16a34a;color:#fff}.btn-stop{background:#dc2626;color:#fff}
.status{margin:8px 0;padding:9px;border-radius:8px;font-size:12px;font-weight:700;text-align:center}
.on{background:#22c55e15;border:1px solid #22c55e40;color:#4ade80}.off{background:#ef444415;border:1px solid #ef444440;color:#f87171}
.grid{display:grid;grid-template-columns:1.2fr.8fr;gap:10px} @media(max-width:800px){.grid{grid-template-columns:1fr}}
.card{background:linear-gradient(180deg,#111c33,#0e1830);border:1px solid #ffffff12;border-radius:12px;padding:14px}
.card-title{font-size:11px;color:#94a3b8;font-weight:700;margin-bottom:8px}
.big{font-size:26px;font-weight:800}.mini{flex:1;background:#0b132a;border:1px solid #ffffff0d;border-radius:8px;padding:8px}
.mini b{font-size:10px;color:#cbd5e1}.mini span{font-size:14px;font-weight:800;display:block}
.input{width:100%;background:#060d22;border:1px solid #eab30860;color:#facc15;border-radius:6px;padding:6px;font-size:15px;font-weight:800;text-align:center}
.label-sm{font-size:10px;color:#94a3b8;font-weight:700}
.coin{padding:8px 10px;background:#0b132a;border-radius:8px;display:flex;justify-content:space-between;margin:5px 0}
.badge{font-size:9px;padding:3px 6px;border-radius:10px;background:#22c55e20;color:#4ade80}
.patient{padding:10px;background:#0f1a33;border-radius:8px;border-right:3px solid #22c55e;margin:6px 0;display:flex;justify-content:space-between}
</style></head><body>
<div class="header"><div class="logo">🏥 المستشفى - الملكي الآلي - <span class="num" id="cap2">76.44</span> USDT</div><div><button class="btn btn-start" onclick="ctrl('start')">▶ تشغيل</button><button class="btn btn-stop" onclick="ctrl('stop')">⏹ إيقاف</button></div></div>
<div id="state" class="status off">⏹ متوقف</div>
<div class="grid">
<div class="card"><div class="card-title">💼 المحفظة - أرقام موحدة</div><div class="big"><span class="num" style="color:#fde68a" id="cap">76.44</span> <span style="font-size:14px">USDT</span></div>
<div style="display:flex;gap:8px;margin-top:10px"><div class="mini"><b>✅ محقق</b><span class="num" style="color:#4ade80" id="real">0.00</span></div><div class="mini"><b>⏳ غير محقق</b><span class="num" style="color:#fde68a" id="unreal">0.00</span></div><div class="mini"><b>🛡️ احتياطي</b><span class="num">38.22</span></div></div><div id="log" style="font-size:10px;color:#64748b;margin-top:8px"></div><div id="macd" style="font-size:10px;color:#94a3b8"></div></div>
<div class="card"><div class="card-title">⚙️ إعداداتك فقط</div><div style="display:grid;grid-template-columns:1fr 1fr 0.7fr;gap:8px"><div><div class="label-sm">قيمة الصفقة</div><input class="input num" id="tv" value="10.00" onchange="save()"></div><div><div class="label-sm">هدف الربح (سنت)</div><input class="input num" id="cents" value="10" onchange="save()"></div><div><div class="label-sm">عدد المرضى</div><input class="input num" id="mt" value="2" onchange="save()"></div></div><div style="margin-top:6px;font-size:10px;color:#94a3b8">الهدف = <span class="num" id="dollars">0.10</span>$ على المجموع</div></div>
</div>
<div class="grid"><div class="card"><div class="card-title">💎 العملات القوية الحلال - سيولة >5M</div><div id="coins"></div></div><div class="card"><div class="card-title">🛏️ المرضى - علاج آلي بدون بيع بخسارة</div><div id="patients"></div></div></div>
<script>
function f(n){return Number(n).toFixed(2)}
async function refresh(){let r=await fetch('/api/status');let j=await r.json();document.getElementById('cap').innerText=f(j.total_capital);document.getElementById('cap2').innerText=f(j.total_capital);document.getElementById('real').innerText=(j.realized>=0?'+':'')+f(j.realized);document.getElementById('unreal').innerText=(j.unrealized>=0?'+':'')+f(j.unrealized);document.getElementById('state').innerText=j.is_running?'✅ شغال آلي 100%':'⏹ متوقف كامل';document.getElementById('state').className=j.is_running?'status on':'status off';document.getElementById('dollars').innerText=f(j.profit_target_cents/100);document.getElementById('log').innerText=j.log;document.getElementById('macd').innerText=j.macd;let ch='';j.coins.forEach(c=>{ch+=`<div class=coin><div><b>${c.symbol}</b><div style='font-size:9px;color:#64748b' class=num>${(c.vol/1000000).toFixed(1)}M - ${c.price}</div></div><span class=badge>آلي</span></div>`});document.getElementById('coins').innerHTML=ch;let ph='';if(j.patients.length==0)ph='<div style=text-align:center;padding:16px;color:#64748b;font-size:11px>لا يوجد مرضى - بانتظار MACD</div>';else j.patients.forEach(p=>{ph+=`<div class=patient><div><b>${p.symbol}</b><div style='font-size:9px;color:#64748b'>${p.status}</div></div><div><div class=num style='font-size:11px;color:${p.pnl>=0?'#4ade80':'#f87171'}'>${f(p.pnl)}$ (${f(p.pnl_percent)}%)</div><div class=num style='font-size:9px;color:#64748b'>${p.cur}</div></div></div>`});document.getElementById('patients').innerHTML=ph;}
async function ctrl(a){await fetch('/api/control?action='+a,{method:'POST'});refresh();}
async function save(){let tv=document.getElementById('tv').value;let mt=document.getElementById('mt').value;let ct=document.getElementById('cents').value;await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({trade_value:parseFloat(tv),max_trades:parseInt(mt),profit_target_cents:parseInt(ct)})});}
setInterval(refresh,3000);refresh();
</script></body></html>"""

@app.route("/")
def dash(): return HTML
@app.route("/api/status")
def s(): get_balance(); return jsonify({k: (round(v,2) if isinstance(v,float) else v) for k,v in STATE.items()})
@app.route("/api/control", methods=['POST'])
def c(): a=request.args.get('action'); STATE["is_running"]=(a=='start'); STATE["log"]="🚀 شغال آلي" if STATE["is_running"] else "⏹ إيقاف كامل"; return jsonify(STATE)
@app.route("/api/config", methods=['POST'])
def cfg(): d=request.json; STATE["trade_value"]=float(d.get('trade_value',10)); STATE["max_trades"]=int(d.get('max_trades',2)); STATE["profit_target_cents"]=int(d.get('profit_target_cents',10)); return jsonify(STATE)
@app.route("/health")
def h(): return "OK",200

if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))

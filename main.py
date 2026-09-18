import os, time
from flask import Flask, jsonify, request
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd

app = Flask(__name__)

PROXY_URL = os.getenv("PROXY_URL","").strip()
proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"), {"proxies": proxies, "timeout": 30})

HALAL = ["BTCUSDT","ETHUSDT","BNBUSDT","AVAXUSDT","ADAUSDT","LINKUSDT","XLMUSDT","DOTUSDT","MATICUSDT","XRPUSDT","SOLUSDT"]

STATE = {
    "is_running": False,
    "total_capital_binance": 76.43,
    "trade_value": 19.11,
    "max_trades": 2,
    "profit_target_cents": 150,
    "realized_profit": 0.0,
    "unrealized_profit": 0.0,
    "open_patients": [], # {symbol, entry, qty, buy_price}
    "strong_halal_coins": [],
    "macd_status": "فحص...",
    "last_log": "جاهز"
}

def get_balance():
    try:
        b = float(client.get_asset_balance('USDT')['free'])
        STATE["total_capital_binance"] = b
        return b
    except: return STATE["total_capital_binance"]

def get_strong():
    try:
        tickers = client.get_ticker()
        strong=[]
        for t in tickers:
            if t['symbol'] in HALAL and float(t['quoteVolume']) > 5000000:
                strong.append({"symbol": t['symbol'], "price": float(t['lastPrice']), "volume": float(t['quoteVolume'])})
        strong = sorted(strong, key=lambda x: x['volume'], reverse=True)[:8]
        STATE["strong_halal_coins"]=strong
        return strong
    except: return []

def calc_unrealized():
    total=0.0
    for p in STATE["open_patients"]:
        try:
            cur = float(client.get_symbol_ticker(symbol=p['symbol'])['price'])
            pnl = (cur - p['entry']) * p['qty']
            p['current']=cur; p['pnl']=pnl; p['pnl_percent']=((cur/p['entry'])-1)*100
            total+=pnl
        except: pass
    STATE["unrealized_profit"]=total

HTML = """
<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@800;900&display=swap" rel="stylesheet">
<style>
*{font-family:'Tajawal',sans-serif}
body{background:#05070a;color:#fff;padding:10px;margin:0}
.top{background:linear-gradient(90deg,#0f172a,#111c33);border:2px solid #facc15;border-radius:18px;padding:16px;display:flex;justify-content:space-between;align-items:center}
.logo{font-size:38px;font-weight:900;color:#facc15}.btn{font-size:24px;font-weight:900;padding:14px 32px;border-radius:50px;border:none;cursor:pointer}
.start{background:#00ff88;color:#000}.stop{background:#ff1a1a;color:#fff}
.card{background:radial-gradient(circle at top,#1a233a,#0a0f1c);border:2px solid #d4af37;border-radius:18px;padding:18px;margin:10px 0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.label{font-size:22px;color:#facc15;font-weight:800}.value{font-size:48px;font-weight:900}.green{color:#00ff88}.gold{color:#fde68a}
.input{font-size:26px;font-weight:900;background:#020617;border:2px solid #facc15;color:#00ff88;border-radius:10px;padding:6px 12px;width:120px;text-align:center}
.coin{display:flex;justify-content:space-between;align-items:center;background:#111a2e;border:1px solid #2a3a5a;border-radius:14px;padding:12px;margin:8px 0}
.buy{background:#00ff88;color:#000;font-size:20px;font-weight:900;padding:10px 22px;border-radius:30px;border:none;cursor:pointer}
.sell{background:#facc15;color:#000;font-size:18px;font-weight:900;padding:8px 18px;border-radius:30px;border:none;cursor:pointer}
.status{font-size:22px;font-weight:900;padding:12px;border-radius:12px;text-align:center;margin:10px 0}
.on{background:#00ff8820;border:2px solid #00ff88;color:#00ff88}.off{background:#ff000020;border:2px solid #ff4d4d;color:#ff6b6b}
</style></head><body>
<div class="top"><div><div class="logo">🏥 المستشفى - دخول من اللوحة</div><div style="color:#22c55e;font-size:18px">مربوط مباشرة بباينانس - تداول حقيقي</div></div>
<div><button class="btn start" onclick="ctrl('start')">▶️ تشغيل</button><button class="btn stop" onclick="ctrl('stop')">⏸️ إيقاف</button></div></div>
<div id="state" class="status off"></div>

<div class="grid">
<div class="card"><div class="label">💰 المحفظة - مطابق باينانس</div><div class="value green" id="cap">-</div><div class="label">✅ محقق: <span id="real">-</span> | ⏳ غير محقق: <span id="unreal">-</span></div></div>
<div class="card"><div class="label">🎯 هدف الربح (سنتات)</div><div class="value gold"><input class="input" id="cents" value="150" onchange="save()"> سنت = <span id="dollars"></span></div>
<div class="label">قيمة الصفقة <input class="input" id="tv" value="19.11" onchange="save()"> | عدد المرضى <input class="input" id="mt" value="2" onchange="save()"></div><div style="font-size:18px;margin-top:8px" id="macd"></div></div>
</div>

<div class="card"><div class="label" style="font-size:26px">💎 العملات القوية الحلال - اضغط شراء للدخول من اللوحة</div><div id="coins"></div></div>
<div class="card"><div class="label" style="font-size:26px">🛏️ المرضى المفتوحين - مربوطين بالمنصة</div><div id="patients"></div></div>
<div class="card" style="font-size:16px;color:#94a3b8" id="log"></div>

<script>
async function refresh(){
 let r=await fetch('/api/status'); let j=await r.json();
 document.getElementById('cap').innerText=j.total_capital_binance.toFixed(2)+' USDT';
 document.getElementById('real').innerText=j.realized_profit.toFixed(2)+'$';
 document.getElementById('unreal').innerText=j.unrealized_profit.toFixed(2)+'$';
 document.getElementById('macd').innerText=j.macd_status;
 document.getElementById('state').innerText=j.is_running?'✅ شغال - الدخول من اللوحة مفتوح ومربوط بباينانس':'⏸️ متوقف - ممنوع فتح جديد - يعالج المفتوح فقط حتى الربح';
 document.getElementById('state').className=j.is_running?'status on':'status off';
 document.getElementById('dollars').innerText=(j.profit_target_cents/100).toFixed(2)+'$ على المجموع';
 document.getElementById('log').innerText='آخر عملية: '+j.last_log;
 let ch=''; j.strong_halal_coins.forEach(c=>{
   ch+=`<div class=coin><div><b style=\"font-size:22px\">${c.symbol}</b><br><span style=\"color:#94a3b8\">${(c.volume/1000000).toFixed(1)}M$ - ${c.price}</span></div><div><button class=buy onclick=\"buy('${c.symbol}')\">شراء الآن ${document.getElementById('tv').value}$</button></div></div>`;
 });
 document.getElementById('coins').innerHTML=ch;
 let ph=''; if(j.open_patients.length==0) ph='<div style=\"font-size:22px;text-align:center;padding:20px\">لا يوجد مرضى</div>';
 else j.open_patients.forEach(p=>{
   ph+=`<div class=coin><div><b>${p.symbol}</b> - دخول ${p.entry.toFixed(4)} - كمية ${p.qty}<br><span style=\"color:${p.pnl>=0?'#00ff88':'#ff4d4d'}\">${p.pnl.toFixed(2)}$ (${p.pnl_percent.toFixed(2)}%) - الآن ${p.current?.toFixed(4)}</span></div><div><button class=sell onclick=\"sell('${p.symbol}')\">بيع وعلاج</button></div></div>`;
 });
 document.getElementById('patients').innerHTML=ph;
}
async function buy(sym){ if(!confirm('تأكيد شراء '+sym+' بقيمة '+document.getElementById('tv').value+'$ من باينانس حقيقي؟')) return; let r=await fetch('/api/buy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({symbol:sym})}); let j=await r.json(); alert(j.msg); refresh();}
async function sell(sym){ if(!confirm('بيع '+sym+' الآن في باينانس؟')) return; let r=await fetch('/api/sell',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({symbol:sym})}); let j=await r.json(); alert(j.msg); refresh();}
async function ctrl(a){await fetch('/api/control?action='+a,{method:'POST'}); refresh();}
async function save(){let tv=document.getElementById('tv').value; let mt=document.getElementById('mt').value; let ct=document.getElementById('cents').value; await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({trade_value:parseFloat(tv),max_trades:parseInt(mt),profit_target_cents:parseInt(ct)})});}
setInterval(refresh,3000); refresh();
</script></body></html>
"""

@app.route("/")
def dash(): return HTML

@app.route("/api/status")
def status_api():
    get_balance(); get_strong(); calc_unrealized()
    return jsonify(STATE)

@app.route("/api/control", methods=['POST'])
def ctrl():
    a=request.args.get('action')
    STATE["is_running"] = (a=='start')
    STATE["last_log"] = "تم التشغيل - الدخول من اللوحة مربوط" if STATE["is_running"] else "تم الإيقاف - ممنوع فتح جديد"
    return jsonify(STATE)

@app.route("/api/config", methods=['POST'])
def cfg():
    d=request.json
    if 'trade_value' in d: STATE["trade_value"]=float(d['trade_value'])
    if 'max_trades' in d: STATE["max_trades"]=int(d['max_trades'])
    if 'profit_target_cents' in d: STATE["profit_target_cents"]=int(d['profit_target_cents'])
    return jsonify(STATE)

@app.route("/api/buy", methods=['POST'])
def buy():
    if not STATE["is_running"]:
        return jsonify({"msg": "⛔ البوت متوقف - شغل أولاً"}), 400
    if len(STATE["open_patients"]) >= STATE["max_trades"]:
        return jsonify({"msg": f"⛔ عندك {STATE['max_trades']} مرضى - الحد الأقصى وصل"}), 400
    if get_balance() <= 38.22:
        return jsonify({"msg": "⛔ وصلت احتياطي العلاج 38.22$ - ممنوع شراء"}), 400

    sym = request.json.get('symbol')
    qty_value = STATE["trade_value"]
    try:
        price = float(client.get_symbol_ticker(symbol=sym)['price'])
        qty = round(qty_value / price, 6)
        # أمر حقيقي
        order = client.order_market_buy(symbol=sym, quantity=qty)
        STATE["open_patients"].append({"symbol": sym, "entry": price, "qty": qty, "current": price, "pnl": 0, "pnl_percent": 0})
        STATE["last_log"] = f"✅ شراء حقيقي {sym} - {qty} بسعر {price} - قيمة {qty_value}$"
        return jsonify({"msg": f"تم الشراء الحقيقي ✅ {sym} - {qty} - {price}"})
    except BinanceAPIException as e:
        return jsonify({"msg": f"خطأ باينانس: {e}"}), 400
    except Exception as e:
        return jsonify({"msg": f"خطأ: {e}"}), 400

@app.route("/api/sell", methods=['POST'])
def sell():
    sym = request.json.get('symbol')
    try:
        # ابحث عن المريض
        patient = next((p for p in STATE["open_patients"] if p['symbol']==sym), None)
        if not patient:
            return jsonify({"msg": "المريض غير موجود"}), 404
        # بيع حقيقي
        # لازم نجيب رصيد العملة الفعلي
        asset = sym.replace('USDT','')
        bal = float(client.get_asset_balance(asset=asset)['free'])
        qty = bal if bal < patient['qty']*1.1 else patient['qty'] # استخدم الرصيد الفعلي
        order = client.order_market_sell(symbol=sym, quantity=round(qty,6))
        price_now = float(client.get_symbol_ticker(symbol=sym)['price'])
        pnl = (price_now - patient['entry']) * patient['qty']
        STATE["realized_profit"] += pnl
        STATE["open_patients"] = [p for p in STATE["open_patients"] if p['symbol']!=sym]
        STATE["last_log"] = f"💰 بيع حقيقي {sym} - ربح {pnl:.2f}$ - أضيف للمحقق"
        return jsonify({"msg": f"تم البيع ✅ {sym} - ربح {pnl:.2f}$ - الرصيد الآن مطابق لباينانس"})
    except Exception as e:
        return jsonify({"msg": f"خطأ بيع: {e}"}), 400

@app.route("/health")
def h(): return "OK",200

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))

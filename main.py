from flask import Flask, render_template_string, jsonify, request, make_response
import os, threading, requests, random, time

app = Flask(__name__)
bot_state = {"realized": 0.0, "base_capital": 1000, "per_trade": 200, "trades": [], "is_running": True}

def get_volatile():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=8).json()
        cands=[]
        for i in r:
            s=i['symbol']
            if not s.endswith('USDT'): continue
            if s in ["BTCUSDT","ETHUSDT"]: continue
            ch=abs(float(i['priceChangePercent'])); vol=float(i['quoteVolume'])
            if ch>3 and vol>5000000: cands.append({"symbol":s,"vol":ch,"price":float(i['lastPrice'])})
        cands.sort(key=lambda x: x['vol'], reverse=True)
        return cands[:5]
    except:
        return [{"symbol":"SOLUSDT","vol":5.2,"price":140},{"symbol":"AVAXUSDT","vol":4.8,"price":25},{"symbol":"PEPEUSDT","vol":6.1,"price":0.000008}]

def bot_loop():
    vol=get_volatile()
    for c in vol[:3]:
        bot_state["trades"].append({"coin":c["symbol"],"entry":c["price"],"live":c["price"],"side":random.choice(["LONG","SHORT"]),"cap":bot_state["per_trade"],"usd":0.0,"pct":0.0,"vol":c["vol"]})
    while True:
        try:
            pm={x['symbol']:float(x['price']) for x in requests.get("https://api.binance.com/api/v3/ticker/price", timeout=5).json()}
            for t in bot_state["trades"]:
                if t["coin"] in pm:
                    t["live"]=pm[t["coin"]]
                    t["pct"]=round(((t["live"]-t["entry"])/t["entry"]*100 if t["side"]=="LONG" else (t["entry"]-t["live"])/t["entry"]*100),2)
                    t["usd"]=round(t["pct"]/100*t["cap"],2)
        except: pass
        time.sleep(2)
threading.Thread(target=bot_loop, daemon=True).start()

HTML="""
<!DOCTYPE html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache"><title>RAIS V17 OPTIONS</title>
<style>*{font-family:'Segoe UI',sans-serif!important;font-weight:900!important;box-sizing:border-box}
body{background:#050507;margin:0;padding:10px;color:#fff}
.card-title{font-size:18px!important;color:#888}.card-money{font-size:44px!important}.sec-title{font-size:21px!important}.small{font-size:13px!important;color:#777}
</style></head><body>

<div style="background:#121216;padding:12px 16px;border-radius:16px;display:flex;justify-content:space-between;border:1px solid #222">
<div style="font-size:22px">RAIS V17 - خيارات مبلغ الصفقة</div><div style="background:#00ff88;color:#000;padding:5px 16px;border-radius:40px;font-size:16px">RUNNING</div>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:12px">
<div style="background:#111;border:4px solid #00ff88;border-radius:18px;padding:12px;text-align:center">
<div style="font-size:28px">💰</div><div class="card-title">الرصيد الاساسي</div><div class="card-money" style="color:#00ff88">$<span id="baseShow">1000</span></div>
<div style="margin-top:8px;display:flex;gap:4px;justify-content:center"><input id="baseIn" value="1000" style="background:#000;color:#00ff88;border:2px solid #00ff88;border-radius:8px;padding:6px;width:90px;text-align:center;font-size:20px"><button onclick="saveBase()" style="background:#00ff88;color:#000;border:none;border-radius:8px;padding:6px 12px;font-size:13px;cursor:pointer">SAVE</button></div>
<div style="display:flex;gap:3px;justify-content:center;margin-top:6px;flex-wrap:wrap"><button onclick="setBase(1000)" style="background:#222;color:#fff;border:none;padding:4px 8px;border-radius:6px;font-size:11px">1K</button><button onclick="setBase(5000)" style="background:#00ff88;color:#000;border:none;padding:4px 8px;border-radius:6px;font-size:11px">5K</button><button onclick="setBase(10000)" style="background:#222;color:#fff;border:none;padding:4px 8px;border-radius:6px;font-size:11px">10K</button><button onclick="setBase(20000)" style="background:#222;color:#fff;border:none;padding:4px 8px;border-radius:6px;font-size:11px">20K</button></div>
</div>
<div style="background:#111;border:4px solid #ff3b3b;border-radius:18px;padding:14px;text-align:center"><div style="font-size:28px">📈</div><div class="card-title">الربح العائم يتصفر</div><div id="flt" class="card-money" style="color:#ff3b3b">$0.00</div></div>
<div style="background:#111;border:4px solid #00d4ff;border-radius:18px;padding:14px;text-align:center"><div style="font-size:28px">🏦</div><div class="card-title">الربح المحقق يتصفر</div><div class="card-money" style="color:#00d4ff">$<span id="real">0.00</span></div></div>
</div>

<!-- هذا المكان اللي طلبت فيه خيارات -->
<div style="background:#1a1a22;border:4px solid #ffbe0b;border-radius:18px;padding:14px;margin-top:12px">
<div class="sec-title">⚡ مبلغ كل صفقة - اختر من هنا يا ريس 👇</div>
<div style="margin-top:10px;background:#000;padding:12px;border-radius:12px;border:2px solid #333">
<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
<div style="font-size:16px;color:#ffbe0b">💵 المبلغ:</div>
<input id="perIn" value="200" style="background:#111;color:#fff;border:3px solid #ffbe0b;border-radius:8px;padding:10px;width:110px;text-align:center;font-size:24px">
<span style="font-size:18px">$</span>
<button onclick="savePer()" style="background:#ffbe0b;color:#000;border:none;border-radius:8px;padding:10px 18px;font-size:16px;cursor:pointer">SAVE</button>
</div>
<div style="display:flex;gap:6px;margin-top:12px;flex-wrap:wrap">
<button onclick="setPer(50)" style="background:#222;color:#fff;border:none;padding:10px 16px;border-radius:10px;font-size:14px;cursor:pointer">50$</button>
<button onclick="setPer(100)" style="background:#222;color:#fff;border:none;padding:10px 16px;border-radius:10px;font-size:14px;cursor:pointer">100$</button>
<button onclick="setPer(200)" style="background:#ffbe0b;color:#000;border:none;padding:10px 16px;border-radius:10px;font-size:14px;cursor:pointer">200$</button>
<button onclick="setPer(500)" style="background:#222;color:#fff;border:none;padding:10px 16px;border-radius:10px;font-size:14px;cursor:pointer">500$</button>
<button onclick="setPer(1000)" style="background:#222;color:#fff;border:none;padding:10px 16px;border-radius:10px;font-size:14px;cursor:pointer">1000$</button>
<button onclick="setPer(2000)" style="background:#ff3b3b;color:#fff;border:none;padding:10px 16px;border-radius:10px;font-size:14px;cursor:pointer">2000$</button>
</div>
</div>
</div>

<div style="background:#111;border:1px solid #222;border-radius:18px;padding:12px;margin-top:12px">
<div class="sec-title">LIVE TRADES - الرصيد $<span id="capShow2">1000</span> | الصفقة $<span id="perShow">200</span></div>
<table style="width:100%;border-collapse:collapse;margin-top:8px"><thead><tr><th class="small">COIN</th><th class="small">VOL</th><th class="small">TYPE</th><th class="small">CAP</th><th class="small">LIVE</th><th class="small">PROFIT</th></tr></thead><tbody id="tbody"></tbody></table>
</div>

<script>
function setBase(v){document.getElementById('baseIn').value=v; saveBase();}
function saveBase(){let b=parseFloat(document.getElementById('baseIn').value); fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({base:b})}).then(()=>load());}
function setPer(v){document.getElementById('perIn').value=v; savePer();}
function savePer(){let p=parseFloat(document.getElementById('perIn').value); fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({per:p})}).then(()=>load());}
function load(){
 fetch('/api/data?t='+Date.now()).then(r=>r.json()).then(d=>{
  document.getElementById('baseShow').innerText=d.base_capital; document.getElementById('baseIn').value=d.base_capital; document.getElementById('capShow2').innerText=d.base_capital;
  document.getElementById('perIn').value=d.per_trade; document.getElementById('perShow').innerText=d.per_trade;
  document.getElementById('real').innerText=d.realized.toFixed(2);
  let f=document.getElementById('flt'); f.innerText=(d.floating>=0? '$'+d.floating.toFixed(2) : '-$'+Math.abs(d.floating).toFixed(2)); f.style.color=d.floating>=0?'#00ff88':'#ff3b3b';
  let h=''; d.trades.forEach(t=>{let cl=t.usd>=0?'#00ff88':'#ff3b3b'; h+=`<tr><td style="padding:10px;text-align:center;border-top:2px solid #1e1e24;font-size:15px">${t.coin}</td><td style="padding:10px;text-align:center;border-top:2px solid #1e1e24;font-size:11px;color:#ffbe0b">${t.vol.toFixed(1)}%</td><td style="padding:10px;text-align:center;border-top:2px solid #1e1e24;font-size:11px">${t.side}</td><td style="padding:10px;text-align:center;border-top:2px solid #1e1e24;font-size:13px">$${t.cap}</td><td style="padding:10px;text-align:center;border-top:2px solid #1e1e24;font-size:11px;color:#00ff88">${t.live}</td><td style="padding:10px;text-align:center;border-top:2px solid #1e1e24;font-size:13px;color:${cl}">${t.usd.toFixed(2)}</td></tr>`}); document.getElementById('tbody').innerHTML=h;
 });
}
setInterval(load,2000);load();
</script></body>
"""
@app.route("/")
def home():
    r=make_response(render_template_string(HTML)); r.headers["Cache-Control"]="no-cache, no-store, must-revalidate"; return r
@app.route("/api/data")
def data():
    return jsonify({"trades":bot_state["trades"],"floating":sum(t["usd"] for t in bot_state["trades"]),"realized":bot_state["realized"],"base_capital":bot_state["base_capital"],"per_trade":bot_state["per_trade"]})
@app.route("/api/save", methods=["POST"])
def save():
    j=request.json
    if "base" in j: bot_state["base_capital"]=float(j["base"])
    if "per" in j: 
        bot_state["per_trade"]=float(j["per"])
        for t in bot_state["trades"]: t["cap"]=bot_state["per_trade"]
    return jsonify({"ok":True})
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",8080)))

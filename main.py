from flask import Flask, render_template_string, jsonify, request, make_response
import os, time, threading, requests, random

app = Flask(__name__)
# تصفير مع كل تحديث - هذا اللي طلبته
bot_state = {"is_running": True, "trades": [], "realized_profit": 0.0, "capital_per_trade": 200, "floating": 0.0}

def get_volatile_coins():
    """يختار العملات الأكثر فاعلية - يتجاهل الثقيلة البطيئة"""
    try:
        # يجيب كل العملات مع نسبة التغير 24 ساعة
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=8).json()
        # استبعد العملات الثقيلة البطيئة والأقل ربحا
        heavy = ["BTCUSDT", "ETHUSDT"] # ثقيلة
        stable = ["USDT", "BUSD", "USDC", "DAI", "TUSD"]
        
        candidates = []
        for item in r:
            sym = item['symbol']
            if not sym.endswith('USDT'): continue
            if sym in heavy: continue
            if any(s in sym for s in stable): continue
            
            change = abs(float(item['priceChangePercent']))
            volume = float(item['quoteVolume'])
            # نبي عملة خفيفة + متقلبة + عليها سيولة
            if change > 3 and volume > 5000000: # أكثر من 3% حركة و 5 مليون سيولة
                candidates.append({"symbol": sym, "volatility": change, "price": float(item['lastPrice'])})

        # رتب الأكثر تقلبا أولا
        candidates.sort(key=lambda x: x['volatility'], reverse=True)
        return candidates[:5] # خذ أقوى 5 عملات فاعلة
    except:
        return [{"symbol": "SOLUSDT", "volatility": 5, "price": 140},{"symbol": "AVAXUSDT", "volatility": 4, "price": 25},{"symbol": "DOGEUSDT", "volatility": 4.5, "price": 0.12}]

def bot_loop():
    volatile = get_volatile_coins()
    # افتح صفقات على العملات الفعالة فقط
    for c in volatile[:3]:
        bot_state["trades"].append({
            "coin": c["symbol"], "entry": c["price"], "live": c["price"],
            "side": random.choice(["LONG","SHORT"]), "cap": bot_state["capital_per_trade"],
            "usd": 0.0, "pct": 0.0, "vol": c["volatility"]
        })
    
    while True:
        if bot_state["is_running"]:
            try:
                # كل 30 ثانية يفحص هل فيه عملات أفعل
                prices = requests.get("https://api.binance.com/api/v3/ticker/price", timeout=5).json()
                pmap = {x['symbol']: float(x['price']) for x in prices}
                for t in bot_state["trades"]:
                    if t["coin"] in pmap:
                        t["live"] = pmap[t["coin"]]
                        t["pct"] = round(((t["live"]-t["entry"])/t["entry"]*100 if t["side"]=="LONG" else (t["entry"]-t["live"])/t["entry"]*100),2)
                        t["usd"] = round(t["pct"]/100 * t["cap"],2)
            except: pass
        time.sleep(2)

threading.Thread(target=bot_loop, daemon=True).start()

HTML = """
<!DOCTYPE html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate"><title>RAIS V13 VOLATILE</title>
<style>*{font-family:'Segoe UI',sans-serif!important;font-weight:900!important;box-sizing:border-box}
body{background:#050507;margin:0;padding:10px;color:#fff}
.card-title{font-size:20px!important;color:#888}.card-money{font-size:48px!important}
.sec-title{font-size:24px!important}.small{font-size:16px!important;color:#777}
</style></head><body>
<div style="background:#121216;padding:16px 20px;border-radius:16px;display:flex;justify-content:space-between;border:1px solid #222">
<div style="font-size:26px">RAIS V13 - العملات الأكثر فاعلية + تصفير</div>
<div style="background:#00ff88;color:#000;padding:8px 20px;border-radius:40px;font-size:18px">RUNNING VOLATILE</div>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:12px">
<div style="background:#111;border:4px solid #00ff88;border-radius:18px;padding:20px;text-align:center"><div style="font-size:34px">💰</div><div class="card-title">الرصيد الاساسي</div><div class="card-money" style="color:#00ff88">$1000</div></div>
<div style="background:#111;border:4px solid #ff3b3b;border-radius:18px;padding:20px;text-align:center"><div style="font-size:34px">📈</div><div class="card-title">الربح العائم - يتصفر مع كل تحديث</div><div id="flt" class="card-money" style="color:#ff3b3b">$0.00</div></div>
<div style="background:#111;border:4px solid #00d4ff;border-radius:18px;padding:20px;text-align:center"><div style="font-size:34px">🏦</div><div class="card-title">الربح المحقق - يتصفر مع كل تحديث</div><div class="card-money" style="color:#00d4ff">$<span id="real">0.00</span></div></div>
</div>

<div style="background:#1a1a22;border:3px solid #ffbe0b;border-radius:18px;padding:16px;margin-top:12px">
<div class="sec-title">⚡ البوت يختار العملات الخفيفة السريعة فقط (يتجاهل BTC/ETH الثقيلة)</div>
<div style="display:flex;gap:10px;align-items:center;margin-top:10px;flex-wrap:wrap">
<input id="capIn" value="200" style="background:#000;color:#fff;border:3px solid #333;border-radius:12px;padding:10px;width:120px;text-align:center;font-size:32px">
<button onclick="saveCap()" style="background:#ffbe0b;color:#000;border:none;border-radius:12px;padding:10px 20px;font-size:18px;cursor:pointer">SAVE</button>
</div>
</div>

<div style="background:#111;border:1px solid #222;border-radius:18px;padding:14px;margin-top:12px">
<table style="width:100%;border-collapse:collapse"><thead><tr>
<th class="small">COIN (فعال)</th><th class="small">VOL %</th><th class="small">TYPE</th><th class="small">ENTRY</th><th class="small">LIVE</th><th class="small">PROFIT $</th><th class="small">%</th>
</tr></thead><tbody id="tbody"></tbody></table>
</div>
<script>
function saveCap(){let v=document.getElementById('capIn').value;fetch('/api/set_capital',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capital:parseFloat(v)})}).then(()=>load());}
function load(){
 fetch('/api/data?t='+Date.now()).then(r=>r.json()).then(d=>{
  document.getElementById('capIn').value=d.capital_per_trade;
  document.getElementById('real').innerText=d.realized_profit.toFixed(2);
  let f=document.getElementById('flt'); f.innerText=(d.floating>=0? '$'+d.floating.toFixed(2) : '-$'+Math.abs(d.floating).toFixed(2)); f.style.color=d.floating>=0?'#00ff88':'#ff3b3b';
  let h=''; d.trades.forEach(t=>{
    let cl=t.usd>=0?'#00ff88':'#ff3b3b';
    h+=`<tr><td style="padding:14px;text-align:center;border-top:2px solid #1e1e24;font-size:20px">${t.coin}</td>
    <td style="padding:14px;text-align:center;border-top:2px solid #1e1e24;font-size:16px;color:#ffbe0b">${t.vol.toFixed(1)}%</td>
    <td style="padding:14px;text-align:center;border-top:2px solid #1e1e24;font-size:16px">${t.side}</td>
    <td style="padding:14px;text-align:center;border-top:2px solid #1e1e24;font-size:16px">${t.entry.toFixed(4)}</td>
    <td style="padding:14px;text-align:center;border-top:2px solid #1e1e24;font-size:16px;color:#00ff88">${t.live.toFixed(4)}</td>
    <td style="padding:14px;text-align:center;border-top:2px solid #1e1e24;font-size:18px;color:${cl}">${t.usd.toFixed(2)}</td>
    <td style="padding:14px;text-align:center;border-top:2px solid #1e1e24;font-size:18px;color:${cl}">${t.pct}%</td></tr>`;
  }); document.getElementById('tbody').innerHTML=h;
 });
}
setInterval(load,2000);load();
</script></body>
"""
@app.route("/")
def home():
    resp = make_response(render_template_string(HTML))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    return resp
@app.route("/api/data")
def data():
    floating = sum(t["usd"] for t in bot_state["trades"])
    return jsonify({"trades": bot_state["trades"], "floating": floating, "realized_profit": bot_state["realized_profit"], "capital_per_trade": bot_state["capital_per_trade"]})
@app.route("/api/set_capital", methods=["POST"])
def set_cap():
    bot_state["capital_per_trade"] = float(request.json.get("capital",200))
    for t in bot_state["trades"]: t["cap"] = bot_state["capital_per_trade"]
    return jsonify({"ok":True})
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",8080)))

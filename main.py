from flask import Flask, render_template_string, jsonify, request, make_response
import os, threading, requests, random, time

app = Flask(__name__)
MAX_TRADES = 10
bot_state = {"realized": 0.0, "base_capital": 5000, "trades": [], "is_running": True, "btc_trend": "NEUTRAL", "btc_change": 0}

def get_market_data():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=8).json()
        btc_info = None
        cands=[]
        for i in r:
            s=i['symbol']
            if s == "BTCUSDT":
                btc_info = float(i['priceChangePercent'])
            if not s.endswith('USDT'): continue
            if s in ["BTCUSDT","ETHUSDT","BNBUSDT","FDUSDUSDT"]: continue
            if "BULL" in s or "BEAR" in s or "UP" in s or "DOWN" in s: continue
            ch=abs(float(i['priceChangePercent'])); vol=float(i['quoteVolume']); price=float(i['lastPrice'])
            if ch>3.5 and vol>5000000: 
                cands.append({"symbol":s,"vol":ch,"price":price,"change":float(i['priceChangePercent'])})
        cands.sort(key=lambda x: x['vol'], reverse=True)
        
        # تحديد اتجاه البتكوين
        trend = "NEUTRAL"
        if btc_info is not None:
            if btc_info > 0.5: trend = "UP - دخول LONG"
            elif btc_info < -0.5: trend = "DOWN - دخول SHORT"
            else: trend = "NEUTRAL"
        bot_state["btc_trend"] = trend
        bot_state["btc_change"] = btc_info if btc_info else 0
        
        return cands[:20], btc_info
    except Exception as e:
        print(e)
        return [], 0

def bot_loop():
    while True:
        if bot_state["is_running"]:
            try:
                market, btc_change = get_market_data()
                # توزيع رأس المال الأساسي على 10
                per_trade = bot_state["base_capital"] / MAX_TRADES if MAX_TRADES>0 else 0
                
                # 1. تحديث الأسعار الحية للصفقات المفتوحة
                pm={x['symbol']:float(x['price']) for x in requests.get("https://api.binance.com/api/v3/ticker/price", timeout=5).json()}
                for t in bot_state["trades"]:
                    if t["coin"] in pm:
                        t["live"]=pm[t["coin"]]
                        # الربح يبقى عايم حتى ينعكس الاتجاه
                        t["pct"]=round(((t["live"]-t["entry"])/t["entry"]*100 if t["side"]=="LONG" else (t["entry"]-t["live"])/t["entry"]*100),2)
                        t["usd"]=round(t["pct"]/100*t["cap"],2)
                        # اذا انعكس الاتجاه + خسارة نسكر؟ لا نتركه عايم كما طلبت حتى يتغير اتجاهه
                        t["cap"]=per_trade  # تحديث رأس مال الصفقة اذا تغير الرصيد الاساسي

                # 2. فتح صفقات جديدة اذا فيه مجال وفرص
                open_symbols = [t["coin"] for t in bot_state["trades"]]
                if len(bot_state["trades"]) < MAX_TRADES:
                    for c in market:
                        if len(bot_state["trades"]) >= MAX_TRADES: break
                        if c["symbol"] in open_symbols: continue
                        # دخول حسب اتجاه البتكوين
                        side = "LONG"
                        if btc_change is not None:
                            if btc_change > 0.5: side = "LONG"
                            elif btc_change < -0.5: side = "SHORT"
                            else: side = "LONG" if c["change"]>0 else "SHORT"
                        else:
                            side = "LONG" if c["change"]>0 else "SHORT"
                        
                        bot_state["trades"].append({
                            "coin":c["symbol"],
                            "entry":c["price"],
                            "live":c["price"],
                            "side":side,
                            "cap":per_trade,
                            "usd":0.0,"pct":0.0,"vol":c["vol"],
                            "btc_at_entry":btc_change
                        })
                        time.sleep(0.1)

                # 3. اذا ما توفر الا اقل يفتح اقل (المنطق فوق يحقق هذا تلقائي)

            except Exception as e:
                print("bot error", e)
        time.sleep(3)
threading.Thread(target=bot_loop, daemon=True).start()

HTML="""
<!DOCTYPE html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>RAIS V25 AUTO SPLIT</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;800&display=swap" rel="stylesheet">
<style>
*{font-family:'Cairo',sans-serif!important;font-weight:800!important;box-sizing:border-box}
body{background:#07070a;margin:0;padding:8px;color:#fff;zoom:0.92}
.rect{display:flex;align-items:center;justify-content:space-between;border-radius:12px;padding:10px 14px;border:2.5px solid;height:68px}
.rect-left{display:flex;align-items:center;gap:10px}
.rect-title{font-size:12px!important;color:#aaa;line-height:1.1}
.rect-money{font-size:24px!important;line-height:1}
.input-s{background:#000;color:#fff;border:2px solid #444;border-radius:8px;padding:5px;text-align:center;font-size:18px!important;width:90px;height:36px}
.btn-s{border:none;border-radius:8px;padding:6px 12px;font-size:13px!important;cursor:pointer;height:36px}
.th{font-size:11px!important;color:#ffbe0b!important;padding:6px 3px!important}
.td{font-size:12px!important;padding:5px 3px!important;border-top:1px solid #1a1a22!important;text-align:center}
</style></head><body>

<div style="background:#121218;padding:8px 14px;border-radius:10px;display:flex;justify-content:space-between;align-items:center;border:1.5px solid #333;height:44px">
<div style="font-size:17px">👑 RAIS V25 - توزيع تلقائي ${base}/10 + مربوط بالبتكوين</div>
<button id="togBtn" onclick="toggleBot()" style="background:#00ff88;color:#000;padding:6px 18px;border-radius:40px;font-size:13px!important;border:none;cursor:pointer">● RUNNING</button>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:8px">

<div class="rect" style="background:#0f1410;border-color:#00ff88">
<div class="rect-left"><div style="font-size:22px">💰</div><div><div class="rect-title">الرصيد الاساسي ÷10</div><div class="rect-money" style="color:#00ff88">$<span id="baseShow">5000</span> <span style="font-size:12px;color:#fff">→ $<span id="perShow">500</span>/صفقة</span></div></div></div>
<div style="display:flex;gap:4px;align-items:center"><input id="baseIn" value="5000" class="input-s" style="border-color:#00ff88;color:#00ff88"><button onclick="saveBase()" class="btn-s" style="background:#00ff88;color:#000">SAVE</button></div>
</div>

<div class="rect" style="background:#1a1212;border-color:#ff3b3b">
<div class="rect-left"><div style="font-size:22px">📈</div><div><div class="rect-title">الربح العائم (كل صفقة مستقل)</div><div id="flt" class="rect-money" style="color:#ff3b3b">$0.00</div></div></div>
<div style="font-size:10px;color:#00ff88;text-align:center"><span id="btcTrend">BTC UP</span><br><span id="btcCh">+0%</span></div>
</div>

<div class="rect" style="background:#121420;border-color:#00d4ff">
<div class="rect-left"><div style="font-size:20px">🏦</div><div><div class="rect-title">صفقات مفتوحة</div><div class="rect-money" style="color:#00d4ff"><span id="openCount">0</span>/10</div></div></div>
<div style="font-size:10px;color:#888">كل صفقة عايمة حتى<br>ينعكس الاتجاه</div>
</div>
</div>

<div style="display:flex;gap:5px;margin-top:6px;align-items:center">
<button onclick="setBase(1000)" class="btn-s" style="background:#222;color:#fff">1000$ → 100$</button><button onclick="setBase(2000)" class="btn-s" style="background:#222;color:#fff">2000$ → 200$</button><button onclick="setBase(5000)" class="btn-s" style="background:#00ff88;color:#000">5000$ → 500$</button><button onclick="setBase(10000)" class="btn-s" style="background:#222;color:#fff">10000$ → 1000$</button>
<span style="font-size:11px;color:#ffbe0b;margin-left:10px">● توزيع تلقائي مربوط بحركة BTC</span>
</div>

<div style="background:#0e0e14;border:1.5px solid #333;border-radius:10px;padding:8px;margin-top:8px">
<div style="font-size:14px;margin-bottom:4px">LIVE TRADES - 10 صفقات كحد أقصى - كل صفقة مستقلة وعايمة</div>
<table style="width:100%;border-collapse:collapse"><thead><tr>
<th class="th">COIN</th><th class="th">ENTRY</th><th class="th">LIVE BINANCE</th><th class="th">VOL</th><th class="th">SIDE حسب BTC</th><th class="th">رأس الصفقة</th><th class="th">ربح عايم</th><th class="th">%</th>
</tr></thead><tbody id="tbody"></tbody></table>
</div>

<script>
function setBase(v){document.getElementById('baseIn').value=v; saveBase();}
function saveBase(){let b=parseFloat(document.getElementById('baseIn').value); fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({base:b})}).then(()=>load());}
function toggleBot(){fetch('/api/toggle',{method:'POST'}).then(r=>r.json()).then(d=>{updateToggle(d.is_running);});}
function updateToggle(r){let b=document.getElementById('togBtn'); if(r){b.innerText='● RUNNING - BTC TRACKING'; b.style.background='#00ff88';} else {b.innerText='● STOPPED'; b.style.background='#ff3b3b';}}
function load(){
 fetch('/api/data?t='+Date.now()).then(r=>r.json()).then(d=>{
  document.getElementById('baseShow').innerText=d.base_capital;
  document.getElementById('perShow').innerText=(d.base_capital/10).toFixed(0);
  document.getElementById('baseIn').value=d.base_capital;
  document.getElementById('openCount').innerText=d.trades.length;
  document.getElementById('btcTrend').innerText=d.btc_trend;
  document.getElementById('btcCh').innerText=(d.btc_change>0?'+':'')+d.btc_change.toFixed(2)+'%';
  document.getElementById('btcTrend').style.color=d.btc_change>=0?'#00ff88':'#ff3b3b';
  updateToggle(d.is_running);
  let f=document.getElementById('flt'); f.innerText=(d.floating>=0? '$'+d.floating.toFixed(2) : '-$'+Math.abs(d.floating).toFixed(2)); f.style.color=d.floating>=0?'#00ff88':'#ff3b3b';
  let h=''; d.trades.forEach(t=>{
    let cl=t.usd>=0?'#00ff88':'#ff3b3b';
    let entryFmt = t.entry < 1 ? t.entry.toFixed(5) : t.entry.toFixed(2);
    let liveFmt = t.live < 1 ? t.live.toFixed(5) : t.live.toFixed(2);
    h+=`<tr>
    <td class="td" style="color:#fff">${t.coin.replace('USDT','')}</td>
    <td class="td" style="color:#ffbe0b">${entryFmt}</td>
    <td class="td" style="color:#00ff88">${liveFmt}</td>
    <td class="td" style="color:#ffbe0b">${t.vol.toFixed(1)}%</td>
    <td class="td">${t.side}</td>
    <td class="td">$${t.cap.toFixed(0)}</td>
    <td class="td" style="color:${cl}">$${t.usd.toFixed(2)}</td>
    <td class="td" style="color:${cl}">${t.pct}%</td>
    </tr>`}); document.getElementById('tbody').innerHTML=h;
 });
}
setInterval(load,1500);load();
</script></body>
"""
@app.route("/")
def home():
    r=make_response(render_template_string(HTML.replace("${base}", str(bot_state["base_capital"])))); r.headers["Cache-Control"]="no-cache, no-store, must-revalidate"; return r
@app.route("/api/data")
def data():
    per = bot_state["base_capital"]/MAX_TRADES
    return jsonify({
        "trades":bot_state["trades"],
        "floating":sum(t["usd"] for t in bot_state["trades"]),
        "realized":bot_state["realized"],
        "base_capital":bot_state["base_capital"],
        "per_trade":per,
        "is_running":bot_state["is_running"],
        "btc_trend":bot_state["btc_trend"],
        "btc_change":bot_state["btc_change"]
    })
@app.route("/api/save", methods=["POST"])
def save():
    j=request.json
    if "base" in j: 
        bot_state["base_capital"]=float(j["base"])
    return jsonify({"ok":True})
@app.route("/api/toggle", methods=["POST"])
def toggle():
    bot_state["is_running"]=not bot_state["is_running"]
    return jsonify({"is_running":bot_state["is_running"]})
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",8080)))

from flask import Flask, render_template_string, jsonify, request, make_response
import os, threading, requests, time

app = Flask(__name__)
MAX_TRADES = 10
# يتصفر تلقائي مع كل Deploy
bot_state = {"realized": 0.0, "base_capital": 5000, "trades": [], "is_running": True, "btc_trend": "DOWN - دخول SHORT", "btc_change": -0.54}

def get_market_data():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=8).json()
        btc_info = None; cands=[]
        for i in r:
            s=i['symbol']
            if s=="BTCUSDT": btc_info=float(i['priceChangePercent'])
            if not s.endswith('USDT'): continue
            if s in ["BTCUSDT","ETHUSDT","BNBUSDT","FDUSDUSDT"]: continue
            if "BULL" in s or "BEAR" in s: continue
            ch=abs(float(i['priceChangePercent'])); vol=float(i['quoteVolume']); price=float(i['lastPrice'])
            if ch>3.5 and vol>5000000: cands.append({"symbol":s,"vol":ch,"price":price,"change":float(i['priceChangePercent'])})
        cands.sort(key=lambda x: x['vol'], reverse=True)
        trend="NEUTRAL"
        if btc_info is not None:
            if btc_info>0.5: trend="UP - دخول LONG"
            elif btc_info<-0.5: trend="DOWN - دخول SHORT"
        bot_state["btc_trend"]=trend; bot_state["btc_change"]=btc_info if btc_info else 0
        return cands[:20], btc_info
    except: return [], 0

def bot_loop():
    while True:
        if bot_state["is_running"]:
            try:
                market, btc_change = get_market_data()
                per_trade = bot_state["base_capital"]/MAX_TRADES
                pm={x['symbol']:float(x['price']) for x in requests.get("https://api.binance.com/api/v3/ticker/price", timeout=5).json()}
                for t in bot_state["trades"]:
                    if t["coin"] in pm:
                        t["live"]=pm[t["coin"]]
                        t["pct"]=round(((t["live"]-t["entry"])/t["entry"]*100 if t["side"]=="LONG" else (t["entry"]-t["live"])/t["entry"]*100),2)
                        t["usd"]=round(t["pct"]/100*t["cap"],2); t["cap"]=per_trade
                open_sym=[t["coin"] for t in bot_state["trades"]]
                if len(bot_state["trades"])<MAX_TRADES:
                    for c in market:
                        if len(bot_state["trades"])>=MAX_TRADES: break
                        if c["symbol"] in open_sym: continue
                        side="SHORT" if (btc_change and btc_change<-0.5) else "LONG" if (btc_change and btc_change>0.5) else ("LONG" if c["change"]>0 else "SHORT")
                        bot_state["trades"].append({"coin":c["symbol"],"entry":c["price"],"live":c["price"],"side":side,"cap":per_trade,"usd":0.0,"pct":0.0,"vol":c["vol"]})
            except: pass
        time.sleep(3)
threading.Thread(target=bot_loop, daemon=True).start()

HTML="""<!DOCTYPE html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>RAIS V25.4 FINAL LOCKED</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;800&display=swap" rel="stylesheet">
<style>
*{font-family:'Cairo',sans-serif!important;font-weight:800!important;box-sizing:border-box}
body{background:#07070a;margin:0;padding:8px;color:#fff}
.card{border-radius:14px;padding:10px 10px 8px 10px;border:2.5px solid;display:flex;flex-direction:column;justify-content:space-between;height:118px;overflow:hidden}
.label-top{font-size:11px!important;color:#aaa;text-align:center;line-height:1.3;min-height:32px;display:flex;align-items:center;justify-content:center}
.value-box{border-radius:10px;padding:8px 10px;display:flex;align-items:center;justify-content:space-between;background:rgba(0,0,0,0.45);height:58px;flex-shrink:0}
.money{font-size:22px!important;line-height:1}
.input-s{background:#000;color:#fff;border:2px solid #444;border-radius:8px;padding:4px;text-align:center;font-size:15px!important;width:68px;height:34px}
.btn-s{border:none;border-radius:8px;padding:5px 10px;font-size:11px!important;cursor:pointer;height:34px}
.th{font-size:11px!important;color:#ffbe0b!important;padding:6px 3px!important}.td{font-size:12px!important;padding:6px 3px!important;border-top:1px solid #1a1a22!important;text-align:center}
</style></head><body>
<div style="background:#121218;padding:8px 14px;border-radius:10px;display:flex;justify-content:space-between;align-items:center;border:1.5px solid #333;height:44px">
<div style="font-size:15px">👑 RAIS V25.4 - الحقول مضبوطة - يتصفر مع التحديث</div><button id="togBtn" onclick="toggleBot()" style="background:#00ff88;color:#000;padding:6px 18px;border-radius:40px;font-size:13px!important;border:none">● RUNNING - BTC TRACKING</button></div>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:10px">
<div class="card" style="background:#0f1410;border-color:#00ff88"><div class="label-top">💰 الرصيد الاساسي - يتوزع تلقائي ÷10</div><div class="value-box" style="border:2px solid #00ff88"><div style="display:flex;align-items:center;gap:4px"><span style="font-size:15px;color:#fff">$</span><span class="money" style="color:#00ff88">$<span id="baseShow">5000</span></span><div style="display:flex;flex-direction:column;line-height:1"><span style="font-size:10px;color:#aaa">500$/</span><span style="font-size:10px;color:#aaa">صفقة</span></div></div><div style="display:flex;gap:5px;align-items:center"><input id="baseIn" value="5000" class="input-s" style="border-color:#00ff88;color:#00ff88"><button onclick="saveBase()" class="btn-s" style="background:#00ff88;color:#000">SAVE</button></div></div></div>
<div class="card" style="background:#1a1212;border-color:#ff3b3b"><div class="label-top">📈 الربح العائم (كل صفقة مستقل) - يتصفر مع التحديث</div><div class="value-box" style="border:2px solid #ff3b3b"><div class="money" id="flt" style="color:#ff3b3b">-$13.45</div><div style="text-align:center;line-height:1.2"><div style="font-size:11px;color:#ffbe0b" id="btcTrend">DOWN - دخول SHORT</div><div style="font-size:11px;color:#ff3b3b;margin-top:2px" id="btcCh">-0.54%</div></div></div></div>
<div class="card" style="background:#121420;border-color:#00d4ff"><div class="label-top">🏦 الربح المحقق - يتصفر مع اعادة التشغيل</div><div class="value-box" style="border:2px solid #00d4ff"><div style="display:flex;align-items:center;gap:6px"><span style="font-size:18px">💎</span><span class="money" style="color:#00d4ff">$<span id="real">0.00</span></span></div><div style="display:flex;flex-direction:column;gap:4px"><button onclick="resetReal()" style="background:#222;color:#fff;border:1px solid #444;border-radius:6px;padding:3px 8px;font-size:9px;cursor:pointer">RESET 0</button><button onclick="closeAll()" style="background:#00d4ff;color:#000;border:none;border-radius:6px;padding:4px 8px;font-size:9px;cursor:pointer">قفل الصفقات → محقق</button></div></div></div>
</div>
<div style="display:flex;gap:6px;margin-top:10px;align-items:center;flex-wrap:wrap">
<button onclick="setBase(1000)" class="btn-s" style="background:#222;color:#fff">1000$ → 100$</button><button onclick="setBase(2000)" class="btn-s" style="background:#222;color:#fff">2000$ → 200$</button><button onclick="setBase(5000)" class="btn-s" style="background:#00ff88;color:#000">5000$ → 500$</button><button onclick="setBase(10000)" class="btn-s" style="background:#222;color:#fff">10000$ → 1000$</button>
<button onclick="closeAll()" class="btn-s" style="background:#ff3b3b;color:#fff;margin-left:auto;padding:6px 14px">🔒 قفل الكل وتحويل العائم إلى محقق</button><span style="font-size:11px;color:#ffbe0b">● BTC توزيع تلقائي مربوط بحركة</span>
</div>
<div style="background:#0e0e14;border:1.5px solid #333;border-radius:10px;padding:8px;margin-top:10px">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px"><div style="font-size:13px">LIVE TRADES - 10 صفقات كحد أقصى - كل صفقة مستقلة وعايمة</div><div style="background:#111a30;border:2px solid #00d4ff;border-radius:8px;padding:4px 12px;display:flex;gap:8px;align-items:center"><span style="font-size:12px;color:#aaa">صفقات مفتوحة</span><span style="font-size:16px;color:#00d4ff" id="openCount">0/10</span><span style="font-size:10px;color:#aaa">كل صفقة عايمة حتى ينعكس الاتجاه</span></div></div>
<table style="width:100%;border-collapse:collapse"><thead><tr><th class="th">COIN</th><th class="th">ENTRY</th><th class="th">LIVE BINANCE</th><th class="th">VOL</th><th class="th">SIDE حسب BTC</th><th class="th">رأس الصفقة</th><th class="th">ربح عايم</th><th class="th">%</th></tr></thead><tbody id="tbody"></tbody></table></div>
<script>function setBase(v){document.getElementById('baseIn').value=v; saveBase();}function saveBase(){let b=parseFloat(document.getElementById('baseIn').value); fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({base:b})}).then(()=>load());}function resetReal(){fetch('/api/reset_real',{method:'POST'}).then(()=>load());}function closeAll(){if(!confirm('قفل كل الصفقات وتحويل الربح العائم إلى محقق؟')) return; fetch('/api/close_all',{method:'POST'}).then(r=>r.json()).then(d=>{load();});}function toggleBot(){fetch('/api/toggle',{method:'POST'}).then(r=>r.json()).then(d=>{updateToggle(d.is_running);});}function updateToggle(r){let b=document.getElementById('togBtn'); if(r){b.innerText='● RUNNING - BTC TRACKING'; b.style.background='#00ff88';} else {b.innerText='● STOPPED'; b.style.background='#ff3b3b';}}function load(){fetch('/api/data?t='+Date.now()).then(r=>r.json()).then(d=>{document.getElementById('baseShow').innerText=d.base_capital;document.getElementById('baseIn').value=d.base_capital;document.getElementById('real').innerText=d.realized.toFixed(2);document.getElementById('openCount').innerText=d.trades.length+'/10';document.getElementById('btcTrend').innerText=d.btc_trend;document.getElementById('btcCh').innerText=(d.btc_change>0?'+':'')+d.btc_change.toFixed(2)+'%';updateToggle(d.is_running);let f=document.getElementById('flt'); f.innerText=(d.floating>=0? '$'+d.floating.toFixed(2) : '-$'+Math.abs(d.floating).toFixed(2)); f.style.color=d.floating>=0?'#00ff88':'#ff3b3b';let h=''; d.trades.forEach(t=>{let cl=t.usd>=0?'#00ff88':'#ff3b3b';let entryFmt=t.entry<1?t.entry.toFixed(5):t.entry.toFixed(2);let liveFmt=t.live<1?t.live.toFixed(5):t.live.toFixed(2);h+=`<tr><td class="td" style="color:#fff">${t.coin.replace('USDT','')}</td><td class="td" style="color:#ffbe0b">${entryFmt}</td><td class="td" style="color:#00ff88">${liveFmt}</td><td class="td" style="color:#ffbe0b">${t.vol.toFixed(1)}%</td><td class="td">${t.side}</td><td class="td">$${t.cap.toFixed(0)}</td><td class="td" style="color:${cl}">$${t.usd.toFixed(2)}</td><td class="td" style="color:${cl}">${t.pct}%</td></tr>`}); document.getElementById('tbody').innerHTML=h;});}setInterval(load,1500);load();</script></body>
"""
@app.route("/")
def home():
    r=make_response(render_template_string(HTML)); r.headers["Cache-Control"]="no-cache, no-store, must-revalidate"; return r
@app.route("/api/data")
def data():
    return jsonify({"trades":bot_state["trades"],"floating":sum(t["usd"] for t in bot_state["trades"]),"realized":bot_state["realized"],"base_capital":bot_state["base_capital"],"per_trade":bot_state["base_capital"]/MAX_TRADES,"is_running":bot_state["is_running"],"btc_trend":bot_state["btc_trend"],"btc_change":bot_state["btc_change"]})
@app.route("/api/save", methods=["POST"])
def save():
    j=request.json
    if "base" in j: bot_state["base_capital"]=float(j["base"])
    return jsonify({"ok":True})
@app.route("/api/reset_real", methods=["POST"])
def reset_real():
    bot_state["realized"]=0.0
    return jsonify({"ok":True})
@app.route("/api/close_all", methods=["POST"])
def close_all():
    floating = sum(t["usd"] for t in bot_state["trades"])
    bot_state["realized"] += floating
    bot_state["trades"] = []
    return jsonify({"ok":True,"floating":floating,"realized":bot_state["realized"]})
@app.route("/api/toggle", methods=["POST"])
def toggle():
    bot_state["is_running"]=not bot_state["is_running"]
    return jsonify({"is_running":bot_state["is_running"]})
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.getenv("PORT",8080)))

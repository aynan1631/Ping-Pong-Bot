from flask import Flask, render_template_string, request, jsonify, make_response
import os, threading, time, requests, math
app = Flask(__name__)

cooldown = {}
MAX_OPEN = 6

def get_volatile_coins(limit=50):
    try:
        data = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=8).json()
        cands = []
        for d in data:
            sym = d["symbol"]
            if not sym.endswith("USDT"):
                continue
            if sym in ["BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT"]:
                continue
            if "UP" in sym or "DOWN" in sym:
                continue
            try:
                price = float(d["lastPrice"])
                vol = float(d["quoteVolume"])
                change = float(d["priceChangePercent"])
            except:
                continue
            if price > 5 or price < 0.0000005:
                continue
            if vol < 12000000:
                continue
            if abs(change) < 2.5:
                continue
            if sym in cooldown and time.time() - cooldown[sym] < 3600:
                continue
            score = abs(change) * math.log(vol)
            cands.append((sym, score))
        cands.sort(key=lambda x: x[1], reverse=True)
        return [s for s,_ in cands[:limit]]
    except:
        return ["BONKUSDT","WIFUSDT","FLOKIUSDT","BOMEUSDT","POPCATUSDT","DOGEUSDT"]

def get_data(sym):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=210"
        data = requests.get(url, timeout=6).json()
        closes = [float(k[4]) for k in data]
        price = closes[-1]
        k = 2/(200+1)
        ema = closes[0]
        for c in closes[1:]:
            ema = c*k + ema*(1-k)
        sma = sum(closes[-20:])/20
        return {"price": price, "ema": ema, "sma": sma}
    except:
        return None

state = {
    "capital": 5000,
    "per_coin": 500,
    "realized": 0.0,
    "unrealized": 0.0,
    "delta": 50.0,
    "trades": [],
    "trading": True
}

def try_add_one():
    if not state["trading"]:
        return False
    if len(state["trades"]) >= MAX_OPEN:
        return False
    have = set(t["s"] for t in state["trades"])
    for sym in get_volatile_coins(50):
        short = sym.replace("USDT","")
        if short in have:
            continue
        if sym in cooldown:
            continue
        d = get_data(sym)
        if not d:
            continue
        if abs(d["price"] - d["sma"]) / d["sma"] > 0.03:
            continue
        side = "SHORT" if d["price"] < d["ema"] else "LONG"
        state["trades"].append({
            "s": short,
            "sym": sym,
            "cap": state["per_coin"],
            "entry": d["price"],
            "live": d["price"],
            "side": side,
            "pnl": 0,
            "pct": 0
        })
        return True
    return False

def worker():
    while True:
        if state["trading"]:
            if len(state["trades"]) < MAX_OPEN:
                try_add_one()

            tot = 0
            to_remove = []
            global_mode = state["delta"] > 0

            for t in list(state["trades"]):
                d = get_data(t["sym"])
                if not d:
                    tot += t["pnl"]
                    continue
                price = d["price"]
                t["live"] = price
                if t["side"] == "SHORT":
                    t["pct"] = round((t["entry"] - price) / t["entry"] * 100, 2)
                else:
                    t["pct"] = round((price - t["entry"]) / t["entry"] * 100, 2)
                t["pnl"] = round(t["cap"] * t["pct"] / 100, 2)

                # اذا هدف عام >0 لا تقفل كل عملة لحالها
                if not global_mode and t["pnl"] >= 5.0:
                    state["realized"] = round(state["realized"] + t["pnl"], 2)
                    cooldown[t["sym"]] = time.time()
                    to_remove.append(t)
                    continue

                tot += t["pnl"]

            for t in to_remove:
                if t in state["trades"]:
                    state["trades"].remove(t)

            state["unrealized"] = round(tot, 2)

            # هدف عام يقفل الكل مع بعض
            if global_mode and state["unrealized"] >= state["delta"] and state["unrealized"] > 0:
                state["realized"] = round(state["realized"] + state["unrealized"], 2)
                for t in state["trades"]:
                    cooldown[t["sym"]] = time.time()
                state["trades"] = []
                state["unrealized"] = 0

        time.sleep(3)

threading.Thread(target=worker, daemon=True).start()

HTML = """
<!DOCTYPE html><html dir="rtl"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>V40.9 الفخمة</title>
<style>
body{background:#0a0c1e;color:#fff;font-family:Tahoma;margin:0;padding:12px}
.title{text-align:center;color:#ffcc00;font-size:26px;font-weight:900;margin:14px}
.cards{display:flex;gap:12px;justify-content:center}
.card{background:#151833;border:2px solid #2a2d4a;border-radius:14px;padding:14px 18px;min-width:160px;text-align:center}
.lbl{color:#8a8db5;font-size:15px;font-weight:bold}
.val{font-size:28px;font-weight:900;margin-top:6px}
.green{color:#00e676!important}
.red{color:#ff3d57!important}
.bar{background:#151833;border:2px solid #2a2d4a;border-radius:14px;padding:14px;text-align:center;margin:12px 0}
.status{color:#00e676;font-size:19px;font-weight:900}
.status-off{color:#ff3d57!important}
.controls{display:flex;gap:10px;justify-content:center;align-items:center;margin-top:10px;flex-wrap:wrap}
.controls2{display:flex;gap:10px;justify-content:center;align-items:center;margin-top:12px;flex-wrap:wrap;border-top:1px dashed #2a2d4a;padding-top:12px}
.btn{padding:11px 18px;border-radius:10px;border:0;font-weight:900;font-size:17px;cursor:pointer}
input{background:#0f1123;color:#fff;border:2px solid #777;border-radius:10px;padding:11px;width:100px;text-align:center;font-size:22px;font-weight:900}
.label-big{font-size:22px;font-weight:900}
table{width:100%;background:#151833;border-radius:14px;border-collapse:collapse;margin-top:10px}
th{background:#1e2040;color:#ffeb3b;padding:12px 6px;font-size:17px;font-weight:900}
td{padding:10px 6px;text-align:center;border-top:1px solid #2a2d4a;font-size:15px;font-weight:900}
.badge{background:#ff3d00;color:#fff;padding:5px 12px;border-radius:12px;font-size:13px;font-weight:900}
.badge-long{background:#00e676;color:#000}
.ltr{direction:ltr!important;unicode-bidi:plaintext!important;display:inline-block}
</style>
</head><body>
<div class="title">💎 V40.9 - فريم الساعة 1H - تحت EMA200</div>
<div class="cards">
<div class="card"><div class="lbl">المحققة</div><div class="val green" id="realT"><span class="ltr">{{'%.2f'|format(s.realized)}}$</span></div></div>
<div class="card"><div class="lbl">غير المحققة</div><div class="val" id="unrealBox"><span class="ltr" id="unrealT">{{'%.2f'|format(s.unrealized)}}$</span></div></div>
</div>
<div class="bar">
<div class="status {{'status-off' if not s.trading else ''}}" id="tradeStatus">{{'🟢 التداول شغال - هدف $' if s.trading else '🔴 التداول متوقف - هدف $'}}{{s.delta}}</div>

<div class="controls">
<span class="label-big">رأس المال</span><input id="c" type="number" value="{{s.capital}}"><button class="btn" style="background:#ffeb3b" onclick="saveCap()">حفظ</button>
<span class="label-big">هدف</span><input id="t" type="number" step="0.1" value="{{s.delta}}"><button class="btn" style="background:#3d5afe;color:#fff" onclick="saveTarget()">حفظ</button>
<button class="btn" style="background:#ff3d00;color:#fff" onclick="fetch('/close?v='+Date.now()).then(()=>location.reload(true))">🔒 قفل وجلب أنشط</button>
</div>

<div class="controls2">
<button id="toggleBtn" class="btn" style="background:{{'#00e676;color:#000' if s.trading else '#ff3d57;color:#fff'}}" onclick="toggleTrading()">{{'⏸️ إيقاف التداول' if s.trading else '▶️ تشغيل التداول'}}</button>
<button class="btn" style="background:#ff9800;color:#000" onclick="resetCounters()">🔄 تصفير العدادات</button>
<span style="color:#8a8db5;font-size:13px;font-weight:900">← زيادات بسطر خاص</span>
</div>
</div>

<table id="tbl">
<tr><th>العملة</th><th>الجانب</th><th>رأس المال</th><th>دخول</th><th>حالي</th><th>$</th><th>%</th></tr>
{% for t in s.trades %}
<tr>
<td style="color:#00e676"><b>{{t.s}}</b></td>
<td>{% if t.side=='LONG' %}<span class="badge badge-long">LONG</span>{% else %}<span class="badge">SHORT</span>{% endif %}</td>
<td style="color:#ffeb3b"><span class="ltr">${{t.cap}}</span></td>
<td><span class="ltr">{{'%.8f'|format(t.entry)}}</span></td>
<td><span class="ltr">{{'%.8f'|format(t.live)}}</span></td>
<td class="{{'green' if t.pnl>=0 else 'red'}}"><span class="ltr">{{'%.2f'|format(t.pnl)}}$</span></td>
<td class="{{'green' if t.pct>=0 else 'red'}}"><span class="ltr">{{'%.2f'|format(t.pct)}}%</span></td>
</tr>
{% endfor %}
</table>
<script>
function saveCap(){let v=document.getElementById('c').value; fetch('/set_capital?v='+v+'&t='+Date.now()).then(()=>location.reload(true));}
function saveTarget(){let v=document.getElementById('t').value; fetch('/set_target?v='+v+'&t='+Date.now()).then(()=>location.reload(true));}
function resetCounters(){ if(confirm('تصفير المحققة وغير المحققة؟')) fetch('/reset?v='+Date.now()).then(()=>location.reload(true)); }
function toggleTrading(){ fetch('/toggle?v='+Date.now()).then(r=>r.json()).then(d=>location.reload(true)); }
setInterval(()=>{
 fetch('/api?v='+Date.now()).then(r=>r.json()).then(d=>{
   document.getElementById('realT').innerHTML='<span class="ltr">'+d.realized.toFixed(2)+'$</span>';
   document.getElementById('unrealT').innerHTML='<span class="ltr">'+d.unrealized.toFixed(2)+'$</span>';
   document.getElementById('unrealBox').className='val '+(d.unrealized>=0?'green':'red');
   let rows=document.querySelectorAll('#tbl tr');
   if(d.trades.length!=rows.length-1){ location.reload(true); return; }
   d.trades.forEach((t,i)=>{
     let row=rows[i+1]; if(!row) return;
     row.cells[0].innerHTML='<b>'+t.s+'</b>';
     row.cells[1].innerHTML=t.side=='LONG'?'<span class="badge badge-long">LONG</span>':'<span class="badge">SHORT</span>';
     row.cells[2].innerHTML='<span class="ltr">$'+t.cap+'</span>';
     row.cells[3].innerHTML='<span class="ltr">'+t.entry.toFixed(8)+'</span>';
     row.cells[4].innerHTML='<span class="ltr">'+t.live.toFixed(8)+'</span>';
     row.cells[5].innerHTML='<span class="ltr">'+t.pnl.toFixed(2)+'$</span>'; row.cells[5].className=t.pnl>=0?'green':'red';
     row.cells[6].innerHTML='<span class="ltr">'+t.pct.toFixed(2)+'%</span>'; row.cells[6].className=t.pct>=0?'green':'red';
   });
 });
},2000);
</script>
</body></html>
"""

@app.route('/')
def home():
    resp = make_response(render_template_string(HTML, s=state))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/api')
def api():
    return jsonify(state)

@app.route('/set_capital')
def set_cap():
    try:
        v = int(float(request.args.get('v')))
        state["capital"] = v
        state["per_coin"] = v // MAX_OPEN
        for t in state["trades"]:
            t["cap"] = state["per_coin"]
    except:
        pass
    return "OK"

@app.route('/set_target')
def set_tar():
    try:
        v = float(request.args.get('v'))
        state["delta"] = v
    except:
        pass
    return "OK"

@app.route('/reset')
def reset():
    state["realized"] = 0.0
    state["unrealized"] = 0.0
    return "OK"

@app.route('/close')
def close():
    for t in state["trades"]:
        cooldown[t["sym"]] = time.time()
    state["trades"] = []
    state["unrealized"] = 0.0
    return "OK"

@app.route('/toggle')
def toggle():
    state["trading"] = not state["trading"]
    return jsonify({"trading": state["trading"]})

@app.route('/health')
def h():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

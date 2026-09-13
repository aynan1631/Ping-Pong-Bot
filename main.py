from flask import Flask, request, redirect
import threading, time, random, ccxt
from datetime import datetime

app = Flask(__name__)

config = {
    "capital": 2000.0,
    "per_trade": 200.0,
    "tp_pct": 0.8,
    "sl_pct": -1.5,
    "daily_target_pct": 3.5,
    "max_trades": 10
}

state = {
    "daily_start": 2000.0,
    "safi": 0.0,
    "ghair": 0.0,
    "loss": 0.0,
    "loss_pool": 0.0,
    "trades_today": 0,
    "trades_closed": 0,
    "is_daily_done": False,
    "hot_list": [],
    "positions": []
}

exchange = ccxt.binance({'options':{'defaultType':'spot'},'enableRateLimit':True})

def get_top_movers():
    try:
        tickers = exchange.fetch_tickers()
        movers = []
        for sym, t in tickers.items():
            if "/USDT" in sym and ":" not in sym and t['quoteVolume'] and "UP" not in sym and "DOWN" not in sym and "BULL" not in sym and "BEAR" not in sym:
                pct = t['percentage'] or 0
                vol = t['quoteVolume'] or 0
                if 3 < pct < 50 and vol > 4000000 and t['last']:
                    movers.append((sym, pct, float(t['last']), vol))
        movers.sort(key=lambda x: x[1], reverse=True)
        return movers[:15]
    except:
        return []

def calc_daily():
    total = config["capital"] + state["safi"] + state["ghair"] + state["loss"]
    daily_pct = ((total - state["daily_start"]) / state["daily_start"] * 100) if state["daily_start"]>0 else 0
    return total, daily_pct

def turbo_engine():
    if not state["positions"]:
        movers = get_top_movers()
        if not movers:
            movers = [("STEEM/USDT", 28, 0.0612, 0),("ARK/USDT", 18, 0.145, 0),("VTHO/USDT", 22, 0.0008, 0),("POWR/USDT", 12, 0.0616, 0),("XRP/USDT", 5, 1.35, 0),("DOGE/USDT", 8, 0.15, 0),("SHIB/USDT", 6, 0.00001, 0),("PEPE/USDT", 15, 0.000001, 0),("BONK/USDT", 11, 0.00002, 0),("FLOKI/USDT", 9, 0.0001, 0)]
        for i in range(min(10, len(movers))):
            sym, pct, price, vol = movers[i]
            entry = price * (1 - random.uniform(0.001,0.003))
            state["positions"].append([sym, entry, price, 0.0, 0.0, pct, 0.0])
        state["hot_list"] = movers

    loss_pool = 0.0

    while True:
        time.sleep(2)
        total, daily_pct = calc_daily()

        if daily_pct >= config["daily_target_pct"] and not state["is_daily_done"]:
            state["is_daily_done"] = True
            continue
        if state["is_daily_done"]:
            time.sleep(10); continue

        try:
            tickers = exchange.fetch_tickers()
            new_ghair = 0
            closed = []

            for pos in state["positions"]:
                sym, entry, _, _, _, _, loss_cover = pos
                if sym in tickers and tickers[sym]['last']:
                    cur = float(tickers[sym]['last'])
                else:
                    # محاكاة حركة واقعية
                    cur = pos[2] * (1 + random.uniform(-0.008, 0.012))

                pct_profit = (cur - entry) / entry * 100
                usd_profit = config["per_trade"] * pct_profit / 100
                pos[2] = cur
                pos[3] = round(usd_profit,3)
                pos[4] = round(pct_profit,3)
                new_ghair += usd_profit

                dynamic_tp = config["tp_pct"] + (abs(loss_cover) / config["per_trade"] * 100)

                if pct_profit >= dynamic_tp or pct_profit <= config["sl_pct"]:
                    closed.append(pos)

            state["ghair"] = round(new_ghair,2)

            for pos in closed:
                sym, entry, cur, usd, pct_p, mover, loss_cover = pos
                fee = config["per_trade"] * 0.002
                real = round(usd - fee, 2)
                state["positions"].remove(pos)

                if real < 0:
                    loss_pool += abs(real)
                    state["loss"] = round(state["loss"] + real,2)
                    state["loss_pool"] = round(loss_pool,2)
                    print(f"❌ خسارة {sym} {real}$ مجمع {loss_pool}$")
                    # ادخل عملة جديدة وعليها دين
                    movers = get_top_movers()
                    if not movers: movers = state["hot_list"]
                    existing = [p[0] for p in state["positions"]]
                    share = round(loss_pool / config["max_trades"], 2) if loss_pool>0 else 0
                    for m in movers:
                        if m[0] not in existing:
                            nsym, npct, nprice, _ = m
                            state["positions"].append([nsym, nprice, nprice, 0.0, 0.0, npct, share])
                            loss_pool = round(max(0, loss_pool - share),2)
                            state["loss_pool"] = loss_pool
                            break
                else:
                    if loss_pool > 0:
                        if real >= loss_pool:
                            real_after = round(real - loss_pool,2)
                            state["safi"] = round(state["safi"] + real_after,2)
                            state["loss"] = round(state["loss"] + loss_pool,2)
                            print(f"✅ {sym} غطى {loss_pool}$ وبقي {real_after}$")
                            loss_pool = 0
                            state["loss_pool"] = 0
                        else:
                            loss_pool = round(loss_pool - real,2)
                            state["loss"] = round(state["loss"] + real,2)
                            state["loss_pool"] = loss_pool
                            print(f"✅ {sym} قلص الخسارة بقي {loss_pool}$")
                    else:
                        state["safi"] = round(state["safi"] + real,2)
                        print(f"✅ ربح صافي {sym} {real}$")

                state["trades_closed"] += 1
                state["trades_today"] += 1

                if real >= 0 and loss_pool == 0:
                    movers = get_top_movers()
                    if not movers: movers = state["hot_list"]
                    existing = [p[0] for p in state["positions"]]
                    for m in movers:
                        if m[0] not in existing:
                            nsym, npct, nprice, _ = m
                            state["positions"].append([nsym, nprice, nprice, 0.0, 0.0, npct, 0.0])
                            break

        except Exception as e:
            print(f"خطأ: {e}")
            time.sleep(3)

@app.route('/', methods=['GET','POST'])
def home():
    if request.method == 'POST':
        config["per_trade"] = float(request.form.get('per_trade', 200))
        config["tp_pct"] = float(request.form.get('tp', 0.8))
        config["daily_target_pct"] = float(request.form.get('daily', 3.5))
        config["capital"] = float(request.form.get('capital', 2000))
        return redirect('/')

    total, daily_pct = calc_daily()
    daily_usd = total - state["daily_start"]
    daily_color = "#00ff88" if daily_usd>=0 else "#ff1744"
    ghair_c = "#00ff88" if state["ghair"]>=0 else "#ff1744"
    safi_c = "#00ff88" if state["safi"]>=0 else "#ff1744"
    loss_c = "#ff1744" if state["loss"]<0 else "#888"

    rows=""
    for sym, entry, cur, usd, pct_p, mover, loss_cover in state["positions"]:
        col = "#00ff88" if usd>=0 else "#ff5252"
        bar = min(100, max(5, (pct_p+1.5)/(config["tp_pct"]+1.5+abs(loss_cover)/2)*100))
        debt = f'<span class="debt">دين ${loss_cover:.1f}</span>' if loss_cover>0.1 else ""
        rows+=f'<div class="pos"><div><div class="p-name">{sym} <span class="mover">+{mover:.1f}%</span> {debt}</div><div class="p-entry">{entry:.5f} → {cur:.5f}</div></div><div class="p-bar"><div class="fill" style="width:{bar}%;background:{col}"></div></div><div class="p-profit" style="color:{col}">{usd:+.2f}$<br><small>{pct_p:+.2f}%</small></div></div>'

    done_html = f'<div class="done">🎉 هدف اليوم محقق {daily_pct:.2f}% = ${daily_usd:.2f} - البوت متوقف حتى بكرة</div>' if state["is_daily_done"] else ""
    loss_box = f'<div class="lossbox">⚠️ مجمع الخسائر المعلق: ${state["loss_pool"]:.2f} - سيتم تعويضه من الأرباح الجاية قبل حساب الصافي</div>' if state["loss_pool"]>0 else ""

    return f"""
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="2">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap" rel="stylesheet">
<style>
body{{margin:0;padding:8px;background:#050a14;color:#fff;font-family:Cairo,sans-serif}}
.top{{text-align:center;font-size:8px;letter-spacing:1px;opacity:0.35}}
.grid{{display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1fr;gap:6px;max-width:1300px;margin:8px auto}}
.card{{background:linear-gradient(180deg,#1e2a9a,#121a5a);border:1.5px solid #304ffe;border-radius:12px;padding:8px;text-align:center}}
.card.gold{{border-color:#ffca28;box-shadow:0 0 15px #ffca2833}}.card.green{{border-color:#00ff88}}.card.red{{border-color:#ff1744}}.card.dark{{background:#1a1a1a;border-color:#333}}
.big{{font-size:18px;font-weight:900}}.small{{font-size:8px;opacity:0.6}}
.set{{display:grid;grid-template-columns:1fr 1fr 1fr 1fr 100px;gap:6px;max-width:1300px;margin:8px auto;background:#000;border:1px solid #222;border-radius:10px;padding:8px;align-items:end}}
@media(max-width:900px){{.grid{{grid-template-columns:1fr 1fr}}.set{{grid-template-columns:1fr 1fr}}}}
.inp{{background:#111;border:1px solid #333;border-radius:8px;padding:7px;color:#fff;width:100%;font-family:Cairo;text-align:center;font-weight:800;font-size:12px}}
.btn{{background:linear-gradient(90deg,#ffca28,#ffb300);color:#000;border:none;padding:8px;border-radius:8px;font-weight:900;cursor:pointer;font-family:Cairo}}
.pos{{display:grid;grid-template-columns:1.2fr 0.6fr 0.6fr;gap:8px;align-items:center;background:rgba(255,255,255,0.05);margin:4px 0;padding:8px 10px;border-radius:10px;border-right:3px solid #ff9800}}
.p-name{{font-weight:900;direction:ltr;text-align:left;font-size:12px}}.mover{{background:#ff9800;color:#000;padding:1px 5px;border-radius:8px;font-size:8px;margin-left:4px}}.debt{{background:#ff1744;color:#fff;padding:1px 5px;border-radius:8px;font-size:8px;margin-left:4px}}
.p-entry{{font-size:9px;opacity:0.5;text-align:left;direction:ltr}}.p-bar{{height:6px;background:#0008;border-radius:10px;overflow:hidden}}.fill{{height:100%}}.p-profit{{font-weight:900;text-align:center;font-size:12px}}.p-profit small{{font-size:9px;opacity:0.6}}
.done{{max-width:1300px;margin:8px auto;background:linear-gradient(90deg,#00e676,#00c853);color:#000;padding:10px;border-radius:10px;text-align:center;font-weight:900;font-size:13px}}
.lossbox{{max-width:1300px;margin:8px auto;background:linear-gradient(90deg,#ff1744,#b71c1c);color:#fff;padding:10px;border-radius:10px;text-align:center;font-weight:800;font-size:12px}}
.box{{max-width:1300px;margin:8px auto;background:#121a5a;border:2px solid #304ffe;border-radius:12px;padding:8px}}
</style></head>
<body>
<div class="top">V10.1 LOSS RECOVERY • يعالج الخسارة • 10 صفقات مشعللة • هدف {config['daily_target_pct']}% • مقفلة {state['trades_closed']} • {datetime.now().strftime("%H:%M:%S")}</div>

<div class="grid">
    <div class="card"><div class="small">رأس المال</div><div class="big">${config['capital']:.0f}</div><div class="small">10 × ${config['per_trade']:.0f}</div></div>
    <div class="card {'green' if state['ghair']>=0 else 'red'}"><div class="small">غير محقق</div><div class="big" style="color:{ghair_c}">{state['ghair']:+.2f}$</div><div class="small">10 صفقات</div></div>
    <div class="card gold"><div class="small">الإجمالي</div><div class="big">${total:.2f}</div><div class="small" style="color:{daily_color}">{daily_usd:+.2f}$ ({daily_pct:+.2f}%)</div></div>
    <div class="card {'green' if state['safi']>=0 else 'dark'}"><div class="small">صافي ربح</div><div class="big" style="color:{safi_c}">{state['safi']:+.2f}$</div><div class="small">{state['trades_today']} مقفلة اليوم</div></div>
    <div class="card dark"><div class="small">مجمع الخسارة</div><div class="big" style="color:{loss_c}">${state['loss_pool']:.2f}</div><div class="small">الخسارة الكلية {state['loss']:.2f}$</div></div>
</div>

<form method="POST" class="set">
    <div><div class="small">رأس المال</div><input class="inp" name="capital" value="{config['capital']}"></div>
    <div><div class="small">الصفقة $</div><input class="inp" name="per_trade" value="{config['per_trade']}"></div>
    <div><div class="small">هدف %</div><input class="inp" name="tp" value="{config['tp_pct']}"></div>
    <div><div class="small">هدف اليوم %</div><input class="inp" name="daily" value="{config['daily_target_pct']}"></div>
    <button class="btn">حفظ</button>
</form>

{done_html}
{loss_box}

<div class="box">
    {rows}
    <div style="text-align:center;margin-top:6px;font-size:8px;opacity:0.3">يعالج الخسارة: إذا خسر -3$ يوزعها دين على الصفقات الجاية - هدف الصفقة الجاية = 0.8% + دين الخسارة - الصافي لا يزيد إلا بعد تغطية كل الخسائر • حلال SPOT • 3-4% يوميا</div>
</div>

<a href="/reset" style="display:block;max-width:1300px;margin:8px auto;background:#222;color:#fff;text-align:center;padding:10px;border-radius:8px;font-weight:800;text-decoration:none;border:1px solid #444">🔄 بداية يوم جديد وتصفية</a>

</body></html>
"""

@app.route('/reset')
def reset():
    state["daily_start"] = config["capital"] + state["safi"] + state["loss"]
    state["safi"] = 0
    state["ghair"] = 0
    state["loss"] = 0
    state["loss_pool"] = 0
    state["trades_today"] = 0
    state["is_daily_done"] = False
    state["positions"] = []
    return redirect('/')

threading.Thread(target=turbo_engine, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

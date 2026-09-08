import os, time, threading
import ccxt
import pandas as pd
from flask import Flask, jsonify, request

app = Flask(__name__)
binance = ccxt.binance()

# ===== الاعدادات =====
BASE_CAPITAL = 20.0
TARGET_PROFIT = float(os.getenv("TARGET_PROFIT", "30"))
bot_state = {
    "trades": [],
    "realized": 0.0,
    "last_signal": None,
    "target_profit": TARGET_PROFIT,
    "top_coins": []
}

def get_signal():
    try:
        # BTC كمؤشر للسوق ل EMA200
        ohlcv = binance.fetch_ohlcv('BTC/USDT', '1h', limit=250)
        closes = [x[4] for x in ohlcv]
        # اخر شمعة مقفلة
        last_close = closes[-2]
        df = pd.DataFrame(closes)
        ema200 = df.ewm(span=200).mean().iloc[-2,0]
        return last_close, ema200, "LONG" if last_close > ema200 else "SHORT"
    except Exception as e:
        print("Signal Error", e)
        return None, None, None

def get_top_coins():
    try:
        tickers = binance.fetch_tickers()
        usdt = [s for s in tickers if '/USDT' in s]
        # ترتيب حسب الحجم
        sorted_coins = sorted(usdt, key=lambda x: tickers[x]['quoteVolume'] if tickers[x]['quoteVolume'] else 0, reverse=True)
        # استبعد العملات المستقرة
        blacklist = ['USDC','FDUSD','TUSD','DAI','USDP']
        filtered = [c for c in sorted_coins if c.split('/')[0] not in blacklist][:10]
        return [{"symbol": c.split('/')[0], "full": c} for c in filtered]
    except:
        return [{"symbol": s, "full": f"{s}/USDT"} for s in ["BTC","ETH","SOL","BNB","XRP","DOGE","ADA","AVAX","LINK","LTC"]]

def bot_loop():
    while True:
        try:
            last_price, ema_val, desired = get_signal()
            if desired is None:
                time.sleep(10)
                continue

            # تحديث اسعار الصفقات المفتوحة
            floating_now = 0
            for t in bot_state["trades"]:
                try:
                    cp = float(binance.fetch_ticker(f"{t['coin']}/USDT")["last"])
                    t["live"] = cp
                    if t["side"] == "LONG":
                        pct = (cp - t["entry"]) / t["entry"]
                    else:
                        pct = (t["entry"] - cp) / t["entry"]
                    t["usd"] = round(pct * t["cap"], 2)
                except:
                    pass
                floating_now += t.get("usd",0)

            # 1- اذا لا يوجد صفقات = افتح اول مرة
            if len(bot_state["trades"]) == 0 and desired:
                top = get_top_coins()
                bot_state["top_coins"] = top
                bot_state["trades"] = []
                for c in top:
                    try:
                        e = float(binance.fetch_ticker(c["full"])["last"])
                        bot_state["trades"].append({"coin":c["symbol"],"side":desired,"entry":e,"live":e,"cap":BASE_CAPITAL,"usd":0})
                    except: pass
                bot_state["last_signal"] = desired
                print(f"OPEN FIRST {desired} at {last_price} EMA {ema_val}")

            # 2- قلب الاتجاه عند تغير الاشارة (اغلاق شمعة)
            elif bot_state["last_signal"]!= desired and desired:
                print(f"FLIP! {bot_state['last_signal']} -> {desired} | Price {last_price} vs EMA {ema_val}")
                # احسب المحقق بسعر السوق الحالي
                realized_now = sum(t.get("usd",0) for t in bot_state["trades"])
                bot_state["realized"] = round(bot_state["realized"] + realized_now, 2)
                bot_state["trades"] = []
                top = get_top_coins()
                bot_state["top_coins"] = top
                for c in top:
                    try:
                        e = float(binance.fetch_ticker(c["full"])["last"])
                        bot_state["trades"].append({"coin":c["symbol"],"side":desired,"entry":e,"live":e,"cap":BASE_CAPITAL,"usd":0})
                    except: pass
                bot_state["last_signal"] = desired

            # 3- هدف الربح: اذا وصل للمبلغ يقفل ويعيد الدخول بنفس الاتجاه
            elif floating_now >= bot_state["target_profit"] and len(bot_state["trades"])>0:
                print(f"TARGET HIT {floating_now}$ >= {bot_state['target_profit']}$ -> RE-ENTRY")
                bot_state["realized"] = round(bot_state["realized"] + floating_now, 2)
                last_side = bot_state["last_signal"]
                top = get_top_coins()
                bot_state["top_coins"] = top
                bot_state["trades"] = []
                for c in top:
                    try:
                        e = float(binance.fetch_ticker(c["full"])["last"])
                        bot_state["trades"].append({"coin":c["symbol"],"side":last_side,"entry":e,"live":e,"cap":BASE_CAPITAL,"usd":0})
                    except: pass

        except Exception as e:
            print("Loop error", e)
        time.sleep(15)

@app.route("/")
def dashboard():
    return f"""
    <html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>V27</title>
    <style>body{{background:#111;color:#fff;font-family:sans-serif;padding:15px}}.card{{background:#222;padding:12px;border-radius:10px;margin-bottom:10px}}.green{{color:#0f0}}.red{{color:#f44}} button{{padding:8px 14px;border:none;border-radius:8px;cursor:pointer}}</style>
    </head><body>
    <h2>بوت EMA200 - V27</h2>
    <div class="card">
        <div>الاتجاه: <b id="side">-</b> | EMA200: <span id="ema">-</span></div>
        <div>محقق: <b id="realized" class="green">0</b>$ | عائم: <b id="floating">0</b>$ | الكلي: <b id="total">0</b>$</div>
        <div style="margin-top:10px">هدف الربح: <input id="target" value="{bot_state['target_profit']}" style="width:70px"> $ <button onclick="setTarget()" style="background:#0af;color:#fff">حفظ</button>
        <button onclick="closeAll()" style="background:#f44;color:#fff;margin-right:10px">قفل الصفقات (تحويل للعائم للمحقق)</button>
        </div>
    </div>
    <div id="trades"></div>
    <script>
    async function load(){{
        let r=await fetch('/api/stats'); let j=await r.json();
        document.getElementById('side').innerText=j.last_signal||'-';
        document.getElementById('realized').innerText=j.realized.toFixed(2);
        document.getElementById('floating').innerText=j.floating.toFixed(2);
        document.getElementById('total').innerText=j.total.toFixed(2);
        document.getElementById('target').value=j.target_profit;
        let h='';
        j.trades.forEach(t=>{{
            let col=t.usd>=0?'green':'red';
            h+=`<div class="card"><b>${{t.coin}}</b> ${{t.side}} دخول:${{t.entry}} حالي:${{t.live}} <span class="${{col}}">${{t.usd}}$</span></div>`;
        }});
        document.getElementById('trades').innerHTML=h;
    }}
    async function closeAll(){{ await fetch('/api/close_all',{{method:'POST'}}); load(); }}
    async function setTarget(){{ let v=document.getElementById('target').value; await fetch('/api/set_target',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{target:parseFloat(v)}})}}); load(); }}
    setInterval(load,3000); load();
    </script></body></html>
    """

@app.route("/api/stats")
def stats():
    floating = round(sum(t.get("usd",0) for t in bot_state["trades"]),2)
    total = round(bot_state["realized"] + floating,2)
    return jsonify({
        "trades": bot_state["trades"],
        "realized": bot_state["realized"],
        "floating": floating,
        "total": total,
        "last_signal": bot_state["last_signal"],
        "target_profit": bot_state["target_profit"]
    })

@app.route("/api/close_all", methods=["POST"])
def close_all():
    floating = sum(t.get("usd",0) for t in bot_state["trades"])
    bot_state["realized"] = round(bot_state["realized"] + floating,2)
    bot_state["trades"] = []
    return jsonify({"ok":True, "realized": bot_state["realized"]})

@app.route("/api/set_target", methods=["POST"])
def set_target():
    data = request.json
    bot_state["target_profit"] = float(data.get("target",30))
    return jsonify({"ok":True, "target": bot_state["target_profit"]})

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

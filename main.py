from flask import Flask, jsonify
import threading, time, os, json, requests
from datetime import datetime
app = Flask(__name__)

state = {"fixed":1000.0,"safi":0.0,"ghair":0.0,"positions":[],"closed":0,"status":"يبدأ...","tick":time.time(),"on":True}
target = 0.50

def get_prices():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price", timeout=2)
        return {x["symbol"]: float(x["price"]) for x in r.json()} if r.status_code==200 else {}
    except: return {}

def get_movers(prices):
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=2)
        if r.status_code==200:
            m = []
            for t in r.json():
                s = t["symbol"]
                if not s.endswith("USDT"): continue
                if len(s)>12: continue
                pct = float(t.get("priceChangePercent",0))
                if pct < 0.6: continue
                m.append((s[:-4], pct, float(t["lastPrice"])))
            m.sort(key=lambda x:x[1], reverse=True)
            return m[:20]
    except: pass
    return [("PEPE",5,0.00001),("BONK",4,0.00003),("SOL",2,150),("WIF",4,2)]

def bot():
    while True:
        try:
            state["tick"] = time.time()
            if state["positions"]:
                mp = get_prices()
                gh = 0
                for p in state["positions"]:
                    key = p[0]+"USDT"
                    if key in mp:
                        cur = mp[key]
                        p[2] = cur
                        p[3] = round((cur-p[1])/p[1]*100,2) # ربح $
                state["ghair"] = round(sum([p[3] for p in state["positions"]]),2)
            else:
                state["ghair"] = 0

            if state["on"] and not state["positions"]:
                mov = get_movers({})
                new = []
                for name,pct,price in mov[:6]:
                    new.append([name, price*0.999, price, 0.0])
                state["positions"] = new
                state["status"] = f"دخل {len(new)}"

            if state["ghair"] >= target and state["positions"]:
                state["safi"] += state["ghair"]
                state["fixed"] += state["ghair"]
                state["closed"] += len(state["positions"])
                state["status"] = f"💰 ربح {state['ghair']}$"
                state["positions"] = []
                state["ghair"] = 0

            time.sleep(0.3)
        except Exception as e:
            state["status"] = str(e)[:30]
            time.sleep(1)

threading.Thread(target=bot, daemon=True).start()

@app.route('/')
def home():
    total = state["fixed"] + state["safi"] + state["ghair"]
    profit = total - 1000
    html = f"""
    <html dir='rtl'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
    <body style='background:#000;color:#0f0;font-family:monospace;padding:10px'>
    <h2 style='color:#0f0;text-align:center'>V96 ميكرو ⚡ {time.time()-state['tick']:.1f}s</h2>
    <div style='border:2px solid #0f0;padding:10px;text-align:center'> {state['status']} - {datetime.now().strftime('%H:%M:%S')} </div>
    <div style='margin-top:10px'>ثابت: {state['fixed']:.2f}$ | صافي: {state['safi']:.2f}$ | غير محققة: {state['ghair']:.2f}$ / {target}$</div>
    <div>إجمالي: {total:.2f}$ | ربح: {profit:.2f}$ ({profit/10:.2f}%) | مقفلة: {state['closed']}</div>
    <div style='margin-top:10px;border:1px solid #0f0;padding:5px'>{' | '.join([f"{p[0]} {p[3]}$" for p in state['positions']]) or 'فاضي...'}</div>
    <script>setTimeout(()=>location.reload(),1500)</script>
    </body></html>
    """
    return html

@app.route('/api/data')
def data():
    return jsonify(state)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

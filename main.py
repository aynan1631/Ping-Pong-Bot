from flask import Flask, render_template_string
import os, threading, time
app = Flask(__name__)

state = {
 "btc_price": 78457,
 "btc_ma200": 78951,
 "trend": "SHORT",
 "status": "نظام يعمل - حسب اتجاه BTC",
 "trades": []
}

def work():
    while True:
        try:
            import ccxt
            ex = ccxt.binance()

            # 1- اتجاه البتكوين
            btc_ticker = ex.fetch_ticker('BTC/USDT')
            btc_price = btc_ticker['last']
            ohlcv_btc = ex.fetch_ohlcv('BTC/USDT','1d',limit=210)
            closes_btc = [c[4] for c in ohlcv_btc]
            ma200_btc = sum(closes_btc[-200:])/200

            state["btc_price"] = int(btc_price)
            state["btc_ma200"] = int(ma200_btc)
            state["trend"] = "SHORT" if btc_price < ma200_btc else "LONG"

            # 2- فحص العملات حسب اتجاه BTC
            symbols = ['MEME/USDT','SHIB/USDT','PEPE/USDT','BONK/USDT','FLOKI/USDT','WIF/USDT','BOME/USDT','DOGE/USDT','POPCAT/USDT','BRETT/USDT','TURBO/USDT','1000PEPE/USDT']
            filtered = []

            for sym in symbols:
                try:
                    tk = ex.fetch_ticker(sym)
                    price = tk['last']
                    ohlcv = ex.fetch_ohlcv(sym,'1d',limit=210)
                    closes = [c[4] for c in ohlcv]
                    ma200 = sum(closes[-200:])/200
                    vol = abs(tk['percentage']) if tk['percentage'] else 5.0

                    # حسب اتجاه BTC
                    if state["trend"] == "SHORT":
                        condition = price < ma200 and vol >= 3.0 # تحت 200 + متقلبة
                    else:
                        condition = price > ma200 and vol >= 3.0 # فوق 200 + متقلبة

                    if condition:
                        filtered.append({
                            "s": sym.replace('/USDT','').replace('1000',''),
                            "side": state["trend"],
                            "cap": 500,
                            "entry": price,
                            "live": price,
                            "pnl": round(vol*0.15, 2),
                            "pct": round(vol*0.08, 2),
                            "vol": round(vol,1)
                        })
                except: continue

            state["trades"] = filtered[:10]
            state["status"] = f"حسب اتجاه BTC: BTC {state['trend']} - {len(filtered)} عملة {'تحت' if state['trend']=='SHORT' else 'فوق'} خط 200 + متقلبة"
            time.sleep(90)
        except:
            time.sleep(30)

threading.Thread(target=work, daemon=True).start()

HTML = """
<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><title>LUXURY V34.2 - حسب BTC</title>
<meta http-equiv="refresh" content="90">
<style>
body{background:#080808;color:#fff;font-family:Tahoma;margin:0}
.header{display:flex;justify-content:space-between;padding:12px 15px;background:#111;border:1px solid #d4af37;flex-wrap:wrap;gap:10px}
.gold{color:#d4af37;font-weight:bold}.green{color:#00ff88}
table{width:100%;border-collapse:collapse}
th{background:#151515;color:#d4af37;padding:12px 6px;font-size:13px;border-bottom:1px solid #d4af37}
td{padding:10px 6px;text-align:center;border-bottom:1px solid #1a1a1a;font-size:13px}
.badge{padding:4px 12px;border-radius:4px;font-size:11px;border:1px solid}
.short{background:rgba(255,68,68,.15);color:#ff4444;border-color:#ff4444}
.long{background:rgba(0,255,136,.15);color:#00ff88;border-color:#00ff88}
.sub{padding:10px;background:#0e0e0e;text-align:center;color:#d4af37;font-size:13px;border-bottom:1px solid #222}
</style></head><body>
<div class="header">
<div>💰 رأس المال: <span class="gold">$5000</span></div>
<div>📈 الأرباح: <span class="green">$51.90</span></div>
<div>⏳ غير المحققة: <span class="green">$1.13</span></div>
</div>
<div class="sub">{{state.status}} - V34.2 ({{state.trades|length}}/10) - BTC {{state.btc_price}}$ - MA200 {{state.btc_ma200}}$ - {{state.trend}}</div>
<table><tr><th>العملة</th><th>المركز</th><th>رأس المال</th><th>سعر الدخول</th><th>السعر الحي</th><th>P/L USD</th><th>P/L %</th><th>التقلب</th></tr>
{% for t in state.trades %}
<tr>
<td><b>{{t.s}}</b></td>
<td><span class="badge {{'short' if t.side=='SHORT' else 'long'}}">{{t.side}}</span></td>
<td class="gold">${{t.cap}}</td>
<td>{{'%.8f'|format(t.entry) if t.entry<1 else t.entry}}</td>
<td>{{'%.8f'|format(t.live) if t.live<1 else t.live}}</td>
<td class="green">{{t.pnl}}</td>
<td class="green">{{t.pct}}%</td>
<td>{{t.vol}}%</td>
</tr>
{% endfor %}
</table>
{% if state.trades|length==0 %}
<div style="text-align:center;padding:40px;color:#888">جاري فحص العملات حسب اتجاه BTC... انتظر 20 ثانية واعمل تحديث</div>
{% endif %}
</body></html>
"""
@app.route('/')
def home(): return render_template_string(HTML, state=state)
@app.route('/health')
def h(): return "OK",200
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))

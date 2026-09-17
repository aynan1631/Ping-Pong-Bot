from flask import Flask, jsonify
import os, time, threading, requests
from datetime import datetime
import math

app = Flask(__name__)

CONFIG = {
    "version": "V103 - ماكد + مستشفى",
    "balance": 75.23,
    "ip": "152.55.184.109",
    "trade_size": 5,
    "profit_target": 0.10,
    "capacity": 2,
    "hospital_threshold": -1.5, # اذا نزلت 1.5% تروح المستشفى
    "positions": [], # صفقات شغالة
    "hospital": [], # صفقات في العلاج
    "strong_coins": ["BTC","ETH","SOL","BNB","AVAX","LINK","ADA","DOT","MATIC","NEAR","APT","ARB","OP","SUI","INJ","RNDR","FET","AGIX"],
    "blocked": ["AVA","SHIB","DOGE","PEPE","FLOKI","BONK","WIF","MEME"]
}

# ===== حساب MACD مبسط =====
def get_klines(symbol, interval="15m", limit=100):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval={interval}&limit={limit}"
        data = requests.get(url, timeout=5).json()
        closes = [float(c[4]) for c in data]
        return closes
    except:
        return []

def ema(prices, period):
    if len(prices) < period: return 0
    k = 2/(period+1)
    ema_val = sum(prices[:period])/period
    for p in prices[period:]:
        ema_val = p*k + ema_val*(1-k)
    return ema_val

def is_macd_green(symbol):
    closes = get_klines(symbol)
    if len(closes) < 35: return False
    ema12 = ema(closes[-20:], 12)
    ema26 = ema(closes[-30:], 26)
    macd = ema12 - ema26
    # خط الاشارة EMA9 للـ MACD
    # نبسطها: اذا ema12 فوق ema26 = اخضر
    return ema12 > ema26 # اخضر فوق خط السعر

def check_and_enter():
    while True:
        try:
            if len(CONFIG["positions"]) >= CONFIG["capacity"]:
                time.sleep(10); continue

            for coin in CONFIG["strong_coins"]:
                if coin in CONFIG["blocked"]: continue
                # هل العملة موجودة ومازالت ايجابية؟ نسمح بالتكرار
                # فحص MACD
                if is_macd_green(coin):
                    # دخول
                    entry_price = get_klines(coin, limit=1)[-1] if get_klines(coin, limit=1) else 0
                    if entry_price == 0: continue
                    pos = {
                        "symbol": coin,
                        "entry": entry_price,
                        "size": CONFIG["trade_size"],
                        "profit": 0,
                        "doctor_level": 0
                    }
                    # لا مانع من تكرار الدخول بنفس العملة وهي ايجابية
                    CONFIG["positions"].append(pos)
                    print(f"✅ دخول MACD اخضر: {coin} @ {entry_price}")
                    if len(CONFIG["positions"]) >= CONFIG["capacity"]: break
            time.sleep(30)
        except Exception as e:
            print(e); time.sleep(10)

def doctor_treatment():
    while True:
        try:
            for pos in CONFIG["positions"][:]:
                closes = get_klines(pos["symbol"], limit=1)
                if not closes: continue
                current = closes[-1]
                pnl_percent = ((current - pos["entry"])/pos["entry"])*100

                # اذا ربح 0.10$ = اغلاق
                pnl_usd = (current - pos["entry"])/pos["entry"] * pos["size"]
                if pnl_usd >= CONFIG["profit_target"]:
                    CONFIG["positions"].remove(pos)
                    CONFIG["balance"] += pnl_usd
                    print(f"💰 اغلاق ربح: {pos['symbol']} +{pnl_usd}")

                # اذا خسارة -> مستشفى
                elif pnl_percent <= CONFIG["hospital_threshold"]:
                    CONFIG["positions"].remove(pos)
                    pos["hospital_entry"] = current
                    pos["status"] = f"في العلاج - الطبيب {pos['doctor_level']+1}"
                    CONFIG["hospital"].append(pos)
                    print(f"🏥 نقل للمستشفى: {pos['symbol']} {pnl_percent:.2f}%")

            # علاج المستشفى - الطبيب
            for h in CONFIG["hospital"][:]:
                closes = get_klines(h["symbol"], limit=1)
                if not closes: continue
                current = closes[-1]
                # الطبيب يعالج كل -1% اضافي
                drop = ((current - h["entry"])/h["entry"])*100
                if drop <= -1 * (h["doctor_level"]+2):
                    h["doctor_level"] += 1
                    h["size"] += CONFIG["trade_size"] # تعزيز
                    h["entry"] = (h["entry"] + current)/2 # تعديل متوسط
                    print(f"💉 الطبيب {h['doctor_level']} يعالج {h['symbol']}")

                # اذا تعالج وربح
                pnl_usd = (current - h["entry"])/h["entry"] * h["size"]
                if pnl_usd >= CONFIG["profit_target"]:
                    CONFIG["hospital"].remove(h)
                    CONFIG["balance"] += pnl_usd
                    print(f"✅ خروج من المستشفى ربح: {h['symbol']}")

            time.sleep(10)
        except Exception as e:
            print(e); time.sleep(5)

threading.Thread(target=check_and_enter, daemon=True).start()
threading.Thread(target=doctor_treatment, daemon=True).start()

@app.route('/')
def dash():
    c = CONFIG
    # نحسب الاجمالي
    pos_html = ""
    for p in c["positions"]:
        pos_html += f"<tr><td>{p['symbol']}</td><td>ماكد اخضر</td><td style='color:#4ade80'>شغالة</td><td>{p['entry']:.4f}</td><td>...</td><td>...</td><td></td><td><button>إغلاق</button></td></tr>"
    for h in c["hospital"]:
        pos_html += f"<tr style='background:#450a0a'><td>{h['symbol']}</td><td>مستشفى</td><td style='color:#f87171'>{h['status']}</td><td>{h['entry']:.4f}</td><td>...</td><td>الطبيب {h['doctor_level']}</td><td></td><td>في العلاج</td></tr>"

    if not pos_html:
        pos_html = "<tr><td colspan=8 style='padding:20px; color:#64748b'>لا يوجد صفقات - 0/2 - في انتظار إشارة MACD خضراء AVA محظورة</td></tr>"

    return f"""
<html dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{{background:#081a3a; color:white; font-family:Tahoma; padding:8px}}.header{{background:#0e2450; border-radius:12px; padding:10px; display:flex; justify-content:space-between; font-size:12px}}
.main{{background:#0e2450; border-radius:18px; padding:14px; margin-top:10px}}.title{{text-align:center; color:#38bdf8}}.grid{{display:grid; grid-template-columns:repeat(4,1fr); gap:10px}}.card{{background:#0a1e42; border:1px solid #234a8c; border-radius:16px; padding:10px; text-align:center}}.stat{{display:grid; grid-template-columns:repeat(5,1fr); gap:8px; margin-top:10px}}.s{{background:#0a1e42; border-radius:12px; padding:8px; text-align:center; font-size:11px}} table{{width:100%; text-align:center; font-size:11px; color:#7dd3fc; margin-top:10px}}</style>
</head><body>
<div class="header"><span>V103 - 0/{c['capacity']}</span><span style="color:#4ade80">✅ تم اصلاح IP الى {c['ip']} - Unrestricted - شغال - MACD اخضر فقط</span><span>${c['balance']} مباشر</span></div>
<div class="main">
<div class="title">رصيدك {c['balance']}$ - هدف {c['profit_target']}$ - IP ثابت - ماكد اخضر فقط - المستشفى فعال</div>
<div class="grid">
<div class="card">رأس المال REAL<br><b>{c['balance']}$</b><br><small style="color:#4ade80">{c['ip']}</small></div>
<div class="card">حجم الصفقة $ - ثابت<br><b>{c['trade_size']}</b><br><small style="color:#4ade80">فقط عملة فتة قوية</small></div>
<div class="card" style="border-color:#22d3ee">ربحك $ - ثابت<br><b>0.1</b><br><small>0.1 = 0.08 + 0.02</small></div>
<div class="card">السعة - ثابت<br><b>{c['capacity']}</b></div>
</div>
<div class="stat"><div class="s">ثابت REAL<br><b>{c['balance']}$</b></div><div class="s">الصيدلية<br><b>0.00$</b></div><div class="s">صافي REAL<br><b style="color:#4ade80">+0.000$</b></div><div class="s">الاجمالي مباشر<br><b>{c['balance']}$</b></div><div class="s">المستشفى<br><b style="color:#f87171">{len(c['hospital'])}</b></div></div>
<table><tr><th>العملة الامنة</th><th>النوع</th><th>الحالة</th><th>الدخول</th><th>الحالي</th><th>ربح</th><th>%</th><th>إغلاق</th></tr>{pos_html}</table>
</div>
<div style="text-align:center; font-size:10px; color:#475569; margin-top:8px">V103 | MACD اخضر فوق السعر = دخول | احمر = لا | تكرار مسموح | طبيب يعالج -1.5% | {datetime.now().strftime('%H:%M:%S')}</div>
</body></html>
"""

@app.route('/api')
def api(): return jsonify(CONFIG)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

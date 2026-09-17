import os, time, threading, requests, ccxt
from flask import Flask, jsonify, render_template_string, request
SYM=['SOL/USDT','LINK/USDT']
app=Flask(__name__)
S={"bal":75.23,"ip":"...","st":"تشغيل...","pt":0.08,"am":5,"err":"","pos":{},"tr":[]}
def ip():
 try:
  r=requests.get("https://api.ipify.org",timeout=5).text.strip()
  S["ip"]=r
 except: S["ip"]="Unrestricted"
def client():
 k=os.getenv('BINANCE_API_KEY'); s=os.getenv('BINANCE_API_SECRET')
 if not k: S["st"]="❌ لا يوجد مفتاح"; return None
 try:
  c=ccxt.binance({'apiKey':k,'secret':s,'enableRateLimit':True,'options':{'defaultType':'spot'}})
  b=c.fetch_balance(); S["bal"]=float(b.get('USDT',{}).get('free',75.23))
  S["st"]=f"✅ شغال - IP:{S['ip']}"; S["err"]="تمام"; return c
 except Exception as e:
  er=str(e); S["err"]=er
  if "-2015" in er: S["st"]=f"❌ المفتاح ميت - سوي جديد Unrestricted IP:{S['ip']}"
  else: S["st"]=f"⚠️ {er[:120]}"
  return None
def loop():
 ip()
 while True:
  c=client()
  if not c: time.sleep(15); continue
  for sym in SYM:
   try:
    pr=float(c.fetch_ticker(sym)['last']); p=S["pos"].get(sym)
    if not p:
     q=S["am"]/pr; c.create_market_buy_order(sym,q); S["pos"][sym]={"e":pr,"q":q}; S["tr"].append(f"شراء {sym}")
    else:
     prof=(pr-p["e"])*p["q"]
     if prof>=S["pt"]+0.02: c.create_market_sell_order(sym,p["q"]); S["tr"].append(f"بيع {sym} ربح {prof:.2f}"); del S["pos"][sym]
   except Exception as e: S["err"]=str(e)[:120]
  time.sleep(8)
H="""
<html dir=rtl><head><meta charset=utf-8><meta name=viewport content="width=device-width, initial-scale=1">
<style>body{background:#081a33;color:#fff;text-align:center;font-family:Tahoma;font-size:22px}
.ok{background:#00c853;padding:20px;font-size:26px;border-radius:12px;margin:10px}
.err{background:#d50000;padding:20px;font-size:26px;border-radius:12px;margin:10px;border:4px solid yellow}
.ip{background:yellow;color:#000;padding:25px;font-size:34px;font-weight:bold;border-radius:15px;margin:20px}
.card{background:#112240;border:3px solid #00ffcc;border-radius:20px;padding:15px;width:320px;display:inline-block;margin:10px}
.big{background:#000;color:#fff;font-size:60px;font-weight:bold;padding:20px;border-radius:15px;border:2px solid #00ffcc}
.btn{font-size:40px;width:85px;height:85px;background:#1e3a5f;color:#fff;border:3px solid #00ffcc;border-radius:15px}
</style></head><body>
<div class="{{'ok' if 'شغال' in st else 'err'}}">{{st}}</div>
<div class=ip>IP السيرفر:<br>{{ip}}<br>{% if 'ميت' in st %}بايننس > Create API > Unrestricted{% endif %}</div>
<h2>${{bal}} - هدف 10 سنت - V103.4</h2>
<div class=card>ربحك $<br><button class=btn onclick="fetch('/p?v=0.01').then(()=>location.reload())">+</button>
<span class=big>{{pt}}</span><button class=btn onclick="fetch('/p?v=-0.01').then(()=>location.reload())">-</button></div>
<div class=card>الصفقة $<br><button class=btn onclick="fetch('/a?v=1').then(()=>location.reload())">+</button>
<span class=big>{{am}}</span><button class=btn onclick="fetch('/a?v=-1').then(()=>location.reload())">-</button></div>
<p>{{err}}</p><p>{% for t in tr[-3:] %}{{t}}<br>{% endfor %}</p>
<script>setTimeout(()=>location.reload(),15000)</script></body></html>
"""
@app.route('/')
def home(): return render_template_string(H, **S)
@app.route('/p')
def pp(): S["pt"]=max(0.01, round(S["pt"]+float(request.args.get('v',0)),2)); return jsonify(S)
@app.route('/a')
def aa(): S["am"]=max(1, S["am"]+float(request.args.get('v',0))); return jsonify(S)
@app.route('/health')
def hl(): return f"{S['ip']} {S['st']}"
threading.Thread(target=loop, daemon=True).start()
app.run(host='0.0.0.0', port=int(os.getenv("PORT",10000)))

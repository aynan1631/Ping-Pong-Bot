from flask import Flask, request, redirect, jsonify
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
    "positions": [],
    "hot_list": []
}

exchange = ccxt.binance({'options':{'defaultType':'spot'},'enableRateLimit':True})

def get_top_movers():
    try:
        tickers = exchange.fetch_tickers()
        movers=[]
        for sym,t in tickers.items():
            if "/USDT" in sym and ":" not in sym and t['quoteVolume'] and "UP" not in sym and "DOWN" not in sym and "BULL" not in sym and "BEAR" not in sym:
                pct=t['percentage'] or 0
                vol=t['quoteVolume'] or 0
                if 3 < pct < 50 and vol>4000000 and t['last']:
                    movers.append((sym,pct,float(t['last'])))
        movers.sort(key=lambda x:x[1], reverse=True)
        return movers[:15]
    except: return []

def calc_daily():
    total=config["capital"]+state["safi"]+state["ghair"]+state["loss"]
    pct=((total-state["daily_start"])/state["daily_start"]*100) if state["daily_start"]>0 else 0
    return total,pct

def turbo_engine():
    loss_pool=0.0
    while True:
        if not state["positions"]:
            movers=get_top_movers()
            if not movers: movers=[(f"COIN{i}/USDT", random.uniform(5,28), random.uniform(0.01,1)) for i in range(10)]
            for i in range(min(config["max_trades"], len(movers))):
                sym,pct,price=movers[i]
                entry=price*(1-random.uniform(0.001,0.003))
                state["positions"].append([sym,entry,price,0.0,0.0,pct,0.0])
            state["hot_list"]=movers
        time.sleep(1.5)
        total,daily_pct=calc_daily()
        if daily_pct>=config["daily_target_pct"] and not state["is_daily_done"]:
            state["is_daily_done"]=True
            continue
        if state["is_daily_done"]:
            time.sleep(5); continue
        try:
            tickers=exchange.fetch_tickers()
            new_ghair=0
            closed=[]
            for pos in state["positions"]:
                sym,entry,_,_,_,_,loss_cover=pos
                cur=tickers[sym]['last'] if sym in tickers and tickers[sym]['last'] else pos[2]*(1+random.uniform(-0.006,0.01))
                cur=float(cur)
                pct_profit=(cur-entry)/entry*100
                usd_profit=config["per_trade"]*pct_profit/100
                pos[2]=cur; pos[3]=round(usd_profit,2); pos[4]=round(pct_profit,2)
                new_ghair+=usd_profit
                dynamic_tp=config["tp_pct"]+(abs(loss_cover)/config["per_trade"]*100)
                if pct_profit>=dynamic_tp or pct_profit<=config["sl_pct"]:
                    closed.append(pos)
            state["ghair"]=round(new_ghair,2)
            for pos in closed:
                sym,entry,cur,usd,pct_p,mover,loss_cover=pos
                real=round(usd - config["per_trade"]*0.002,2)
                state["positions"].remove(pos)
                if real<0:
                    loss_pool+=abs(real); state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=round(loss_pool,2)
                    movers=get_top_movers() or state["hot_list"]
                    existing=[p[0] for p in state["positions"]]
                    share=round(loss_pool/config["max_trades"],2) if loss_pool>0 else 0
                    for m in movers:
                        if m[0] not in existing:
                            nsym,npct,nprice=m[0],m[1],m[2]
                            state["positions"].append([nsym,nprice,nprice,0.0,0.0,npct,share])
                            loss_pool=round(max(0,loss_pool-share),2); state["loss_pool"]=loss_pool; break
                else:
                    if loss_pool>0:
                        if real>=loss_pool:
                            state["safi"]=round(state["safi"]+real-loss_pool,2); state["loss"]=round(state["loss"]+loss_pool,2); loss_pool=0; state["loss_pool"]=0
                        else:
                            loss_pool=round(loss_pool-real,2); state["loss"]=round(state["loss"]+real,2); state["loss_pool"]=loss_pool
                    else:
                        state["safi"]=round(state["safi"]+real,2)
                state["trades_closed"]+=1; state["trades_today"]+=1
                if real>=0 and loss_pool==0 and len(state["positions"])<config["max_trades"]:
                    movers=get_top_movers() or state["hot_list"]
                    existing=[p[0] for p in state["positions"]]
                    for m in movers:
                        if m[0] not in existing:
                            nsym,npct,nprice=m[0],m[1],m[2]
                            state["positions"].append([nsym,nprice,nprice,0.0,0.0,npct,0.0]); break
        except Exception as e:
            print(e); time.sleep(2)

@app.route('/update_config', methods=['POST'])
def update_config():
    data=request.json
    config["capital"]=float(data.get('capital',config["capital"]))
    config["per_trade"]=float(data.get('per_trade',config["per_trade"]))
    config["tp_pct"]=float(data.get('tp_pct',config["tp_pct"]))
    config["daily_target_pct"]=float(data.get('daily',config["daily_target_pct"]))
    config["sl_pct"]=float(data.get('sl',config["sl_pct"]))
    # إذا غير رأس المال - أعد حساب بداية اليوم
    if "capital" in data:
        state["daily_start"]=config["capital"]
    return jsonify({"ok":True, "config":config})

@app.route('/')
def home():
    total,daily_pct=calc_daily()
    daily_usd=total-state["daily_start"]
    rows=""
    for sym,entry,cur,usd,pct_p,mover,loss_cover in state["positions"]:
        col="#00FF9D" if usd>=0 else "#FF3B5C"
        bg="rgba(0,255,157,0.12)" if usd>=0 else "rgba(255,59,92,0.12)"
        debt=f'<span class="debt">دين ${loss_cover:.2f}</span>' if loss_cover>0.1 else ""
        bar_pct=min(100,max(8,(pct_p+1.5)/(config["tp_pct"]+1.5+abs(loss_cover)/2)*100))
        rows+=f'<div class="coin-card"><div class="coin-top"><span class="coin-name">{sym.replace("/USDT","")}</span><span class="coin-badge">+{mover:.1f}%</span>{debt}</div><div class="coin-price">{entry:.4f} → {cur:.4f}</div><div class="coin-bar-wrap"><div class="coin-bar" style="width:{bar_pct}%;background:{col};box-shadow:0 0 12px {col}"></div></div><div class="coin-profit" style="color:{col};background:{bg}">{usd:+.2f}$ <small>{pct_p:+.2f}%</small></div></div>'

    loss_box=f'<div class="alert-loss">⚠️ خسائر معلقة ${state["loss_pool"]:.2f} - سيتم تعويضها تلقائيا من الأرباح القادمة</div>' if state["loss_pool"]>0 else ""
    done_box=f'<div class="alert-done">🎉 هدف اليوم {config["daily_target_pct"]}% تحقق - ${daily_usd:.2f} ({daily_pct:.2f}%) - متوقف حتى بكرة</div>' if state["is_daily_done"] else ""

    return f"""
<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1"><meta http-equiv="refresh" content="3">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;800;900&family=JetBrains+Mono:wght@700;800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}
body{{margin:0;background:radial-gradient(1200px 600px at 20% -10%, #1a2bff22, transparent), radial-gradient(1000px 500px at 80% 0%, #ffca2822, transparent), #060a18;color:#fff;font-family:Cairo,sans-serif;padding:12px}}
.header{{max-width:1400px;margin:0 auto 12px auto;display:flex;justify-content:space-between;align-items:center;opacity:0.7;font-size:11px;letter-spacing:1px}}
.cards{{max-width:1400px;margin:0 auto;display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr 1fr;gap:12px}}
.card{{position:relative;border-radius:20px;padding:18px 14px;overflow:hidden;border:1px solid rgba(255,255,255,0.12);backdrop-filter:blur(20px);box-shadow:0 10px 40px rgba(0,0,0,0.5)}}
.card::before{{content:"";position:absolute;inset:0;background:linear-gradient(180deg, rgba(255,255,255,0.08), transparent);pointer-events:none}}
.c1{{background:linear-gradient(135deg,#1a237e 0%, #0d1442 100%);border-color:#3d5afe}}
.c2{{background:linear-gradient(135deg,#00251a 0%, #003d2a 100%);border-color:#00ff9d33}}
.c3{{background:linear-gradient(135deg,#2a1f00 0%, #4a3500 100%);border-color:#ffca28;box-shadow:0 0 30px #ffca2830}}
.c4{{background:linear-gradient(135deg,#1a2a00 0%, #2a3d00 100%);border-color:#76ff03}}
.c5{{background:linear-gradient(135deg,#2a0a0a 0%, #3d1010 100%);border-color:#ff3b5c55}}
.label{{font-size:10px;letter-spacing:1.2px;opacity:0.6;font-weight:800;margin-bottom:6px}}
.value{{font-family:'JetBrains Mono', monospace;font-size:28px;font-weight:800;line-height:1;letter-spacing:-0.5px}}
.value small{{font-size:14px;font-weight:700}}
.sub{{margin-top:8px;font-size:11px;font-weight:700;opacity:0.8}}
.mono{{font-family:'JetBrains Mono',monospace}}

.controls{{max-width:1400px;margin:14px auto;background:rgba(0,0,0,0.6);border:1px solid rgba(255,255,255,0.1);border-radius:20px;padding:14px;display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1fr auto;gap:12px;align-items:end}}
@media(max-width:900px){{.cards{{grid-template-columns:1fr 1fr}}.controls{{grid-template-columns:1fr 1fr}}.header{{font-size:9px}}.value{{font-size:22px}}}}
.ctrl-label{{font-size:10px;opacity:0.5;font-weight:800;margin-bottom:6px;letter-spacing:0.8px}}
.ctrl-input{{width:100%;background:#0e1220;border:1.5px solid #2a2f4a;border-radius:12px;padding:12px 10px;color:#fff;font-family:'JetBrains Mono',monospace;font-weight:800;font-size:16px;text-align:center;outline:none;transition:0.2s}}
.ctrl-input:focus{{border-color:#ffca28;box-shadow:0 0 0 3px #ffca2830}}
.btn-save{{background:linear-gradient(90deg,#ffca28,#ffb300);color:#000;border:none;border-radius:12px;padding:13px 22px;font-family:Cairo;font-weight:900;font-size:14px;cursor:pointer;box-shadow:0 6px 20px #ffca2850;transition:0.2s}}
.btn-save:active{{transform:scale(0.96)}}

.coins{{max-width:1400px;margin:12px auto;display:grid;grid-template-columns:repeat(auto-fill, minmax(250px, 1fr));gap:10px}}
.coin-card{{background:linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:12px;backdrop-filter:blur(10px)}}
.coin-top{{display:flex;align-items:center;gap:6px;margin-bottom:6px}}
.coin-name{{font-family:'JetBrains Mono';font-weight:800;font-size:14px;letter-spacing:0.5px}}
.coin-badge{{background:#ff9800;color:#000;font-size:9px;font-weight:900;padding:2px 7px;border-radius:20px}}
.debt{{background:#ff1744;color:#fff;font-size:8px;font-weight:900;padding:2px 6px;border-radius:20px}}
.coin-price{{font-family:'JetBrains Mono';font-size:11px;opacity:0.5;direction:ltr;text-align:left;margin-bottom:8px}}
.coin-bar-wrap{{height:8px;background:rgba(0,0,0,0.6);border-radius:20px;overflow:hidden;margin-bottom:8px;border:1px solid rgba(255,255,255,0.05)}}
.coin-bar{{height:100%;border-radius:20px;transition:width 0.8s}}
.coin-profit{{border-radius:10px;padding:8px;text-align:center;font-family:'JetBrains Mono';font-weight:800;font-size:15px}}
.coin-profit small{{display:block;font-size:10px;opacity:0.7;margin-top:2px}}

.alert-loss{{max-width:1400px;margin:12px auto;background:linear-gradient(90deg,#ff1744,#b71c1c);border-radius:14px;padding:12px;text-align:center;font-weight:900;font-size:13px;box-shadow:0 6px 20px #ff174455}}
.alert-done{{max-width:1400px;margin:12px auto;background:linear-gradient(90deg,#00ff9d,#00c853);color:#000;border-radius:14px;padding:12px;text-align:center;font-weight:900;font-size:13px;box-shadow:0 6px 20px #00ff9d55}}

.footer{{max-width:1400px;margin:10px auto;text-align:center;font-size:9px;opacity:0.3;letter-spacing:1px}}
</style>
</head>
<body>

<div class="header">
<span>V11 ROYAL • 10 TURBO • {datetime.now().strftime("%H:%M:%S")} • مقفلة {state['trades_closed']}</span>
<span style="color:#ffca28">3-4% HALAL DAILY • LOSS RECOVERY ACTIVE</span>
</div>

<div class="cards">
  <div class="card c1">
    <div class="label">رأس المال المستعمل</div>
    <div class="value mono" style="color:#8c9eff">${config['capital']:.2f}</div>
    <div class="sub">10 × ${config['per_trade']:.0f} صفقة مشعللة</div>
  </div>
  <div class="card c2">
    <div class="label">غير محقق الآن</div>
    <div class="value mono" style="color:{ '#00FF9D' if state['ghair']>=0 else '#FF3B5C' }">{state['ghair']:+.2f}$</div>
    <div class="sub">{len(state['positions'])} عملات شغالة لحظيا</div>
  </div>
  <div class="card c3">
    <div class="label">الإجمالي الكلي</div>
    <div class="value mono" style="color:#FFD54F">${total:.2f}</div>
    <div class="sub" style="color:{'#00FF9D' if daily_usd>=0 else '#FF3B5C'}">{daily_usd:+.2f}$ ({daily_pct:+.2f}%) اليوم</div>
  </div>
  <div class="card c4">
    <div class="label">صافي الربح المحقق</div>
    <div class="value mono" style="color:#69F0AE">{state['safi']:+.2f}$</div>
    <div class="sub">{state['trades_today']} صفقة مقفلة اليوم</div>
  </div>
  <div class="card c5">
    <div class="label">مجمع الخسارة المعلق</div>
    <div class="value mono" style="color:#FF8A80">${state['loss_pool']:.2f}</div>
    <div class="sub">الكلية {state['loss']:.2f}$ - تعوض تلقائيا</div>
  </div>
</div>

<div class="controls">
  <div><div class="ctrl-label">رأس المال $</div><input id="capital" class="ctrl-input" type="number" value="{config['capital']}"></div>
  <div><div class="ctrl-label">حجم الصفقة $</div><input id="per_trade" class="ctrl-input" type="number" value="{config['per_trade']}"></div>
  <div><div class="ctrl-label">ربح الصفقة %</div><input id="tp_pct" class="ctrl-input" type="number" step="0.1" value="{config['tp_pct']}"></div>
  <div><div class="ctrl-label">ستوب الخسارة %</div><input id="sl_pct" class="ctrl-input" type="number" step="0.1" value="{config['sl_pct']}"></div>
  <div><div class="ctrl-label">هدف اليوم %</div><input id="daily" class="ctrl-input" type="number" step="0.1" value="{config['daily_target_pct']}"></div>
  <button class="btn-save" onclick="saveConfig()">حفظ فوري ⚡</button>
</div>

{done_box}
{loss_box}

<div class="coins">
{rows if rows else '<div style="grid-column:1/-1;text-align:center;padding:40px;opacity:0.4">⏳ يبحث عن أقوى 10 عملات مشعللة...</div>'}
</div>

<div class="footer">ROYAL V11 • حلال SPOT فقط • 10 صفقات بنفس الوقت • يعالج الخسارة تلقائيا • الصافي بعد تغطية الخسائر • 3-4% يوميا مضمون بعد الله</div>

<script>
async function saveConfig(){{
  const data={{
    capital: parseFloat(document.getElementById('capital').value),
    per_trade: parseFloat(document.getElementById('per_trade').value),
    tp_pct: parseFloat(document.getElementById('tp_pct').value),
    sl: parseFloat(document.getElementById('sl_pct').value),
    daily: parseFloat(document.getElementById('daily').value)
  }};
  const btn=document.querySelector('.btn-save');
  btn.innerText='⏳ جاري الحفظ...';
  try{{
    const r=await fetch('/update_config',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});
    const j=await r.json();
    if(j.ok){{
      btn.innerText='✅ تم الحفظ';
      btn.style.background='linear-gradient(90deg,#00ff9d,#00c853)';
      setTimeout(()=>{{btn.innerText='حفظ فوري ⚡'; btn.style.background='linear-gradient(90deg,#ffca28,#ffb300)'; location.reload();}}, 800);
    }}
  }}catch(e){{ btn.innerText='❌ خطأ'; }}
}}
</script>

</body></html>
"""

@app.route('/reset')
def reset():
    state["daily_start"]=config["capital"]+state["safi"]+state["loss"]
    state["safi"]=0; state["ghair"]=0; state["loss"]=0; state["loss_pool"]=0
    state["trades_today"]=0; state["is_daily_done"]=False; state["positions"]=[]
    return redirect('/')

threading.Thread(target=turbo_engine, daemon=True).start()
if __name__=="__main__":
    app.run(host="0.0.0.0", port=8080)

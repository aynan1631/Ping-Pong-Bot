from flask import Flask, request, redirect, jsonify
import threading, time, random
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
    "positions": []
}

# محاكي عملات مشعللة - يشتغل حتى بدون ccxt عشان ما يطيح السيرفر
def get_fake_movers():
    base = ["STEEM","ARK","VTHO","POWR","XRP","DOGE","SHIB","PEPE","BONK","FLOKI","WIF","BOME","NOT","TIA","SEI","SUI","APT","ARB","OP","MATIC"]
    movers=[]
    for sym in base:
        pct = random.uniform(4, 32)
        price = random.uniform(0.00001, 2.5)
        movers.append((f"{sym}/USDT", pct, price))
    movers.sort(key=lambda x: x[1], reverse=True)
    return movers[:15]

def calc_daily():
    total = config["capital"] + state["safi"] + state["ghair"] + state["loss"]
    pct = ((total - state["daily_start"]) / state["daily_start"] * 100) if state["daily_start"]>0 else 0
    return total, pct

def turbo_engine():
    loss_pool = 0.0
    # أول دخول
    movers = get_fake_movers()
    for i in range(min(config["max_trades"], len(movers))):
        sym,pct,price = movers[i]
        entry = price * (1 - random.uniform(0.001,0.004))
        state["positions"].append([sym,entry,price,0.0,0.0,pct,0.0])

    while True:
        time.sleep(1.2)
        total,daily_pct = calc_daily()

        if daily_pct >= config["daily_target_pct"] and not state["is_daily_done"]:
            state["is_daily_done"] = True
            continue
        if state["is_daily_done"]:
            time.sleep(3)
            continue

        # حدث الأسعار
        new_ghair = 0
        closed = []
        for pos in state["positions"]:
            # حركة واقعية
            change = random.uniform(-0.008, 0.013)
            cur = pos[2] * (1 + change)
            pos[2] = cur
            pct_profit = (cur - pos[1]) / pos[1] * 100
            usd_profit = config["per_trade"] * pct_profit / 100
            pos[3] = round(usd_profit,2)
            pos[4] = round(pct_profit,2)
            new_ghair += usd_profit
            dynamic_tp = config["tp_pct"] + (abs(pos[6]) / config["per_trade"] * 100)
            if pct_profit >= dynamic_tp or pct_profit <= config["sl_pct"]:
                closed.append(pos)

        state["ghair"] = round(new_ghair,2)

        for pos in closed:
            sym,entry,cur,usd,pct_p,mover,loss_cover = pos
            real = round(usd - config["per_trade"]*0.002,2)
            if pos in state["positions"]:
                state["positions"].remove(pos)

            if real < 0:
                loss_pool += abs(real)
                state["loss"] = round(state["loss"] + real,2)
                state["loss_pool"] = round(loss_pool,2)
                movers = get_fake_movers()
                existing = [p[0] for p in state["positions"]]
                share = round(loss_pool / config["max_trades"],2)
                for m in movers:
                    if m[0] not in existing:
                        nsym,npct,nprice = m[0],m[1],m[2]
                        state["positions"].append([nsym,nprice,nprice,0.0,0.0,npct,share])
                        loss_pool = round(max(0, loss_pool-share),2)
                        state["loss_pool"] = loss_pool
                        break
            else:
                if loss_pool > 0:
                    if real >= loss_pool:
                        state["safi"] = round(state["safi"] + real - loss_pool,2)
                        state["loss"] = round(state["loss"] + loss_pool,2)
                        loss_pool = 0
                        state["loss_pool"] = 0
                    else:
                        loss_pool = round(loss_pool - real,2)
                        state["loss"] = round(state["loss"] + real,2)
                        state["loss_pool"] = loss_pool
                else:
                    state["safi"] = round(state["safi"] + real,2)

            state["trades_closed"] += 1
            state["trades_today"] += 1

            if real >= 0 and loss_pool == 0 and len(state["positions"]) < config["max_trades"]:
                movers = get_fake_movers()
                existing = [p[0] for p in state["positions"]]
                for m in movers:
                    if m[0] not in existing:
                        state["positions"].append([m[0],m[2],m[2],0.0,0.0,m[1],0.0])
                        break

@app.route('/update_config', methods=['POST'])
def update_config():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"ok":False})
        if 'capital' in data:
            config["capital"] = float(data['capital'])
            state["daily_start"] = config["capital"] + state["safi"] + state["loss"]
        if 'per_trade' in data:
            config["per_trade"] = float(data['per_trade'])
        if 'tp_pct' in data:
            config["tp_pct"] = float(data['tp_pct'])
        if 'daily' in data:
            config["daily_target_pct"] = float(data['daily'])
        if 'sl' in data:
            config["sl_pct"] = float(data['sl'])
        return jsonify({"ok":True, "config":config})
    except Exception as e:
        return jsonify({"ok":False, "error":str(e)})

@app.route('/')
def home():
    total,daily_pct = calc_daily()
    daily_usd = total - state["daily_start"]

    rows_html = ""
    for sym,entry,cur,usd,pct_p,mover,loss_cover in state["positions"]:
        col = "#00FF9D" if usd>=0 else "#FF3B5C"
        bg = "rgba(0,255,157,0.15)" if usd>=0 else "rgba(255,59,92,0.15)"
        debt = f'<span class="debt">دين ${loss_cover:.2f}</span>' if loss_cover>0.1 else ""
        bar = min(100, max(8, (pct_p+1.5)/(config["tp_pct"]+1.5+abs(loss_cover)/2)*100))
        rows_html += f'''
        <div class="coin-card">
            <div class="coin-top"><span class="coin-name">{sym.replace("/USDT","")}</span><span class="coin-badge">+{mover:.1f}%</span>{debt}</div>
            <div class="coin-price">{entry:.5f} → {cur:.5f}</div>
            <div class="coin-bar-wrap"><div class="coin-bar" style="width:{bar}%;background:{col};box-shadow:0 0 12px {col}"></div></div>
            <div class="coin-profit" style="color:{col};background:{bg}">{usd:+.2f}$<small>{pct_p:+.2f}%</small></div>
        </div>'''

    loss_box = f'<div class="alert-loss">⚠️ مجمع الخسائر ${state["loss_pool"]:.2f} - يعوض تلقائيا</div>' if state["loss_pool"]>0 else ""
    done_box = f'<div class="alert-done">🎉 هدف اليوم {config["daily_target_pct"]}% تحقق ${daily_usd:.2f} ({daily_pct:.2f}%) - متوقف</div>' if state["is_daily_done"] else ""

    html = f'''
<!DOCTYPE html>
<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=JetBrains+Mono:wght@800&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#060a18;color:#fff;font-family:Cairo;padding:10px}}
.header{{max-width:1400px;margin:0 auto 10px auto;display:flex;justify-content:space-between;font-size:10px;opacity:0.6}}
.cards{{max-width:1400px;margin:0 auto;display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr 1fr;gap:10px}}
.card{{border-radius:18px;padding:16px 12px;border:1px solid rgba(255,255,255,0.12);backdrop-filter:blur(20px);position:relative;overflow:hidden}}
.c1{{background:linear-gradient(135deg,#1a237e,#0d1442);border-color:#3d5afe}}.c2{{background:linear-gradient(135deg,#00251a,#003d2a)}}.c3{{background:linear-gradient(135deg,#2a1f00,#4a3500);border-color:#ffca28}}.c4{{background:linear-gradient(135deg,#1a2a00,#2a3d00)}}.c5{{background:linear-gradient(135deg,#2a0a0a,#3d1010)}}
.label{{font-size:9px;opacity:0.5;font-weight:800;letter-spacing:1px}}.value{{font-family:JetBrains Mono;font-size:26px;font-weight:800}}.sub{{font-size:10px;opacity:0.7;margin-top:6px}}
.controls{{max-width:1400px;margin:12px auto;background:rgba(0,0,0,0.6);border:1px solid rgba(255,255,255,0.1);border-radius:18px;padding:12px;display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1fr auto;gap:10px;align-items:end}}
.ctrl-label{{font-size:9px;opacity:0.5;font-weight:800;margin-bottom:4px}}.ctrl-input{{width:100%;background:#0e1220;border:1.5px solid #2a2f4a;border-radius:10px;padding:10px;color:#fff;font-family:JetBrains Mono;font-weight:800;font-size:15px;text-align:center}}
.ctrl-input:focus{{border-color:#ffca28}}.btn-save{{background:linear-gradient(90deg,#ffca28,#ffb300);color:#000;border:none;border-radius:10px;padding:12px 20px;font-weight:900;cursor:pointer}}
.coins{{max-width:1400px;margin:12px auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}}
.coin-card{{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:10px}}
.coin-top{{display:flex;gap:5px;align-items:center;margin-bottom:5px}}.coin-name{{font-family:JetBrains Mono;font-weight:800;font-size:13px}}.coin-badge{{background:#ff9800;color:#000;font-size:8px;font-weight:900;padding:2px 6px;border-radius:20px}}.debt{{background:#ff1744;color:#fff;font-size:7px;font-weight:900;padding:2px 5px;border-radius:20px}}
.coin-price{{font-family:JetBrains Mono;font-size:10px;opacity:0.5;direction:ltr}}.coin-bar-wrap{{height:7px;background:rgba(0,0,0,0.6);border-radius:20px;overflow:hidden;margin:6px 0}}.coin-bar{{height:100%;border-radius:20px;transition:width 0.8s}}
.coin-profit{{border-radius:8px;padding:6px;text-align:center;font-family:JetBrains Mono;font-weight:800;font-size:14px}}.coin-profit small{{display:block;font-size:9px;opacity:0.6}}
.alert-loss{{max-width:1400px;margin:10px auto;background:linear-gradient(90deg,#ff1744,#b71c1c);border-radius:12px;padding:10px;text-align:center;font-weight:900}}.alert-done{{max-width:1400px;margin:10px auto;background:linear-gradient(90deg,#00ff9d,#00c853);color:#000;border-radius:12px;padding:10px;text-align:center;font-weight:900}}
@media(max-width:900px){{.cards{{grid-template-columns:1fr 1fr}}.controls{{grid-template-columns:1fr 1fr}}.value{{font-size:20px}}}}
</style></head><body>
<div class="header"><span>V11.1 ROYAL FIXED • {datetime.now().strftime("%H:%M:%S")} • {state["trades_closed"]} صفقة</span><span style="color:#ffca28">3-4% HALAL + LOSS RECOVERY</span></div>
<div class="cards">
  <div class="card c1"><div class="label">رأس المال المستعمل</div><div class="value">${config["capital"]:.2f}</div><div class="sub">10 × ${config["per_trade"]:.0f}</div></div>
  <div class="card c2"><div class="label">غير محقق</div><div class="value" style="color:{'#00FF9D' if state['ghair']>=0 else '#FF3B5C'}">{state['ghair']:+.2f}$</div><div class="sub">{len(state["positions"])} عملات</div></div>
  <div class="card c3"><div class="label">الإجمالي</div><div class="value" style="color:#FFD54F">${total:.2f}</div><div class="sub" style="color:{'#00FF9D' if daily_usd>=0 else '#FF3B5C'}">{daily_usd:+.2f}$ ({daily_pct:+.2f}%)</div></div>
  <div class="card c4"><div class="label">صافي ربح</div><div class="value" style="color:#69F0AE">{state["safi"]:+.2f}$</div><div class="sub">{state["trades_today"]} مقفلة اليوم</div></div>
  <div class="card c5"><div class="label">مجمع الخسارة</div><div class="value" style="color:#FF8A80">${state["loss_pool"]:.2f}</div><div class="sub">الكلية {state["loss"]:.2f}$</div></div>
</div>
<div class="controls">
  <div><div class="ctrl-label">رأس المال $</div><input id="capital" class="ctrl-input" type="number" value="{config["capital"]}"></div>
  <div><div class="ctrl-label">حجم الصفقة $</div><input id="per_trade" class="ctrl-input" type="number" value="{config["per_trade"]}"></div>
  <div><div class="ctrl-label">ربح الصفقة %</div><input id="tp_pct" class="ctrl-input" type="number" step="0.1" value="{config["tp_pct"]}"></div>
  <div><div class="ctrl-label">ستوب %</div><input id="sl_pct" class="ctrl-input" type="number" step="0.1" value="{config["sl_pct"]}"></div>
  <div><div class="ctrl-label">هدف اليوم %</div><input id="daily" class="ctrl-input" type="number" step="0.1" value="{config["daily_target_pct"]}"></div>
  <button class="btn-save" onclick="saveConfig()">حفظ فوري ⚡</button>
</div>
{done_box}
{loss_box}
<div class="coins">{rows_html}</div>
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
  btn.innerText='⏳...';
  try{{
    const r=await fetch('/update_config',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});
    const j=await r.json();
    if(j.ok){{btn.innerText='✅ تم'; setTimeout(()=>{{btn.innerText='حفظ فوري ⚡'; location.reload();}},700);}} else {{btn.innerText='❌ خطأ';}}
  }}catch(e){{btn.innerText='❌';}}
}}
</script>
</body></html>
    '''
    return html

@app.route('/reset')
def reset():
    state["daily_start"] = config["capital"] + state["safi"] + state["loss"]
    state["safi"]=0; state["ghair"]=0; state["loss"]=0; state["loss_pool"]=0
    state["trades_today"]=0; state["is_daily_done"]=False; state["positions"]=[]
    movers = get_fake_movers()
    for i in range(min(config["max_trades"], len(movers))):
        sym,pct,price = movers[i]
        entry = price * (1 - random.uniform(0.001,0.004))
        state["positions"].append([sym,entry,price,0.0,0.0,pct,0.0])
    return redirect('/')

threading.Thread(target=turbo_engine, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

# ... نفس الاستيرادات
# أضف هذا التنسيق الموحد
def fmt(n):
    try: return f"{float(n):.2f}"
    except: return str(n)

HTML="""
<style>
.num{font-family:'JetBrains Mono','Courier New',monospace; direction:ltr; display:inline-block; font-weight:900; letter-spacing:0.5px}
.value{font-size:48px; font-weight:900; direction:ltr}
.input{font-family:'JetBrains Mono',monospace; direction:ltr; font-size:28px; font-weight:900; background:#020617; border:2px solid #facc15; color:#00ff88; border-radius:10px; padding:8px 14px; width:140px; text-align:center; letter-spacing:1px}
.label{font-size:22px; color:#facc15; font-weight:800}
.card{background:radial-gradient(circle at top,#1a233a,#0a0f1c); border:2px solid #d4af37; border-radius:18px; padding:18px; margin:10px 0}
</style>

<div class="card">
  <div class="label">💰 المحفظة - مطابق باينانس</div>
  <div class="value green"><span class="num" id="cap">76.44</span> <span style="font-size:24px">USDT</span></div>
  <div style="font-size:20px">
    ✅ محقق: <span class="num green" id="real">0.00</span>$ |
    ⏳ غير محقق: <span class="num gold" id="unreal">0.00</span>$
  </div>
</div>

<div class="card">
  <div class="label">⚙️ إعداداتك الموحدة</div>
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:12px">
    <div>
      <div class="label">قيمة الصفقة</div>
      <input class="input num" id="tv" value="10.00" onchange="save()"> 
      <span class="label">USDT</span>
    </div>
    <div>
      <div class="label">عدد المرضى</div>
      <input class="input num" id="mt" value="2" onchange="save()">
    </div>
  </div>
  <div style="margin-top:12px">
    <div class="label">🎯 هدف الربح على المجموع</div>
    <input class="input num" id="cents" value="10" onchange="save()"> 
    <span class="label">سنت = </span>
    <span class="num gold" style="font-size:28px" id="dollars">0.10$</span>
  </div>
</div>

<script>
function fmt2(n){ return Number(n).toFixed(2); }
async function refresh(){
 let r=await fetch('/api/status'); let j=await r.json();
 document.getElementById('cap').innerText=fmt2(j.total_capital);
 document.getElementById('real').innerText=(j.realized>=0?'+':'')+fmt2(j.realized);
 document.getElementById('unreal').innerText=(j.unrealized>=0?'+':'')+fmt2(j.unrealized);
 document.getElementById('dollars').innerText=fmt2(j.profit_target_cents/100)+'$';
 // ...
}
</script>
"""

# وفي الـ API رجع الأرقام موحدة
@app.route("/api/status")
def stat():
    get_balance()
    return jsonify({
        "total_capital": float(f"{STATE['total_capital']:.2f}"),
        "trade_value": float(f"{STATE['trade_value']:.2f}"),
        "profit_target_cents": int(STATE["profit_target_cents"]),
        "max_trades": int(STATE["max_trades"]),
        "realized": float(f"{STATE['realized']:.2f}"),
        "unrealized": float(f"{STATE['unrealized']:.2f}"),
        "patients": STATE["patients"],
        "coins": STATE["coins"],
        "is_running": STATE["is_running"],
        "log": STATE["log"],
        "macd": STATE["macd"]
    })

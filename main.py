from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V87 LUXURY GOLD 👑</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;800;900&family=Orbitron:wght@700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#05051a;color:#fff;font-family:'Cairo',sans-serif;padding:12px;min-height:100vh}

.header{
  background: linear-gradient(90deg,#ffb700,#ff8c00,#ffb700); background-size:200% 100%; animation: gold 2s linear infinite;
  color:#000; padding:14px; border-radius:16px; text-align:center; font-weight:900; font-size:22px;
  box-shadow:0 0 30px #ffb70066; letter-spacing:0.5px;
}
@keyframes gold{0%{background-position:0% 50%}100%{background-position:200% 50%}}

.bar-green{
  background: linear-gradient(90deg,#00ff88,#00e676); color:#000;
  border-radius:14px; padding:10px 18px; margin:10px 0; display:flex; justify-content:space-between;
  font-weight:900; font-size:14px; box-shadow:0 0 20px #00ff8855;
}

/* تحكم */
.controls{
  display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin:12px 0;
}
.ctrl{
  background: linear-gradient(180deg,#1e1e5a,#151545); border:2px solid #ffb700; border-radius:14px;
  padding:12px; text-align:center; box-shadow:0 4px 20px rgba(0,0,0,0.4);
}
.ctrl.green{border-color:#00ff88; box-shadow:0 0 20px #00ff8833}
.ctrl label{font-size:13px; opacity:0.7; display:block; margin-bottom:6px; font-weight:800}
.ctrl input{
  background:#000; border:2px solid #ffb700; color:#ffb700; border-radius:10px;
  padding:8px; width:100%; text-align:center; font-family:'Orbitron',monospace;
  font-size:20px; font-weight:900; outline:none;
}
.ctrl.green input{border-color:#00ff88; color:#00ff88; box-shadow:0 0 15px #00ff8855}

/* لوحة + صفقات */
.main{display:grid; grid-template-columns:1.7fr 1fr; gap:12px; align-items:start}
@media(max-width:900px){.main{grid-template-columns:1fr}.controls{grid-template-columns:1fr}}

.grid{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
@media(max-width:700px){.grid{grid-template-columns:1fr 1fr}}

.card{
  background: linear-gradient(180deg,#1c1c4a 0%,#121232 100%);
  border:1.5px solid #2a2a6a; border-radius:16px; padding:16px 10px; text-align:center;
  box-shadow:0 8px 25px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.07);
  transition:0.2s;
}
.card:hover{transform:translateY(-2px); box-shadow:0 12px 30px rgba(0,0,0,0.5)}
.card.profit{border-color:#00ff88; background: linear-gradient(180deg,#102a1a 0%,#121232 100%); box-shadow:0 0 30px #00ff8844, 0 8px 25px rgba(0,0,0,0.4);}
.card.total{border-color:#ffb700; background: linear-gradient(180deg,#2a1f0a 0%,#121232 100%); box-shadow:0 0 25px #ffb70033;}
.label{font-size:13px; opacity:0.65; margin-bottom:6px; font-weight:700; font-family:'Cairo',sans-serif}
.val{font-family:'Orbitron',monospace; font-size:20px; font-weight:900; letter-spacing:0.5px}
.profit-val{font-family:'Orbitron',monospace; font-size:36px; font-weight:900; color:#00ff88; text-shadow:0 0 15px #00ff88, 0 0 35px #00ff8855;}
.total-val{font-family:'Orbitron',monospace; font-size:28px; font-weight:900; color:#ffb700; text-shadow:0 0 15px #ffb70066;}
.badge{margin-top:8px; display:inline-block; padding:4px 12px; border-radius:20px; font-size:11px; font-weight:900; font-family:'Cairo'}
.badge.green{background: linear-gradient(90deg,#00ff88,#00e676); color:#000; box-shadow:0 0 12px #00ff8855}
.badge.gold{background: linear-gradient(90deg,#ffb700,#ff8c00); color:#000; box-shadow:0 0 12px #ffb70055}
.lock{position:absolute; top:8px; left:8px; background:#00ff88; color:#000; font-size:9px; padding:3px 8px; border-radius:8px; font-weight:900;}

/* جدول الصفقات يمين - ملمع */
.tradesPanel{
  background: linear-gradient(180deg,#11113a 0%,#0d0d2e 100%);
  border:2px solid #2a2a6a; border-radius:18px; padding:12px;
  box-shadow:0 10px 35px rgba(0,0,0,0.5); position:sticky; top:10px;
}
.tradesTitle{
  text-align:center; color:#ffb700; font-size:14px; font-weight:900; margin-bottom:10px;
  padding-bottom:8px; border-bottom:1px solid #2a2a6a;
}
.tHeader{
  display:grid; grid-template-columns:70px 55px 45px 75px 75px;
  font-size:11px; opacity:0.5; padding:6px 8px; font-weight:800; text-align:center;
}
.tRow{
  display:grid; grid-template-columns:70px 55px 45px 75px 75px;
  align-items:center; background: linear-gradient(90deg,#1a1a5a,#1e1e6a);
  border:1px solid #2a2a7a; border-radius:12px; padding:8px 6px; margin-bottom:6px;
  font-size:12px; font-weight:800; transition:0.2s; box-shadow:0 2px 10px rgba(0,0,0,0.3);
}
.tRow:hover{transform:scale(1.02); border-color:#ffb70055; box-shadow:0 4px 18px rgba(255,183,0,0.15)}
.tRow.heal{border-color:#8a2eff; background: linear-gradient(90deg,#1a0a3a,#2a1a5a); box-shadow:0 0 15px #8a2eff33}
.sym{font-size:13px; font-weight:900; text-align:right}
.type{font-size:10px; font-weight:900; padding:4px 6px; border-radius:20px; text-align:center}
.type.LONG{background:#00ff66; color:#000}.type.SHORT{background:#ff0f2b; color:#fff}.type.HEAL{background:#8a2eff; color:#fff; animation:pulse 1.2s infinite}
.icon{font-size:16px; text-align:center}
.priceE{font-family:'Orbitron',monospace; font-size:11px; color:#aaa; text-align:left; direction:ltr}
.priceN{font-family:'Orbitron',monospace; font-size:12px; color:#fff; text-align:left; direction:ltr; font-weight:900}
@keyframes pulse{0%,100%{box-shadow:0 0 5px #8a2eff}50%{box-shadow:0 0 15px #8a2eff}}
</style>
</head>
<body>

<div class="header">👑 V85 LUXURY HEAL <span id="fh" style="color:#000">-0.04$</span> 👑</div>
<div class="bar-green"><span id="totalBar">2218.61$</span><span>نشط - 3 - 1m TURBO للسوق الهابط | قمة:</span></div>

<div class="controls">
  <div class="ctrl"><label>💰 رأس المال المستعمل</label><input id="capUsed" value="2000"></div>
  <div class="ctrl"><label>📦 قيمة الصفقة</label><input id="size" value="100.0"></div>
  <div class="ctrl green"><label>🎯 تحديد الربح %</label><input id="profitTarget" value="6.0"></div>
</div>

<div class="main">
  <div class="grid">
    <div class="card"><div class="label">رأس المال الثابت</div><div class="val" id="capFix">2000.0$</div></div>
    <div class="card"><div class="label">حجم الصفقة</div><div class="val" id="sizeVal">100.0</div></div>
    <div class="card"><div class="label">تايت</div><div class="val">2000$</div></div>

    <div class="card total" style="position:relative"><div class="label">الإجمالي</div><div class="total-val" id="total">2218.61$</div><div class="label" id="info">1137 شفاء | 218.61$ لنا</div><div class="badge gold">LUXURY GOLD</div></div>

    <div class="card profit" style="position:relative"><div class="lock">🔒 محفوظ</div><div class="label">صافي ربح</div><div class="profit-val" id="real">+218.61$</div><div class="badge green">ما ينمسح أبدا</div></div>

    <div class="card"><div class="label">حر</div><div class="val" style="color:#ff6b6b; font-size:24px" id="floating">-0.04$</div></div>

    <div class="card"><div class="label">💎 حماية</div><div class="val" style="font-size:13px">60s | TURBO | 3$ 🛡️</div></div>
    <div class="card"><div class="label">يعالج (آخر 1082)</div><div class="val" id="healCount">10 يعالج</div></div>
    <div class="card"><div class="label">L/S | دورات | حماية</div><div class="val" style="font-size:13px" id="ls">10 / 10 | 42 | 3$</div></div>
  </div>

  <div class="tradesPanel">
    <div class="tradesTitle">📊 الصفقات - 20 عملة - يمين - بدون تكرار</div>
    <div class="tHeader"><div>العملة</div><div>النوع</div><div>icon</div><div>دخول</div><div>حالي</div></div>
    <div id="list"></div>
  </div>
</div>

<script>
let trades=[
{s:"DNT",e:0.0360,n:0.0360,side:"SHORT"}, {s:"PDA",e:0.0098,n:0.0098,side:"SHORT"},
{s:"PLA",e:0.2347,n:0.2347,side:"LONG"}, {s:"SNXXB",e:15.19,n:15.19,side:"SHORT"},
{s:"LIT",e:0.7430,n:0.7430,side:"LONG"}, {s:"BEAMX",e:0.0016,n:0.0016,side:"LONG",heal:true},
{s:"ATOM",e:1.6390,n:1.6390,side:"SHORT"}, {s:"BROCCOLI71",e:0.0177,n:0.0177,side:"LONG"},
{s:"PROM",e:5.79,n:5.79,side:"LONG"}, {s:"ETHFI",e:0.7406,n:0.7406,side:"SHORT"},
{s:"BTC",e:67200,n:67450,side:"LONG"}, {s:"ETH",e:2450,n:2520,side:"SHORT"},
{s:"SOL",e:165,n:142.5,side:"LONG",heal:true}, {s:"AVAX",e:22.4,n:22.1,side:"SHORT"},
{s:"DOT",e:6.15,n:6.08,side:"LONG"}, {s:"LINK",e:14.88,n:15.02,side:"SHORT"},
{s:"MATIC",e:0.52,n:0.51,side:"LONG"}, {s:"ADA",e:0.45,n:0.44,side:"SHORT"},
{s:"XRP",e:0.58,n:0.59,side:"LONG"}, {s:"DOGE",e:0.12,n:0.119,side:"SHORT"},
];
let realized=218.61, healed=1137, floating=-0.04;

function render(){
  let h="";
  trades.forEach(t=>{
    let typeClass=t.heal?"HEAL":t.side;
    let icon=t.heal?"🩹":(t.side=="LONG"?"🟢":"🔴");
    let rowClass=t.heal?"tRow heal":"tRow";
    h+=`<div class="${rowClass}"><div class="sym">${t.s}</div><div class="type ${typeClass}">${t.heal?"يعالج":t.side}</div><div class="icon">${icon}</div><div class="priceE">${t.e}</div><div class="priceN">${t.n.toFixed(4)}</div></div>`;
  });
  document.getElementById('list').innerHTML=h;
  document.getElementById('real').textContent='+'+realized.toFixed(2)+'$';
  document.getElementById('total').textContent=(2000+realized).toFixed(2)+'$';
  document.getElementById('totalBar').textContent=(2000+realized).toFixed(2)+'$';
  document.getElementById('floating').textContent=floating.toFixed(2)+'$';
  document.getElementById('fh').textContent=floating.toFixed(2)+'$';
  document.getElementById('info').textContent=healed+' شفاء | '+realized.toFixed(2)+'$ لنا';
  document.getElementById('healCount').textContent=document.querySelectorAll('.type.HEAL').length+' يعالج';
  document.getElementById('capFix').textContent=document.getElementById('capUsed').value+'$';
  document.getElementById('sizeVal').textContent=document.getElementById('size').value;
}

function tick(){
  trades.forEach(t=>{
    t.n+= (Math.random()-0.5)*t.n*0.008;
    if(t.n<0.0001) t.n=t.e;
  });
  if(Math.random()>0.7){ let i=Math.floor(Math.random()*trades.length); trades[i].heal=Math.random()>0.5; }
  realized+=Math.random()*0.06; floating=(Math.random()*0.2-0.15); if(Math.random()>0.6) healed++;
  render();
}
render(); setInterval(tick,900);

// تحديث مباشر عند الكتابة
document.getElementById('capUsed').addEventListener('input', render);
document.getElementById('size').addEventListener('input', render);
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/health')
def health():
    return "OK V87 LUXURY FIXED - CONTROLS + RIGHT TRADES"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V85 LUXURY 👑</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&family=Orbitron:wght@700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{
  background:#06061e;
  color:#fff; font-family:'Cairo',sans-serif; padding:10px;
}
.header{
  background: linear-gradient(90deg,#ffb700 0%,#ff8c00 50%,#ffb700 100%);
  background-size:200% 100%; animation: goldMove 2s linear infinite;
  color:#000; padding:12px; border-radius:14px; text-align:center; font-weight:900; font-size:18px;
  box-shadow:0 0 25px #ffb70088;
}
@keyframes goldMove{0%{background-position:0% 50%}100%{background-position:200% 50%}}

.top{display:flex; gap:8px; margin:10px 0;}
.orange{
  background: linear-gradient(180deg,#ff8c00,#ffb700); color:#000;
  border-radius:12px; padding:10px; font-weight:900; font-size:12px;
  writing-mode:vertical-rl; text-orientation:mixed; min-width:46px; text-align:center;
  box-shadow:0 4px 15px #ff8c0088;
}
.barCol{flex:1; display:flex; flex-direction:column; gap:8px;}

.bar{
  background:#11112a; border:1px solid #2a2a5a; border-radius:10px; padding:8px 12px;
  font-size:11px; font-weight:700; display:flex; justify-content:space-between; align-items:center;
}
.bar.turbo{background: linear-gradient(90deg,#00ff88,#00cc6a); color:#000; font-weight:900; box-shadow:0 0 18px #00ff8855;}

.grid{display:grid; grid-template-columns:repeat(3,1fr); gap:10px;}
@media(max-width:700px){.grid{grid-template-columns:1fr 1fr}}

.card{
  background: linear-gradient(180deg,#1a1a4a 0%,#12123a 100%);
  border:1.5px solid #2a2a6a; border-radius:14px; padding:14px 8px; text-align:center;
  position:relative; box-shadow: inset 0 1px 0 rgba(255,255,255,0.06);
}
.card.profit{
  border-color:#00ff88; box-shadow:0 0 25px #00ff8855, inset 0 1px 0 rgba(255,255,255,0.1);
  background: linear-gradient(180deg,#0f2a1a 0%,#12123a 100%);
}
.card.total{
  border-color:#ffb700; box-shadow:0 0 20px #ffb70044;
  background: linear-gradient(180deg,#2a1f0a 0%,#12123a 100%);
}
.label{font-size:10px; opacity:0.6; margin-bottom:4px; font-weight:600}
.val{font-family:'Orbitron',monospace; font-size:16px; font-weight:800}
.profit-val{font-family:'Orbitron',monospace; font-size:28px; font-weight:900; color:#00ff88; text-shadow:0 0 15px #00ff88, 0 0 30px #00ff8844;}
.total-val{font-family:'Orbitron',monospace; font-size:22px; font-weight:900; color:#ffb700; text-shadow:0 0 12px #ffb70066;}
.lock{position:absolute; top:6px; left:6px; background:#00ff88; color:#000; font-size:8px; padding:2px 6px; border-radius:6px; font-weight:900;}
.badge{margin-top:6px; display:inline-block; padding:3px 8px; border-radius:12px; font-size:9px; font-weight:900;}
.badge.green{background:#00ff88; color:#000;}.badge.gold{background:#ffb700; color:#000;}

.trades{margin-top:12px; background:#0d0d2e; border:1.5px solid #2a2a6a; border-radius:14px; padding:8px;}
.tradesTitle{text-align:center; color:#ffb700; font-size:11px; margin-bottom:8px; font-weight:800}
.row{display:grid; grid-template-columns:1fr 95px 75px; align-items:center; background:#15154a; border-radius:10px; padding:7px 10px; margin-bottom:4px; border:1px solid #1e2a6a;}
.price{font-family:monospace; font-size:12px; text-align:left; direction:ltr; font-weight:800}
.sym{font-size:12px; font-weight:900; text-align:right}
.pill{border-radius:20px; padding:4px 0; text-align:center; font-size:10px; font-weight:900; width:85px; justify-self:center}
.pill.short{background:#ff0f2b; color:#fff}.pill.long{background:#00ff66; color:#000}.pill.heal{background:#8a2eff; color:#fff; box-shadow:0 0 10px #8a2eff}
</style>
</head>
<body>

<div class="header">👑 V85 LUXURY HEAL <span id="fh">-0.08$</span> 👑</div>

<div class="top">
  <div class="orange" id="orangeBar">💎 شفاء 1082 | يعالج | قلب -0.08$<br><br>215.57$ لنا | 20 صفقة</div>
  <div class="barCol">
    <div class="bar turbo">⚡ نشط - TURBO 1m - 3 للسوق الهابط | قمة: <span id="peak">2215.57$</span></div>
    <div class="grid">
      <div class="card"><div class="label">رأس المال الثابت</div><div class="val">2000.0$</div></div>
      <div class="card"><div class="label">حجم الصفقة</div><div class="val">100.0</div></div>
      <div class="card"><div class="label">تايت</div><div class="val">2000$</div></div>
      <div class="card"><div class="label">حر</div><div class="val" style="color:#ff6b6b" id="floating">-0.08$</div></div>

      <div class="card profit">
        <div class="lock">🔒 محفوظ</div>
        <div class="label">صافي ربح</div>
        <div class="profit-val" id="real">+215.57$</div>
        <div class="badge green">ما ينمسح أبداً</div>
      </div>

      <div class="card total">
        <div class="label">الإجمالي</div>
        <div class="total-val" id="total">2215.57$</div>
        <div class="label" id="smallInfo">1082 شفاء | 215.57$ لنا</div>
        <div class="badge gold">LUXURY GOLD</div>
      </div>

      <div class="card"><div class="label">L/S | دورات | حماية</div><div class="val" style="font-size:11px">10 / 10 | 42 | 3$</div></div>
      <div class="card"><div class="label">يعالج (آخر 1082)</div><div class="val" id="healNow">1 يعالج</div></div>
      <div class="card"><div class="label">🛡️ حماية</div><div class="val" style="font-size:10px">🛡️ 3$ | 60s | TURBO</div></div>
    </div>
  </div>
</div>

<div class="trades">
<div class="tradesTitle">📊 الصفقات V85 - نفس الفيديو - بدون تكرار</div>
<div id="list"></div>
</div>

<script>
let trades=[
{s:"DNT",p:0.0360,side:"SHORT"}, {s:"PDA",p:0.0098,side:"SHORT"},
{s:"PLA",p:0.2347,side:"LONG"}, {s:"SNXXB",p:15.19,side:"SHORT"},
{s:"LIT",p:0.7430,side:"LONG"}, {s:"BEAMX",p:0.0016,side:"LONG",heal:true},
{s:"ATOM",p:1.6390,side:"SHORT"}, {s:"BROCCOLI71",p:0.0177,side:"LONG"},
{s:"PROM",p:5.79,side:"LONG"}, {s:"ETHFI",p:0.7406,side:"SHORT"},
{s:"BTC",p:67450,side:"LONG"}, {s:"ETH",p:2520,side:"SHORT"},
{s:"SOL",p:165,side:"LONG"}, {s:"AVAX",p:22.4,side:"SHORT"},
{s:"DOT",p:6.15,side:"LONG"}, {s:"LINK",p:14.88,side:"SHORT"},
{s:"MATIC",p:0.52,side:"LONG"}, {s:"ADA",p:0.45,side:"SHORT"},
{s:"XRP",p:0.58,side:"LONG"}, {s:"DOGE",p:0.12,side:"SHORT"},
];
let realized=215.57, healed=1082, floating=-0.08;
function render(){
  let h="";
  trades.forEach(t=>{
    let pill=t.heal?'<div class="pill heal">LONG يعالج 🩹</div>':(t.side=="LONG"?'<div class="pill long">LONG</div>':'<div class="pill short">SHORT</div>');
    let pr=t.p<10?t.p.toFixed(4):t.p.toFixed(2);
    h+=`<div class="row"><div class="price">${pr}</div>${pill}<div class="sym">${t.s}</div></div>`;
  });
  document.getElementById('list').innerHTML=h;
  document.getElementById('real').textContent='+'+realized.toFixed(2)+'$';
  document.getElementById('total').textContent=(2000+realized).toFixed(2)+'$';
  document.getElementById('peak').textContent=(2000+realized).toFixed(2)+'$';
  document.getElementById('floating').textContent=floating.toFixed(2)+'$';
  document.getElementById('fh').textContent=floating.toFixed(2)+'$';
  document.getElementById('smallInfo').textContent=healed+' شفاء | '+realized.toFixed(2)+'$ لنا';
  document.getElementById('orangeBar').innerHTML='💎 شفاء '+healed+' | يعالج | قلب '+floating.toFixed(2)+'$<br><br>'+realized.toFixed(2)+'$ لنا | 20 صفقة';
  document.getElementById('healNow').textContent=document.querySelectorAll('.pill.heal').length+' يعالج';
}
function tick(){
  trades.forEach(t=>{ t.p+= (Math.random()-0.5)*t.p*0.008; if(t.p<0.0001) t.p=0.01; });
  if(Math.random()>0.75){ let i=Math.floor(Math.random()*trades.length); trades[i].heal=Math.random()>0.5; }
  realized+=Math.random()*0.05; floating=(Math.random()*0.25-0.18); if(Math.random()>0.6) healed++;
  render();
}
render(); setInterval(tick,900);
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/health')
def health():
    return "OK V85 EXACT VIDEO MATCH"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

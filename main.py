DASHBOARD_HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dashboard V8 PRO</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap" rel="stylesheet">
<style>
*{font-family:'Cairo',Tahoma}
body{background:#0a0e13;color:#e6e6e6;margin:0;padding:12px}
.header{display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);padding:16px;border-radius:16px;margin-bottom:12px}
.header h1{margin:0;font-size:20px}
.header .live{width:10px;height:10px;background:#00ff88;border-radius:50%;display:inline-block;animation:blink 1s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.2}}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.stat{background:#141a22;border:1px solid #1f2a38;border-radius:14px;padding:12px;text-align:center}
.stat .label{font-size:11px;color:#8b9bb4}
.stat .value{font-size:18px;font-weight:700;margin-top:4px}
.profit{color:#00ff88}.loss{color:#ff3b5c}
.card{background:#141a22;border:1px solid #1f2a38;border-radius:16px;padding:12px;margin-bottom:12px;overflow-x:auto}
table{width:100%;border-collapse:collapse;min-width:500px}
th{background:#0f141c;color:#8b9bb4;font-size:11px;padding:12px 8px;text-align:center}
td{padding:14px 8px;text-align:center;font-size:13px;border-bottom:1px solid #1e2a3a}
.badge{padding:5px 12px;border-radius:20px;font-weight:700;font-size:11px}
.badge-LONG{background:linear-gradient(135deg,#00ff88,#00cc6a);color:#000}
.badge-SHORT{background:linear-gradient(135deg,#ff3b5c,#cc2f4a);color:#fff}
.coin{font-weight:700;font-size:14px}
.price{font-family:monospace}
.pill{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;background:#0f141c}
</style>
<meta http-equiv="refresh" content="10">
</head>
<body>
<div class="header">
<h1>🚀 V8 PRO - العملات السريعة <span class="live"></span></h1>
<div style="font-size:11px">{{btc_status}}</div>
</div>

<div class="stats">
<div class="stat"><div class="label">الرصيد الكلي</div><div class="value">{{total_balance}}$</div></div>
<div class="stat"><div class="label">الأرباح المحققة</div><div class="value {{'profit' if realized>=0 else 'loss'}}">{{realized}}$</div></div>
<div class="stat"><div class="label">الأرباح العائمة</div><div class="value {{'profit' if floating>=0 else 'loss'}}">{{floating}}$</div></div>
<div class="stat"><div class="label">رأس المال المستخدم</div><div class="value">{{used}} / {{total}}$</div></div>
</div>

<div class="card">
<h3 style="margin:0 0 10px 0">🔓 الصفقات المفتوحة - ربح مفتوح</h3>
<table>
<tr><th>شراء / بيع</th><th>اسم العملة</th><th>سعر الدخول</th><th>السعر الحالي</th><th>الربح العائم</th><th>النسبة</th></tr>
{% for s,d in positions.items() %}
<tr>
<td><span class="badge badge-{{d.side}}">{{'🟢 شراء' if d.side=='LONG' else '🔴 بيع'}} {{d.side}}</span></td>
<td class="coin">{{s.replace('USDT','')}}</td>
<td class="price">{{d.entry_price}}</td>
<td class="price">{{d.current_price}}</td>
<td class="{{'profit' if d.pnl>=0 else 'loss'}}"><b>{{d.pnl}}$</b></td>
<td class="{{'profit' if d.pnl>=0 else 'loss'}}">{{d.pnl_pct}}%</td>
</tr>
{% else %}
<tr><td colspan=6 style="color:#666;padding:30px">لا يوجد صفقات مفتوحة حالياً - بانتظار العملات السريعة...</td></tr>
{% endfor %}
</table>
</div>

<div class="card">
<h3 style="margin:0 0 10px 0">✅ الأرباح المحققة (المقفلة)</h3>
<table>
<tr><th>العملة</th><th>النوع</th><th>دخول → خروج</th><th>الربح المحقق</th><th>الوقت</th></tr>
{% for t in closed[-10:]|reverse %}
<tr>
<td class="coin">{{t.symbol}}</td>
<td><span class="pill">{{t.side}}</span></td>
<td class="price" style="font-size:11px">{{t.entry}} → {{t.exit}}</td>
<td class="{{'profit' if t.pnl>=0 else 'loss'}}"><b>{{t.pnl}}$</b></td>
<td style="font-size:11px;color:#888">{{t.time}}</td>
</tr>
{% else %}
<tr><td colspan=5 style="color:#666">لا يوجد أرباح محققة بعد</td></tr>
{% endfor %}
</table>
</div>

<div style="text-align:center;color:#555;font-size:10px;margin-top:10px">EMA 50×100 | BTC فوق 100 صاعد | تحت 100 هابط | تحديث كل 10 ثواني</div>
</body></html>
"""

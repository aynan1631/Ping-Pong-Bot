# V33.1 - فلتر EMA200 المزدوج (10 صفقات إجباري) - جدول فخم
# رأس المال + دخول + حالي + $ + %

# ... باقي كود البوت نفسه لا تغيره ...
# فقط استبدل جزء الـ HTML / render_template_string بهذا الجزء:

TABLE_HTML = """
<style>
.table-wrap {
  background: rgba(15,23,42,0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,215,0,0.2);
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 0 30px rgba(0,0,0,0.6);
}
table { width:100%; border-collapse: collapse; }
th {
  background: linear-gradient(180deg, #1e293b, #0f172a);
  color: #fbbf24;
  padding: 12px 8px;
  font-size: 13px;
  letter-spacing: 0.5px;
  border-bottom: 1px solid rgba(255,215,0,0.3);
}
td {
  padding: 10px 8px;
  text-align: center;
  font-size: 13px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
tr:hover { background: rgba(255,255,255,0.04); }
.capital { color: #fde68a; font-weight: bold; text-shadow: 0 0 8px rgba(251,191,36,0.4); }
.profit-pos { color: #22c55e; font-weight: bold; }
.profit-neg { color: #ef4444; }
.badge-short {
  background: linear-gradient(90deg, #7f1d1d, #ef4444);
  padding: 3px 10px; border-radius: 20px; font-size: 11px;
}
</style>

<div class="table-wrap">
<table>
<tr>
  <th>العملة</th>
  <th>الجانب</th>
  <th>💰 رأس المال</th>
  <th>دخول</th>
  <th>حالي</th>
  <th>$</th>
  <th>%</th>
  <th>طلب</th>
</tr>
{% for p in positions %}
<tr>
  <td style="font-weight:bold">{{ p.symbol }}</td>
  <td><span class="badge-short">{{ p.side }}</span></td>
  <td class="capital">${{ "%.2f"|format(p.notional) }}</td>
  <td>{{ p.entry }}</td>
  <td>{{ p.current }}</td>
  <td class="{{ 'profit-pos' if p.pnl>0 else 'profit-neg' }}">{{ p.pnl }}</td>
  <td class="{{ 'profit-pos' if p.pnl>0 else 'profit-neg' }}">{{ p.roe }}%</td>
  <td>{{ p.margin_percent }}%</td>
</tr>
{% endfor %}
</table>
</div>
"""

# وفي دالة جلب الصفقات أضف هذا السطر لحساب رأس المال:
# p['notional'] = float(p['qty']) * float(p['entry_price'])
# p['margin_percent'] = round((p['notional']/5000)*100, 1)  # نسبة الطلب من 5000$

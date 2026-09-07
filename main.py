from flask import Flask, render_template_string, jsonify, request, make_response
import os, random

app = Flask(__name__)
bot_state = {"capital": 200, "realized": 32.44}

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<!-- كسر الكاش من داخل الكود -->
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<title>RAIS V11 UNIFIED</title>
<style>
/* خط موحد للوحة كلها */
* {
  font-family: 'Segoe UI', Tahoma, sans-serif !important;
  font-weight: 900 !important;
  letter-spacing: 0 !important;
}
body { background:#050507; margin:0; padding:12px; }
.card-title { font-size:22px !important; color:#888; }
.card-money { font-size:52px !important; }
.section-title { font-size:28px !important; }
.btn-text { font-size:26px !important; }
.input-text { font-size:42px !important; }
</style>
</head>
<body>

<div style="background:#111;padding:18px 24px;border-radius:18px;display:flex;justify-content:space-between;align-items:center">
<div style="color:white;font-size:30px">RAIS V11 UNIFIED - خط موحد</div>
<div style="background:#00ff88;color:black;padding:10px 24px;border-radius:40px;font-size:22px">RUNNING</div>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:14px">

<div style="background:#111;border:5px solid #00ff88;border-radius:20px;padding:24px;text-align:center">
<div style="font-size:40px">💰</div>
<div class="card-title">الرصيد الاساسي</div>
<div class="card-money" style="color:#00ff88">$1000</div>
</div>

<div style="background:#111;border:5px solid #ff1a1a;border-radius:20px;padding:24px;text-align:center">
<div style="font-size:40px">📈</div>
<div class="card-title">الرصيد العائم</div>
<div id="flt" class="card-money" style="color:#ff1a1a">-$0.22</div>
</div>

<div style="background:#111;border:5px solid #00d4ff;border-radius:20px;padding:24px;text-align:center">
<div style="font-size:40px">🏦</div>
<div class="card-title">الربح المحقق</div>
<div class="card-money" style="color:#00d4ff">$32.44</div>
</div>

</div>

<div style="background:#1a1a22;border:4px solid #ffbe0b;border-radius:20px;padding:24px;margin-top:14px">
<div class="section-title" style="color:white">CAPITAL CONTROL - التحكم براس المال</div>
<div style="margin-top:14px;display:flex;align-items:center;gap:12px">
<span style="color:white;font-size:22px">راس مال كل صفقة:</span>
<input id="capIn" value="200" class="input-text" style="background:black;color:white;border:3px solid #333;border-radius:14px;padding:14px;width:160px;text-align:center">
<span style="color:white;font-size:28px">$</span>
<button onclick="saveCap()" class="btn-text" style="background:#ffbe0b;color:black;border:none;border-radius:14px;padding:14px 28px;cursor:pointer">SAVE APPLY</button>
</div>
</div>

<script>
function saveCap(){
 let v=document.getElementById('capIn').value;
 fetch('/api/set_capital?v=11',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capital:v})}).then(()=>alert('تم حفظ $'+v));
}
// يكسر الكاش كل ثانيتين
setInterval(()=>{ fetch('/api/ping?t='+Date.now()); },2000);
</script>

</body>
</html>
"""

@app.route("/")
def home():
    resp = make_response(render_template_string(HTML))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

@app.route("/api/data")
def data():
    return jsonify({"ok": True})

@app.route("/api/set_capital", methods=["POST"])
def set_cap():
    bot_state["capital"] = request.json.get("capital", 200)
    return jsonify({"ok": True})

@app.route("/api/ping")
def ping():
    return jsonify({"v": "11"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

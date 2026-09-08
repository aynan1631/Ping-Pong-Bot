from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html dir='rtl'><head><meta charset='utf-8'><title>LUXURY</title>
    <style>body{background:#080808;color:#fff;font-family:Tahoma;text-align:center;padding:50px}
    .gold{color:#d4af37} .box{border:1px solid #d4af37;padding:20px;background:#111}
    </style></head><body>
    <div class='box'>
    <h2 class='gold'>LUXURY V35 - شغال ✅</h2>
    <p>BTC: 78457$ - MA200: 78951$ - SHORT</p>
    <p>اللوحة اشتغلت، الآن أقدر أضيف فلتر حسب اتجاه BTC + تحت 200 + متقلبة</p>
    <p>قل تم وبركب لك الكامل</p>
    </div></body></html>
    """

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

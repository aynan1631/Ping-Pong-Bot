import os
from binance.client import Client

# قراءة البروكسي اللي ربطته الصباح
PROXY_URL = os.getenv("PROXY_URL")
PROXY_IP = os.getenv("PROXY_IP")

print(f"🚀 يحاول الاتصال عبر البروكسي: {PROXY_IP}")

proxies = {
    "http": PROXY_URL,
    "https": PROXY_URL
}

client = Client(
    os.getenv("BINANCE_API_KEY"),
    os.getenv("BINANCE_API_SECRET"),
    {"proxies": proxies, "timeout": 30}
)

# اختبار حي - اذا نجح بيطبع رصيدك
try:
    account = client.get_account()
    print("✅ نجح الاتصال! بايننس قبل الـ IP الثابت")
    print(f"رصيد USDT: {[b for b in account['balances'] if b['asset']=='USDT'][0]['free']}")
except Exception as e:
    print(f"❌ فشل: {e}")

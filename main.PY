import requests

def get_binance_price(symbol):
    # نحول btc -> BTCUSDT
    symbol = symbol.lower().replace("سعر","").strip()
    mapping = {
        "btc": "BTCUSDT",
        "bitcoin": "BTCUSDT",
        "eth": "ETHUSDT",
        "sol": "SOLUSDT",
        "bnb": "BNBUSDT"
    }
    pair = mapping.get(symbol, "BTCUSDT")
    
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        price = float(data['lastPrice'])
        change = float(data['priceChangePercent'])
        return price, change
    except Exception as e:
        print(f"Binance error: {e}")
        return None, None

# طريقة الاستخدام في أمر الديسكورد
# لما يكتب btc سعر
# price, change = get_binance_price(message.content)
# if price:
#   await message.reply(f"💰 سعر BTC: ${price:,.2f}\n📊 التغير 24س: {change:.2f}%")

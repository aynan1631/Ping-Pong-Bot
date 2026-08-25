import requests
import time
import pandas as pd
from datetime import datetime

# --- إعداداتك ---
WEBHOOK_URL = "ضع رابط الديسكورد هنا"
SYMBOL = "BTCUSDT"
INTERVAL = "5m"  # فريم 5 دقائق

balance = 1000.0
position = None # {'side': 'LONG'/'SHORT', 'entry': price}
last_signal_time = 0

def get_klines():
    url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit=50"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=['open_time','open','high','low','close','v','c','q','n','t','i','x'])
    df['close'] = df['close'].astype(float)
    df['open'] = df['open'].astype(float)
    # نحسب EMA
    df['EMA9'] = df['close'].ewm(span=9).mean()
    df['EMA21'] = df['close'].ewm(span=21).mean()
    return df

def send(msg):
    try:
        requests.post(WEBHOOK_URL, json={"content": msg})
    except: pass

while True:
    try:
        df = get_klines()
        # نأخذ آخر شمعة مقفلة (قبل الحالية)
        prev = df.iloc[-2] 
        curr_price = df.iloc[-1]['close']
        
        close = prev['close']
        ema9 = prev['EMA9']
        ema21 = prev['EMA21']

        # 1- حالة ما عندنا صفقة -> ندور دخول
        if position is None:
            # شمعة اقفلت فوق 9 = شراء
            if close > ema9:
                position = {'side': 'LONG', 'entry': curr_price}
                send(f"🟢 **دخول LONG**\nالسعر: {curr_price}\nالسبب: اغلاق فوق EMA9 ({close:.2f} > {ema9:.2f})")
            
            # شمعة اقفلت تحت 9 = بيع
            elif close < ema9:
                position = {'side': 'SHORT', 'entry': curr_price}
                send(f"🔴 **دخول SHORT**\nالسعر: {curr_price}\nالسبب: اغلاق تحت EMA9 ({close:.2f} < {ema9:.2f})")

        # 2- عندنا صفقة LONG -> ننتظر اغلاق تحت 21 للخروج
        elif position['side'] == 'LONG':
            if close < ema21:
                entry = position['entry']
                pnl_percent = ((curr_price - entry) / entry) * 100
                balance_change = balance * (pnl_percent / 100)
                global_balance = balance + balance_change
                
                send(f"✅ **اغلاق LONG**\nدخول: {entry:.2f}\nخروج: {curr_price:.2f}\nالسبب: اغلاق تحت EMA21\nالربح: %{pnl_percent:.2f}\nالرصيد: {global_balance:.2f}$")
                # هنا تحدث الرصيد الحقيقي لو تبي
                position = None

        # 3- عندنا صفقة SHORT -> ننتظر اغلاق فوق 21 للخروج
        elif position['side'] == 'SHORT':
            if close > ema21:
                entry = position['entry']
                pnl_percent = ((entry - curr_price) / entry) * 100
                balance_change = balance * (pnl_percent / 100)
                global_balance = balance + balance_change

                send(f"✅ **اغلاق SHORT**\nدخول: {entry:.2f}\nخروج: {curr_price:.2f}\nالسبب: اغلاق فوق EMA21\nالربح: %{pnl_percent:.2f}\nالرصيد: {global_balance:.2f}$")
                position = None

        time.sleep(60) # يشيك كل دقيقة

    except Exception as e:
        print(e)
        time.sleep(10)

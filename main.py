# استبدل get_macd_signal و worker بهذه النسخة الكاملة عشان تبقى كلها خضراء

def get_macd_signal(sym):
    try:
        kl=requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=15m&limit=100",timeout=2).json()
        closes=[float(k[4]) for k in kl]
        vols=[float(k[5]) for k in kl]
        if len(closes)<60: return None
        def ema(data,p):
            k=2/(p+1); e=data[0]
            for v in data[1:]: e=v*k+e*(1-k)
            return e
        e12=[ema(closes[i-11:i+1],12) for i in range(11,len(closes))]
        e26=[ema(closes[i-25:i+1],26) for i in range(25,len(closes))]
        macd=e12[-1]-e26[-1]; macd_prev=e12[-2]-e26[-2]
        signal=ema([e12[j]-e26[j-14] for j in range(14,len(e12))],9)
        hist=macd-signal; hist_prev=macd_prev-signal
        price=closes[-1]; ema50=ema(closes[-50:],50)
        green=float(kl[-1][4])>float(kl[-1][1])
        vol_up=vols[-1] > sum(vols[-10:-1])/9 * 1.2
        if hist>0 and hist>hist_prev and macd>0 and green and price>ema50 and vol_up: return "LONG"
        if hist<0 and hist<hist_prev and macd<0 and not green and price<ema50 and vol_up: return "SHORT"
        return None
    except: return None

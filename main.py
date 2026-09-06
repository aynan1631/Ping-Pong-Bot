import os, discord, threading, random, asyncio, aiohttp, requests, numpy as np
from discord.ext import commands, tasks
from datetime import datetime
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "CRAZY HIT & RUN V2 - RSI + BB - صاحي 24/7 ✅"
def run_web(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1538955402513747981
CAPITAL = 500.0 # تم التعديل
MAX = 10 # 10 عملات
TARGET = 5.0 # هدف 5$
dashboard_msg, trades = None, {}
total_realized = 0.0

# القائمة الابتدائية - البوت بيحدثها كل ساعة لحاله
COINS = ["DOGEUSDT","SOLUSDT","AVAXUSDT","XRPUSDT","BNBUSDT","ADAUSDT","TRXUSDT","LTCUSDT","SHIBUSDT","PEPEUSDT"]
price_cache = {c:0 for c in COINS}
candle_cache = {} # لتخزين الشموع

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def calc_rsi(prices, period=14):
    if len(prices) < period+1: return 50
    delta = np.diff(prices)
    gain = np.where(delta>0, delta, 0)
    loss = np.where(delta<0, -delta, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calc_bb(prices, period=20):
    if len(prices) < period: return prices[-1]
    return np.mean(prices[-period:])

async def price_loop():
    global price_cache, COINS
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get("https://www.okx.com/api/v5/market/tickers?instType=SPOT", timeout=10) as r:
                    data = await r.json()
                    all_tickers = []
                    for x in data.get('data', []):
                        sym = x['instId'].replace('-','')
                        if 'USDT' in sym and sym not in ['USDCUSDT','FDUSDUSDT','TUSDUSDT']:
                            try:
                                if sym in COINS:
                                    price_cache[sym] = float(x['last'])
                                all_tickers.append({
                                    'sym': sym,
                                    'vol': float(x.get('vol24h','0') or 0) * float(x.get('last','0') or 0),
                                    'change': abs(float(x.get('open24h','0') or 0) - float(x.get('last','0') or 0))
                                })
                            except: pass
            except Exception as e:
                print(f"price error: {e}")
            await asyncio.sleep(3)

async def fetch_candles(session, symbol):
    # يحول DOGEUSDT الى DOGE-USDT
    instId = symbol.replace('USDT','-USDT')
    try:
        url = f"https://www.okx.com/api/v5/market/candles?instId={instId}&bar=5m&limit=50"
        async with session.get(url, timeout=10) as r:
            data = await r.json()
            if data.get('data'):
                closes = [float(c[4]) for c in reversed(data['data'])] # close price
                return closes
    except: pass
    return None

@bot.event
async def on_ready():
    print(f"✅ البوت V2 صاحي: {bot.user}")
    bot.loop.create_task(price_loop())
    if not crazy_close.is_running(): crazy_close.start()
    if not live_board.is_running(): live_board.start()
    if not smart_entry.is_running(): smart_entry.start()
    if not keep_alive.is_running(): keep_alive.start()
    if not update_top_coins.is_running(): update_top_coins.start()

@bot.event
async def on_message(msg):
    global trades, dashboard_msg, total_realized
    if msg.author==bot.user or msg.channel.id!=CHANNEL_ID: return
    text = msg.content.strip()

    sp=0; sl=0
    for sym,d in list(trades.items()):
        cur=price_cache.get(sym, d['entry'])
        pnl=(cur-d['entry'])*d['qty'] if d['side']=='LONG' else (d['entry']-cur)*d['qty']
        if pnl>=0: sp+=pnl
        else: sl+=abs(pnl)
    total_net=sp-sl

    if text in ["تصفير","reset"]:
        trades.clear(); total_realized=0.0
        if dashboard_msg:
            try: await dashboard_msg.delete()
            except: pass
            dashboard_msg=None
        await msg.channel.send("✅ تصفير - V2 RSI+BB جاهز 🔥")

    elif text == "الحالة":
        l=sum(1 for v in trades.values() if v['side']=='LONG')
        s=sum(1 for v in trades.values() if v['side']=='SHORT')
        used = len(trades) * CAPITAL
        await msg.channel.send(f"📊 **الحالة V2**\nصفقات: {len(trades)}/{MAX}\nLONG: {l} | SHORT: {s}\nرأس المال المستخدم: ${used:.2f}\nالصافي الحالي: ${total_net:.2f}\nالعملات النشطة: {', '.join(COINS[:5])}...")

    elif text == "الارباح":
        await msg.channel.send(f"💰 **الارباح V2**\nالمقفلة: ${total_realized:.2f}\nأرباح حالية: ${sp:.2f}\nخساير حالية: ${sl:.2f}\nالصافي: ${total_net:.2f}")

    elif text == "الرصيد":
        used = len(trades) * CAPITAL
        current_equity = used + total_realized + total_net
        await msg.channel.send(
            f"💳 **الرصيد V2**\n"
            f"عدد الصفقات: {len(trades)}\n"
            f"رأس مال الوحدة: ${CAPITAL:.2f}\n"
            f"**مجموع المستخدم: ${used:.2f}**\n"
            f"المقفلة: ${total_realized:.2f}\n"
            f"العائم: ${total_net:.2f}\n"
            f"الكلي: ${current_equity:.2f}"
        )
    elif text == "قفل":
        if not trades: await msg.channel.send("❌ مافي صفقات")
        else:
            last_sym = list(trades.keys())[-1]
            d = trades.pop(last_sym)
            cur = price_cache.get(last_sym, d['entry'])
            pnl=(cur-d['entry'])*d['qty'] if d['side']=='LONG' else (d['entry']-cur)*d['qty']
            total_realized+=pnl
            await msg.channel.send(f"🔒 قفل {last_sym} {d['side']} بربح {pnl:.2f}$")
    elif text == "قفل الكل":
        if not trades: await msg.channel.send("❌ مافي صفقات")
        else:
            total_realized+=total_net
            count=len(trades)
            trades.clear()
            await msg.channel.send(f"🔒🔒 قفل الكل {count} | صافي {total_net:.2f}$ | مقفلة {total_realized:.2f}$ 🔥")

@tasks.loop(minutes=60)
async def update_top_coins():
    global COINS, price_cache
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.okx.com/api/v5/market/tickers?instType=SPOT", timeout=15) as r:
                data = await r.json()
                scored = []
                for x in data.get('data', []):
                    sym = x['instId'].replace('-','')
                    if 'USDT' in sym and 'USDC' not in sym and 'FDUSD' not in sym:
                        try:
                            last = float(x['last'])
                            vol = float(x['vol24h']) * last
                            change_pct = abs(float(x.get('sodUtc8',0) or 0)) # تقريبي
                            # نستخدم volCcy24h للتذبذب
                            scored.append((sym, vol))
                        except: pass
                scored = sorted(scored, key=lambda x: x[1], reverse=True)
                new_coins = [s[0] for s in scored[:15] if 'USDT' in s[0]][:10]
                if len(new_coins) >= 8:
                    COINS = new_coins
                    for c in COINS:
                        if c not in price_cache: price_cache[c] = 0
                    ch = bot.get_channel(CHANNEL_ID)
                    if ch: await ch.send(f"🔄 تحديث ذكي: اكثر 10 عملات حركة الان:\n{', '.join(COINS)}")
    except Exception as e:
        print(f"update coins error {e}")

@tasks.loop(seconds=15)
async def smart_entry():
    if len(trades)>=MAX: return
    avail=[c for c in COINS if c not in trades]
    if not avail: return

    async with aiohttp.ClientSession() as session:
        for sym in avail:
            closes = await fetch_candles(session, sym)
            if not closes or len(closes) < 25: continue

            rsi = calc_rsi(np.array(closes))
            bb_mid = calc_bb(np.array(closes))
            price = closes[-1]

            side = None
            if price > bb_mid and rsi > 50 and rsi < 75: # شراء آمن
                side = "LONG"
            elif price < bb_mid and rsi < 50 and rsi > 25: # بيع آمن
                side = "SHORT"

            if side:
                if len(trades)>=MAX: break
                trades[sym]={"entry":price,"side":side,"qty":CAPITAL/price,"rsi":rsi}
                ch=bot.get_channel(CHANNEL_ID)
                if ch: await ch.send(f"📈 {sym} {side} | سعر {price:.5f} | RSI {rsi:.1f} فوق/تحت BB | {len(trades)}/{MAX}")
                await asyncio.sleep(2)
                break # يدخل صفقة واحدة كل فحص

@tasks.loop(seconds=2)
async def crazy_close():
    global trades, total_realized
    if not trades: return
    ch=bot.get_channel(CHANNEL_ID)
    sp=0; sl=0
    for sym,d in list(trades.items()):
        cur=price_cache.get(sym,0)
        if cur==0: continue
        pnl=(cur-d['entry'])*d['qty'] if d['side']=='LONG' else (d['entry']-cur)*d['qty']
        if pnl>=0: sp+=pnl
        else: sl+=abs(pnl)
    total_net=sp-sl

    # شرطين للخروج: 1- حقق 5$ 2- انعكاس مفاجئ
    should_close = False
    reason = ""
    if total_net >= TARGET:
        should_close = True
        reason = f"هدف {TARGET}$ تحقق"

    if should_close:
        total_realized+=total_net
        trades.clear()
        if ch: await ch.send(f"💰 هروب ذكي V2 - {reason} | صافي {total_net:.2f}$ | مقفلة {total_realized:.2f}$ 🔥")

@tasks.loop(seconds=8)
async def live_board():
    global dashboard_msg
    ch=bot.get_channel(CHANNEL_ID)
    if not ch: return
    txt=""; sp=0; sl=0
    for sym,d in list(trades.items()):
        cur=price_cache.get(sym, d['entry'])
        if cur==0: cur=d['entry']
        pnl=(cur-d['entry'])*d['qty'] if d['side']=='LONG' else (d['entry']-cur)*d['qty']
        if pnl>=0: sp+=pnl
        else: sl+=abs(pnl)
        txt+=f"{sym} {d['side']} RSI:{d.get('rsi',0):.0f}\nدخول {d['entry']:.5f} حالي {cur:.5f}\nربح {pnl:.2f}$\n\n"
    if not txt: txt="🧠 بانتظار اشارة RSI+BB...\n"
    total_net=sp-sl
    l=sum(1 for v in trades.values() if v['side']=='LONG')
    s=sum(1 for v in trades.values() if v['side']=='SHORT')
    footer=f"مقفلة= ${total_realized:.2f}\nأرباح= ${sp:.2f} | خساير= ${sl:.2f}\nالصافي= ${total_net:.2f} | L:{l} S:{s}\nهدف 5$ - رأس مال 500$\nToday at {datetime.now().strftime('%I:%M %p')}"
    embed=discord.Embed(title=f"🧠 ذكي V2 {len(trades)}/{MAX} | صافي {total_net:.2f}$", description=txt, color=0x00ff00)
    embed.add_field(name="\u200b", value=footer, inline=False)
    try:
        if dashboard_msg: await dashboard_msg.edit(embed=embed)
        else: dashboard_msg=await ch.send(embed=embed)
    except: pass

@tasks.loop(minutes=4)
async def keep_alive():
    try:
        requests.get("http://127.0.0.1:10000/", timeout=5)
        url = os.getenv("RENDER_EXTERNAL_URL")
        if url: requests.get(url, timeout=5)
    except: pass

bot.run(TOKEN)

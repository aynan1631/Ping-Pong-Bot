# V84 TRADINGVIEW + BINANCE REAL - GOLD EDITION
from flask import Flask, request, jsonify
import threading, time, os, random, requests
from datetime import datetime
app = Flask(__name__)

BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.environ.get("BINANCE_API_SECRET", "")
REAL_TRADING = bool(BINANCE_API_KEY and BINANCE_API_SECRET)

config = {"capital":1000.0,"per_trade":100.0,"tp_pct":0.80,"sl_pct":0.30,"instant_target":0.50,"real_mode":REAL_TRADING}
state = {"fixed":1000.0,"free":0.0,"safi":0.0,"ghair":0.0,"trades_closed":0,"loss_pool":0.0,"treatment_count":0,"positions":[],"treatment_positions":[],"binance_status":"جاري الربط...","last_update":"...","doctor_stats":{"healed":0,"total_healed_profit":0.0,"failed":0,"start_time":time.time()},"specialty_active":False,"is_running":True,"heartbeat":time.time(),"data_source":"TradingView","real_orders":[]}

def get_tradingview_movers(limit=60):
    try:
        url = "https://scanner.tradingview.com/crypto/scan"
        payload = {"filter": [{"left": "exchange", "operation": "equal", "right": "BINANCE"}],"options": {"lang": "en"},"symbols": {"query": {"types": []}, "tickers": []},"columns": ["name", "close", "change", "volume"],"sort": {"sortBy": "change", "sortOrder": "desc"},"range": {"from": 0, "to": limit}}
        r = requests.post(url, json=payload, timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code == 200:
            data = r.json(); movers=[]
            for row in data.get("data", []):
                d=row.get("d", [])
                if len(d)>=3:
                    name=str(d[0]); close=float(d[1]) if d[1] else 0; change=float(d[2]) if d[2] else 0
                    sym=name.replace("USDT","").replace("BINANCE:","")
                    if sym and close>0 and abs(change)<200:
                        movers.append((sym, change, close))
            if movers:
                state["data_source"]=f"TradingView ({len(movers)}) ✅"
                return movers
    except: pass
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=5)
        if r.status_code==200:
            arr=r.json(); mov=[]
            for t in arr:
                if t["symbol"].endswith("USDT"):
                    mov.append((t["symbol"].replace("USDT",""), float(t["priceChangePercent"]), float(t["lastPrice"])))
            mov.sort(key=lambda x: x[1], reverse=True)
            state["data_source"]="Binance Direct ✅"
            return mov[:limit]
    except: pass
    state["data_source"]="LIGHT محاكي ⚠️"
    coins=["BTC","ETH","SOL","PEPE","FIL","AVAX","DOT","LINK","MATIC","SHIB","DOGE","CREAM","PNT","KDA","CLV","ARK"]
    random.shuffle(coins)
    return [(c, round(random.uniform(0.5,85),1), round(random.uniform(0.001,100),4)) for c in coins[:limit]]

binance_client=None
if REAL_TRADING:
    try:
        from binance.client import Client
        binance_client=Client(BINANCE_API_KEY, BINANCE_API_SECRET)
        bal=binance_client.get_asset_balance(asset='USDT')
        state["binance_status"]=f"✅ Binance حقيقي متصل - USDT: {bal['free']}"
    except Exception as e:
        print(f"Binance fail: {e}"); binance_client=None; config["real_mode"]=False

def place_real_order(symbol, side, amount_usdt):
    if not binance_client: return None, "محاكاة"
    try:
        pair=f"{symbol}USDT"; price=float(binance_client.get_symbol_ticker(symbol=pair)['price'])
        if side=="BUY": order=binance_client.order_market_buy(symbol=pair, quoteOrderQty=amount_usdt)
        else:
            qty=amount_usdt/price
            order=binance_client.order_market_sell(symbol=pair, quantity=qty)
        state["real_orders"].append({"time":datetime.now().strftime("%H:%M:%S"), "sym":symbol, "side":side, "price":price})
        return order, f"حقيقي ✅ {side} {symbol}"
    except Exception as e: return None, f"خطأ: {e}"

def init_positions():
    movers=get_tradingview_movers(60); state["positions"]=[]
    for i in range(min(6, len(movers))):
        sym,pct,price=movers[i]
        if config["real_mode"]: place_real_order(sym, "BUY", config["per_trade"])
        state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}% TV",0,"NORMAL",time.time()])
init_positions()

def engine():
    while True:
        try:
            state["heartbeat"]=time.time()
            movers=get_tradingview_movers(60); mover_dict={m[0]:m for m in movers}
            for p in state["positions"]:
                if p[0] in mover_dict:
                    _,pct,new_price=mover_dict[p[0]]; p[3]=new_price; p[6]=f"مولعة {pct:.1f}% TV"
                    pp=(p[3]-p[2])/p[2]*100; p[4]=round(config["per_trade"]*pp/100,3); p[5]=round(pp,2)
            for p in state["treatment_positions"]:
                if p[0] in mover_dict:
                    _,pct,new_price=mover_dict[p[0]]; p[3]=new_price
                    pp=(p[3]-p[2])/p[2]*100; p[4]=round(config["per_trade"]*pp/100,3); p[5]=round(pp,2)
            tc=len(state["treatment_positions"]); state["treatment_count"]=tc
            if 10<=tc<=15: state["specialty_active"]=True; state["is_running"]=False; state["binance_status"]=f"🏥 تخصصي {tc} مريض ⛔ {state['data_source']}"
            elif tc>15: state["specialty_active"]=True; state["is_running"]=False; state["binance_status"]=f"🚨 عناية {tc}!"
            else:
                if state["specialty_active"] and tc<5: state["specialty_active"]=False; state["is_running"]=True
                elif not state["specialty_active"]: state["is_running"]=True; state["binance_status"]=f"📡 {state['data_source']} | {'حقيقي' if config['real_mode'] else 'محاكي'}"
            state["ghair"]=round(sum([p[4] for p in state["positions"]]),3); state["loss_pool"]=round(sum([abs(p[9]) for p in state["treatment_positions"]]),3); state["last_update"]=datetime.now().strftime("%H:%M:%S")
            if state["is_running"] and state["ghair"]>=config["instant_target"] and state["ghair"]>0 and len(state["positions"])>0:
                if config["real_mode"]:
                    for p in state["positions"]: place_real_order(p[0], "SELL", config["per_trade"])
                state["safi"]=round(state["safi"]+state["ghair"],3); state["trades_closed"]+=len(state["positions"]); state["positions"]=[]; state["ghair"]=0.0
                for i in range(min(6, len(movers))):
                    sym,pct,price=movers[i]
                    if sym not in [x[0] for x in state["treatment_positions"]]:
                        if config["real_mode"]: place_real_order(sym, "BUY", config["per_trade"])
                        state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}% TV",0,"NORMAL",time.time()])
                        if len(state["positions"])>=6: break
                continue
            to_treat=[]; now=time.time()
            for p in list(state["positions"]):
                if p[5]<=-config["sl_pct"] or (p[5]<-0.5 and (now-p[9])>30): to_treat.append(p)
            for p in to_treat:
                loss=abs(p[4])
                if p in state["positions"]:
                    if config["real_mode"]: place_real_order(p[0], "SELL", config["per_trade"])
                    state["positions"].remove(p)
                for sym,pct,price in movers:
                    if sym not in [x[0] for x in state["positions"]+state["treatment_positions"]]:
                        target_needed=loss+config["instant_target"]
                        if config["real_mode"]: place_real_order(sym, "BUY", config["per_trade"])
                        state["treatment_positions"].append([sym,"علاج",price*0.9995,price,0.0,0.0,f"يعالج {p[0]} {loss:.2f}$",0,"TREAT",loss,target_needed,sym+"/USDT",time.time()])
                        break
            cured=[p for p in list(state["treatment_positions"]) if p[4]>=p[10]]
            for p in cured:
                loss=p[9]; net=p[4]-loss
                if config["real_mode"]: place_real_order(p[0], "SELL", config["per_trade"])
                state["safi"]=round(state["safi"]+net,3); state["trades_closed"]+=1; state["doctor_stats"]["healed"]+=1; state["doctor_stats"]["total_healed_profit"]=round(state["doctor_stats"]["total_healed_profit"]+net,3); state["treatment_positions"].remove(p)
            if state["is_running"] and len(state["positions"])<6:
                ex=[x[0] for x in state["positions"]+state["treatment_positions"]]
                for sym,pct,price in movers:
                    if sym not in ex:
                        if config["real_mode"]: place_real_order(sym, "BUY", config["per_trade"])
                        state["positions"].append([sym,"SPOT",price*0.9995,price,0.0,0.0,f"مولعة {pct:.1f}% TV",0,"NORMAL",time.time()])
                        if len(state["positions"])>=6: break
            time.sleep(1.5)
        except Exception as e: print(f"ERR: {e}"); time.sleep(1)
threading.Thread(target=engine,daemon=True).start()

@app.route('/health')
def health(): return f"OK src={state['data_source']} real={config['real_mode']} hb={time.time()-state['heartbeat']:.1f}s",200
@app.route('/api/data')
def api_data():
    total=state["fixed"]+state["safi"]+state["ghair"]-state["loss_pool"]; healed=state["doctor_stats"]["healed"]; total_cases=healed+len(state["treatment_positions"]); heal_rate=round((healed/total_cases*100) if total_cases>0 else 50,1)
    return jsonify({"fixed":state["fixed"],"safi":state["safi"],"ghair":state["ghair"],"total":total,"trades_closed":state["trades_closed"],"loss_pool":state["loss_pool"],"treatment_count":state["treatment_count"],"positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6]] for p in state["positions"]],"treatment_positions":[[p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[9],p[10]] for p in state["treatment_positions"]],"binance_status":state["binance_status"],"last_update":state["last_update"],"instant_target":config["instant_target"],"doctor":state["doctor_stats"],"heal_rate":heal_rate,"specialty_active":state["specialty_active"],"is_running":state["is_running"],"heartbeat":round(time.time()-state["heartbeat"],1),"data_source":state["data_source"],"real_mode":config["real_mode"],"real_orders":state["real_orders"][-5:]})
@app.route('/')
def home(): return "<h1>V84 TV+BINANCE REAL ONLINE - راجع /api/data</h1>"
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))

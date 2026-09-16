def engine():
    while True:
        try:
            if not state["is_running"]: time.sleep(1); continue

            # === حماية الرصيد الحقيقي ===
            if state["mode"]=="REAL":
                try:
                    rb = float(state["real_balance"]) if state["real_balance"]!="--" else 0
                    if rb < 1.0 or rb < config["per_trade"]:
                        state["is_running"]=False
                        state["binance_status"]=f"⛔ تنبيه: لا يوجد رصيد حقيقي كافي {rb}$ - اشحن Binance"
                        state["protect_triggered"]=True
                        time.sleep(3)
                        continue
                except: pass

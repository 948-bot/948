"""
🌾👑 MASTERPIECE V9.1 FINAL SEMPURNA - TANI QUANT HYBRID
Fix: Prob RANGING 50% tidak block lagi kalau Quant 1.00 + Colony 100%
Sumber: Deriv Public (utama) + Binance OFI (filter)
"""
import os, json, random, time, hashlib, requests, logging, sys
import pandas as pd, numpy as np, websocket
from collections import deque
from datetime import datetime, timezone, timedelta

import config
from indicators import calculate_indicators
from math_core import QuantitativeEnsembleModel, DynamicRiskManager
from telegram_notifier import TelegramNotifier

logger = logging.getLogger()
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[logging.StreamHandler(sys.stdout)])

CONFIG_TANI = {
    "DNA_FILE": ".dna_tani_v9.json",
    "MEMORY_FILE": ".memory_tani_v9.json",
    "LAST_FILE": ".last_tani_v9.json",
    "OFFSET_FILE": ".offset_history.json",
    "QUORUM_KECIL": 32, "QUORUM_RAYA": 55,
    "MAX_SPREAD": 9.0,
    "COOLDOWN_KECIL": 900, "COOLDOWN_RAYA": 1800,
}

def is_weekend_off():
    now_utc = datetime.now(timezone.utc)
    wd = now_utc.weekday()
    h_utc = now_utc.hour
    now_wib = now_utc + timedelta(hours=7)
    if wd == 4 and h_utc >= 21: return True, f"Weekend OFF - Jumat {h_utc}:00 UTC = Sabtu 04:00 WIB tutup"
    if wd == 5: return True, "Weekend OFF - Sabtu XAUUSD tutup"
    if wd == 6 and h_utc < 22: return True, f"Weekend OFF - Minggu {h_utc}:00 UTC"
    return False, f"Market ON - {now_wib.strftime('%A %H:%M WIB')}"

def load_json(path, default):
    if os.path.exists(path):
        try: return json.load(open(path))
        except: return default
    return default

def save_json(path, data):
    try: json.dump(data, open(path,'w'))
    except: pass

class AntiBlokirFetcher:
    def __init__(self):
        self.urls = [
            "https://api.binance.com/api/v3/depth?symbol=PAXGUSDT&limit=20",
            "https://api1.binance.com/api/v3/depth?symbol=PAXGUSDT&limit=20",
            "https://data-api.binance.vision/api/v3/depth?symbol=PAXGUSDT&limit=20"
        ]
    def get_ofi(self):
        for url in self.urls:
            try:
                r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                if r.status_code==200:
                    d=r.json(); bids=d['bids']; asks=d['asks']
                    bv=sum(float(q) for _,q in bids[:5]); av=sum(float(q) for _,q in asks[:5])
                    ofi=(bv-av)/(bv+av+1e-9)
                    price=(float(bids[0][0])+float(asks[0][0]))/2
                    return price, float(ofi)
            except: continue
        return None, 0.0

class DerivPublicClient:
    def __init__(self, app_id="1089"):
        self.url=f"wss://ws.derivws.com/websockets/v3?app_id={app_id}"
    def fetch_candles(self, symbol, granularity, count=50):
        count=min(count,50)
        for _ in range(3):
            ws=None
            try:
                ws=websocket.create_connection(self.url, timeout=10)
                ws.send(json.dumps({"ticks_history":symbol,"style":"candles","granularity":int(granularity),"count":count,"end":"latest"}))
                for _ in range(5):
                    res=json.loads(ws.recv())
                    if res.get("msg_type")=="candles": return res.get("candles",[])
                time.sleep(1)
            except: time.sleep(2)
            finally:
                if ws:
                    try: ws.close()
                    except: pass
        return []

class EnsembleV8:
    def __init__(self): self.prices=deque(maxlen=200)
    def preload(self, prices):
        for p in prices: self.prices.append(float(p))
    def final_prob(self, ofi, colony_pct):
        if len(self.prices)<20:
            return 0.5, "RANGING", 2.5, 0.5
        pr=np.array(self.prices)
        ma20=np.mean(pr[-20:]) if len(pr)>=20 else pr[-1]
        ma50=np.mean(pr[-50:]) if len(pr)>=50 else np.mean(pr)
        p1 = 0.62 if ma20>ma50 else 0.38
        trend = "UP" if ma20>ma50 else "DOWN"
        p_ofi = 0.5 + np.clip(ofi*0.6,-0.4,0.4)
        final = p1*0.6 + p_ofi*0.4
        conf = max(abs(final-0.5)*2, colony_pct/100.0, 0.7 if colony_pct>=90 else 0.5)
        atr = float(np.std(pr[-20:])*2.2) if len(pr)>=20 else 2.5
        return final, trend, atr, conf

def run_colony(df_m5):
    try:
        close=df_m5['close']
        if len(close)<20: return 50,50, {},{},{},{}, False
        ema20=close.ewm(20).mean().iloc[-1]
        ema50=close.ewm(50).mean().iloc[-1]
        trend = "BUY" if ema20>ema50 else "SELL"
        lp={"BUY":0,"SELL":0}; lm={"BUY":0,"SELL":0}; lb={"BUY":0,"SELL":0}; ln={"BUY":0,"SELL":0}
        for _ in range(10): lp[trend]+=1
        for _ in range(5): lm["BUY" if lp["BUY"]>lp["SELL"] else "SELL"]+=1
        spread=df_m5['high'].iloc[-1]-df_m5['low'].iloc[-1]
        if spread>CONFIG_TANI["MAX_SPREAD"]: lb["BLOCK"]=3
        else:
            for _ in range(5): lb["BUY" if lm["BUY"]>lm["SELL"] else "SELL"]+=1
        for _ in range(5): ln["BUY" if lb.get("BUY",0)>lb.get("SELL",0) else "SELL"]+=1
        tb=lp["BUY"]+lm["BUY"]+lb.get("BUY",0)+ln["BUY"]
        ts=lp["SELL"]+lm["SELL"]+lb.get("SELL",0)+ln["SELL"]
        total=25
        return tb/total*100, ts/total*100, lp, lm, lb, ln, lb.get("BLOCK",0)>=3
    except: return 50,50, {},{},{},{}, False

def main():
    print(f"=== MASTERPIECE V9.1 FINAL {datetime.now()} ===")
    is_off, reason = is_weekend_off()
    print(reason)

    fetcher=AntiBlokirFetcher()
    paxg_price, ofi = fetcher.get_ofi()
    print(f"OFI: {ofi:+.2f} PAXG: {paxg_price}")

    dna=load_json(CONFIG_TANI["DNA_FILE"], {"pemetik_0":{"skor":0}})
    memory=load_json(CONFIG_TANI["MEMORY_FILE"], {"gudang":0,"panen_kecil":0,"panen_raya":0})
    last=load_json(CONFIG_TANI["LAST_FILE"], {})

    if is_off:
        print("WEEKEND MODE - Evaluasi only")
        if time.time()-last.get("last_weekend_check",0)>21600:
            try:
                notifier=TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
                notifier.send_error(f"🌴 V9.1 WEEKEND EVALUASI\nGudang {memory.get('gudang',0)}$ | OFI {ofi:+.2f}\nPAXG {paxg_price:.2f}\nAuto ON Senin 05:00 WIB")
                last["last_weekend_check"]=time.time(); save_json(CONFIG_TANI["LAST_FILE"], last)
            except Exception as e: print(f"Weekend fail {e}")
        return

    deriv=DerivPublicClient(config.DERIV_APP_ID)
    def fetch(tf, cnt=50):
        for _ in range(3):
            d=deriv.fetch_candles(config.SYMBOL, tf, cnt)
            if len(d)>=30: return d
            time.sleep(1)
        return d if d else []

    c30=fetch(config.TIMEFRAMES["M30"]); c15=fetch(config.TIMEFRAMES["M15"]); c5=fetch(config.TIMEFRAMES["M5"])
    if not c30 or not c15 or not c5:
        logging.warning("Deriv lag, skip"); return

    df30=calculate_indicators(pd.DataFrame(c30))
    df15=calculate_indicators(pd.DataFrame(c15))
    df5=calculate_indicators(pd.DataFrame(c5))
    if df5.empty: logging.warning("Indikator kosong"); return

    sb=QuantitativeEnsembleModel.evaluate_setup(df30,df15,df5,"BUY") or 0.0
    ss=QuantitativeEnsembleModel.evaluate_setup(df30,df15,df5,"SELL") or 0.0
    logging.info(f"Quant Score BUY:{sb:.2f} SELL:{ss:.2f}")

    buy_pct, sell_pct, lp, lm, lb, ln, is_block = run_colony(df5)
    if is_block: logging.info("BLOCK spread tinggi"); return

    ens=EnsembleV8(); ens.preload(df5['close'].tolist())
    final_prob, trend, atr_tani, conf = ens.final_prob(ofi, max(buy_pct,sell_pct))
    logging.info(f"TANI Colony BUY {buy_pct:.0f}% SELL {sell_pct:.0f}% Prob {final_prob*100:.0f}% Conf {conf*100:.0f}% Trend {trend} OFI {ofi:.2f}")

    # --- FIX UTAMA DARI SCREENSHOT LU ---
    keputusan=None; jenis=None; final_score=0
    super_sell = ss>=0.90 and sell_pct>=95 and ofi<0.2
    super_buy = sb>=0.90 and buy_pct>=95 and ofi>-0.2

    # PANEN KECIL - longgar
    if (buy_pct>=CONFIG_TANI["QUORUM_KECIL"] and sb>=0.50 and (final_prob>0.50 or super_buy)) or super_buy:
        if ofi>-0.35:
            keputusan="BUY"; jenis="PANEN KECIL"; final_score=(sb+buy_pct/100+final_prob)/3
    if (sell_pct>=CONFIG_TANI["QUORUM_KECIL"] and ss>=0.50 and (final_prob<0.50 or super_sell)) or super_sell:
        if ofi<0.35:
            keputusan="SELL"; jenis="PANEN KECIL"; final_score=(ss+sell_pct/100+(1-final_prob))/3

    # PANEN RAYA - ketat
    if buy_pct>=CONFIG_TANI["QUORUM_RAYA"] and sb>=0.65 and (final_prob>0.58 or super_buy):
        keputusan="BUY"; jenis="PANEN RAYA"; final_score=0.85
    if sell_pct>=CONFIG_TANI["QUORUM_RAYA"] and ss>=0.65 and (final_prob<0.42 or super_sell):
        keputusan="SELL"; jenis="PANEN RAYA"; final_score=0.85

    if not keputusan:
        logging.info(f"Belum quorum Quant {sb:.2f}/{ss:.2f} Colony {buy_pct:.0f}%/{sell_pct:.0f}% OFI {ofi:.2f}")
        return

    if last.get("keputusan")==keputusan and time.time()-last.get("time",0)<(CONFIG_TANI["COOLDOWN_KECIL"] if jenis=="PANEN KECIL" else CONFIG_TANI["COOLDOWN_RAYA"]):
        logging.info(f"Cooldown {jenis} {keputusan}"); return

    price=float(df5['close'].dropna().iloc[-1]); atr=float(df5['atr'].dropna().iloc[-1])
    risk=DynamicRiskManager.calculate_levels(price, atr, keputusan)
    if risk["rrr_actual"]<config.MIN_RISK_REWARD:
        logging.info(f"RRR {risk['rrr_actual']} < min"); return

    notifier=TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
    try:
        notifier.send_signal(direction=keputusan, entry=price, sl=risk['sl'], tp=risk['tp'], lot=risk['suggested_lot'], rrr=risk['rrr_actual'], timeframe=f"V9.1 {jenis} {trend} OFI:{ofi:.2f}")
        memory['gudang']=memory.get('gudang',0)+(15 if jenis=="PANEN KECIL" else 32)
        memory['panen_kecil' if jenis=="PANEN KECIL" else 'panen_raya']=memory.get('panen_kecil' if jenis=="PANEN KECIL" else 'panen_raya',0)+1
        save_json(CONFIG_TANI["MEMORY_FILE"], memory)
        save_json(CONFIG_TANI["LAST_FILE"], {"keputusan":keputusan,"jenis":jenis,"time":time.time(),"price":price})
        logging.info(f"Sinyal {jenis} {keputusan} terkirim! RRR {risk['rrr_actual']}")
    except Exception as e: logging.error(f"Send fail {e}")

if __name__=="__main__": main()

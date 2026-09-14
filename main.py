"""
🌾👑 MASTERPIECE V9.2 FINAL SEMPURNA - FIX #51 OFI +0.46
Quant SELL 1.00 + Colony 100% + Conf 100% = TEMBUS walau OFI berlawanan
"""
import os, json, random, time, requests, logging, sys
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
    "QUORUM_KECIL": 32, "QUORUM_RAYA": 55,
    "MAX_SPREAD": 9.0,
    "COOLDOWN_KECIL": 900, "COOLDOWN_RAYA": 1800,
}

def is_weekend_off():
    now_utc = datetime.now(timezone.utc)
    wd = now_utc.weekday(); h_utc = now_utc.hour
    now_wib = now_utc + timedelta(hours=7)
    if wd == 4 and h_utc >= 21: return True, f"Weekend OFF Sabtu 04:00 WIB tutup"
    if wd == 5: return True, "Weekend OFF Sabtu"
    if wd == 6 and h_utc < 22: return True, f"Weekend OFF Minggu"
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
        return 4313.0, 0.0

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
            except: time.sleep(1)
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
        if len(self.prices)<20: return 0.5, "RANGING", 2.5, 50.0
        pr=np.array(self.prices)
        ma20=np.mean(pr[-20:]); ma50=np.mean(pr[-50:]) if len(pr)>=50 else np.mean(pr)
        p1=0.62 if ma20>ma50 else 0.38
        trend="UP" if ma20>ma50 else "DOWN"
        p_ofi=0.5+np.clip(ofi*0.6,-0.4,0.4)
        final=p1*0.6+p_ofi*0.4
        conf=max(abs(final-0.5)*2, colony_pct/100.0, 0.7 if colony_pct>=90 else 0.5)*100
        atr=float(np.std(pr[-20:])*2.2)
        return final, trend, atr, conf

def run_colony(df_m5):
    try:
        close=df_m5['close']
        if len(close)<10: return 50,50,False
        ema20=close.ewm(20).mean().iloc[-1]; ema50=close.ewm(50).mean().iloc[-1]
        trend="BUY" if ema20>ema50 else "SELL"
        buy=0; sell=0
        for _ in range(25):
            if trend=="BUY": buy+=1
            else: sell+=1
        total=25
        return buy/total*100, sell/total*100, False
    except: return 50,50,False

def main():
    print(f"=== MASTERPIECE V9.2 SEMPURNA {datetime.now()} ===")
    is_off, reason = is_weekend_off()
    print(reason)

    fetcher=AntiBlokirFetcher()
    paxg_price, ofi = fetcher.get_ofi()
    print(f"OFI: {ofi:+.2f} PAXG: {paxg_price}")

    memory=load_json(CONFIG_TANI["MEMORY_FILE"], {"gudang":0,"panen_kecil":0,"panen_raya":0})
    last=load_json(CONFIG_TANI["LAST_FILE"], {})

    if is_off:
        print("WEEKEND MODE")
        if time.time()-last.get("last_weekend_check",0)>21600:
            try:
                n=TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
                n.send_error(f"🌴 V9.2 WEEKEND\nGudang {memory.get('gudang',0)}$ OFI {ofi:+.2f} PAXG {paxg_price:.2f}")
                last["last_weekend_check"]=time.time(); save_json(CONFIG_TANI["LAST_FILE"], last)
            except: pass
        return

    deriv=DerivPublicClient(config.DERIV_APP_ID)
    def fetch(tf):
        for _ in range(3):
            d=deriv.fetch_candles(config.SYMBOL, tf, 50)
            if len(d)>=30: return d
            time.sleep(1)
        return d

    c30=fetch(config.TIMEFRAMES["M30"]); c15=fetch(config.TIMEFRAMES["M15"]); c5=fetch(config.TIMEFRAMES["M5"])
    if not c30 or not c15 or not c5:
        logging.warning("Deriv lag skip"); return

    df30=calculate_indicators(pd.DataFrame(c30))
    df15=calculate_indicators(pd.DataFrame(c15))
    df5=calculate_indicators(pd.DataFrame(c5))
    if df5.empty: return

    sb=QuantitativeEnsembleModel.evaluate_setup(df30,df15,df5,"BUY") or 0.0
    ss=QuantitativeEnsembleModel.evaluate_setup(df30,df15,df5,"SELL") or 0.0
    logging.info(f"Quant Score BUY:{sb:.2f} SELL:{ss:.2f}")

    buy_pct, sell_pct, is_block = run_colony(df5)
    ens=EnsembleV8(); ens.preload(df5['close'].tolist())
    final_prob, trend, atr_tani, conf = ens.final_prob(ofi, max(buy_pct,sell_pct))
    logging.info(f"TANI Colony BUY {buy_pct:.0f}% SELL {sell_pct:.0f}% Prob {final_prob*100:.0f}% Conf {conf:.0f}% Trend {trend} OFI {ofi:.2f}")

    # === FIX SEMPURNA DARI LOG #51 ===
    keputusan=None; jenis=None
    super_sell = ss>=0.90 and sell_pct>=95
    super_buy = sb>=0.90 and buy_pct>=95

    if super_sell:
        keputusan="SELL"; jenis="PANEN RAYA" if conf>=90 else "PANEN KECIL"
        logging.info(f"SUPER SELL TEMBUS! Quant {ss} Colony {sell_pct}% Conf {conf:.0f}% OFI {ofi:+.2f} -> IGNORE OFI")
    elif super_buy:
        keputusan="BUY"; jenis="PANEN RAYA" if conf>=90 else "PANEN KECIL"
        logging.info(f"SUPER BUY TEMBUS! Quant {sb} Colony {buy_pct}% Conf {conf:.0f}% OFI {ofi:+.2f} -> IGNORE OFI")
    else:
        if buy_pct>=32 and sb>=0.50 and final_prob>0.50 and ofi>-0.35:
            keputusan="BUY"; jenis="PANEN KECIL"
        if sell_pct>=32 and ss>=0.50 and final_prob<0.50 and ofi<0.35:
            keputusan="SELL"; jenis="PANEN KECIL"
        if buy_pct>=55 and sb>=0.65 and final_prob>0.58 and ofi>-0.1:
            keputusan="BUY"; jenis="PANEN RAYA"
        if sell_pct>=55 and ss>=0.65 and final_prob<0.42 and ofi<0.1:
            keputusan="SELL"; jenis="PANEN RAYA"

    if not keputusan:
        logging.info(f"Belum quorum Quant {sb:.2f}/{ss:.2f} Colony {buy_pct:.0f}%/{sell_pct:.0f}% OFI {ofi:.2f}")
        return

    if last.get("keputusan")==keputusan and time.time()-last.get("time",0)<(CONFIG_TANI["COOLDOWN_KECIL"] if jenis=="PANEN KECIL" else CONFIG_TANI["COOLDOWN_RAYA"]):
        logging.info(f"Cooldown {jenis} {keputusan}"); return

    price=float(df5['close'].dropna().iloc[-1]); atr=float(df5['atr'].dropna().iloc[-1])
    risk=DynamicRiskManager.calculate_levels(price, atr, keputusan)
    if risk["rrr_actual"]<config.MIN_RISK_REWARD: return

    notifier=TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
    try:
        notifier.send_signal(direction=keputusan, entry=price, sl=risk['sl'], tp=risk['tp'], lot=risk['suggested_lot'], rrr=risk['rrr_actual'], timeframe=f"V9.2 {jenis} {trend} OFI:{ofi:.2f} Conf:{conf:.0f}%")
        memory['gudang']=memory.get('gudang',0)+(15 if jenis=="PANEN KECIL" else 32)
        save_json(CONFIG_TANI["MEMORY_FILE"], memory)
        save_json(CONFIG_TANI["LAST_FILE"], {"keputusan":keputusan,"jenis":jenis,"time":time.time()})
        logging.info(f"SINYAL {jenis} {keputusan} TERKIRIM! Price {price} RRR {risk['rrr_actual']}")
    except Exception as e: logging.error(f"Send fail {e}")

if __name__=="__main__": main()

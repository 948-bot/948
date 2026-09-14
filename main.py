"""
🌾👑 MASTERPIECE V9 - TANI QUANT HYBRID
Gabungan: Deriv Quant (akurat) + TANI V8.8 (OFI, Colony, Weekend, DNA)
- Sumber utama: Deriv Public WS (anti blokir yfinance)
- Sumber filter: Binance OFI PAXG (anti fake signal)
- Weekend: Evaluasi + lapor PAXG
- Tanpa MT5 auto trade, Telegram ONLY
"""
import os, json, random, time, hashlib, requests, logging, sys
import pandas as pd, numpy as np, websocket
from collections import deque
from datetime import datetime, timezone, timedelta

import config
from indicators import calculate_indicators
from math_core import QuantitativeEnsembleModel, DynamicRiskManager
from telegram_notifier import TelegramNotifier

# --- Setup Logging ---
logger = logging.getLogger()
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[logging.StreamHandler(sys.stdout)])

# --- CONFIG HYBRID ---
CONFIG_TANI = {
    "DNA_FILE": ".dna_tani_v9.json",
    "MEMORY_FILE": ".memory_tani_v9.json",
    "LAST_FILE": ".last_tani_v9.json",
    "OFFSET_FILE": ".offset_history.json",
    "PEMETIK": 10, "MANDOR": 5, "PEMBAJAK": 5, "PENUAI": 5,
    "QUORUM_KECIL": 32, "QUORUM_RAYA": 55,
    "MAX_SPREAD": 9.0, "MIN_FVG": 0.4,
    "MAX_SIGNALS_PER_HOUR": 4, "CONF_THRESHOLD": 0.68,
    "COOLDOWN_KECIL": 900, "COOLDOWN_RAYA": 1800,
}

# --- 1. WEEKEND OFF LOGIC (Dari TANI, lebih akurat) ---
def is_weekend_off():
    now_utc = datetime.now(timezone.utc)
    now_wib = now_utc + timedelta(hours=7)
    wd = now_utc.weekday()
    h_utc = now_utc.hour
    if wd == 4 and h_utc >= 21: return True, f"Weekend OFF - Jumat {h_utc}:00 UTC = Sabtu 04:00 WIB tutup"
    if wd == 5: return True, "Weekend OFF - Sabtu XAUUSD tutup"
    if wd == 6 and h_utc < 22: return True, f"Weekend OFF - Minggu {h_utc}:00 UTC, buka Senin 05:00 WIB"
    return False, f"Market ON - {now_wib.strftime('%A %H:%M WIB')}"

def load_json(path, default):
    if os.path.exists(path):
        try: return json.load(open(path))
        except: return default
    return default
def save_json(path, data):
    try: json.dump(data, open(path,'w'))
    except: pass

# --- 2. ANTI BLOKIR FETCHER (Bagusnya TANI) - Cuma untuk OFI & PAXG ---
class AntiBlokirFetcher:
    def __init__(self):
        self.ua = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"]
        self.depth_urls = ["https://api.binance.com/api/v3/depth?symbol=PAXGUSDT&limit=20",
                           "https://api1.binance.com/api/v3/depth?symbol=PAXGUSDT&limit=20",
                           "https://data-api.binance.vision/api/v3/depth?symbol=PAXGUSDT&limit=20"]
    def get_ofi(self):
        for url in self.depth_urls:
            try:
                r = requests.get(url, headers={"User-Agent": random.choice(self.ua)}, timeout=5)
                if r.status_code==200:
                    data=r.json(); bids=data['bids']; asks=data['asks']
                    bv=sum(float(q) for _,q in bids[:5]); av=sum(float(q) for _,q in asks[:5])
                    ofi=(bv-av)/(bv+av+1e-9)
                    price=(float(bids[0][0])+float(asks[0][0]))/2
                    return price, ofi
            except: continue
        return None, 0.0

# --- 3. DERIV CLIENT (Bagusnya Masterpiece) - Sumber Utama ---
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

# --- 4. ENSEMBLE V8 (Bagusnya TANI) ---
class EnsembleV8:
    def __init__(self): self.prices=deque(maxlen=200)
    def preload(self, prices):
        for p in prices: self.prices.append(float(p))
    def final_prob(self, ofi, colony_pct):
        if len(self.prices)<50: return 0.5, "RANGING", 2.5, 0.5
        pr=np.array(self.prices); ma20=np.mean(pr[-20:]); ma50=np.mean(pr[-50:])
        p1 = 0.62 if ma20>ma50 else 0.38
        trend = "UP" if ma20>ma50 else "DOWN"
        p_ofi = 0.5 + np.clip(ofi*0.6,-0.4,0.4)
        final = p1*0.6 + p_ofi*0.4
        conf = max(abs(final-0.5)*2, colony_pct/100.0)
        atr = float(np.std(pr[-20:])*2.2)
        return final, trend, atr, conf

# --- 5. COLONY LOGIC (Bagusnya TANI, gue bikin deterministik) ---
def init_dna():
    dna={}
    for i in range(CONFIG_TANI["PEMETIK"]): dna[f"pemetik_{i}"]={"skor":0,"panen":0,"alat_lv":1}
    for i in range(CONFIG_TANI["MANDOR"]): dna[f"mandor_{i}"]={"skor":5,"panen":0,"alat_lv":2}
    for i in range(CONFIG_TANI["PEMBAJAK"]): dna[f"pembajak_{i}"]={"skor":10,"panen":0,"alat_lv":2}
    for i in range(CONFIG_TANI["PENUAI"]): dna[f"penuai_{i}"]={"skor":15,"panen":0,"alat_lv":3}
    return dna

def run_colony(df_m5):
    # Deterministik, tanpa random
    try:
        close=df_m5['close']; ema20=close.ewm(20).mean().iloc[-1]; ema50=close.ewm(50).mean().iloc[-1]
        trend = "BUY" if ema20>ema50 else "SELL"
        lp={"BUY":0,"SELL":0}; lm={"BUY":0,"SELL":0}; lb={"BUY":0,"SELL":0}; ln={"BUY":0,"SELL":0}
        # Pemetik 10 suara
        for _ in range(10): lp[trend]+=1
        # Mandor ikut pemetik
        for _ in range(5): lm["BUY" if lp["BUY"]>lp["SELL"] else "SELL"]+=1
        # Pembajak cek spread
        spread=df_m5['high'].iloc[-1]-df_m5['low'].iloc[-1]
        if spread>CONFIG_TANI["MAX_SPREAD"]: lb["BLOCK"]=3
        else:
            for _ in range(5): lb["BUY" if lm["BUY"]>lm["SELL"] else "SELL"]+=1
        # Penuai final
        for _ in range(5): ln["BUY" if lb.get("BUY",0)>lb.get("SELL",0) else "SELL"]+=1

        tb=lp["BUY"]+lm["BUY"]+lb.get("BUY",0)+ln["BUY"]
        ts=lp["SELL"]+lm["SELL"]+lb.get("SELL",0)+ln["SELL"]
        total=25; buy_pct=tb/total*100; sell_pct=ts/total*100
        return buy_pct, sell_pct, lp, lm, lb, ln, lb.get("BLOCK",0)>=3
    except: return 50,50, {},{},{},{}, False

# --- MAIN HYBRID ---
def main():
    print(f"=== MASTERPIECE V9 HYBRID {datetime.now()} ===")
    is_off, reason = is_weekend_off()
    print(reason)

    fetcher=AntiBlokirFetcher()
    paxg_price, ofi = fetcher.get_ofi()
    print(f"OFI: {ofi:+.2f} PAXG: {paxg_price}")

    # Load DNA/Memory
    dna=load_json(CONFIG_TANI["DNA_FILE"], init_dna())
    memory=load_json(CONFIG_TANI["MEMORY_FILE"], {"gudang":0,"panen_kecil":0,"panen_raya":0,"evolutions":0})
    last=load_json(CONFIG_TANI["LAST_FILE"], {})

    # WEEKEND MODE
    if is_off:
        print("WEEKEND MODE - Evaluasi only")
        if time.time()-last.get("last_weekend_check",0)>21600: # 6 jam sekali
            try:
                notifier=TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
                notifier.send_error(f"🌴 V9 WEEKEND EVALUASI\nGudang {memory['gudang']}$ | OFI {ofi:+.2f}\nPAXG {paxg_price:.2f}\nPasar tutup, auto ON Senin 05:00 WIB")
                last["last_weekend_check"]=time.time(); save_json(CONFIG_TANI["LAST_FILE"], last)
            except Exception as e: print(f"Weekend send fail {e}")
        return

    # WEEKDAY - Fetch Deriv (Utama)
    deriv=DerivPublicClient(config.DERIV_APP_ID)
    def fetch(tf, cnt=50):
        for _ in range(3):
            d=deriv.fetch_candles(config.SYMBOL, tf, cnt)
            if len(d)>=30: return d
            time.sleep(2)
        return d if d else []

    c30=fetch(config.TIMEFRAMES["M30"]); c15=fetch(config.TIMEFRAMES["M15"]); c5=fetch(config.TIMEFRAMES["M5"])
    if not c30 or not c15 or not c5:
        logging.warning("Deriv lag, skip"); return

    df30=calculate_indicators(pd.DataFrame(c30)); df15=calculate_indicators(pd.DataFrame(c15)); df5=calculate_indicators(pd.DataFrame(c5))
    if df5.empty: logging.warning("Indikator kosong"); return

    # --- QUANT SCORE (Masterpiece) ---
    sb=QuantitativeEnsembleModel.evaluate_setup(df30,df15,df5,"BUY")
    ss=QuantitativeEnsembleModel.evaluate_setup(df30,df15,df5,"SELL")
    logging.info(f"Quant Score BUY:{sb:.2f} SELL:{ss:.2f}")

    # --- TANI COLONY + ENSEMBLE ---
    buy_pct, sell_pct, lp, lm, lb, ln, is_block = run_colony(df5)
    if is_block: logging.info("BLOCK spread tinggi"); return

    ens=EnsembleV8(); ens.preload(df5['close'].tolist())
    final_prob, trend, atr_tani, conf = ens.final_prob(ofi, max(buy_pct,sell_pct))
    logging.info(f"TANI Colony BUY {buy_pct:.0f}% SELL {sell_pct:.0f}% Prob {final_prob*100:.0f}% Conf {conf*100:.0f}% Trend {trend} OFI {ofi:+.2f}")

    # --- GABUNGKAN KEPUTUSAN ---
    keputusan=None; jenis=None; final_score=0
    # Syarat: Quant + Colony + OFI harus searah
    if buy_pct>=CONFIG_TANI["QUORUM_KECIL"] and sb>=0.55 and final_prob>0.58 and ofi>-0.3:
        keputusan="BUY"; jenis="PANEN KECIL"; final_score=(sb+buy_pct/100+final_prob)/3
    if sell_pct>=CONFIG_TANI["QUORUM_KECIL"] and ss>=0.55 and final_prob<0.42 and ofi<0.3:
        keputusan="SELL"; jenis="PANEN KECIL"; final_score=(ss+sell_pct/100+(1-final_prob))/3

    if buy_pct>=CONFIG_TANI["QUORUM_RAYA"] and sb>=0.70 and final_prob>0.65 and ofi>0.1:
        keputusan="BUY"; jenis="PANEN RAYA"; final_score=(sb+buy_pct/100+final_prob)/3
    if sell_pct>=CONFIG_TANI["QUORUM_RAYA"] and ss>=0.70 and final_prob<0.35 and ofi<-0.1:
        keputusan="SELL"; jenis="PANEN RAYA"; final_score=(ss+sell_pct/100+(1-final_prob))/3

    if not keputusan:
        logging.info(f"Belum quorum Quant {sb:.2f}/{ss:.2f} Colony {buy_pct:.0f}%/{sell_pct:.0f}% OFI {ofi:.2f}"); return

    # Anti spam
    if last.get("keputusan")==keputusan and time.time()-last.get("time",0)<(CONFIG_TANI["COOLDOWN_KECIL"] if jenis=="PANEN KECIL" else CONFIG_TANI["COOLDOWN_RAYA"]):
        logging.info(f"Cooldown {jenis} {keputusan}"); return

    # Hitung Risk
    price=float(df5['close'].dropna().iloc[-1]); atr=float(df5['atr'].dropna().iloc[-1])
    risk=DynamicRiskManager.calculate_levels(price, atr, keputusan)

    if risk["rrr_actual"]<config.MIN_RISK_REWARD:
        logging.info(f"RRR {risk['rrr_actual']} < min"); return

    # Kirim Telegram
    notifier=TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
    # Format pesan hybrid
    msg = (f"{'🌾👑🔥' if jenis=='PANEN RAYA' else '🌿'} V9 {jenis} {keputusan} {final_score*100:.0f}%\n"
           f"{'BUY 🟢' if keputusan=='BUY' else 'SELL 🔴'} {trend} | Conf {conf*100:.0f}% | OFI {ofi:+.2f}\n"
           f"Quant BUY {sb*100:.0f}% SELL {ss*100:.0f}% | Colony {buy_pct:.0f}% vs {sell_pct:.0f}%\n"
           f"ENTRY {price:.2f} SL {risk['sl']:.2f} TP {risk['tp']:.2f} RRR {risk['rrr_actual']}\n"
           f"Gudang {memory['gudang']}$")

    try:
        notifier.send_signal(direction=keputusan, entry=price, sl=risk['sl'], tp=risk['tp'], lot=risk['suggested_lot'], rrr=risk['rrr_actual'], timeframe=f"V9 {jenis} {trend} OFI:{ofi:.2f}")
        # Update DNA & Memory
        memory['gudang']+=15 if jenis=="PANEN KECIL" else 32
        memory['panen_kecil' if jenis=="PANEN KECIL" else 'panen_raya']+=1
        save_json(CONFIG_TANI["MEMORY_FILE"], memory)
        save_json(CONFIG_TANI["LAST_FILE"], {"keputusan":keputusan,"jenis":jenis,"time":time.time(),"price":price})
        logging.info(f"Sinyal {jenis} {keputusan} terkirim!")
    except Exception as e: logging.error(f"Send fail {e}")

if __name__=="__main__": main()

import logging, pandas as pd, time, sys
import config
from indicators import calculate_indicators
from math_core import QuantitativeEnsembleModel, DynamicRiskManager
from deriv_client import DerivPublicClient
from telegram_notifier import TelegramNotifier

logger = logging.getLogger()
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("bot.log", encoding="utf-8")])

MIN_CANDLES_REQUIRED = 30
ATR_PERIOD = 14

def validate_config():
    req = ["DERIV_APP_ID","TELEGRAM_BOT_TOKEN","TELEGRAM_CHAT_ID","SYMBOL","TIMEFRAMES","MIN_RISK_REWARD"]
    miss = [a for a in req if not hasattr(config,a) or not getattr(config,a)]
    if miss: raise AttributeError(f"Config hilang: {miss}")

def ensure_atr(df, period=14):
    if df is None or df.empty: return df
    df.columns=[c.lower() for c in df.columns]
    if 'atr' in df.columns and not df['atr'].dropna().empty: return df
    try:
        tr = pd.concat([(df['high']-df['low']), (df['high']-df['close'].shift()).abs(), (df['low']-df['close'].shift()).abs()], axis=1).max(axis=1)
        df['atr']=tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    except: pass
    return df

def get_last_closed(df):
    df_valid=df.dropna(subset=['close','atr'])
    if df_valid.empty: raise ValueError("atr/close NaN semua")
    try:
        p=df['close'].iloc[-2]; a=df['atr'].iloc[-2]
        if not pd.isna(p) and not pd.isna(a) and a>0: return p,a
    except: pass
    r=df_valid.iloc[-1]; return r['close'], r['atr']

def fetch_with_retry(deriv, symbol, tf, count=50, retries=3):
    rc=min(int(count),50); last=[]
    for i in range(retries):
        try:
            data=deriv.fetch_candles(symbol,tf,count=rc)
            if data: last=data
            if len(data)>=30: return data
            logging.warning(f"Data {tf} kurang ({len(data) if data else 0}), retry {i+1}")
        except Exception as e: logging.warning(f"Fetch {tf} err {i+1}: {e}")
        time.sleep(3)
    if last and len(last)>=20:
        logging.warning(f"Pakai seadanya {len(last)} untuk {tf}"); return last
    logging.error(f"Gagal fetch {tf} setelah {retries}x"); return []

def safe_calc(candles, name):
    df=pd.DataFrame(candles)
    if df.empty: raise ValueError(f"{name} kosong")
    df=calculate_indicators(df); df=ensure_atr(df, ATR_PERIOD)
    if df.empty or 'atr' not in df.columns: raise ValueError(f"{name} no ATR")
    logging.info(f"{name} OK Len:{len(df)} ATR:{df['atr'].dropna().iloc[-1]:.3f}"); return df

def main():
    try:
        validate_config()
        if not config.is_market_hours():
            logging.info("Luar jam operasional WIB. Standby."); return
        deriv=DerivPublicClient(config.DERIV_APP_ID)
        notifier=TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
        logging.info("Fetch M30 M15 M5...")
        c30=fetch_with_retry(deriv,config.SYMBOL,config.TIMEFRAMES["M30"],50)
        c15=fetch_with_retry(deriv,config.SYMBOL,config.TIMEFRAMES["M15"],50)
        c5=fetch_with_retry(deriv,config.SYMBOL,config.TIMEFRAMES["M5"],50)
        if not c30 or not c15 or not c5:
            logging.warning("Deriv lag / data kosong, skip cycle, tetap SUCCESS"); return
        df30=safe_calc(c30,"M30"); df15=safe_calc(c15,"M15"); df5=safe_calc(c5,"M5")
        sb=QuantitativeEnsembleModel.evaluate_setup(df30,df15,df5,"BUY") or 0.0
        ss=QuantitativeEnsembleModel.evaluate_setup(df30,df15,df5,"SELL") or 0.0
        logging.info(f"Score BUY:{sb:.2f} SELL:{ss:.2f}")
        try:
            if notifier.check_recent_signal(15): logging.info("Anti-spam aktif"); return
        except Exception as e: logging.warning(f"Anti-spam skip: {e}")
        price,atr=get_last_closed(df5)
        logging.info(f"Price:{price} ATR:{atr}")
        sent=False
        for dirc, sc in [("BUY",sb),("SELL",ss)]:
            if sent: break
            if sc>=0.75:
                risk=DynamicRiskManager.calculate_levels(price,atr,dirc)
                if risk["rrr_actual"]>=config.MIN_RISK_REWARD:
                    notifier.send_signal(direction=dirc, entry=price, sl=risk["sl"], tp=risk["tp"], lot=risk["suggested_lot"], rrr=risk["rrr_actual"], timeframe="M5/M15/M30")
                    sent=True
        if not sent: logging.info("Tidak ada setup >=0.75 RRR")
    except Exception as e:
        logging.error(f"Critical: {e}", exc_info=True)
        try: TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID).send_error(str(e))
        except: pass
        raise

if __name__=="__main__": main()

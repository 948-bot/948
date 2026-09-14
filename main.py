import logging
import pandas as pd
import time
import sys

import config
from indicators import calculate_indicators
from math_core import QuantitativeEnsembleModel, DynamicRiskManager
from deriv_client import DerivPublicClient
from telegram_notifier import TelegramNotifier

# Setup logging biar tidak duplikat di GitHub Actions
logger = logging.getLogger()
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("bot.log", encoding="utf-8"),
        ],
    )

# INI FIX UTAMA: Butuh minimal 100 candle, bukan 2
MIN_CANDLES_REQUIRED = 100 
ATR_PERIOD = 14
CANDLE_BUFFER = 20 # buffer buat warmup indikator

def validate_config():
    required = ["DERIV_APP_ID", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "SYMBOL", "TIMEFRAMES", "MIN_RISK_REWARD"]
    missing = []
    for attr in required:
        if not hasattr(config, attr) or not getattr(config, attr):
            missing.append(attr)
    if missing:
        raise AttributeError(f"Konfigurasi kosong/hilang: {missing}")

def ensure_atr(df: pd.DataFrame, period=14) -> pd.DataFrame:
    """Fallback manual kalau calculate_indicators gagal bikin ATR. Ini yang selamatkan dari KeyError"""
    if df is None or df.empty:
        return df
    # normalisasi nama kolom biar case-insensitive
    df.columns = [c.lower() for c in df.columns]
    if 'atr' in df.columns and not df['atr'].dropna().empty:
        return df
    
    logging.warning("Kolom 'atr' tidak ada / NaN semua, hitung manual fallback...")
    try:
        high, low, close = df['high'], df['low'], df['close']
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=period, min_periods=period).mean()
    except Exception as e:
        logging.error(f"Gagal hitung ATR manual: {e}")
    return df

def get_last_closed_candle(df: pd.DataFrame):
    """Ambil candle close terakhir yang valid dan tidak NaN"""
    if df is None or len(df) < 2:
        raise ValueError("Dataframe kurang dari 2 baris")
    
    # Coba iloc[-2] dulu (untuk hindari repainting), kalau NaN fallback ke last valid
    df_valid = df.dropna(subset=['close', 'atr'])
    if df_valid.empty:
        raise ValueError("Semua atr/close NaN, warmup belum selesai")
    
    # Kalau candle terakhir masih forming, -2 adalah yang closed. Kita ambil yang terakhir yang valid
    last_row = df_valid.iloc[-1]
    if len(df_valid) >= 2:
        # cek apakah candle terakhir di Deriv adalah forming (opsional)
        # untuk aman, kita ambil iloc[-2] dari data valid
        if len(df) >= 3 and df['close'].iloc[-1] != last_row['close']:
             last_row = df_valid.iloc[-2] if len(df_valid) >=2 else df_valid.iloc[-1]

    return last_row['close'], last_row['atr']

def fetch_with_retry(deriv, symbol, tf, count, retries=3):
    for i in range(retries):
        try:
            data = deriv.fetch_candles(symbol, tf, count=count)
            if data and len(data) >= MIN_CANDLES_REQUIRED - CANDLE_BUFFER:
                return data
            logging.warning(f"Data {tf} kurang ({len(data) if data else 0}), retry {i+1}/{retries}")
        except Exception as e:
            logging.warning(f"Fetch {tf} gagal attempt {i+1}: {e}")
        time.sleep(2)
    raise ConnectionError(f"Gagal fetch {tf} setelah {retries}x percobaan")

def main():
    try:
        validate_config()

        if not config.is_market_hours():
            logging.info("Di luar jam operasional WIB. Standby.")
            return

        deriv = DerivPublicClient(config.DERIV_APP_ID)
        notifier = TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)

        logging.info("Mengambil data M30, M15, M5...")
        # FIX: Count diperbesar biar indikator matang
        candles_m30 = fetch_with_retry(deriv, config.SYMBOL, config.TIMEFRAMES["M30"], count=150)
        candles_m15 = fetch_with_retry(deriv, config.SYMBOL, config.TIMEFRAMES["M15"], count=150)
        candles_m5 = fetch_with_retry(deriv, config.SYMBOL, config.TIMEFRAMES["M5"], count=150)

        # Preprocessing dengan try-except per timeframe
        def safe_calc(candles, name):
            df = pd.DataFrame(candles)
            df = calculate_indicators(df)
            df = ensure_atr(df, period=ATR_PERIOD)
            if df is None or df.empty or len(df) < MIN_CANDLES_REQUIRED:
                raise ValueError(f"Data {name} tidak usable setelah indikator. Len={len(df) if df is not None else 0}")
            if 'atr' not in df.columns:
                raise ValueError(f"Data {name} tetap tidak punya kolom ATR setelah fallback")
            logging.info(f"{name} OK - Len: {len(df)} - Last ATR: {df['atr'].dropna().iloc[-1]:.2f}")
            return df

        df_m30 = safe_calc(candles_m30, "M30")
        df_m15 = safe_calc(candles_m15, "M15")
        df_m5 = safe_calc(candles_m5, "M5")

        # Evaluasi Model
        score_buy = QuantitativeEnsembleModel.evaluate_setup(df_m30, df_m15, df_m5, "BUY")
        score_sell = QuantitativeEnsembleModel.evaluate_setup(df_m30, df_m15, df_m5, "SELL")
        
        score_buy = 0.0 if score_buy is None else float(score_buy)
        score_sell = 0.0 if score_sell is None else float(score_sell)

        logging.info(f"Ensemble Score - BUY: {score_buy:.2f} | SELL: {score_sell:.2f}")

        # Anti-spam jangan bikin crash
        try:
            if notifier.check_recent_signal(minutes_threshold=15):
                logging.info("Anti-spam aktif, suppressing.")
                return
        except Exception as e:
            logging.warning(f"Gagal cek anti-spam (diabaikan): {e}")

        current_price, current_atr = get_last_closed_candle(df_m5)
        
        if current_atr <= 0 or pd.isna(current_atr):
            raise ValueError(f"ATR tidak valid: {current_atr}")

        logging.info(f"Price: {current_price} | ATR: {current_atr}")

        # Eksekusi
        signal_sent = False
        for direction, score in [("BUY", score_buy), ("SELL", score_sell)]:
            if signal_sent: break
            if score >= 0.75:
                risk_data = DynamicRiskManager.calculate_levels(current_price, current_atr, direction)
                if risk_data["rrr_actual"] >= config.MIN_RISK_REWARD:
                    notifier.send_signal(
                        direction=direction, entry=current_price, sl=risk_data["sl"],
                        tp=risk_data["tp"], lot=risk_data["suggested_lot"],
                        rrr=risk_data["rrr_actual"], timeframe="M5/M15/M30"
                    )
                    signal_sent = True
                else:
                    logging.info(f"{direction} skor lolos {score:.2f} tapi RRR {risk_data['rrr_actual']:.2f} < {config.MIN_RISK_REWARD}")

        if not signal_sent:
            logging.info("Tidak ada setup valid >= 0.75 dan RRR minimum.")

    except Exception as e:
        logging.error(f"Critical Error: {e}", exc_info=True)
        try:
            TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID).send_error(str(e))
        except:
            pass
        raise

if __name__ == "__main__":
    main()

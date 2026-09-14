import logging
import pandas as pd
import time
import sys

import config
from indicators import calculate_indicators
from math_core import QuantitativeEnsembleModel, DynamicRiskManager
from deriv_client import DerivPublicClient
from telegram_notifier import TelegramNotifier

# ------------------------------------------------------------------
# Logging - anti duplicate handler di GitHub Actions
# ------------------------------------------------------------------
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

# Deriv public API cuma kasih max 50 candle, jadi kita sesuaikan
MIN_CANDLES_REQUIRED = 45
CANDLE_BUFFER = 10
ATR_PERIOD = 14

def validate_config():
    """Validasi isi config, bukan cuma hasattr"""
    required = ["DERIV_APP_ID", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "SYMBOL", "TIMEFRAMES", "MIN_RISK_REWARD"]
    missing = [attr for attr in required if not hasattr(config, attr) or not getattr(config, attr)]
    if missing:
        raise AttributeError(f"Konfigurasi kosong/hilang: {missing}")

def ensure_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Fallback kalau calculate_indicators gagal bikin ATR - ini penyelamat dari KeyError"""
    if df is None or df.empty:
        return df
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
        df['atr'] = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    except Exception as e:
        logging.error(f"Gagal hitung ATR manual: {e}")
    return df

def get_last_closed_candle(df: pd.DataFrame):
    """Ambil candle closed terakhir yang valid (anti NaN & anti repaint)"""
    if df is None or df.empty:
        raise ValueError("Dataframe kosong")
    
    df_valid = df.dropna(subset=['close', 'atr'])
    if df_valid.empty:
        raise ValueError("Semua atr/close NaN, warmup indikator belum selesai")
    if len(df_valid) < 2:
        row = df_valid.iloc[-1]
        return row['close'], row['atr']
    
    # ambil -2 untuk hindari candle yang masih forming, kalau -2 NaN pakai last valid
    try:
        price = df['close'].iloc[-2]
        atr = df['atr'].iloc[-2]
        if pd.isna(price) or pd.isna(atr):
            raise ValueError("NaN")
        return price, atr
    except:
        row = df_valid.iloc

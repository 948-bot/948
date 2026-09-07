import os
from datetime import datetime, timezone, timedelta

# --- KONFIGURASI SISTEM (PUBLIC API MODE) ---
DERIV_APP_ID = os.getenv("DERIV_APP_ID", "1089")
# DERIV_TOKEN DIHAPUS TOTAL. Sistem berjalan murni di Public Endpoint.

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")

SYMBOL = "frxXAUUSD"
TIMEFRAMES = {"M5": 300, "M15": 900, "M30": 1800}

# --- PARAMETER RISIKO & VOLATILITAS ---
ATR_PERIOD = 14
RRR_RATIO = 2.5
MIN_RISK_REWARD = 2.0
# Buffer spread Deriv XAUUSD. SL TIDAK BOLEH < 2.5 USD (25 poin) untuk menghindari spread-kill.
MIN_SL_DISTANCE_USD = 2.5 
MAX_RISK_PER_TRADE_PCT = 0.02 # 2% risiko per trade

# --- JADWAL OPERASIONAL (WIB = UTC+7) ---
WIB_OFFSET = timedelta(hours=7)

def is_market_hours() -> bool:
    now_utc = datetime.now(timezone.utc)
    now_wib = now_utc + WIB_OFFSET
    weekday = now_wib.weekday() # 0=Senin, 5=Sabtu, 6=Minggu
    
    if weekday == 6: return False # Minggu
    if weekday == 5 and now_wib.hour >= 5: return False # Sabtu >= 05:00
    if weekday == 0 and now_wib.hour < 5: return False # Senin < 05:00
    return True

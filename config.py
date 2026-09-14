import os
from datetime import datetime, timezone, timedelta

DERIV_APP_ID = os.getenv("DERIV_APP_ID", "1089")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")

SYMBOL = "frxXAUUSD"
TIMEFRAMES = {"M5": 300, "M15": 900, "M30": 1800}

# --- PARAMETER RISIKO ---
ATR_PERIOD = 14
RRR_RATIO = 2.5 # Sekarang DIPAKAI di math_core
MIN_RISK_REWARD = 2.0
MIN_SL_DISTANCE_USD = 2.5 # Ini anti spread-kill Deriv XAUUSD, sekarang DIPAKAI
MAX_RISK_PER_TRADE_PCT = 0.02

WIB_OFFSET = timedelta(hours=7)

def is_market_hours() -> bool:
    now_utc = datetime.now(timezone.utc)
    now_wib = now_utc + WIB_OFFSET
    weekday = now_wib.weekday() # 0=Senin, 6=Minggu

    if weekday == 6: # Minggu tutup total
        return False
    if weekday == 5 and now_wib.hour >= 5: # Sabtu jam 5 pagi WIB tutup
        return False
    if weekday == 0 and now_wib.hour < 5: # Senin sebelum jam 5 pagi belum buka
        return False
    return True

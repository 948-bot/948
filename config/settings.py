"""
XAUUSD AI DERIV BOT
Configuration
Version: V0
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ============================================================
# DERIV
# ============================================================
DERIV_APP_ID = os.getenv("DERIV_APP_ID", "")
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN", "")
DERIV_SYMBOL = os.getenv("DERIV_SYMBOL", "XAUUSD")

# ============================================================
# TIMEFRAME
# ============================================================
M15_SECONDS = 15 * 60
M30_SECONDS = 30 * 60

# ============================================================
# OPERATING SCHEDULE
# ============================================================
TRADING_DAYS = {
    0: True,   # Monday
    1: True,   # Tuesday
    2: True,   # Wednesday
    3: True,   # Thursday
    4: True,   # Friday
    5: False,  # Saturday
    6: False,  # Sunday
}

# ============================================================
# SIGNAL SETTINGS
# ============================================================
MIN_TP_PIPS = 200

# ============================================================
# RISK SETTINGS
# ============================================================
DEFAULT_RISK_PERCENT = 0.50
MAX_DAILY_LOSS_PERCENT = 2.00
MAX_ACTIVE_SIGNALS = 1

# ============================================================
# AI SETTINGS
# ============================================================
AI_REQUIRE_REALTIME_DATA = True
AI_REQUIRE_STRUCTURED_OUTPUT = True
AI_MIN_CONFIDENCE = 80

# ============================================================
# ANTI-SPAM
# ============================================================
ANTI_SPAM_ENABLED = True
SIGNAL_COOLDOWN_SECONDS = 15 * 60

# ============================================================
# DATA VALIDATION
# ============================================================
REQUIRE_COMPLETE_CANDLE = True
REQUIRE_FRESH_DATA = True
MAX_DATA_AGE_SECONDS = 10

# ============================================================
# LOGGING
# ============================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def is_trading_day() -> bool:
    """
    Mengembalikan True jika hari ini adalah hari trading.
    Senin = 0
    Minggu = 6
    """
    from datetime import datetime
    today = datetime.utcnow().weekday()
    return TRADING_DAYS.get(today, False)

def validate_basic_config() -> tuple[bool, str]:
    """
    Validasi konfigurasi dasar.
    Tidak melakukan koneksi ke Deriv.
    """
    if not DERIV_APP_ID:
        return False, "DERIV_APP_ID belum diisi."

    if not DERIV_API_TOKEN:
        return False, "DERIV_API_TOKEN belum diisi."

    if not DERIV_SYMBOL:
        return False, "DERIV_SYMBOL belum diisi."

    return True, "Configuration OK"

if __name__ == "__main__":
    ok, message = validate_basic_config()

    print("===================================")
    print("XAUUSD AI DERIV BOT")
    print("Configuration Check")
    print("===================================")

    print(f"Symbol       : {DERIV_SYMBOL}")
    print(f"M15          : {M15_SECONDS} seconds")
    print(f"M30          : {M30_SECONDS} seconds")
    print(f"Min TP       : {MIN_TP_PIPS} pips")
    print(f"AI Confidence: {AI_MIN_CONFIDENCE}%")
    print(f"Risk         : {DEFAULT_RISK_PERCENT}%")
    print(f"Config       : {'OK' if ok else 'ERROR'}")
    print(f"Message      : {message}")

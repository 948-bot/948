"""
XAUUSD AI DERIV BOT
Configuration
Version: V0
"""
import os
from dotenv import load_dotenv

load_dotenv()

DERIV_APP_ID = os.getenv("DERIV_APP_ID", "")
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN", "")
# Menggunakan format standar simbol Deriv untuk XAUUSD (Gold)
DERIV_SYMBOL = os.getenv("DERIV_SYMBOL", "frxXAUUSD")

M15_SECONDS = 15 * 60
M30_SECONDS = 30 * 60

TRADING_DAYS = {
    0: True,   # Monday
    1: True,   # Tuesday
    2: True,   # Wednesday
    3: True,   # Thursday
    4: True,   # Friday
    5: False,  # Saturday
    6: False,  # Sunday
}

MIN_TP_PIPS = 200
DEFAULT_RISK_PERCENT = 0.50
MAX_DAILY_LOSS_PERCENT = 2.00
MAX_ACTIVE_SIGNALS = 1

AI_REQUIRE_REALTIME_DATA = True
AI_REQUIRE_STRUCTURED_OUTPUT = True
AI_MIN_CONFIDENCE = 80

ANTI_SPAM_ENABLED = True
SIGNAL_COOLDOWN_SECONDS = 15 * 60

REQUIRE_COMPLETE_CANDLE = True
REQUIRE_FRESH_DATA = True
MAX_DATA_AGE_SECONDS = 10

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def is_trading_day() -> bool:
    from datetime import datetime
    today = datetime.utcnow().weekday()
    return TRADING_DAYS.get(today, False)

def validate_basic_config() -> tuple[bool, str]:
    if not DERIV_APP_ID:
        return False, "DERIV_APP_ID belum diisi."
    if not DERIV_API_TOKEN:
        return False, "DERIV_API_TOKEN belum diisi."
    if not DERIV_SYMBOL:
        return False, "DERIV_SYMBOL belum diisi."
    return True, "Configuration OK"

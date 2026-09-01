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

# Symbol akan kita validasi dari Deriv pada tahap berikutnya.
DERIV_SYMBOL = os.getenv("DERIV_SYMBOL", "XAUUSD")


# ============================================================
# TIMEFRAME
# ============================================================

# Timeframe utama sistem
M15_SECONDS = 15 * 60
M30_SECONDS = 30 * 60


# ============================================================
# OPERATING SCHEDULE
# ============================================================

# Bot aktif Senin-Jumat.
# Weekend otomatis OFF.

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

# Target minimum TP.
# Nilai pip/point final akan mengikuti specification
# instrumen Deriv, bukan asumsi harga.

MIN_TP_PIPS = 200


# ============================================================
# RISK SETTINGS
# ============================================================

# Contoh awal. Belum digunakan untuk membuka posisi.
DEFAULT_RISK_PERCENT = 0.50

# Proteksi harian.
MAX_DAILY_LOSS_PERCENT = 2.00

# Maksimum signal aktif yang boleh dipantau.
MAX_ACTIVE_SIGNALS = 1


# ============================================================
# AI SETTINGS
# ============================================================

# AI tidak boleh membuat signal apabila data tidak lengkap.
AI_REQUIRE_REALTIME_DATA = True

# AI wajib memberikan keputusan terstruktur.
AI_REQUIRE_STRUCTURED_OUTPUT = True

# Confidence threshold awal.
# Angka ini BELUM berarti jaminan akurasi 80%.
# Akan divalidasi melalui backtest dan forward test.
AI_MIN_CONFIDENCE = 80


# ============================================================
# ANTI-SPAM
# ============================================================

# Signal yang identik tidak boleh dikirim berulang kali.
ANTI_SPAM_ENABLED = True

# Cooldown dalam detik.
SIGNAL_COOLDOWN_SECONDS = 15 * 60


# ============================================================
# DATA VALIDATION
# ============================================================

REQUIRE_COMPLETE_CANDLE = True
REQUIRE_FRESH_DATA = True

# Maksimum umur data real-time yang masih dianggap valid.
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

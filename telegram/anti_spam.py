"""
XAUUSD AI DERIV BOT
Anti-Spam & Duplicate Detection Module
"""
import time

_last_signal_timestamp = 0
_last_signal_fingerprint = ""

def check_anti_spam(signal_type: str, entry_price: float) -> bool:
    """
    Memeriksa apakah sinyal teridentifikasi spam atau berulang dalam waktu cooldown.
    """
    global _last_signal_timestamp, _last_signal_fingerprint
    
    from config.settings import ANTI_SPAM_ENABLED, SIGNAL_COOLDOWN_SECONDS
    
    if not ANTI_SPAM_ENABLED:
        return True

    current_time = time.time()
    current_fingerprint = f"{signal_type}_{int(entry_price / 5)}" # Fingerprint per bucket harga 5 pip

    # Cek cooldown waktu
    if (current_time - _last_signal_timestamp) < SIGNAL_COOLDOWN_SECONDS:
        if current_fingerprint == _last_signal_fingerprint:
            return False # Terdeteksi spam / sinyal kembar berulang

    # Update cache
    _last_signal_timestamp = current_time
    _last_signal_fingerprint = current_fingerprint
    return True

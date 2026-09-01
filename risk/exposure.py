"""
XAUUSD AI DERIV BOT
Exposure Control Module
"""
from config.settings import MAX_ACTIVE_SIGNALS

def check_exposure_limit(active_signals_count: int) -> bool:
    """
    Memastikan jumlah sinyal aktif tidak melebihi batas maksimum yang diizinkan.
    """
    return active_signals_count < MAX_ACTIVE_SIGNALS

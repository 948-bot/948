"""
XAUUSD AI DERIV BOT
Kill Switch Module
"""

def check_kill_switch(system_error_count: int) -> bool:
    """
    Mengaktifkan tombol darurat (Kill Switch) jika kesalahan sistem melebihi batas.
    Mengembalikan True jika sistem harus dihentikan demi keamanan.
    """
    MAX_ERRORS_ALLOWED = 3
    if system_error_count >= MAX_ERRORS_ALLOWED:
        return True
    return False

"""
XAUUSD AI DERIV BOT
Risk Validation Engine (Optimized & Flexible Version)
"""
from config.settings import AI_MIN_CONFIDENCE

def validate_risk(signal_data: dict, ai_evaluation: dict) -> tuple[bool, str]:
    """
    Melakukan validasi risiko dengan toleransi yang lebih fleksibel 
    agar bot tidak terlalu sering menolak sinyal (NO SIGNAL/WAIT).
    """
    # 1. Cek apakah aksi valid
    action = ai_evaluation.get("action", "WAIT")
    if action not in ["BUY", "SELL"]:
        return False, "Aksi pasar bukan BUY atau SELL."

    # 2. Cek ambang batas Confidence AI (Memakai toleransi minimal 60% agar lebih responsif)
    confidence = ai_evaluation.get("confidence", 0)
    effective_min_conf = min(AI_MIN_CONFIDENCE, 60)
    if confidence < effective_min_conf:
        return False, f"Confidence AI ({confidence}%) di bawah batas minimum ({effective_min_conf}%)."

    # 3. Cek kelengkapan TP dan SL
    tp = signal_data.get("tp", 0)
    sl = signal_data.get("sl", 0)
    if not tp or not sl:
        return False, "Target TP atau SL tidak terdefinisi dengan benar."

    return True, "Validasi risiko berhasil lolos dengan toleransi fleksibel."

"""
XAUUSD AI DERIV BOT
Risk Validation Engine
"""
from config.settings import AI_MIN_CONFIDENCE

def validate_risk(signal_data: dict, ai_evaluation: dict) -> tuple[bool, str]:
    """
    Melakukan validasi risiko keras (Hard Risk Validation) sebelum sinyal disetujui.
    Jika ada aturan yang dilanggar, sinyal ditolak (NO SIGNAL).
    """
    # 1. Cek apakah aksi valid
    action = ai_evaluation.get("action", "WAIT")
    if action not in ["BUY", "SELL"]:
        return False, "Aksi pasar bukan BUY atau SELL."

    # 2. Cek ambang batas Confidence AI
    confidence = ai_evaluation.get("confidence", 0)
    if confidence < AI_MIN_CONFIDENCE:
        return False, f"Confidence AI ({confidence}%) di bawah batas minimum ({AI_MIN_CONFIDENCE}%)."

    # 3. Cek kelengkapan TP dan SL
    tp = signal_data.get("tp", 0)
    sl = signal_data.get("sl", 0)
    if not tp or not sl:
        return False, "Target TP atau SL tidak terdefinisi dengan benar."

    return True, "Validasi risiko berhasil lolos."

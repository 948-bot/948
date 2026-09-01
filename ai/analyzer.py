"""
XAUUSD AI DERIV BOT
AI Analyzer Module
"""
from config.settings import AI_MIN_CONFIDENCE

def evaluate_with_ai(m30_data: dict, m15_data: dict) -> dict:
    """
    Mengevaluasi kondisi pasar dengan AI / Logika Aturan Terstruktur.
    Jika API AI belum dikonfigurasi, menggunakan fallback rule engine berbasis confidence.
    """
    # Rule engine fallback (Analisis berbasis logika presisi)
    signal = m15_data.get("signal", "NO_SIGNAL")
    m30_bias = m30_data.get("bias", "NEUTRAL")
    rsi = m15_data.get("rsi", 50)

    action = "WAIT"
    confidence = 50
    regime = "RANGING"
    reasoning = "Kondisi pasar belum memenuhi konfirmasi tren M30 dan M15."

    if m30_bias == "BULLISH" and signal == "BUY":
        action = "BUY"
        confidence = 85 if 50 <= rsi <= 65 else 75
        regime = "TRENDING_UP"
        reasoning = "Struktur Bullish M30 dan M15 terkonfirmasi selaras."

    elif m30_bias == "BEARISH" and signal == "SELL":
        action = "SELL"
        confidence = 85 if 35 <= rsi <= 50 else 75
        regime = "TRENDING_DOWN"
        reasoning = "Struktur Bearish M30 dan M15 terkonfirmasi selaras."

    # Filter berdasarkan ambang batas AI Minimum Confidence
    is_valid = confidence >= AI_MIN_CONFIDENCE and action != "WAIT"

    return {
        "action": action,
        "confidence": confidence,
        "market_regime": regime,
        "reasoning": reasoning,
        "is_valid": is_valid
    }

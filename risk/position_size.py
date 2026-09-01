"""
XAUUSD AI DERIV BOT
Position Size Calculator Module
"""
from config.settings import DEFAULT_RISK_PERCENT

def calculate_position_size(account_balance: float, entry_price: float, sl_price: float) -> dict:
    """
    Menghitung rekomendasi ukuran posisi (lot size) berdasarkan risiko akun.
    Berfungsi sebagai informasi manual bagi trader.
    """
    if account_balance <= 0 or entry_price == sl_price:
        return {"recommended_lots": 0.0, "risk_amount": 0.0}

    # Perhitungan risiko berdasarkan presentase modal
    risk_amount = account_balance * (DEFAULT_RISK_PERCENT / 100.0)
    pips_at_risk = abs(entry_price - sl_price) / 0.01

    if pips_at_risk == 0:
        return {"recommended_lots": 0.01, "risk_amount": risk_amount}

    # Estimasi lot size standar untuk XAUUSD ($1 per pip per 0.01 lot)
    value_per_pip_per_lot = 1.0
    calculated_lots = risk_amount / (pips_at_risk * value_per_pip_per_lot)
    
    # Batasi minimum lot 0.01 dan bulatkan
    final_lots = max(0.01, round(calculated_lots, 2))

    return {
        "recommended_lots": final_lots,
        "risk_amount": round(risk_amount, 2),
        "pips_at_risk": round(pips_at_risk, 1)
    }

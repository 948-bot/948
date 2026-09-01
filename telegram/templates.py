"""
XAUUSD AI DERIV BOT
Telegram Message Templates
"""

def format_signal_message(signal_data: dict, ai_evaluation: dict, risk_data: dict) -> str:
    """
    Membuat template pesan Telegram yang rapi dan profesional untuk sinyal BUY/SELL.
    """
    action = ai_evaluation.get("action", "WAIT")
    emoji = "🟢 BUY SIGNAL" if action == "BUY" else "🔴 SELL SIGNAL"
    
    return f"""
{emoji} - XAUUSD DERIV BOT
=========================
🔹 **Aksi**: {action}
🔹 **Harga Masuk**: {signal_data.get('entry', 0)}
🔹 **Take Profit (TP)**: {signal_data.get('tp', 0)} ({signal_data.get('pips', 0)} pips)
🔹 **Stop Loss (SL)**: {signal_data.get('sl', 0)}

📊 **Analisis AI & Pasar**:
- Confidence: {ai_evaluation.get('confidence', 0)}%
- Regime: {ai_evaluation.get('market_regime', 'N/A')}
- Alasan: {ai_evaluation.get('reasoning', 'N/A')}

🛡️ **Manajemen Risiko**:
- Rekomendasi Lot: {risk_data.get('recommended_lots', 0.01)} lot
- Risiko per Akun: ${risk_data.get('risk_amount', 0.0)}

⚠️ *Catatan: Gunakan manajemen risiko mandiri. Eksekusi manual.*
"""

def format_error_message(error_text: str) -> str:
    """
    Template pesan error untuk Telegram.
    """
    return f"""
⚠️ **XAUUSD BOT ERROR ALERT**
=========================
Terjadi kesalahan pada sistem bot:
`{error_text}`
"""

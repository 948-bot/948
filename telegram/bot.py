"""
XAUUSD AI DERIV BOT
Telegram Templates Module (Clean & Safe Plain Text)
"""

def format_signal_message(signal_data: dict, ai_evaluation: dict, risk_data: dict) -> str:
    """
    Memformat pesan sinyal trading untuk dikirim via Telegram tanpa format markdown sensitif.
    """
    action = ai_evaluation.get("action", "WAIT")
    confidence = ai_evaluation.get("confidence", 0)
    market_regime = ai_evaluation.get("market_regime", "UNKNOWN")
    reasoning = ai_evaluation.get("reasoning", "Tidak ada alasan khusus")
    
    entry = signal_data.get("entry", 0.0)
    tp = signal_data.get("tp", 0.0)
    sl = signal_data.get("sl", 0.0)
    pips = signal_data.get("pips", 0.0)
    
    lot_size = risk_data.get("lot_size", 0.01)
    risk_amount = risk_data.get("risk_amount", 0.0)

    # Emoji penanda aksi
    emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "⚪"

    message = f"""
{emoji} SINYAL TERVALIDASI: {action} {emoji}
==================================
🔹 Aset: XAUUSD (Gold)
🔹 Harga Entry: {entry}
🔹 Target TP: {tp}
🔹 Stop Loss: {sl}
🔹 Jarak TP/SL: {pips} Pips

🤖 ANALISIS AI & PASAR:
• Aksi: {action}
• Keyakinan (Confidence): {confidence}%
• Kondisi Pasar: {market_regime}
• Alasan: {reasoning}

🛡️ MANAJEMEN RISIKO:
• Rekomendasi Lot: {lot_size}
• Estimasi Risiko: ${risk_amount}
==================================
Bot XAUUSD Multi-AI Active
"""
    return message.strip()

def format_error_message(error_text: str) -> str:
    """
    Memformat pesan error untuk dikirim via Telegram.
    """
    message = f"""
❌ PERINGATAN ERROR BOT ❌
==================================
Terjadi kendala pada sistem runner:
{error_text}
==================================
Segera periksa log GitHub Actions!
"""
    return message.strip()

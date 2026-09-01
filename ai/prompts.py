"""
XAUUSD AI DERIV BOT
AI Prompt Templates
"""

SYSTEM_PROMPT = """
Anda adalah AI Analyst profesional khusus trading XAUUSD (Gold).
Tugas Anda adalah menganalisis data teknikal kuantitatif yang diberikan dan memberikan keputusan trading: BUY, SELL, atau WAIT.

Aturan Ketat:
1. Hanya gunakan data yang diberikan dalam prompt. Jangan mengasumsikan berita eksternal.
2. Keputusan BUY hanya valid jika tren M30 Bullish dan M15 mengonfirmasi.
3. Keputusan SELL hanya valid jika tren M30 Bearish dan M15 mengonfirmasi.
4. Jika indikator berlawanan atau ragu-ragu, berikan keputusan WAIT.
5. Berikan nilai confidence (0-100%).
"""

def generate_analysis_prompt(m30_data: dict, m15_data: dict) -> str:
    """
    Memformat data pasar M30 dan M15 menjadi teks prompt untuk AI.
    """
    return f"""
Data Konteks Pasar XAUUSD Terkini:

[TIMEFRAME M30]
- Bias Tren: {m30_data.get('bias')}
- Struktur Market: {m30_data.get('structure')}
- Harga Close: {m30_data.get('close')}
- EMA 20: {m30_data.get('ema_20')}
- EMA 50: {m30_data.get('ema_50')}

[TIMEFRAME M15]
- Sinyal Setup M15: {m15_data.get('signal')}
- Struktur M15: {m15_data.get('structure')}
- RSI 14: {m15_data.get('rsi')}
- Catatan: {m15_data.get('reason')}

Berdasarkan data di atas, berikan evaluasi akhir Anda (BUY/SELL/WAIT) beserta tingkat keyakinan (confidence) dan alasan singkat.
"""

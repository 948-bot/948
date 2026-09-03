"""
XAUUSD AI DERIV BOT
M15 Setup Engine (Flexible & Dynamic Version - Optimized)
"""
import pandas as pd
from strategy.indicators import add_all_indicators
from strategy.structure import detect_market_structure

def evaluate_m15_setup(df_m15: pd.DataFrame, m30_bias: str) -> dict:
    """
    Mengevaluasi setup entry pada timeframe M15 dengan filter yang lebih fleksibel.
    """
    if df_m15.empty or len(df_m15) < 30:
        return {
            "signal": "NO_SIGNAL",
            "reason": "Data M15 tidak cukup"
        }

    # Tambahkan indikator
    df = add_all_indicators(df_m15.copy())
    last_row = df.iloc[-1]
    
    close_price = last_row['close']
    ema_20 = last_row['ema_20']
    rsi = last_row.get('rsi_14', 50)
    structure_m15 = detect_market_structure(df)

    signal = "NO_SIGNAL"
    reason = "Kondisi market belum memenuhi kriteria setup fleksibel"

    # Toleransi fleksibel: Jika M30 Netral, baca struktur M15
    effective_bias = m30_bias
    if m30_bias == "NEUTRAL":
        if structure_m15 in ["BULLISH", "SIDEWAYS_BULLISH"]:
            effective_bias = "BULLISH"
        elif structure_m15 in ["BEARISH", "SIDEWAYS_BEARISH"]:
            effective_bias = "BEARISH"

    # Logika Setup BUY (Diperluas toleransinya agar tidak terlalu sering NO_SIGNAL)
    if effective_bias == "BULLISH":
        # RSI dilegaan saeutik (35 - 80) jeung toleransi jarak EMA dilegakeun
        if rsi >= 35 and rsi <= 80 and close_price >= (ema_20 * 0.995):
            signal = "BUY"
            reason = f"Setup BUY terdeteksi: Tren Bullish, RSI ({rsi:.1f}), harga mendukung."

    # Logika Setup SELL (Diperluas toleransinya)
    elif effective_bias == "BEARISH":
        # RSI dilegaan saeutik (20 - 65)
        if rsi >= 20 and rsi <= 65 and close_price <= (ema_20 * 1.005):
            signal = "SELL"
            reason = f"Setup SELL terdeteksi: Tren Bearish, RSI ({rsi:.1f}), harga mendukung."

    return {
        "signal": signal,
        "reason": reason,
        "close": close_price,
        "rsi": rsi,
        "structure": structure_m15
    }

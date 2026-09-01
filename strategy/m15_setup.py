"""
XAUUSD AI DERIV BOT
M15 Setup Engine (Flexible & Dynamic Version)
"""
import pandas as pd
from strategy.indicators import add_all_indicators
from strategy.structure import detect_market_structure

def evaluate_m15_setup(df_m15: pd.DataFrame, m30_bias: str) -> dict:
    """
    Mengevaluasi setup entry pada timeframe M15 dengan filter yang lebih dinamis.
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

    # Toleransi fleksibel: Jika M30 Netral, kita andalkan struktur dan momentum M15 sepenuhnya
    effective_bias = m30_bias
    if m30_bias == "NEUTRAL":
        if structure_m15 == "BULLISH":
            effective_bias = "BULLISH"
        elif structure_m15 == "BEARISH":
            effective_bias = "BEARISH"

    # Logika Setup BUY (Lebih fleksibel)
    if effective_bias == "BULLISH":
        # RSI toleransi lebih luas (40 - 75) dan harga di atas EMA20 atau mendekati EMA20
        if rsi >= 40 and rsi <= 75 and close_price >= (ema_20 * 0.998):
            signal = "BUY"
            reason = f"Setup BUY terdeteksi: Struktur Bullish, RSI sehat ({rsi:.1f}), harga mendukung."

    # Logika Setup SELL (Lebih fleksibel)
    elif effective_bias == "BEARISH":
        # RSI toleransi lebih luas (25 - 60) dan harga di bawah EMA20 atau mendekati EMA20
        if rsi >= 25 and rsi <= 60 and close_price <= (ema_20 * 1.002):
            signal = "SELL"
            reason = f"Setup SELL terdeteksi: Struktur Bearish, RSI mendukung ({rsi:.1f}), harga di bawah/dekat EMA20."

    return {
        "signal": signal,
        "reason": reason,
        "close": close_price,
        "rsi": rsi,
        "structure": structure_m15
    }

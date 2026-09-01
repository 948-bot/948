"""
XAUUSD AI DERIV BOT
M15 Setup Engine
"""
import pandas as pd
from strategy.indicators import add_all_indicators
from strategy.structure import detect_market_structure

def evaluate_m15_setup(df_m15: pd.DataFrame, m30_bias: str) -> dict:
    """
    Mengevaluasi setup entry pada timeframe M15 berdasarkan konfirmasi tren M30.
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
    reason = "Kondisi market belum memenuhi kriteria setup"

    # Logika Setup BUY (Harus selaras dengan bias M30 Bullish)
    if m30_bias == "BULLISH" and structure_m15 == "BULLISH":
        if close_price > ema_20 and 45 <= rsi <= 70:
            signal = "BUY"
            reason = "M15 sejalan dengan bias Bullish M30, harga di atas EMA20 dan RSI sehat."

    # Logika Setup SELL (Harus selaras dengan bias M30 Bearish)
    elif m30_bias == "BEARISH" and structure_m15 == "BEARISH":
        if close_price < ema_20 and 30 <= rsi <= 55:
            signal = "SELL"
            reason = "M15 sejalan dengan bias Bearish M30, harga di bawah EMA20 dan RSI mendukung."

    return {
        "signal": signal,
        "reason": reason,
        "close": close_price,
        "rsi": rsi,
        "structure": structure_m15
    }

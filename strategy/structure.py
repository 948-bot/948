"""
XAUUSD AI DERIV BOT
Market Structure Detection Module
"""
import pandas as pd

def detect_market_structure(df: pd.DataFrame) -> str:
    """
    Mendeteksi struktur pasar berdasarkan pergerakan High dan Low terakhir.
    Mengembalikan: 'BULLISH', 'BEARISH', atau 'SIDEWAYS'
    """
    if df.empty or len(df) < 5:
        return "SIDEWAYS"

    # Ambil 3 candle terakhir
    recent = df.tail(3).reset_index(drop=True)
    
    highs = recent['high']
    lows = recent['low']

    # Logika sederhana Higher High & Higher Low
    if highs.iloc[-1] > highs.iloc[-2] and lows.iloc[-1] > lows.iloc[-2]:
        return "BULLISH"
    elif highs.iloc[-1] < highs.iloc[-2] and lows.iloc[-1] < lows.iloc[-2]:
        return "BEARISH"
    else:
        return "SIDEWAYS"

"""
XAUUSD AI DERIV BOT
M30 Market Context Engine
"""
import pandas as pd
from strategy.indicators import add_all_indicators
from strategy.structure import detect_market_structure

def analyze_m30_context(df_m30: pd.DataFrame) -> dict:
    """
    Menganalisis konteks tren makro pada timeframe M30.
    Menghasilkan bias tren dan status indikator utama.
    """
    if df_m30.empty or len(df_m30) < 30:
        return {
            "bias": "NEUTRAL",
            "structure": "SIDEWAYS",
            "reason": "Data M30 tidak cukup"
        }

    # Tambahkan indikator
    df = add_all_indicators(df_m30.copy())
    
    last_row = df.iloc[-1]
    close_price = last_row['close']
    ema_20 = last_row['ema_20']
    ema_50 = last_row['ema_50']
    
    structure = detect_market_structure(df)

    # Penentuan Bias Tren M30
    bias = "NEUTRAL"
    if close_price > ema_20 > ema_50 and structure == "BULLISH":
        bias = "BULLISH"
    elif close_price < ema_20 < ema_50 and structure == "BEARISH":
        bias = "BEARISH"

    return {
        "bias": bias,
        "structure": structure,
        "close": close_price,
        "ema_20": ema_20,
        "ema_50": ema_50,
        "rsi": last_row.get('rsi_14', 50)
    }

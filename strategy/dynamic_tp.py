"""
XAUUSD AI DERIV BOT
Dynamic Take Profit Calculation Module
"""
import pandas as pd
from config.settings import MIN_TP_PIPS

def calculate_dynamic_tp(signal_type: str, entry_price: float, df_m15: pd.DataFrame) -> dict:
    """
    Menghitung Target Take Profit (TP) dan Stop Loss (SL) secara dinamis
    berdasarkan ATR dan minimum TP pips instrumen XAUUSD.
    """
    if df_m15.empty or 'atr_14' not in df_m15.columns:
        # Fallback manual jika ATR belum tersedia
        fallback_pips = max(MIN_TP_PIPS, 200)
        pip_value = 0.01  # Nilai estimasi point untuk XAUUSD
        
        if signal_type == "BUY":
            tp = entry_price + (fallback_pips * pip_value)
            sl = entry_price - (fallback_pips * 0.5 * pip_value)
        elif signal_type == "SELL":
            tp = entry_price - (fallback_pips * pip_value)
            sl = entry_price + (fallback_pips * 0.5 * pip_value)
        else:
            tp, sl = 0.0, 0.0
            
        return {"tp": round(tp, 2), "sl": round(sl, 2), "pips": fallback_pips}

    last_atr = df_m15.iloc[-1]['atr_14']
    
    # Konversi ATR ke point/pip target (menggunakan kelipatan ATR yang sehat)
    calculated_pips = max(MIN_TP_PIPS, int(last_atr * 100 * 1.5))
    pip_value = 0.01

    if signal_type == "BUY":
        tp = entry_price + (calculated_pips * pip_value)
        sl = entry_price - (calculated_pips * 0.5 * pip_value)
    elif signal_type == "SELL":
        tp = entry_price - (calculated_pips * pip_value)
        sl = entry_price + (calculated_pips * 0.5 * pip_value)
    else:
        tp, sl = 0.0, 0.0

    return {
        "tp": round(tp, 2),
        "sl": round(sl, 2),
        "pips": calculated_pips
    }

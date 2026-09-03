"""
XAUUSD AI DERIV BOT
Dynamic Take Profit Calculation Module (Optimized for min 500 Pips)
"""
import pandas as pd
from config.settings import MIN_TP_PIPS

def calculate_dynamic_tp(signal_type: str, entry_price: float, df_m15: pd.DataFrame) -> dict:
    """
    Menghitung Target Take Profit (TP) dan Stop Loss (SL) secara dinamis
    dengan paksaan minimum target 500 pips untuk XAUUSD.
    """
    # Paksa minimum TP pips minimal 500 (atau ikuti setelan jika lebih besar)
    target_min_pips = max(MIN_TP_PIPS, 500)
    pip_value = 0.01  # Nilai estimasi point untuk XAUUSD

    if df_m15.empty or 'atr_14' not in df_m15.columns:
        # Fallback manual jika ATR belum tersedia
        fallback_pips = target_min_pips
        
        if signal_type == "BUY":
            tp = entry_price + (fallback_pips * pip_value)
            sl = entry_price - (fallback_pips * 0.5 * pip_value)  # SL setengah dari TP (RR 1:2)
        elif signal_type == "SELL":
            tp = entry_price - (fallback_pips * pip_value)
            sl = entry_price + (fallback_pips * 0.5 * pip_value)
        else:
            tp, sl = 0.0, 0.0
            
        return {"tp": round(tp, 2), "sl": round(sl, 2), "pips": fallback_pips}

    last_atr = df_m15.iloc[-1]['atr_14']
    
    # Hitung pips berdasarkan ATR, tapi di-lock minimal 500 pips
    atr_calculated = int(last_atr * 100 * 1.5)
    calculated_pips = max(target_min_pips, atr_calculated)

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

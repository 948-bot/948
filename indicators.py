import pandas as pd
import numpy as np

def calculate_indicators(df: pd.DataFrame, atr_period: int = 14) -> pd.DataFrame:
    """
    Masterpiece v5.1 - Fixed Anti KeyError
    Selalu menghasilkan kolom 'atr' lowercase
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    # normalisasi kolom
    df.columns = [c.lower() for c in df.columns]

    for col in ['open', 'high', 'low', 'close']:
        if col not in df.columns:
            # coba mapping dari Deriv yang kadang pakai capital
            alt = col.capitalize()
            if alt in df.columns:
                df[col] = df[alt]
            else:
                raise ValueError(f"Kolom {col} tidak ada")
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # kalau data tipis tetap lanjut, jangan return kosong
    if len(df) < 10:
        return pd.DataFrame()

    # 1. SMA
    df['sma_fast'] = df['close'].rolling(window=9, min_periods=9).mean()
    df['sma_slow'] = df['close'].rolling(window=21, min_periods=21).mean()

    # 2. Kalman approx (EMA 14) + EMA 50
    df['kalman'] = df['close'].ewm(span=14, adjust=False, min_periods=14).mean()
    df['ema_50'] = df['close'].ewm(span=50, adjust=False, min_periods=50).mean()

    # 3. RSI Wilder
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi'] = df['rsi'].clip(0, 100)

    # 4. MACD
    exp1 = df['close'].ewm(span=12, adjust=False, min_periods=12).mean()
    exp2 = df['close'].ewm(span=26, adjust=False, min_periods=26).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False, min_periods=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    # 5. ATR - WAJIB ADA
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = true_range.ewm(alpha=1/atr_period, min_periods=atr_period, adjust=False).mean()
    # fallback biar awal tidak NaN semua
    df['atr'] = df['atr'].fillna(true_range.rolling(window=atr_period, min_periods=1).mean())

    # Trend helper
    df['trend_up'] = (df['sma_fast'] > df['sma_slow']) & (df['close'] > df['kalman'])
    df['trend_down'] = (df['sma_fast'] < df['sma_slow']) & (df['close'] < df['kalman'])

    # Drop hanya yang penting NaN, jangan semua kolom
    df.dropna(subset=['atr', 'sma_slow', 'rsi'], inplace=True)

    if 'atr' not in df.columns:
        df['atr'] = np.nan

    return df

# Alias biar import lama tetap jalan kalau ada file lain yang pakai nama berbeda
def get_indicators(df):
    return calculate_indicators(df)

def add_indicators(df):
    return calculate_indicators(df)

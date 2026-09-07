import pandas as pd
import numpy as np

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menghitung indikator teknik (Kalman Filter approximation, SMA, RSI, MACD, ATR)
    untuk keperluan analisis Masterpiece v5.
    """
    if df.empty or len(df) < 30:
        return df

    # Pastikan kolom harga bertipe float
    for col in ['open', 'high', 'low', 'close']:
        if col in df.columns:
            df[col] = df[col].astype(float)

    # 1. Moving Average (SMA)
    df['sma_fast'] = df['close'].rolling(window=9).mean()
    df['sma_slow'] = df['close'].rolling(window=21).mean()

    # 2. Approximate Kalman Filter (menggunakan EMA adaptif sebagai estimasi tren halus)
    df['kalman'] = df['close'].ewm(span=14, adjust=False).mean()

    # 3. RSI (Relative Strength Index - 14 Periode)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))

    # 4. MACD (Moving Average Convergence Divergence)
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()

    # 5. ATR (Average True Range - 14 Periode untuk SL/TP & Volatility)
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = true_range.rolling(window=14).mean()

    # Bersihkan NaN awal
    df.dropna(inplace=True)
    return df

import pandas as pd, numpy as np
def calculate_indicators(df: pd.DataFrame, atr_period: int = 14) -> pd.DataFrame:
    if df is None or df.empty: return pd.DataFrame()
    df=df.copy(); df.columns=[c.lower() for c in df.columns]
    for col in ['open','high','low','close']:
        if col not in df.columns: raise ValueError(f"{col} missing")
        df[col]=pd.to_numeric(df[col], errors='coerce')
    if len(df)<10: return pd.DataFrame()
    df['sma_fast']=df['close'].rolling(9, min_periods=9).mean()
    df['sma_slow']=df['close'].rolling(21, min_periods=21).mean()
    df['kalman']=df['close'].ewm(span=14, adjust=False, min_periods=14).mean()
    df['ema_50']=df['close'].ewm(span=50, adjust=False, min_periods=50).mean()
    delta=df['close'].diff(); gain=delta.clip(lower=0); loss=-delta.clip(upper=0)
    avg_gain=gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss=loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs=avg_gain/(avg_loss+1e-10); df['rsi']=100-(100/(1+rs)); df['rsi']=df['rsi'].clip(0,100)
    exp1=df['close'].ewm(span=12, min_periods=12, adjust=False).mean()
    exp2=df['close'].ewm(span=26, min_periods=26, adjust=False).mean()
    df['macd']=exp1-exp2; df['macd_signal']=df['macd'].ewm(span=9, min_periods=9, adjust=False).mean()
    df['macd_hist']=df['macd']-df['macd_signal']
    hl=df['high']-df['low']; hc=(df['high']-df['close'].shift()).abs(); lc=(df['low']-df['close'].shift()).abs()
    tr=pd.concat([hl,hc,lc],axis=1).max(axis=1)
    df['atr']=tr.ewm(alpha=1/atr_period, min_periods=atr_period, adjust=False).mean()
    df['atr']=df['atr'].fillna(tr.rolling(atr_period, min_periods=1).mean())
    df.dropna(subset=['atr','sma_slow','rsi'], inplace=True)
    return df
def get_indicators(df): return calculate_indicators(df)
def add_indicators(df): return calculate_indicators(df)

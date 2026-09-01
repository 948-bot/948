import pandas as pd,numpy as np
def df(candles):
    x=pd.DataFrame([c.__dict__ for c in candles]); return x.sort_values("epoch").drop_duplicates("epoch").reset_index(drop=True) if not x.empty else x
def indicators(x):
    x=x.copy(); x["ema20"]=x.close.ewm(span=20,adjust=False).mean(); x["ema50"]=x.close.ewm(span=50,adjust=False).mean(); d=x.close.diff(); g=d.clip(lower=0).rolling(14).mean(); l=(-d.clip(upper=0)).rolling(14).mean(); rs=g/l.replace(0,np.nan); x["rsi"]=100-100/(1+rs); pc=x.close.shift(1); tr=pd.concat([x.high-x.low,(x.high-pc).abs(),(x.low-pc).abs()],axis=1).max(axis=1); x["atr"]=tr.rolling(14).mean(); return x

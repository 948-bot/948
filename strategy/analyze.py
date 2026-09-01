from strategy.indicators import df,indicators
def m30(c):
    x=df(c)
    if len(x)<60:return {"valid":False}
    x=indicators(x); r=x.iloc[-1]; bias="BULLISH" if r.close>r.ema20>r.ema50 else "BEARISH" if r.close<r.ema20<r.ema50 else "NEUTRAL"
    return {"valid":True,"bias":bias,"close":float(r.close),"ema20":float(r.ema20),"ema50":float(r.ema50),"rsi":float(r.rsi) if r.rsi==r.rsi else None,"atr":float(r.atr) if r.atr==r.atr else 0}
def m15(c,m30):
    x=df(c)
    if len(x)<80:return {"valid":False}
    x=indicators(x); r=x.iloc[-1]; body=abs(r.close-r.open); rng=max(r.high-r.low,1e-9); momentum=body/rng; bias=m30.get("bias"); own="BULLISH" if r.close>r.ema20>r.ema50 else "BEARISH" if r.close<r.ema20<r.ema50 else "NEUTRAL"; ok=bias in ("BULLISH","BEARISH") and own==bias and momentum>=0.45
    prior=x.iloc[-7:-1]; sweep_up=r.high>prior.high.max() and r.close<r.high; sweep_down=r.low<prior.low.min() and r.close>r.low
    return {"valid":True,"setup_valid":bool(ok),"direction":"BUY" if ok and bias=="BULLISH" else "SELL" if ok and bias=="BEARISH" else "NONE","close":float(r.close),"atr":float(r.atr) if r.atr==r.atr else 0,"rsi":float(r.rsi) if r.rsi==r.rsi else None,"momentum":float(momentum),"sweep_up":bool(sweep_up),"sweep_down":bool(sweep_down),"swing_high":float(x.high.tail(20).max()),"swing_low":float(x.low.tail(20).min())}

def levels(m15,m30,pip_size,min_pips):
    e=float(m15["close"]); atr=max(float(m15.get("atr") or 0),0); d=min_pips*pip_size; direction=m15.get("direction")
    if direction=="BUY": sl=e-max(1.5*atr,.75*d); tp1=max(e+d,e+2*atr); tp2=max(e+1.75*d,e+3*atr); tp3=max(e+2.75*d,e+5*atr)
    elif direction=="SELL": sl=e+max(1.5*atr,.75*d); tp1=min(e-d,e-2*atr); tp2=min(e-1.75*d,e-3*atr); tp3=min(e-2.75*d,e-5*atr)
    else:return {"valid":False,"reason":"no_direction"}
    tp1p=abs(tp1-e)/pip_size; risk=abs(e-sl); rr=abs(tp1-e)/risk if risk else 0
    return {"valid":tp1p>=min_pips,"reason":"ok" if tp1p>=min_pips else "tp_below_min","entry":e,"sl":sl,"tp1":tp1,"tp2":tp2,"tp3":tp3,"tp1_pips":tp1p,"tp2_pips":abs(tp2-e)/pip_size,"tp3_pips":abs(tp3-e)/pip_size,"rr":rr}

import logging
from deriv.websocket import DerivPublicWS
log=logging.getLogger("deriv.market")
class DerivMarketData:
    def __init__(self,hint,on_tick,on_error,on_history=None):
        self.hint=hint.upper(); self.on_tick=on_tick; self.on_error=on_error; self.on_history=on_history; self.ws=DerivPublicWS(self._handle,on_error); self.symbol=None; self.name=None; self.pip_size=None
    def start(self): self.ws.start()
    def stop(self): self.ws.stop_ws()
    def _handle(self,d):
        typ=d.get("msg_type")
        if typ=="active_symbols": self._select(d.get("active_symbols",[]))
        elif typ=="tick":
            t=d.get("tick",{}); self.symbol and t.get("symbol")==self.symbol and self.on_tick(t)
        elif typ=="history":
            if self.on_history:self.on_history(d)
        elif typ=="error":
            e=d.get("error",{}).get("message","Unknown Deriv API error"); self.on_error(e)
    def _select(self,items):
        cand=[]
        for s in items:
            sym=str(s.get("underlying_symbol",s.get("symbol",""))).upper(); name=str(s.get("underlying_symbol_name",s.get("display_name",""))).upper()
            if self.hint in sym or self.hint in name or ("XAU" in sym and "USD" in sym) or "GOLD" in name:cand.append(s)
        if not cand:raise RuntimeError("No XAUUSD/Gold instrument found in Deriv active_symbols")
        s=sorted(cand,key=lambda x:0 if self.hint in str(x.get("underlying_symbol","")).upper() else 1)[0]
        self.symbol=s.get("underlying_symbol",s.get("symbol")); self.name=s.get("underlying_symbol_name",s.get("display_name",self.symbol)); self.pip_size=float(s.get("pip_size") or 0.01)
        log.info("Selected %s (%s), pip_size=%s",self.symbol,self.name,self.pip_size)
        self.ws.send({"ticks":self.symbol,"subscribe":1,"req_id":2})
        # Seed both timeframes from Deriv historical candles.
        self.ws.send({"ticks_history":self.symbol,"end":"latest","count":300,"style":"candles","granularity":900,"subscribe":0,"req_id":101})
        self.ws.send({"ticks_history":self.symbol,"end":"latest","count":300,"style":"candles","granularity":1800,"subscribe":0,"req_id":102})

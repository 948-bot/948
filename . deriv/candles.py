from dataclasses import dataclass
@dataclass
class Candle:
    epoch:int; open:float; high:float; low:float; close:float; volume:int=0
class Aggregator:
    def __init__(self,seconds): self.seconds=seconds; self.current=None
    def update(self,epoch,price):
        epoch=int(epoch); price=float(price); bucket=epoch-epoch%self.seconds
        if self.current is None: self.current=Candle(bucket,price,price,price,price); return None
        if bucket>self.current.epoch:
            closed=self.current; self.current=Candle(bucket,price,price,price,price); return closed
        if bucket==self.current.epoch:
            self.current.high=max(self.current.high,price); self.current.low=min(self.current.low,price); self.current.close=price; self.current.volume+=1
        return None
class Store:
    def __init__(self,maxlen=500): from collections import deque; self.items=deque(maxlen=maxlen)
    def append(self,c):
        if not c:return
        if self.items and c.epoch<=self.items[-1].epoch:return
        self.items.append(c)
    def list(self): return list(self.items)

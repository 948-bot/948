import websocket, json, time, logging
class DerivPublicClient:
    def __init__(self, app_id="1089"):
        self.app_id=str(app_id); self.url=f"wss://ws.derivws.com/websockets/v3?app_id={self.app_id}"
    def fetch_candles(self, symbol, granularity, count=50):
        count=min(int(count),50); granularity=int(granularity)
        for attempt in range(3):
            ws=None
            try:
                ws=websocket.create_connection(self.url, timeout=15)
                ws.send(json.dumps({"ticks_history":symbol,"style":"candles","granularity":granularity,"count":count,"end":"latest"}))
                for _ in range(10):
                    try: res=json.loads(ws.recv())
                    except: continue
                    if res.get("msg_type")=="candles":
                        c=res.get("candles",[])
                        if c: return c
                    if "error" in res:
                        logging.warning(f"Deriv err: {res['error']}")
                        break
            except Exception as e: logging.warning(f"WS {attempt+1} fail: {e}")
            finally:
                if ws:
                    try: ws.close()
                    except: pass
            time.sleep(2)
        return []

import websocket
import json
import time

class DerivPublicClient:
    def __init__(self, app_id):
        self.app_id = app_id
        self.url = f"wss://ws.derivws.com/websockets/v3?app_id={app_id}"

    def fetch_candles(self, symbol, granularity, count=50):
        # granularity: 300 = M5, 900 = M15, 1800 = M30
        ws = websocket.create_connection(self.url, timeout=10)
        try:
            req = {
                "ticks_history": symbol,
                "style": "candles",
                "granularity": int(granularity),
                "count": int(count),
                "end": "latest"
            }
            ws.send(json.dumps(req))
            # tunggu respon
            start = time.time()
            while time.time() - start < 10:
                res = json.loads(ws.recv())
                if res.get("msg_type") == "candles":
                    return res.get("candles", [])
                if "error" in res:
                    raise Exception(res["error"].get("message"))
            return []
        finally:
            ws.close()

import json
import logging
websocket = None
try:
    import websocket
except ImportError:
    import websocket_client as websocket

class DerivPublicClient:
    def __init__(self, app_id: str):
        self.app_id = app_id
        self.url = f"wss://ws.derivws.com/websockets/v3?app_id={self.app_id}"

    def fetch_candles(self, symbol: str, timeframe, count: int = 60) -> list:
        """
        Mengambil data candle historis dari WebSocket publik Deriv dengan pemetaan detik aman.
        """
        # Konversi cerdas atau pemetaan langsung standar Deriv (dalam detik)
        # M5 = 300 detik, M15 = 900 detik, M30 = 1800 detik, H1 = 3600 detik
        tf_str = str(timeframe).lower()
        
        if "30" in tf_str:
            granularity = 1800
        elif "15" in tf_str:
            granularity = 900
        elif "5" in tf_str:
            granularity = 300
        elif "1" in tf_str and "h" not in tf_str:
            granularity = 60
        elif "h" in tf_str:
            granularity = 3600
        else:
            try:
                granularity = int(timeframe) * 60
            except:
                granularity = 300 # Default fallback ke M5 jika gagal membaca

        request_payload = {
            "ticks_history": symbol,
            "adjust_start_time": 1,
            "count": count,
            "end": "latest",
            "granularity": granularity,
            "style": "candles"
        }

        for attempt in range(1, 4):
            try:
                ws = websocket.create_connection(self.url, timeout=10)
                ws.send(json.dumps(request_payload))
                response_str = ws.recv()
                ws.close()
                
                data = json.loads(response_str)
                if "candles" in data:
                    candles = []
                    for c in data["candles"]:
                        candles.append({
                            "open": float(c.get("open", 0)),
                            "high": float(c.get("high", 0)),
                            "low": float(c.get("low", 0)),
                            "close": float(c.get("close", 0)),
                            "time": c.get("epoch", 0)
                        })
                    return candles
                elif "error" in data:
                    logging.warning(f"Deriv API Error (Attempt {attempt}): {data['error'].get('message')}")
            except Exception as e:
                logging.warning(f"Network error attempt {attempt}: {str(e)}")

        raise ConnectionError("Gagal mengambil data dari Deriv Public API setelah 3 percobaan.")

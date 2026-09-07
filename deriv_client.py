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
        Mengambil data candle historis dari WebSocket publik Deriv dengan konversi granularity yang aman.
        """
        # Konversi timeframe ke detik secara cerdas (mendukung integer menit atau string seperti '5m', '15m')
        if isinstance(timeframe, str):
            tf_lower = timeframe.lower()
            if 'm' in tf_lower:
                minutes = int(tf_lower.replace('m', ''))
                granularity = minutes * 60
            elif 'h' in tf_lower:
                hours = int(tf_lower.replace('h', ''))
                granularity = hours * 3600
            else:
                granularity = int(timeframe) * 60
        else:
            # Jika berupa angka (dianggap menit)
            granularity = int(timeframe) * 60

        # Validasi standar granularity Deriv (contoh umum: 60, 300, 900, 1800, 3600)
        valid_granularities = [60, 120, 180, 300, 600, 900, 1800, 3600, 7200, 14400, 28800, 86400]
        if granularity not in valid_granularities:
            # Fallback terdekat jika tidak standar, atau paksa ke nilai standar terdekat
            pass

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

import requests
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DerivPublicClient:
    """
    Klien khusus untuk Deriv Public API.
    TIDAK ADA authorize(), TIDAK ADA token. Murni data publik.
    """
    def __init__(self, app_id: int):
        self.app_id = app_id
        self.base_url = f"https://ws.derivws.com/websockets/v3?app_id={app_id}"

    def fetch_candles(self, symbol: str, granularity: int, count: int = 60) -> list:
        """
        Mengambil data candle historis dari endpoint publik.
        Payload dirancang minimal untuk menghindari validasi error.
        """
        payload = {
            "ticks_history": symbol,
            "adjust_start_time": 1,
            "count": count,
            "end": "latest",
            "start": 1,
            "style": "candles",
            "granularity": granularity
        }
        
        # Exponential backoff untuk menangani rate limit publik atau timeout jaringan
        for attempt in range(3):
            try:
                response = requests.post(self.base_url, json=payload, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                # Deriv mengembalikan error di dalam JSON, bukan HTTP status code
                if "error" in data:
                    error_msg = data["error"].get("message", "Unknown Deriv Error")
                    raise Exception(f"Deriv API Error: {error_msg}")
                
                if "candles" not in data:
                    raise Exception("Respons Deriv tidak mengandung data candle.")
                    
                return data["candles"]
                
            except requests.exceptions.RequestException as e:
                logging.warning(f"Network error attempt {attempt+1}: {e}")
                time.sleep(2 ** attempt)
            except Exception as e:
                logging.error(f"Deriv API logic error: {e}")
                raise
                
        raise ConnectionError("Gagal mengambil data dari Deriv Public API setelah 3 percobaan.")

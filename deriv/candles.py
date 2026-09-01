"""
XAUUSD AI DERIV BOT
Candle Builder (M15 & M30)
"""
import time
from config.settings import M15_SECONDS, M30_SECONDS

class CandleBuilder:
    def __init__(self):
        self.current_m15_candle = None
        self.current_m30_candle = None
        self.completed_m15_candles = []
        self.completed_m30_candles = []

    def process_tick(self, price: float, epoch: int):
        """
        Memproses tick masuk dan memperbarui/membentuk candle M15 & M30.
        """
        # --- Timeframe M15 ---
        m15_period = epoch - (epoch % M15_SECONDS)
        if self.current_m15_candle is None or self.current_m15_candle["time"] != m15_period:
            if self.current_m15_candle:
                self.completed_m15_candles.append(self.current_m15_candle)
            # Buat candle M15 baru
            self.current_m15_candle = {
                "time": m15_period,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "complete": False
            }
        else:
            # Update high, low, close candle M15 berjalan
            self.current_m15_candle["high"] = max(self.current_m15_candle["high"], price)
            self.current_m15_candle["low"] = min(self.current_m15_candle["low"], price)
            self.current_m15_candle["close"] = price

        # --- Timeframe M30 ---
        m30_period = epoch - (epoch % M30_SECONDS)
        if self.current_m30_candle is None or self.current_m30_candle["time"] != m30_period:
            if self.current_m30_candle:
                self.completed_m30_candles.append(self.current_m30_candle)
            # Buat candle M30 baru
            self.current_m30_candle = {
                "time": m30_period,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "complete": False
            }
        else:
            # Update high, low, close candle M30 berjalan
            self.current_m30_candle["high"] = max(self.current_m30_candle["high"], price)
            self.current_m30_candle["low"] = min(self.current_m30_candle["low"], price)
            self.current_m30_candle["close"] = price

    def get_latest_status(self):
        return {
            "m15": self.current_m15_candle,
            "m30": self.current_m30_candle
        }

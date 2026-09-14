import pandas as pd
import numpy as np
import config

class QuantitativeEnsembleModel:
    @staticmethod
    def _get_last(df, col):
        """Ambil nilai terakhir yang valid, anti NaN"""
        if col not in df.columns:
            return None
        s = df[col].dropna()
        if s.empty:
            return None
        # pakai -1 karena di indicators.py sudah dropna
        return s.iloc[-1]

    @staticmethod
    def evaluate_setup(df_m30, df_m15, df_m5, direction: str) -> float:
        try:
            # Ambil data valid terakhir
            m5_close = QuantitativeEnsembleModel._get_last(df_m5, 'close')
            m5_kalman = QuantitativeEnsembleModel._get_last(df_m5, 'kalman')
            m5_rsi = QuantitativeEnsembleModel._get_last(df_m5, 'rsi')
            m5_sma_fast = QuantitativeEnsembleModel._get_last(df_m5, 'sma_fast')
            m5_sma_slow = QuantitativeEnsembleModel._get_last(df_m5, 'sma_slow')
            m5_macd = QuantitativeEnsembleModel._get_last(df_m5, 'macd')
            m5_macd_sig = QuantitativeEnsembleModel._get_last(df_m5, 'macd_signal')
            m5_ema50 = QuantitativeEnsembleModel._get_last(df_m5, 'ema_50')

            m15_close = QuantitativeEnsembleModel._get_last(df_m15, 'close')
            m15_kalman = QuantitativeEnsembleModel._get_last(df_m15, 'kalman')
            m15_sma_fast = QuantitativeEnsembleModel._get_last(df_m15, 'sma_fast')
            m15_sma_slow = QuantitativeEnsembleModel._get_last(df_m15, 'sma_slow')

            m30_close = QuantitativeEnsembleModel._get_last(df_m30, 'close')
            m30_kalman = QuantitativeEnsembleModel._get_last(df_m30, 'kalman')
            m30_sma_fast = QuantitativeEnsembleModel._get_last(df_m30, 'sma_fast')
            m30_sma_slow = QuantitativeEnsembleModel._get_last(df_m30, 'sma_slow')

            # Validasi data tidak ada yang None
            if None in [m5_close, m5_kalman, m5_rsi, m5_sma_fast, m5_sma_slow, m30_close]:
                return 0.0

            score = 0.0

            if direction == "BUY":
                # 1. Trend Besar M30 (30%)
                if m30_close > m30_kalman: score += 0.15
                if m30_sma_fast > m30_sma_slow: score += 0.15

                # 2. Trend Menengah M15 (25%)
                if m15_close > m15_kalman: score += 0.10
                if m15_sma_fast > m15_sma_slow: score += 0.15

                # 3. Entry M5 (25%)
                if m5_close > m5_kalman: score += 0.10
                if m5_sma_fast > m5_sma_slow: score += 0.10
                if m5_close > m5_ema50: score += 0.05

                # 4. Momentum (20%)
                if 45 <= m5_rsi <= 70: score += 0.10 # RSI ideal buy
                if m5_macd is not None and m5_macd_sig is not None and m5_macd > m5_macd_sig:
                    score += 0.10

            else: # SELL
                if m30_close < m30_kalman: score += 0.15
                if m30_sma_fast < m30_sma_slow: score += 0.15

                if m15_close < m15_kalman: score += 0.10
                if m15_sma_fast < m15_sma_slow: score += 0.15

                if m5_close < m5_kalman: score += 0.10
                if m5_sma_fast < m5_sma_slow: score += 0.10
                if m5_close < m5_ema50: score += 0.05

                if 30 <= m5_rsi <= 55: score += 0.10
                if m5_macd is not None and m5_macd_sig is not None and m5_macd < m5_macd_sig:
                    score += 0.10

            return float(np.clip(score, 0.0, 1.0))

        except Exception as e:
            # JANGAN silent return 0.0, log biar ketahuan
            print(f"[Ensemble Error {direction}] {e}")
            return 0.0

class DynamicRiskManager:
    @staticmethod
    def calculate_levels(current_price: float, current_atr: float, direction: str) -> dict:
        # Anti ATR kecil (market sepi)
        atr = max(float(current_atr), config.MIN_SL_DISTANCE_USD / 1.5)

        # SL minimal anti spread-kill Deriv
        sl_dist_atr = 1.5 * atr
        sl_dist_min = config.MIN_SL_DISTANCE_USD
        sl_distance = max(sl_dist_atr, sl_dist_min)

        # TP pakai RRR dari config
        tp_distance = sl_distance * config.RRR_RATIO

        if direction == "BUY":
            sl = current_price - sl_distance
            tp = current_price + tp_distance
        else:
            sl = current_price + sl_distance
            tp = current_price - tp_distance

        risk = abs(current_price - sl)
        reward = abs(tp - current_price)
        rrr = reward / risk if risk > 0 else 0

        # Lot dinamis (kalau nanti ada balance, bisa dihitung)
        # Untuk sekarang default aman 0.01, tapi sudah siap untuk 2% risk
        lot = 0.01

        return {
            "sl": round(float(sl), 2),
            "tp": round(float(tp), 2),
            "rrr_actual": round(float(rrr), 2),
            "suggested_lot": lot,
            "sl_distance": round(float(sl_distance), 2)
        }

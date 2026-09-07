class QuantitativeEnsembleModel:
    @staticmethod
    def evaluate_setup(df_m30, df_m15, df_m5, direction: str) -> float:
        """
        Mengevaluasi skor probabilitas setup berdasarkan konfluensi multi-timeframe.
        Mengembalikan nilai skor antara 0.0 sampai 1.0.
        """
        try:
            # Ambil data candle terakhir yang sudah close (iloc[-2])
            m5_close = df_m5['close'].iloc[-2]
            m5_kalman = df_m5['kalman'].iloc[-2]
            m5_rsi = df_m5['rsi'].iloc[-2]
            
            m15_close = df_m15['close'].iloc[-2]
            m15_kalman = df_m15['kalman'].iloc[-2]
            
            m30_close = df_m30['close'].iloc[-2]
            m30_kalman = df_m30['kalman'].iloc[-2]

            score = 0.0

            if direction == "BUY":
                # Konisi Tren Multi-Timeframe naik
                if m5_close > m5_kalman: score += 0.35
                if m15_close > m15_kalman: score += 0.35
                if m30_close > m30_kalman: score += 0.20
                # Filter RSI agar tidak *overbought* ekstrem saat beli
                if 40 <= m5_rsi <= 65: score += 0.10
            
            elif direction == "SELL":
                # Kondisi Tren Multi-Timeframe turun
                if m5_close < m5_kalman: score += 0.35
                if m15_close < m15_kalman: score += 0.35
                if m30_close < m30_kalman: score += 0.20
                # Filter RSI agar tidak *oversold* ekstrem saat jual
                if 35 <= m5_rsi <= 60: score += 0.10

            return float(score)
        except Exception:
            return 0.0


class DynamicRiskManager:
    @staticmethod
    def calculate_levels(current_price: float, current_atr: float, direction: str) -> dict:
        """
        Menghitung level Stop Loss, Take Profit, dan RRR berdasarkan ATR dinamis.
        """
        if direction == "BUY":
            sl = current_price - (1.5 * current_atr)
            tp = current_price + (3.0 * current_atr) # RRR 1:2
        else: # SELL
            sl = current_price + (1.5 * current_atr)
            tp = current_price - (3.0 * current_atr)

        risk = abs(current_price - sl)
        reward = abs(tp - current_price)
        rrr = reward / (risk if risk > 0 else 1e-5)

        return {
            "sl": round(sl, 2),
            "tp": round(tp, 2),
            "rrr_actual": round(rrr, 2),
            "suggested_lot": 0.01  # Lot default aman untuk akun mikro/standar
        }

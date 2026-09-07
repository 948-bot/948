import pandas as pd
import config
from indicators import calculate_indicators
from math_core import QuantitativeEnsembleModel, DynamicRiskManager
from deriv_client import DerivPublicClient
from telegram_notifier import TelegramNotifier
import logging

def main():
    try:
        # 1. Filter Waktu Operasional (WIB)
        if not config.is_market_hours():
            logging.info("Di luar jam operasional (Senin 05:00 - Sabtu 05:00 WIB). Standby.")
            return

        # 2. Inisialisasi Klien (TANPA TOKEN)
        deriv = DerivPublicClient(config.DERIV_APP_ID)
        notifier = TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)

        # 3. Ambil Data Multi-Timeframe (Public API)
        logging.info("Mengambil data M30, M15, M5 dari Deriv Public Endpoint...")
        candles_m30 = deriv.fetch_candles(config.SYMBOL, config.TIMEFRAMES["M30"], count=60)
        candles_m15 = deriv.fetch_candles(config.SYMBOL, config.TIMEFRAMES["M15"], count=60)
        candles_m5 = deriv.fetch_candles(config.SYMBOL, config.TIMEFRAMES["M5"], count=60)

        # 4. Preprocessing & Feature Engineering
        df_m30 = calculate_indicators(pd.DataFrame(candles_m30))
        df_m15 = calculate_indicators(pd.DataFrame(candles_m15))
        df_m5 = calculate_indicators(pd.DataFrame(candles_m5))

        if df_m5.empty or df_m15.empty or df_m30.empty:
            raise ValueError("Data indikator kosong. Kemungkinan data Deriv terputus atau simbol salah.")

        # 5. Evaluasi Model Ensemble (AI Inference)
        score_buy = QuantitativeEnsembleModel.evaluate_setup(df_m30, df_m15, df_m5, "BUY")
        score_sell = QuantitativeEnsembleModel.evaluate_setup(df_m30, df_m15, df_m5, "SELL")

        logging.info(f"Ensemble Score - BUY: {score_buy:.2f} | SELL: {score_sell:.2f}")

        # 6. Cek Anti-Spam via Telegram State (Stateless Solution)
        if notifier.check_recent_signal(minutes_threshold=15):
            logging.info("Sinyal baru-baru ini sudah dikirim. Anti-spam aktif. Suppressing.")
            return

        # 7. Eksekusi Logika Sinyal (OP MANUAL TRIGGER)
        # Gunakan iloc[-2] untuk memastikan kita mengevaluasi candle yang SUDAH CLOSE (Zero Repainting)
        current_price = df_m5['close'].iloc[-2]
        current_atr = df_m5['atr'].iloc[-2]

        if score_buy >= 0.75:
            risk_data = DynamicRiskManager.calculate_levels(current_price, current_atr, "BUY")
            if risk_data["rrr_actual"] >= config.MIN_RISK_REWARD:
                notifier.send_signal(
                    direction="BUY", entry=current_price, sl=risk_data["sl"], 
                    tp=risk_data["tp"], lot=risk_data["suggested_lot"], 
                    rrr=risk_data["rrr_actual"], timeframe="M5/M15/M30"
                )
                return

        if score_sell >= 0.75:
            risk_data = DynamicRiskManager.calculate_levels(current_price, current_atr, "SELL")
            if risk_data["rrr_actual"] >= config.MIN_RISK_REWARD:
                notifier.send_signal(
                    direction="SELL", entry=current_price, sl=risk_data["sl"], 
                    tp=risk_data["tp"], lot=risk_data["suggested_lot"], 
                    rrr=risk_data["rrr_actual"], timeframe="M5/M15/M30"
                )
                return

        logging.info("Tidak ada setup yang memenuhi threshold probabilitas (>= 0.75).")

    except Exception as e:
        logging.error(f"Critical Error: {str(e)}")
        try:
            notifier = TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
            notifier.send_error(str(e))
        except:
            pass # Jika Telegram gagal, biarkan GA logging menanganinya
        raise

if __name__ == "__main__":
    main()

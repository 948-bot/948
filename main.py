import logging
import pandas as pd

import config
from indicators import calculate_indicators
from math_core import QuantitativeEnsembleModel, DynamicRiskManager
from deriv_client import DerivPublicClient
from telegram_notifier import TelegramNotifier

# ------------------------------------------------------------------
# 0. Konfigurasi Logging (WAJIB, kalau tidak semua logging.info/error
#    tidak akan pernah tampil di console maupun file)
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)

MIN_CANDLES_REQUIRED = 2  # minimal butuh iloc[-2]


def validate_config():
    """Pastikan semua konfigurasi penting tersedia sebelum bot jalan."""
    required_attrs = [
        "DERIV_APP_ID", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
        "SYMBOL", "TIMEFRAMES", "MIN_RISK_REWARD",
    ]
    missing = [attr for attr in required_attrs if not hasattr(config, attr)]
    if missing:
        raise AttributeError(f"Konfigurasi tidak lengkap, hilang: {missing}")


def is_dataframe_usable(df: pd.DataFrame, name: str) -> bool:
    """Cek dataframe tidak kosong dan punya cukup baris untuk iloc[-2]."""
    if df is None or df.empty:
        logging.warning(f"Dataframe {name} kosong.")
        return False
    if len(df) < MIN_CANDLES_REQUIRED:
        logging.warning(f"Dataframe {name} kurang dari {MIN_CANDLES_REQUIRED} baris.")
        return False
    return True


def safe_send_error(message: str):
    """Kirim notifikasi error ke Telegram, tapi jangan sampai crash kalau gagal."""
    try:
        notifier = TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
        notifier.send_error(message)
    except Exception as notify_err:
        logging.error(f"Gagal mengirim notifikasi error ke Telegram: {notify_err}")


def main():
    try:
        # 1. Validasi konfigurasi dasar
        validate_config()

        # 2. Filter Waktu Operasional (WIB)
        if not config.is_market_hours():
            logging.info("Di luar jam operasional (Senin 05:00 - Sabtu 05:00 WIB). Standby.")
            return

        # 3. Inisialisasi Klien (TANPA TOKEN untuk Deriv, public endpoint)
        deriv = DerivPublicClient(config.DERIV_APP_ID)
        notifier = TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)

        # 4. Ambil Data Multi-Timeframe (Public API)
        logging.info("Mengambil data M30, M15, M5 dari Deriv Public Endpoint...")
        try:
            candles_m30 = deriv.fetch_candles(config.SYMBOL, config.TIMEFRAMES["M30"], count=60)
            candles_m15 = deriv.fetch_candles(config.SYMBOL, config.TIMEFRAMES["M15"], count=60)
            candles_m5 = deriv.fetch_candles(config.SYMBOL, config.TIMEFRAMES["M5"], count=60)
        except Exception as fetch_err:
            raise ConnectionError(f"Gagal mengambil data candle dari Deriv: {fetch_err}")

        # 5. Preprocessing & Feature Engineering
        df_m30 = calculate_indicators(pd.DataFrame(candles_m30))
        df_m15 = calculate_indicators(pd.DataFrame(candles_m15))
        df_m5 = calculate_indicators(pd.DataFrame(candles_m5))

        # Validasi masing-masing dataframe (bukan cuma .empty, tapi juga jumlah baris)
        if not (is_dataframe_usable(df_m30, "M30")
                and is_dataframe_usable(df_m15, "M15")
                and is_dataframe_usable(df_m5, "M5")):
            raise ValueError("Data indikator tidak memadai. Kemungkinan data Deriv terputus, simbol salah, atau candle kurang dari minimum.")

        # 6. Evaluasi Model Ensemble (AI Inference)
        score_buy = QuantitativeEnsembleModel.evaluate_setup(df_m30, df_m15, df_m5, "BUY")
        score_sell = QuantitativeEnsembleModel.evaluate_setup(df_m30, df_m15, df_m5, "SELL")

        if score_buy is None or score_sell is None:
            raise ValueError("Model ensemble mengembalikan skor None, cek implementasi evaluate_setup().")

        logging.info(f"Ensemble Score - BUY: {score_buy:.2f} | SELL: {score_sell:.2f}")

        # 7. Cek Anti-Spam via Telegram State (Stateless Solution)
        if notifier.check_recent_signal(minutes_threshold=15):
            logging.info("Sinyal baru-baru ini sudah dikirim. Anti-spam aktif. Suppressing.")
            return

        # 8. Ambil candle terakhir yang SUDAH CLOSE (Zero Repainting)
        current_price = df_m5['close'].iloc[-2]
        current_atr = df_m5['atr'].iloc[-2]

        # Validasi nilai tidak NaN sebelum dipakai untuk hitung risk management
        if pd.isna(current_price) or pd.isna(current_atr):
            raise ValueError("current_price atau current_atr bernilai NaN. Kemungkinan data warm-up indikator belum cukup.")

        # 9. Eksekusi Logika Sinyal
        # Catatan: BUY dicek lebih dulu. Jika BUY lolos skor tapi RRR gagal,
        # kode akan tetap lanjut mengecek SELL di bawah (disengaja, bukan bug),
        # supaya tidak ada sinyal valid yang terlewat hanya karena BUY gagal RRR.
        signal_sent = False

        if score_buy >= 0.75:
            risk_data = DynamicRiskManager.calculate_levels(current_price, current_atr, "BUY")
            if risk_data["rrr_actual"] >= config.MIN_RISK_REWARD:
                notifier.send_signal(
                    direction="BUY", entry=current_price, sl=risk_data["sl"],
                    tp=risk_data["tp"], lot=risk_data["suggested_lot"],
                    rrr=risk_data["rrr_actual"], timeframe="M5/M15/M30"
                )
                signal_sent = True
            else:
                logging.info(f"Setup BUY lolos skor ({score_buy:.2f}) tapi RRR {risk_data['rrr_actual']:.2f} < minimum {config.MIN_RISK_REWARD}.")

        if not signal_sent and score_sell >= 0.75:
            risk_data = DynamicRiskManager.calculate_levels(current_price, current_atr, "SELL")
            if risk_data["rrr_actual"] >= config.MIN_RISK_REWARD:
                notifier.send_signal(
                    direction="SELL", entry=current_price, sl=risk_data["sl"],
                    tp=risk_data["tp"], lot=risk_data["suggested_lot"],
                    rrr=risk_data["rrr_actual"], timeframe="M5/M15/M30"
                )
                signal_sent = True
            else:
                logging.info(f"Setup SELL lolos skor ({score_sell:.2f}) tapi RRR {risk_data['rrr_actual']:.2f} < minimum {config.MIN_RISK_REWARD}.")

        if not signal_sent:
            logging.info("Tidak ada setup yang memenuhi threshold probabilitas (>= 0.75) dan/atau RRR minimum.")

    except Exception as e:
        logging.error(f"Critical Error: {str(e)}", exc_info=True)
        safe_send_error(str(e))
        raise


if __name__ == "__main__":
    main()

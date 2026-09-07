import requests
import logging
from datetime import datetime, timedelta

class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def check_recent_signal(self, minutes_threshold: int = 15) -> bool:
        """
        Pengecekan anti-spam sederhana berbasis stateless atau file log.
        Untuk tahap awal, mengembalikan False agar sinyal diizinkan terkirim.
        """
        # Anda dapat menyesuaikan logika penyimpanan riwayat waktu kirim di sini jika diperlukan
        return False

    def send_signal(self, direction: str, entry: float, sl: float, tp: float, lot: float, rrr: float, timeframe: str):
        """
        Mengirimkan notifikasi sinyal trading XAUUSD ke Telegram.
        """
        message = (
            f"🚨 **XAUUSD QUANT SIGNAL** 🚨\n\n"
            f"Direction: **{direction}**\n"
            f"Timeframe: {timeframe}\n"
            f"Entry Price: `{entry}`\n"
            f"Stop Loss (SL): `{sl}`\n"
            f"Take Profit (TP): `{tp}`\n"
            f"Suggested Lot: `{lot}`\n"
            f"Risk/Reward Ratio: `1:{rrr}`\n\n"
            f"⚡ *Masterpiece v5 Engine Active*"
        )
        self._send_message(message)

    def send_error(self, error_msg: str):
        """
        Mengirimkan notifikasi jika terjadi error kritis pada bot.
        """
        message = f"❌ **BOT ERROR ALERT** ❌\n\n`{error_msg}`"
        self._send_message(message)

    def _send_message(self, text: str):
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                logging.error(f"Gagal mengirim pesan Telegram: {response.text}")
        except Exception as e:
            logging.error(f"Exception saat kirim Telegram: {str(e)}")

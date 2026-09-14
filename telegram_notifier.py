import requests, logging, json, os, time
from datetime import datetime

class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        # File untuk anti-spam yang bener (bukan return False terus)
        self.last_file = ".last_tani_v9.json"
        self.photo_url = "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800"

    def check_recent_signal(self, minutes_threshold: int = 15) -> bool:
        """Anti-spam beneran pakai file, bukan stateless"""
        try:
            if not os.path.exists(self.last_file):
                return False
            data = json.load(open(self.last_file))
            last_time = data.get("time", 0)
            diff_min = (time.time() - last_time) / 60
            if diff_min < minutes_threshold:
                logging.info(f"Anti-spam: sinyal terakhir {diff_min:.1f} menit lalu, skip")
                return True
            return False
        except:
            return False

    def send_signal(self, direction: str, entry: float, sl: float, tp: float, lot: float, rrr: float, timeframe: str):
        """
        Hybrid: timeframe sekarang isinya info lengkap V9
        Contoh: "V9 PANEN RAYA UP OFI:0.25"
        """
        try:
            # Parse info dari timeframe
            is_raya = "RAYA" in timeframe
            emoji = "🌾👑🔥" if is_raya else "🌿"
            jenis = "PANEN RAYA" if is_raya else "PANEN KECIL"

            # Caption ala TANI V8.8
            caption = (
                f"{emoji} V9 {jenis} {direction}\n"
                f"{'BUY 🟢' if direction=='BUY' else 'SELL 🔴'} {timeframe}\n\n"
                f"💰 ENTRY {entry:.2f}\n"
                f"🛑 SL {sl:.2f}\n"
                f"🎯 TP {tp:.2f}\n"
                f"📦 Lot {lot} | RRR 1:{rrr}\n\n"
                f"⚡ Masterpiece V9 Hybrid Engine\n"
                f"Quant + Colony + OFI Filter"
            )

            # Kirim sebagai FOTO biar kayak TANI (lebih menarik)
            url_photo = f"{self.base_url}/sendPhoto"
            payload_photo = {
                "chat_id": self.chat_id,
                "photo": self.photo_url,
                "caption": caption
            }
            r = requests.post(url_photo, json=payload_photo, timeout=15)
            
            if r.status_code != 200:
                # Fallback kalau sendPhoto gagal, kirim text biasa
                logging.warning(f"sendPhoto gagal {r.text}, fallback ke text")
                self._send_message(caption)
            else:
                logging.info(f"Foto sinyal {jenis} {direction} terkirim")

        except Exception as e:
            logging.error(f"Exception send_signal: {e}")
            # Fallback text
            self._send_message(f"🚨 XAUUSD {direction} ENTRY {entry} SL {sl} TP {tp} RRR {rrr} {timeframe}")

    def send_error(self, error_msg: str):
        """Untuk weekend evaluasi & error"""
        # Kalau pesannya sudah ada emoji V9, jangan tambah ❌ lagi
        if "🌴" in error_msg or "V9" in error_msg or "WEEKEND" in error_msg:
            text = error_msg
        else:
            text = f"❌ BOT ALERT\n\n`{error_msg[:400]}`"
        self._send_message(text)

    def send_weekend_check(self, paxg_price, mt5_est, ofi, gudang):
        """Khusus weekend, dipanggil dari main.py V9"""
        caption = (
            f"🌴 V9 WEEKEND EVALUASI\n"
            f"📊 Gudang {gudang}$ | OFI {ofi:+.2f}\n"
            f"💰 PAXG {paxg_price:.2f} | Deriv est {mt5_est:.2f}\n"
            f"🕐 Pasar tutup Sabtu 04:00 - Senin 05:00 WIB\n"
            f"⏰ Auto ON Senin 05:00 WIB!"
        )
        try:
            requests.post(f"{self.base_url}/sendPhoto",
                          json={"chat_id": self.chat_id, "photo": self.photo_url, "caption": caption},
                          timeout=15)
        except Exception as e:
            logging.error(f"Weekend send fail {e}")

    def _send_message(self, text: str):
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"}
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                logging.error(f"Gagal kirim Telegram: {response.text}")
        except Exception as e:
            logging.error(f"Exception kirim Telegram: {e}")

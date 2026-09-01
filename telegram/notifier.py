"""
XAUUSD AI DERIV BOT
Telegram Notifier Module
"""
import os
import requests

def send_telegram_message(message: str) -> bool:
    """
    Mengirim pesan teks langsung ke chat Telegram menggunakan Bot API HTTP POST.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("⚠️ Telegram Token atau Chat ID belum dikonfigurasi di environment.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Notifikasi Telegram berhasil dikirim.")
            return True
        else:
            print(f"❌ Gagal mengirim Telegram: {response.text}")
            return False
    except Exception as e:
        print(f"🔴 Error koneksi ke Telegram API: {e}")
        return False

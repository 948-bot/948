"""
XAUUSD AI DERIV BOT
Telegram Bot Wrapper Module
"""
from telegram.notifier import send_telegram_message

def send_signal_notification(signal_data: dict, ai_evaluation: dict, risk_data: dict):
    """
    Fungsi utama untuk mengirim notifikasi sinyal tervalidasi ke Telegram.
    """
    from telegram.templates import format_signal_message
    message = format_signal_message(signal_data, ai_evaluation, risk_data)
    return send_telegram_message(message)

def send_error_notification(error_text: str):
    """
    Fungsi utama untuk mengirim notifikasi error ke Telegram.
    """
    from telegram.templates import format_error_message
    message = format_error_message(error_text)
    return send_telegram_message(message)

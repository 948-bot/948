# ... (kode check_recent_signal dan send_error tetap sama) ...

    def send_signal(self, direction: str, entry: float, sl: float, tp: float, 
                    lot: float, rrr: float, timeframe: str):
        msg = (
            f"🚨 **VALID QUANT SIGNAL (MANUAL OP)** 🚨\n"
            f"Symbol: `XAUUSD` ({timeframe} Confluence)\n"
            f"Direction: **{direction}**\n"
            f"Entry Price: `{entry:.2f}`\n"
            f"🛑 SL (Volatility Adjusted): `{sl:.2f}`\n"
            f"🎯 TP (Dynamic): `{tp:.2f}`\n"
            f"📊 RRR: `1:{rrr}`\n"
            f"💰 Suggested Lot (2% Risk): `{lot}`\n\n"
            f"⚠️ *OP MANUAL: Buka posisi secara manual di Deriv. Pastikan spread normal (< 3.0) sebelum entry.*"
        )
        url = f"{self.base_url}/sendMessage"
        requests.post(url, json={"chat_id": self.chat_id, "text": msg, "parse_mode": "Markdown"})
        logging.info(f"Sinyal {direction} (Manual OP) dikirim ke Telegram.")

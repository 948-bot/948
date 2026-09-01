"""
XAUUSD AI DERIV BOT
Main Entry Point - Snapshot Mode (GitHub Actions Friendly)
"""
import time
import json
import websocket
from config.settings import validate_basic_config, is_trading_day, DERIV_APP_ID, DERIV_SYMBOL, LOG_LEVEL

def fetch_market_snapshot():
    """
    Melakukan koneksi sekali jalan (snapshot), meminta data harga/tick terkini,
    lalu menutup koneksi secara bersih setelah data didapat.
    """
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={DERIV_APP_ID}"
    collected_data = {"tick": None}

    def on_message(ws, message):
        data = json.loads(message)
        if data.get("msg_type") == "tick":
            collected_data["tick"] = data.get("tick")
            ws.close() # Langsung tutup begitu data tick didapat

    def on_open(ws):
        # Kirim request tick sekali jalan untuk XAUUSD
        payload = {
            "ticks": DERIV_SYMBOL
        }
        ws.send(json.dumps(payload))

    def on_error(ws, error):
        print(f"🔴 WebSocket Error: {error}")

    def on_close(ws, close_status_code, close_msg):
        print("🔌 Koneksi snapshot ditutup.")

    # Jalankan koneksi singkat
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # Jalankan dengan timeout maksimal 10 detik supaya tidak menggantung
    ws.run_forever(ping_timeout=5)
    return collected_data["tick"]

def main():
    print("==================================================")
    print("XAUUSD AI DERIV BOT - SNAPSHOT ENGINE (V0)")
    print("==================================================")

    # 1. Validasi Konfigurasi Dasar
    ok, msg = validate_basic_config()
    if not ok:
        print(f"❌ Error Konfigurasi: {msg}")
        return
    print(f"✅ Konfigurasi Dasar OK | Simbol: {DERIV_SYMBOL} | Log Level: {LOG_LEVEL}")

    # 2. Cek Jadwal Operasional (Senin - Jumat)
    trading_day = is_trading_day()
    status_teks = "AKTIF 🟢" if trading_day else "LIBUR 🔴"
    print(f"📅 Status Hari Trading (Senin-Jumat): {status_teks}")
    
    if not trading_day:
        print("⚠️ Hari ini adalah akhir pekan (Weekend). Bot otomatis OFF sesuai jadwal.")
        return

    # 3. Tarik Data Snapshot Pasar Terkini
    print(f"🔄 Menghubungkan ke Deriv untuk mengambil data snapshot {DERIV_SYMBOL}...")
    tick_data = fetch_market_snapshot()

    if tick_data:
        price = tick_data.get("quote")
        epoch = tick_data.get("epoch")
        symbol = tick_data.get("symbol")
        print(f"🟢 [SNAPSHOT BERHASIL] Simbol: {symbol} | Harga Terkini: {price} | Waktu: {epoch}")
        # Di sini nanti kita pasang analisis M15 & M30 pada tahap berikutnya!
    else:
        print("⚠️ Gagal mendapatkan data tick snapshot dalam batas waktu yang ditentukan.")

    print("🏁 Eksekusi snapshot 5 menitan selesai. Bot keluar secara aman.")

if __name__ == "__main__":
    main()

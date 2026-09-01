"""
XAUUSD AI DERIV BOT
Main Entry Point (Version V0)
"""
import time
import threading
from config.settings import validate_basic_config, is_trading_day, DERIV_SYMBOL, LOG_LEVEL
from deriv.websocket import DerivWebSocket
from deriv.market_data import subscribe_ticks
from deriv.candles import CandleBuilder

def main():
    print("==================================================")
    print("XAUUSD AI DERIV BOT - MAIN ENGINE (V0)")
    print("==================================================")

    # 1. Validasi Konfigurasi Dasar
    ok, msg = validate_basic_config()
    if not ok:
        print(f"❌ Error Konfigurasi: {msg}")
        return
    print(f"✅ Konfigurasi Dasar OK | Simbol: {DERIV_SYMBOL} | Log Level: {LOG_LEVEL}")

    # 2. Cek Jadwal Operasional (Senin - Jumat)
    trading_day = is_trading_day()
    print(f"📅 Status Hari Trading (Senin-Jumat): {'AKTIF 🟢' : LIBUR 🔴}")
    
    if not trading_day:
        print("⚠️ Hari ini adalah akhir pekan (Weekend). Bot otomatis OFF sesuai jadwal.")
        print("Bot akan kembali standby otomatis pada hari Senin.")
        return

    # 3. Inisialisasi Candle Builder (M15 & M30)
    builder = CandleBuilder()

    # 4. Handler untuk pesan WebSocket yang masuk
    def on_message_handler(data):
        msg_type = data.get("msg_type")
        
        if msg_type == "tick":
            tick = data.get("tick", {})
            price = tick.get("quote")
            epoch = tick.get("epoch")
            symbol = tick.get("symbol")
            
            if price and epoch:
                # Proses tick ke builder M15 & M30
                builder.process_tick(float(price), int(epoch))
                status = builder.get_latest_status()
                
                print(f"🟢 [DATA ENGINE] Tick Masuk | Simbol: {symbol} | Harga: {price}")
                
                # Menampilkan status candle berjalan
                if status["m15"]:
                    m15 = status["m15"]
                    print(f"   └─ [M15] O:{m15['open']} H:{m15['high']} L:{m15['low']} C:{m15['close']}")
                if status["m30"]:
                    m30 = status["m30"]
                    print(f"   └─ [M30] O:{m30['open']} H:{m30['high']} L:{m30['low']} C:{m30['close']}")
        
        elif msg_type == "error":
            print(f"🔴 Deriv Server Error: {data.get('error', {}).get('message')}")

    # 5. Inisialisasi dan Jalankan WebSocket Client di Background Thread
    ws_client = DerivWebSocket(on_message_callback=on_message_handler)
    
    def run_websocket():
        ws_client.connect()

    ws_thread = threading.Thread(target=run_websocket)
    ws_thread.daemon = True
    ws_thread.start()

    # Beri jeda sejenak untuk koneksi, lalu kirim perintah subscribe tick
    time.sleep(3)
    if ws_client.ws and ws_client.ws.sock and ws_client.ws.sock.connected:
        print("Mengirim perintah langganan (subscribe) tick real-time ke Deriv...")
        subscribe_ticks(ws_client)
    else:
        print("🔴 Gagal terhubung ke WebSocket Deriv saat inisialisasi awal.")

    # 6. Main Loop Bot V0
    try:
        while True:
            # Di tahap V0, loop utama menjaga agar bot tetap hidup 
            # dan memantau kesehatan koneksi data real-time.
            time.sleep(1)
            
            # Pengecekan dinamis apakah hari berganti menjadi weekend di tengah jalan
            if not is_trading_day():
                print("⚠️ Memasuki jam weekend. Mematikan bot secara aman...")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Bot dihentikan secara manual oleh pengguna (KeyboardInterrupt).")
        ws_client.close()
    finally:
        print("🔌 Koneksi ditutup. Bot V0 Berhenti.")

if __name__ == "__main__":
    main()

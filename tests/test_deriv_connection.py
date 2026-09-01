"""
XAUUSD AI DERIV BOT
Test Connection & Data Engine (V0)
"""
import time
from config.settings import validate_basic_config, is_trading_day, DERIV_SYMBOL
from deriv.websocket import DerivWebSocket
from deriv.market_data import subscribe_ticks
from deriv.candles import CandleBuilder

def main():
    print("===================================")
    print("XAUUSD AI DERIV BOT - TEST CONNECTION")
    print("===================================")

    # 1. Validasi Konfigurasi Dasar
    ok, msg = validate_basic_config()
    if not ok:
        print(f"❌ Error Konfigurasi: {msg}")
        return
    print(f"✅ Konfigurasi Dasar OK. Simbol: {DERIV_SYMBOL}")

    # 2. Cek Jadwal Trading (5/24)
    trading_day = is_trading_day()
    print(f"📅 Hari Trading Aktif (Senin-Jumat): {trading_day}")
    if not trading_day:
        print("⚠️ Hari ini libur (Weekend). Bot dalam mode OFF sesuai jadwal.")
        return

    # 3. Inisialisasi Candle Builder
    builder = CandleBuilder()

    # 4. Callback saat pesan masuk dari WebSocket
    def on_message_handler(data):
        msg_type = data.get("msg_type")
        
        if msg_type == "tick":
            tick = data.get("tick", {})
            price = tick.get("quote")
            epoch = tick.get("epoch")
            symbol = tick.get("symbol")
            
            if price and epoch:
                # Proses tick ke Candle Builder M15 & M30
                builder.process_tick(float(price), int(epoch))
                status = builder.get_latest_status()
                
                print(f"🟢 TICK | {symbol} | Harga: {price}")
                if status["m15"]:
                    m15 = status["m15"]
                    print(f"   └─ M15 Candle [Time: {m15['time']}] O:{m15['open']} H:{m15['high']} L:{m15['low']} C:{m15['close']}")
        
        elif msg_type == "error":
            print(f"🔴 Deriv Error: {data.get('error', {}).get('message')}")

    # 5. Jalankan WebSocket
    ws_client = DerivWebSocket(on_message_callback=on_message_handler)
    
    # Hubungkan dan subscribe setelah terbuka
    import threading
    def run_ws():
        ws_client.connect()

    ws_thread = threading.Thread(target=run_ws)
    ws_thread.daemon = True
    ws_thread.start()

    # Beri waktu jeda koneksi, lalu kirim permintaan subscribe tick
    time.sleep(3)
    if ws_client.ws and ws_client.ws.sock and ws_client.ws.sock.connected:
        print("Mengirim perintah subscribe tick ke Deriv...")
        subscribe_ticks(ws_client)
    else:
        print("🔴 Gagal terhubung ke WebSocket saat mencoba subscribe.")

    # Biarkan berjalan beberapa saat untuk memantau data masuk
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Menghentikan bot pengujian...")
        ws_client.close()

if __name__ == "__main__":
    main()

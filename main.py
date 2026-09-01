"""
XAUUSD AI DERIV BOT
Main Entry Point - Multi-Symbol Snapshot & Candle Engine (V0)
"""
import time
import json
import websocket
import pandas as pd
from config.settings import validate_basic_config, is_trading_day, LOG_LEVEL

def fetch_deriv_candles(count: int = 150) -> pd.DataFrame:
    """
    Mencoba beberapa alternatif simbol emas resmi di Deriv secara berurutan:
    1. frxXAUUSD (Standar Forex Deriv)
    2. XAUUSD (Alternatif umum)
    3. gold (Alternatif komoditas)
    """
    symbols_to_try = ["frxXAUUSD", "XAUUSD", "gold"]
    app_id = "1089"  # App ID publik Deriv yang stabil
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={app_id}"
    
    selected_symbol = None
    raw_candles = []

    for sym in symbols_to_try:
        print(f"🔄 Mencoba terhubung dan mengambil data untuk simbol: {sym}...")
        
        collected_data = {"candles": None}

        def on_message(ws, message):
            data = json.loads(message)
            msg_type = data.get("msg_type")
            
            if msg_type == "candles":
                collected_data["candles"] = data.get("candles")
                ws.close()
            elif msg_type == "error":
                err_msg = data.get("error", {}).get("message", "Unknown error")
                print(f"⚠️ Simbol '{sym}' ditolak server: {err_msg}")
                ws.close()

        def on_open(ws):
            # Request historical candles (misal timeframe M15 / granularity 900 detik)
            payload = {
                "ticks_history": sym,
                "adjust_start_time": 1,
                "count": count,
                "end": "latest",
                "granularity": 900,  # 15 menit (M15)
                "style": "candles"
            }
            ws.send(json.dumps(payload))

        def on_error(ws, error):
            pass  # Abaikan error koneksi sesaat untuk mencoba simbol berikutnya

        def on_close(ws, close_status_code, close_msg):
            pass

        # Jalankan koneksi WebSocket singkat untuk simbol ini
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws.run_forever(ping_timeout=5)

        if collected_data["candles"]:
            selected_symbol = sym
            raw_candles = collected_data["candles"]
            print(f"✅ Berhasil mendapatkan data menggunakan simbol: {sym}")
            break

    if not raw_candles:
        print("❌ Gagal total: Semua alternatif simbol (frxXAUUSD, XAUUSD, gold) tidak merespons.")
        return pd.DataFrame()

    # Konversi ke Pandas DataFrame
    df = pd.DataFrame(raw_candles)
    # Kolom standar dari Deriv: epoch, open, high, low, close
    df['time'] = pd.to_datetime(df['epoch'], unit='s')
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    
    return df

def main():
    print("==================================================")
    print("XAUUSD AI DERIV BOT - MULTI-SYMBOL ENGINE (V0)")
    print("==================================================")

    # 1. Validasi Konfigurasi Dasar
    ok, msg = validate_basic_config()
    if not ok:
        print(f"❌ Error Konfigurasi: {msg}")
        return
    print(f"✅ Konfigurasi Dasar OK | Log Level: {LOG_LEVEL}")

    # 2. Cek Jadwal Operasional (Senin - Jumat)
    trading_day = is_trading_day()
    status_teks = "AKTIF 🟢" if trading_day else "LIBUR 🔴"
    print(f"📅 Status Hari Trading (Senin-Jumat): {status_teks}")
    
    if not trading_day:
        print("⚠️ Hari ini adalah akhir pekan (Weekend). Bot otomatis OFF sesuai jadwal.")
        return

    # 3. Tarik Data Candle M15 Menggunakan Multi-Symbol Fallback
    print("🔄 Memulai pengambilan data candle M15 dari server Deriv...")
    df_candles = fetch_deriv_candles(count=10)

    if not df_candles.empty:
        print(f"🟢 [BERHASIL] Berhasil menarik {len(df_candles)} candle M15 terakhir:")
        print(df_candles[['time', 'open', 'high', 'low', 'close']].tail(3))
    else:
        print("⚠️ Gagal memuat data candle pasar.")

    print("🏁 Eksekusi snapshot selesai. Bot keluar secara aman.")

if __name__ == "__main__":
    main()

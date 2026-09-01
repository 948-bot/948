"""
XAUUSD AI DERIV BOT
Main Entry Point - Full V1 Pipeline (GitHub Actions Friendly)
"""
import time
import json
import websocket
import pandas as pd
from config.settings import validate_basic_config, is_trading_day, LOG_LEVEL
from strategy.m30_context import analyze_m30_context
from strategy.m15_setup import evaluate_m15_setup
from strategy.dynamic_tp import calculate_dynamic_tp
from ai.analyzer import evaluate_with_ai
from risk.engine import validate_risk
from risk.position_size import calculate_position_size
from telegram.anti_spam import check_anti_spam
from telegram.bot import send_signal_notification
from database.journal import log_signal_to_db

def fetch_deriv_candles(granularity: int, count: int = 100) -> pd.DataFrame:
    """
    Mengambil data candle historis dari server Deriv menggunakan simbol frxXAUUSD.
    Granularity: 900 untuk M15, 1800 untuk M30.
    """
    sym = "frxXAUUSD"
    app_id = "1089"  # App ID publik Deriv yang stabil
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={app_id}"
    
    raw_candles = []

    def on_message(ws, message):
        data = json.loads(message)
        msg_type = data.get("msg_type")
        
        if msg_type == "candles":
            raw_candles.extend(data.get("candles", []))
            ws.close()
        elif msg_type == "error":
            ws.close()

    def on_open(ws):
        payload = {
            "ticks_history": sym,
            "adjust_start_time": 1,
            "count": count,
            "end": "latest",
            "granularity": granularity,
            "style": "candles"
        }
        ws.send(json.dumps(payload))

    def on_error(ws, error):
        pass

    def on_close(ws, close_status_code, close_msg):
        pass

    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever(ping_timeout=5)

    if not raw_candles:
        return pd.DataFrame()

    df = pd.DataFrame(raw_candles)
    df['time'] = pd.to_datetime(df['epoch'], unit='s')
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    
    return df

def main():
    print("==================================================")
    print("XAUUSD AI DERIV BOT - FULL PIPELINE ENGINE (V1)")
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

    # 3. Tarik Data Candle M30 (Konteks Makro) & M15 (Setup)
    print("🔄 Menarik data pasar M30 & M15 dari server Deriv...")
    df_m30 = fetch_deriv_candles(granularity=1800, count=60) # 1800 detik = 30 menit
    df_m15 = fetch_deriv_candles(granularity=900, count=60)  # 900 detik = 15 menit

    if df_m30.empty or df_m15.empty:
        print("⚠️ Gagal menarik data candle pasar secara lengkap.")
        return

    # 4. Analisis Konteks M30 & Setup M15
    print("📊 Menjalankan analisis strategi M30 & M15...")
    m30_context = analyze_m30_context(df_m30)
    m15_setup = evaluate_m15_setup(df_m15, m30_context.get("bias", "NEUTRAL"))

    print(f"   -> M30 Bias: {m30_context.get('bias')} | Struktur: {m30_context.get('structure')}")
    print(f"   -> M15 Setup: {m15_setup.get('signal')} | Alasan: {m15_setup.get('reason')}")

    # 5. Evaluasi AI / Rule Engine
    print("🤖 Menjalankan evaluasi keputusan AI...")
    ai_eval = evaluate_with_ai(m30_context, m15_setup)
    print(f"   -> Keputusan AI: {ai_eval.get('action')} | Confidence: {ai_eval.get('confidence')}%")

    # 6. Validasi Risiko & Pengaman Sinyal
    action = ai_eval.get("action", "WAIT")
    if action in ["BUY", "SELL"]:
        current_price = m15_setup.get("close", 0.0)
        tp_sl_data = calculate_dynamic_tp(action, current_price, df_m15)
        
        signal_payload = {
            "entry": current_price,
            "tp": tp_sl_data.get("tp"),
            "sl": tp_sl_data.get("sl"),
            "pips": tp_sl_data.get("pips")
        }

        # Hard Risk Validation
        is_risk_ok, risk_msg = validate_risk(signal_payload, ai_eval)
        if not is_risk_ok:
            print(f"🛡️ Sinyal ditolak Risk Engine: {risk_msg}")
            return

        # Anti-Spam Check
        if not check_anti_spam(action, current_price):
            print("⏳ Sinyal dicegah oleh modul Anti-Spam (Cooldown aktif).")
            return

        # Hitung posisi risiko lot (asumsi saldo akun demo/default $10,000)
        risk_calc = calculate_position_size(10000.0, current_price, signal_payload["sl"])

        print("🚀 Sinyal Valid! Mengirimkan notifikasi & mencatat ke database...")
        log_signal_to_db(signal_payload, ai_eval)
        send_signal_notification(signal_payload, ai_eval, risk_calc)
    else:
        print("⏸️ Tidak ada sinyal valid saat ini (Status: WAIT). Bot keluar dengan aman.")

    print("🏁 Eksekusi pipeline bot selesai.")

if __name__ == "__main__":
    main()

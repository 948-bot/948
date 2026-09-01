"""
XAUUSD AI DERIV BOT
Instrument Specification Handler
"""
import json
import websocket
from config.settings import DERIV_APP_ID, DERIV_SYMBOL

def fetch_instrument_spec():
    """
    Mengambil spesifikasi instrumen dari Deriv API (active_symbols)
    untuk memastikan digit, pip_size, dan status trading XAUUSD.
    """
    ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={DERIV_APP_ID}"
    instrument_data = None

    def on_message(ws, message):
        nonlocal instrument_data
        data = json.loads(message)
        
        if data.get("msg_type") == "active_symbols":
            symbols = data.get("active_symbols", [])
            for s in symbols:
                # Mencocokkan simbol XAUUSD (biasanya 'frxXAUUSD' atau 'XAUUSD')
                if s.get("symbol") == DERIV_SYMBOL or s.get("display_name", "").lower() in ["gold", "xauusd"]:
                    instrument_data = {
                        "symbol": s.get("symbol"),
                        "display_name": s.get("display_name"),
                        "pip": s.get("pip"),
                        "isin": s.get("isin"),
                        "market": s.get("market"),
                        "submarket": s.get("submarket"),
                        "min_contract_stake": s.get("min_stake")
                    }
                    break
            ws.close()
        elif data.get("msg_type") == "error":
            print(f"Deriv Error: {data['error']['message']}")
            ws.close()

    def on_open(ws):
        # Request daftar active symbols untuk mencari XAUUSD
        payload = {
            "active_symbols": "brief",
            "product_type": "forex" # Atau CFDs
        }
        ws.send(json.dumps(payload))

    try:
        ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
        ws.run_forever()
    except Exception as e:
        print(f"Gagal terhubung ke WebSocket Deriv untuk cek instrumen: {e}")

    return instrument_data

if __name__ == "__main__":
    print("Mengecek spesifikasi instrumen dari Deriv...")
    spec = fetch_instrument_spec()
    if spec:
        print("✅ Berhasil mendeteksi instrumen:")
        for k, v in spec.items():
            print(f" - {k}: {v}")
    else:
        print("❌ Gagal mendeteksi spesifikasi instrumen.")

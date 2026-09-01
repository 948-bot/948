"""
XAUUSD AI DERIV BOT
Market Data Streamer
"""
from config.settings import DERIV_SYMBOL

def subscribe_ticks(ws_client):
    """
    Melakukan subscribe ke aliran tick real-time untuk simbol tertentu (misal: frxXAUUSD).
    """
    payload = {
        "ticks": DERIV_SYMBOL,
        "subscribe": 1
    }
    print(f"Mengirim permintaan subscription tick untuk: {DERIV_SYMBOL}...")
    ws_client.send(payload)

def handle_tick_message(data):
    """
    Contoh fungsi untuk memproses pesan tick yang masuk dari WebSocket.
    """
    msg_type = data.get("msg_type")
    if msg_type == "tick":
        tick = data.get("tick", {})
        symbol = tick.get("symbol")
        price = tick.get("quote")
        epoch = tick.get("epoch")
        print(f"🟢 REAL-TIME TICK | Simbol: {symbol} | Harga: {price} | Waktu (Epoch): {epoch}")
    elif msg_type == "error":
        print(f"🔴 Error dari server Deriv: {data.get('error', {}).get('message')}")

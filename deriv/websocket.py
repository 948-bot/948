"""
XAUUSD AI DERIV BOT
WebSocket Connection Handler
"""
import json
import time
import websocket
from config.settings import DERIV_APP_ID

class DerivWebSocket:
    def __init__(self, on_message_callback=None):
        self.ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={DERIV_APP_ID}"
        self.ws = None
        self.is_running = False
        self.on_message_callback = on_message_callback

    def on_message(self, ws, message):
        data = json.loads(message)
        if self.on_message_callback:
            self.on_message_callback(data)

    def on_error(self, ws, error):
        print(f"🔴 WebSocket Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"🔴 WebSocket Terputus. Kode: {close_status_code}, Pesan: {close_msg}")
        print("Reconnecting dalam 5 detik...")
        time.sleep(5)
        if self.is_running:
            self.connect()

    def on_open(self, ws):
        print("🟢 DERIV CONNECTION : Connected (WebSocket Aktif)")

    def connect(self):
        self.is_running = True
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.run_forever(ping_interval=30, ping_timeout=10)

    def send(self, data: dict):
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps(data))

    def close(self):
        self.is_running = False
        if self.ws:
            self.ws.close()

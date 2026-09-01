import json,logging,threading,time,websocket
from config.settings import DERIV_WS_URL
log=logging.getLogger("deriv.ws")
class DerivPublicWS:
    def __init__(self,on_message,on_error=None):
        self.on_message=on_message; self.on_error=on_error; self.ws=None; self.stop=False; self.connected=False
    def start(self): threading.Thread(target=self._loop,daemon=True).start()
    def stop_ws(self): self.stop=True; self.connected=False; self.ws and self.ws.close()
    def send(self,payload):
        if not self.ws or not self.connected: raise RuntimeError("Deriv WebSocket not connected")
        self.ws.send(json.dumps(payload))
    def _loop(self):
        backoff=2
        while not self.stop:
            try:
                self.ws=websocket.WebSocketApp(DERIV_WS_URL,on_open=self._open,on_message=self._msg,on_error=self._err,on_close=self._close)
                self.ws.run_forever(ping_interval=20,ping_timeout=10)
            except Exception as e:
                log.exception("WebSocket loop error")
                if self.on_error:self.on_error(str(e))
            self.connected=False
            if not self.stop: time.sleep(backoff); backoff=min(60,backoff*2)
    def _open(self,ws):
        self.connected=True; logging.info("Deriv public WebSocket connected"); self.send({"active_symbols":"brief","req_id":1})
    def _msg(self,ws,msg):
        try:self.on_message(json.loads(msg))
        except Exception as e: log.exception("Message handling error: %s",e)
    def _err(self,ws,err):
        self.connected=False; log.error("Deriv WebSocket error: %s",err)
        if self.on_error:self.on_error(str(err))
    def _close(self,ws,code,msg): self.connected=False; log.warning("Deriv WebSocket closed: %s %s",code,msg)

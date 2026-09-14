import os
from datetime import datetime, timezone, timedelta
DERIV_APP_ID=os.getenv("DERIV_APP_ID","1089")
TELEGRAM_BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN","YOUR_BOT_TOKEN")
TELEGRAM_CHAT_ID=os.getenv("TELEGRAM_CHAT_ID","YOUR_CHAT_ID")
SYMBOL="frxXAUUSD"
TIMEFRAMES={"M5":300,"M15":900,"M30":1800}
ATR_PERIOD=14; RRR_RATIO=2.5; MIN_RISK_REWARD=2.0; MIN_SL_DISTANCE_USD=2.5; MAX_RISK_PER_TRADE_PCT=0.02
WIB_OFFSET=timedelta(hours=7)
def is_market_hours()->bool:
    now_utc=datetime.now(timezone.utc); now_wib=now_utc+WIB_OFFSET; wd=now_wib.weekday()
    if wd==6: return False
    if wd==5 and now_wib.hour>=5: return False
    if wd==0 and now_wib.hour<5: return False
    return True

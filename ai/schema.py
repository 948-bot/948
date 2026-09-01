"""
XAUUSD AI DERIV BOT
AI Output Schema
"""

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["BUY", "SELL", "WAIT"]
        },
        "confidence": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100
        },
        "market_regime": {
            "type": "string",
            "enum": ["TRENDING_UP", "TRENDING_DOWN", "RANGING", "HIGH_VOLATILITY"]
        },
        "reasoning": {
            "type": "string"
        }
    },
    "required": ["action", "confidence", "market_regime", "reasoning"]
}

"""
XAUUSD AI DERIV BOT
Collaborative Multi-AI Analyzer Module (Cross-Check & Fallback)
"""
import os
import json
import requests
from config.settings import AI_MIN_CONFIDENCE

def call_deepseek(prompt_text: str) -> dict:
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key: return None
    try:
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt_text}], "temperature": 0.1}
        res = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload, timeout=15)
        if res.status_code == 200:
            content = res.json()["choices"][0]["message"]["content"].replace("```json", "").replace("```", "").strip()
            return json.loads(content)
    except Exception:
        pass
    return None

def call_openrouter(prompt_text: str) -> dict:
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key: return None
    try:
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {"model": "deepseek/deepseek-chat", "messages": [{"role": "user", "content": prompt_text}], "temperature": 0.1}
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=15)
        if res.status_code == 200:
            content = res.json()["choices"][0]["message"]["content"].replace("```json", "").replace("```", "").strip()
            return json.loads(content)
    except Exception:
        pass
    return None

def evaluate_with_ai(m30_data: dict, m15_data: dict) -> dict:
    """
    Sistem kolaborasi AI: DeepSeek dan OpenRouter/AI Studio saling cross-check.
    Jika keduanya sepakat, sinyal diloloskan. Jika beda pendapat, diblokir jadi WAIT.
    """
    prompt_text = f"""
    Anda adalah bagian dari Komite AI Quantitative Analyst XAUUSD.
    Analisis data berikut dan berikan keputusan ketat (BUY, SELL, atau WAIT):
    
    [M30 Context] Bias: {m30_data.get('bias')} | Struktur: {m30_data.get('structure')} | Close: {m30_data.get('close')}
    [M15 Setup] Signal: {m15_data.get('signal')} | RSI: {m15_data.get('rsi')} | Catatan: {m15_data.get('reason')}

    Balas HANYA dalam format JSON valid:
    {{
      "action": "BUY" or "SELL" or "WAIT",
      "confidence": 0-100,
      "market_regime": "TRENDING_UP" or "TRENDING_DOWN" or "RANGING",
      "reasoning": "Alasan singkat"
    }}
    """

    print("🤖 Memanggil Otak AI 1 (DeepSeek)...")
    ai_1 = call_deepseek(prompt_text)
    
    print("🤖 Memanggil Otak AI 2 (OpenRouter Backup/Cross-check)...")
    ai_2 = call_openrouter(prompt_text)

    # Skenario 1: Dua-duanya aktif dan merespon (Sistem Kolaborasi & Silih Séblok)
    if ai_1 and ai_2:
        action_1 = ai_1.get("action")
        action_2 = ai_2.get("action")
        
        print(f"   -> Pendapat AI 1: {action_1} (Conf: {ai_1.get('confidence')}%)")
        print(f"   -> Pendapat AI 2: {action_2} (Conf: {ai_2.get('confidence')}%)")

        # Silih séblok: Lamun béda pamadegan, batalakeun (Jadikeun WAIT demi kaamanan)
        if action_1 != action_2:
            print("🛡️ [BLOCK] Kedua AI berbeda pendapat. Sinyal diblokir demi keamanan (WAIT).")
            return {
                "action": "WAIT",
                "confidence": 50,
                "market_regime": ai_1.get("market_regime", "RANGING"),
                "reasoning": f"Cross-check gagal: AI 1 ({action_1}) tidak sepakat dengan AI 2 ({action_2}).",
                "is_valid": False
            }
        
        # Lamun sapuk, gabungkeun confidence-na
        avg_confidence = int((ai_1.get("confidence", 50) + ai_2.get("confidence", 50)) / 2)
        is_valid = avg_confidence >= AI_MIN_CONFIDENCE and action_1 != "WAIT"
        
        print(f"✅ [AGREEMENT] Kedua AI sepakat pada aksi: {action_1}!")
        return {
            "action": action_1,
            "confidence": avg_confidence,
            "market_regime": ai_1.get("market_regime", "TRENDING_UP"),
            "reasoning": f"Konsensus Multi-AI: {ai_1.get('reasoning')} | Backup: {ai_2.get('reasoning')}",
            "is_valid": is_valid
        }

    # Skenario 2: Salah sahiji AI mogok/down, hiji deui nyandak alih (Silih Bantu / Fallback)
    active_ai = ai_1 or ai_2
    if active_ai:
        print("⚠️ Salah satu AI tidak merespon, berjalan dengan sistem AI tunggal yang aktif.")
        action = active_ai.get("action", "WAIT")
        confidence = int(active_ai.get("confidence", 50))
        is_valid = confidence >= AI_MIN_CONFIDENCE and action != "WAIT"
        active_ai["is_valid"] = is_valid
        return active_ai

    # Skenario 3: Duanana gagal konek, fallback ka Rule Engine lokal
    print("ℹ️ Semua API AI gagal merespon. Beralih ke Rule Engine lokal.")
    signal = m15_data.get("signal", "NO_SIGNAL")
    m30_bias = m30_data.get("bias", "NEUTRAL")
    
    action = "WAIT"
    confidence = 50
    if m30_bias == "BULLISH" and signal == "BUY":
        action, confidence = "BUY", 75
    elif m30_bias == "BEARISH" and signal == "SELL":
        action, confidence = "SELL", 75

    return {
        "action": action,
        "confidence": confidence,
        "market_regime": "RANGING",
        "reasoning": "Fallback Rule Engine lokal (AI API offline).",
        "is_valid": confidence >= AI_MIN_CONFIDENCE and action != "WAIT"
    }

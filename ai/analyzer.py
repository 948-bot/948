"""
XAUUSD AI DERIV BOT
Advanced Multi-AI Pool & Failover Analyzer Module (Maximum Resilience)
"""
import os
import json
import requests
from config.settings import AI_MIN_CONFIDENCE

def call_ai_provider(provider_name: str, prompt_text: str) -> dict:
    """
    Fungsi universal untuk memanggil berbagai provider AI dengan penanganan error mandiri.
    """
    try:
        if provider_name == "deepseek":
            key = os.getenv("DEEPSEEK_API_KEY", "")
            if not key: return None
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt_text}], "temperature": 0.1}
            res = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload, timeout=12)
            if res.status_code == 200:
                content = res.json()["choices"][0]["message"]["content"].replace("```json", "").replace("```", "").strip()
                return json.loads(content)

        elif provider_name == "openrouter":
            key = os.getenv("OPENROUTER_API_KEY", "")
            if not key: return None
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {"model": "deepseek/deepseek-chat", "messages": [{"role": "user", "content": prompt_text}], "temperature": 0.1}
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=12)
            if res.status_code == 200:
                content = res.json()["choices"][0]["message"]["content"].replace("```json", "").replace("```", "").strip()
                return json.loads(content)

        elif provider_name == "openai":
            key = os.getenv("OPENAI_API_KEY", "")
            if not key: return None
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt_text}], "temperature": 0.1}
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=12)
            if res.status_code == 200:
                content = res.json()["choices"][0]["message"]["content"].replace("```json", "").replace("```", "").strip()
                return json.loads(content)

    except Exception as e:
        print(f"⚠️ Provider {provider_name} gagal merespon: {e}")
    
    return None

def evaluate_with_ai(m30_data: dict, m15_data: dict) -> dict:
    """
    Sistem Maksimal: Menggunakan Pool AI bergilir (DeepSeek -> OpenRouter -> OpenAI).
    Saling bantu (Failover) jika salah satu down, dan saling cross-check jika lebih dari satu aktif.
    """
    prompt_text = f"""
    Anda adalah bagian dari Komite AI Quantitative Analyst XAUUSD.
    Analisis data berikut dan berikan keputusan ketat (BUY, SELL, atau WAIT):
    
    [M30 Context] Bias: {m30_data.get('bias')} | Struktur: {m30_data.get('structure')} | Close: {m30_data.get('close')}
    [M15 Setup] Signal: {m15_data.get('signal')} | RSI: {m15_data.get('rsi')} | Catatan: {m15_data.get('reason')}

    Balas HANYA dalam format JSON valid tanpa teks tambahan:
    {{
      "action": "BUY" or "SELL" or "WAIT",
      "confidence": 0-100,
      "market_regime": "TRENDING_UP" or "TRENDING_DOWN" or "RANGING",
      "reasoning": "Alasan singkat"
    }}
    """

    # Daftar antrean prioritas AI (AI Pool)
    pool_providers = ["deepseek", "openrouter", "openai"]
    active_responses = {}

    print("🤖 Memindai dan memanggil AI Pool (Sistem Rotasi & Silih Bantu)...")
    for provider in pool_providers:
        print(f"   -> Mencoba menghubungi: {provider.upper()}...")
        result = call_ai_provider(provider, prompt_text)
        if result and "action" in result:
            active_responses[provider] = result
            print(f"   ✅ {provider.upper()} berhasil merespon! (Aksi: {result.get('action')})")
        else:
            print(f"   ❌ {provider.upper()} offline atau tidak merespon, melewati ke cadangan...")

    # Skenario A: Jika ada 2 atau lebih AI yang merespon (Lakukan Cross-Check / Silih Séblok)
    if len(active_responses) >= 2:
        providers_list = list(active_responses.keys())
        ai_1_name, ai_2_name = providers_list[0], providers_list[1]
        res_1, res_2 = active_responses[ai_1_name], active_responses[ai_2_name]
        
        action_1 = res_1.get("action")
        action_2 = res_2.get("action")
        
        print(f"🛡️ [CROSS-CHECK] Membandingkan {ai_1_name.upper()} ({action_1}) dengan {ai_2_name.upper()} ({action_2})...")

        # Jika berbeda pendapat, blokir jadi WAIT demi keamanan
        if action_1 != action_2:
            print("🛡️ [BLOCK] Perbedaan pendapat terdeteksi antar AI. Sinyal diblokir (WAIT).")
            return {
                "action": "WAIT",
                "confidence": 50,
                "market_regime": res_1.get("market_regime", "RANGING"),
                "reasoning": f"Cross-check gagal: {ai_1_name} ({action_1}) tidak sepakat dengan {ai_2_name} ({action_2}).",
                "is_valid": False
            }
        
        # Jika sepakat, gabungkan nilai confidence
        avg_confidence = int((res_1.get("confidence", 50) + res_2.get("confidence", 50)) / 2)
        is_valid = avg_confidence >= AI_MIN_CONFIDENCE and action_1 != "WAIT"
        
        print(f"✅ [AGREEMENT] Multi-AI sepakat pada aksi: {action_1}!")
        return {
            "action": action_1,
            "confidence": avg_confidence,
            "market_regime": res_1.get("market_regime", "TRENDING_UP"),
            "reasoning": f"Konsensus ({ai_1_name} & {ai_2_name}): {res_1.get('reasoning')}",
            "is_valid": is_valid
        }

    # Skenario B: Jika hanya 1 AI yang merespon (Sistem Fallback / Silih Bantu Jalan)
    elif len(active_responses) == 1:
        provider_name, res = list(active_responses.items())[0]
        print(f"⚠️ Hanya {provider_name.upper()} yang aktif. Melanjutkan dengan AI tunggal.")
        action = res.get("action", "WAIT")
        confidence = int(res.get("confidence", 50))
        is_valid = confidence >= AI_MIN_CONFIDENCE and action != "WAIT"
        res["is_valid"] = is_valid
        return res

    # Skenario C: Semua API AI gagal total, fallback ke Rule Engine lokal
    print("ℹ️ Semua API AI dalam pool offline/gagal merespon. Beralih ke Rule Engine lokal.")
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
        "reasoning": "Fallback Rule Engine lokal (Semua AI API offline).",
        "is_valid": confidence >= AI_MIN_CONFIDENCE and action != "WAIT"
    }

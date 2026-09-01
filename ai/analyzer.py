"""
XAUUSD AI DERIV BOT
Advanced AI Analyzer Module (Support DeepSeek / OpenRouter / OpenAI)
"""
import os
import json
import requests
from config.settings import AI_MIN_CONFIDENCE

def evaluate_with_ai(m30_data: dict, m15_data: dict) -> dict:
    """
    Mengevaluasi kondisi pasar menggunakan AI LLM (DeepSeek/OpenRouter/OpenAI) 
    jika API key tersedia. Jika tidak ada API key, otomatis menggunakan Rule Engine lokal.
    """
    # Cek API Key mana yang aktif (Utamakan DeepSeek atau OpenRouter)
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    # Prompt instruksi untuk AI
    prompt_text = f"""
    Anda adalah AI Quantitative Analyst profesional khusus XAUUSD (Gold).
    Analisis data teknikal berikut dan berikan keputusan ketat (BUY, SELL, atau WAIT):
    
    [TIMEFRAME M30 (Konteks Makro)]
    - Bias: {m30_data.get('bias')}
    - Struktur: {m30_data.get('structure')}
    - Harga Close: {m30_data.get('close')}
    - EMA20: {m30_data.get('ema_20')} | EMA50: {m30_data.get('ema_50')}

    [TIMEFRAME M15 (Setup Entry)]
    - Signal Sinyal: {m15_data.get('signal')}
    - Struktur M15: {m15_data.get('structure')}
    - RSI 14: {m15_data.get('rsi')}
    - Catatan: {m15_data.get('reason')}

    Berikan balasan HANYA dalam format JSON valid tanpa teks tambahan di luar JSON:
    {{
      "action": "BUY" atau "SELL" atau "WAIT",
      "confidence": angka 0 sampai 100,
      "market_regime": "TRENDING_UP" atau "TRENDING_DOWN" atau "RANGING",
      "reasoning": "Alasan singkat dalam bahasa Indonesia"
    }}
    """

    # 1. COBA GUNAKAN DEEPSEEK API (Paling direkomendasikan untuk trading & analisis data)
    if deepseek_key:
        try:
            headers = {
                "Authorization": f"Bearer {deepseek_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt_text}],
                "temperature": 0.1
            }
            response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                result_content = response.json()["choices"][0]["message"]["content"]
                # Bersihkan format markdown block jika ada
                clean_json = result_content.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_json)
                
                action = parsed.get("action", "WAIT")
                confidence = int(parsed.get("confidence", 50))
                is_valid = confidence >= AI_MIN_CONFIDENCE and action != "WAIT"
                parsed["is_valid"] = is_valid
                print("🧠 [AI SUCCESS] Analisis berhasil diproses oleh DeepSeek AI.")
                return parsed
        except Exception as e:
            print(f"⚠️ Gagal menghubungi DeepSeek API, beralih ke fallback: {e}")

    # 2. COBA GUNAKAN OPENROUTER API (Bisa akses Claude/GPT/DeepSeek sekaligus)
    if openrouter_key:
        try:
            headers = {
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "deepseek/deepseek-chat", # Bisa diganti Claude atau GPT-4o
                "messages": [{"role": "user", "content": prompt_text}],
                "temperature": 0.1
            }
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                result_content = response.json()["choices"][0]["message"]["content"]
                clean_json = result_content.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_json)
                
                action = parsed.get("action", "WAIT")
                confidence = int(parsed.get("confidence", 50))
                is_valid = confidence >= AI_MIN_CONFIDENCE and action != "WAIT"
                parsed["is_valid"] = is_valid
                print("🧠 [AI SUCCESS] Analisis berhasil diproses oleh OpenRouter.")
                return parsed
        except Exception as e:
            print(f"⚠️ Gagal menghubungi OpenRouter API: {e}")

    # 3. FALLBACK KE RULE ENGINE (Jika tidak ada API Key yang diisi di GitHub Secrets)
    print("ℹ️ Menggunakan Smart Rule Engine lokal (AI API Key tidak terdeteksi).")
    signal = m15_data.get("signal", "NO_SIGNAL")
    m30_bias = m30_data.get("bias", "NEUTRAL")
    rsi = m15_data.get("rsi", 50)

    action = "WAIT"
    confidence = 50
    regime = "RANGING"
    reasoning = "Kondisi market netral atau belum memenuhi validasi penuh."

    if m30_bias == "BULLISH" and signal == "BUY":
        action = "BUY"
        confidence = 85 if 50 <= rsi <= 65 else 75
        regime = "TRENDING_UP"
        reasoning = "Struktur Bullish M30 dan M15 selaras (Rule Engine Mode)."
    elif m30_bias == "BEARISH" and signal == "SELL":
        action = "SELL"
        confidence = 85 if 35 <= rsi <= 50 else 75
        regime = "TRENDING_DOWN"
        reasoning = "Struktur Bearish M30 dan M15 selaras (Rule Engine Mode)."

    is_valid = confidence >= AI_MIN_CONFIDENCE and action != "WAIT"

    return {
        "action": action,
        "confidence": confidence,
        "market_regime": regime,
        "reasoning": reasoning,
        "is_valid": is_valid
    }

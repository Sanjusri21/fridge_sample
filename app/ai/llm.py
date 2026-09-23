"""
Optional External LLM Integration for ALINA.
Supports optional Gemini or OpenAI APIs via environment configuration.
If unconfigured or offline, seamlessly yields None so local deterministic logic handles the request.
"""

from typing import Optional, Dict, Any
import requests
from app.config.settings import settings, logger


def get_llm_response(prompt: str, context: Optional[str] = None) -> Optional[str]:
    """
    Attempts to query configured external LLM.
    Returns generated text if successful, or None if disabled/failed.
    """
    provider = (settings.AI_PROVIDER or "none").lower()
    api_key = settings.AI_API_KEY

    if provider == "none" or not api_key:
        return None

    system_prompt = (
        "You are ALINA, a helpful AI smart fridge voice assistant. "
        "Your mission is to help reduce food waste, monitor expiry dates, "
        "and suggest recipes using ingredients closest to expiry. "
        "Keep responses brief, conversational, and friendly (1-3 sentences)."
    )
    if context:
        system_prompt += f"\nCurrent Fridge State:\n{context}"

    try:
        if provider == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 150,
                "temperature": 0.7,
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                logger.warning("OpenAI API returned status %s: %s", resp.status_code, resp.text)
                return None

        elif provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": f"{system_prompt}\nUser query: {prompt}"}
                        ]
                    }
                ]
            }
            resp = requests.post(url, json=payload, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
            else:
                logger.warning("Gemini API returned status %s: %s", resp.status_code, resp.text)
                return None

    except Exception as e:
        logger.warning("External LLM request failed: %s. Falling back to local assistant.", e)
        return None

    return None

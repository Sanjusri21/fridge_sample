"""
Voice Input (STT) Listener for ALINA.
Uses SpeechRecognition with Google Speech Recognition.
Handles microphone device absence or errors gracefully with text input fallback.
"""

from typing import Optional, Dict, Any
from app.config.settings import logger

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False


def check_microphone_available() -> Dict[str, Any]:
    """Tests if microphone input is available on the machine."""
    if not SR_AVAILABLE:
        return {
            "available": False,
            "message": "SpeechRecognition package not installed. Text input available."
        }

    try:
        mics = sr.Microphone.list_microphone_names()
        if mics and len(mics) > 0:
            return {
                "available": True,
                "count": len(mics),
                "message": f"Microphone detected ({len(mics)} audio devices found)."
            }
        return {
            "available": False,
            "message": "No microphone hardware detected. Text input available."
        }
    except Exception as e:
        logger.warning("Microphone check failed: %s", e)
        return {
            "available": False,
            "message": f"Microphone access error: {str(e)}. Text input available."
        }


def listen(timeout: int = 5, phrase_time_limit: int = 7) -> str:
    """
    Captures voice input from the default microphone and converts to text.
    Returns lowercase string, or empty string if silent/failed.
    """
    if not SR_AVAILABLE:
        logger.warning("SpeechRecognition not available.")
        return ""

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    try:
        with sr.Microphone() as source:
            print("\n🎤 ALINA is listening... (Speak now)")
            recognizer.adjust_for_ambient_noise(source, duration=0.6)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        print("🔄 Recognizing speech...")
        text = recognizer.recognize_google(audio).strip().lower()
        print(f"👤 You: {text}")
        return text

    except sr.WaitTimeoutError:
        logger.info("Listening timed out without speech input.")
        return ""
    except sr.UnknownValueError:
        logger.info("Speech was unintelligible.")
        return ""
    except Exception as e:
        logger.warning("Voice recognition encountered an issue: %s", e)
        return ""

"""
Voice Output (TTS) Engine for ALINA.
Uses pyttsx3 (SAPI5 on Windows) with an automated fallback to
Windows PowerShell System.Speech.Synthesis so speech never fails.
Always prints to console and returns message string for UI.
"""

import os
import sys
import subprocess
import threading
from typing import Dict, Any, Optional

from app.config.settings import settings, logger

_tts_engine = None
_tts_lock = threading.Lock()
_pyttsx3_usable = True


def _init_pyttsx3():
    """Attempts to initialize pyttsx3 with Windows SAPI5."""
    global _tts_engine, _pyttsx3_usable
    try:
        import pyttsx3
        engine = pyttsx3.init(driverName="sapi5" if os.name == "nt" else None)
        engine.setProperty("rate", settings.VOICE_RATE)
        engine.setProperty("volume", settings.VOICE_VOLUME)
        _tts_engine = engine
        _pyttsx3_usable = True
        logger.info("pyttsx3 TTS engine initialized successfully.")
    except Exception as e:
        logger.warning("pyttsx3 initialization failed: %s. Using PowerShell TTS fallback.", e)
        _pyttsx3_usable = False
        _tts_engine = None


# Initialize on load
_init_pyttsx3()


def _speak_powershell(text: str):
    """Fallback Windows TTS using built-in System.Speech.Synthesis via PowerShell."""
    try:
        clean_text = text.replace("'", " ").replace('"', ' ').replace("\n", " ")
        ps_cmd = (
            f"Add-Type -AssemblyName System.Speech; "
            f"$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$synth.Rate = 0; "
            f"$synth.Speak('{clean_text}');"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15
        )
    except Exception as e:
        logger.error("PowerShell TTS fallback failed: %s", e)


def speak(text: str, wait: bool = True, async_mode: bool = False) -> str:
    """
    Speaks the given text and prints safely to console.
    Safe and non-crashing regardless of Windows console encoding or audio hardware status.
    """
    try:
        # Safe console print that never crashes on Windows cp1252 consoles
        if hasattr(sys.stdout, "buffer"):
            sys.stdout.buffer.write(f"\n[ALINA]: {text}\n".encode("utf-8", errors="replace"))
            sys.stdout.flush()
        else:
            print(f"\n[ALINA]: {text}")
    except Exception:
        pass

    if not settings.VOICE_ENABLED or not text:
        return text

    def _execute():
        with _tts_lock:
            global _pyttsx3_usable, _tts_engine
            co_init = False
            try:
                # Windows COM initialization for worker threads
                if os.name == "nt":
                    try:
                        import pythoncom
                        pythoncom.CoInitialize()
                        co_init = True
                    except Exception:
                        pass

                spoken = False

                # 1. Try pyttsx3
                if _pyttsx3_usable:
                    try:
                        if _tts_engine is None:
                            _init_pyttsx3()
                        if _tts_engine:
                            _tts_engine.say(text)
                            _tts_engine.runAndWait()
                            spoken = True
                    except Exception as e:
                        logger.warning("pyttsx3 speech failed: %s. Switching to PowerShell fallback.", e)
                        _pyttsx3_usable = False

                # 2. Try PowerShell fallback on Windows
                if not spoken and os.name == "nt":
                    _speak_powershell(text)
            except Exception as e:
                logger.warning("TTS execution error: %s", e)
            finally:
                if co_init:
                    try:
                        import pythoncom
                        pythoncom.CoUninitialize()
                    except Exception:
                        pass

    try:
        if async_mode:
            threading.Thread(target=_execute, daemon=True).start()
        else:
            _execute()
    except Exception as e:
        logger.warning("Failed to start TTS thread: %s", e)

    return text


def check_speaker_available() -> Dict[str, Any]:
    """Returns speaker hardware / TTS availability status."""
    return {
        "available": True,
        "engine": "pyttsx3 (SAPI5)" if _pyttsx3_usable else "PowerShell (System.Speech)",
        "enabled": settings.VOICE_ENABLED
    }
